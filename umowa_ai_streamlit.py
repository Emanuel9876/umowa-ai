import streamlit as st
import re
from PyPDF2 import PdfReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import io
import sqlite3
import json
import hashlib
import os
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib
matplotlib.use('Agg')

st.set_page_config(page_title="Umowa AI", layout="wide")

# Baza danych SQLite
conn = sqlite3.connect("umowa_ai.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS analiza (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT,
    tekst TEXT,
    podsumowanie TEXT,
    score INTEGER,
    timestamp TEXT
)''')
conn.commit()

# Użytkownicy
def load_users():
    if os.path.exists("users.json"):
        with open("users.json", "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open("users.json", "w") as f:
        json.dump(users, f)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

users = load_users()
session_state = st.session_state

if "logged_in" not in session_state:
    session_state.logged_in = False
    session_state.username = ""

if "language" not in session_state:
    session_state.language = "PL"

if "sensitivity" not in session_state:
    session_state.sensitivity = "Średni"

if "custom_keywords" not in session_state:
    session_state.custom_keywords = []

lang_options = {"PL": "Polski", "EN": "English", "DE": "Deutsch"}
translations = {
    "Strona Główna": {"PL": "Strona Główna", "EN": "Home", "DE": "Startseite"},
    "Analiza Umowy": {"PL": "Analiza Umowy", "EN": "Contract Analysis", "DE": "Vertragsanalyse"},
    "Ryzyka": {"PL": "Ryzyka", "EN": "Risks", "DE": "Risiken"},
    "Moje Analizy": {"PL": "Moje Analizy", "EN": "My Analyses", "DE": "Meine Analysen"},
    "Witaj w aplikacji": {"PL": "Witaj w aplikacji", "EN": "Welcome to the app", "DE": "Willkommen in der App"},
    "Twoim asystencie do analizy umów": {"PL": "Twoim asystencie do analizy umów", "EN": "Your contract analysis assistant", "DE": "Ihr Vertragsanalyse-Assistent"},
    "Automatycznie analizujemy dokumenty": {"PL": "Automatycznie analizujemy dokumenty", "EN": "We automatically analyze documents", "DE": "Wir analysieren automatisch Dokumente"},
    "i prezentujemy je w czytelnej formie": {"PL": "i prezentujemy je w czytelnej formie", "EN": "and present them in a clear form", "DE": "und präsentieren sie in klarer Form"},
}

selected_lang = st.sidebar.selectbox("\U0001F310 Wybierz język / Select Language / Sprache wählen", list(lang_options.keys()), format_func=lambda x: lang_options[x])
session_state.language = selected_lang

# Styl nowoczesny z gradientem
st.markdown("""
    <style>
        .stApp {
            background: linear-gradient(to right, #2c3e50, #3498db);
            font-family: 'Segoe UI', sans-serif;
        }
        html, body, [class*="css"] {
            background-color: transparent !important;
            color: #ffffff !important;
        }
        h1, h2, h3, h4, h5, h6, p, div, span, label {
            color: #ffffff !important;
        }
        .top-card {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
        }
        ul {
            list-style-type: disc;
            padding-left: 2rem;
        }
    </style>
""", unsafe_allow_html=True)

if not session_state.logged_in:
    st.sidebar.subheader("\U0001F510 Logowanie / Rejestracja")
    choice = st.sidebar.radio("Wybierz opcję", ["Zaloguj się", "Zarejestruj się"])

    username = st.sidebar.text_input("Login")
    password = st.sidebar.text_input("Hasło", type="password")

    if choice == "Zarejestruj się":
        if st.sidebar.button("Zarejestruj"):
            if username in users:
                st.sidebar.warning("Użytkownik już istnieje.")
            else:
                users[username] = hash_password(password)
                save_users(users)
                st.sidebar.success("Rejestracja zakończona sukcesem. Możesz się zalogować.")

    else:
        if st.sidebar.button("Zaloguj"):
            if username in users and users[username] == hash_password(password):
                session_state.logged_in = True
                session_state.username = username
                st.experimental_rerun()
            else:
                st.sidebar.error("Błędny login lub hasło.")
    st.stop()

# Menu główne z ikonkami
menu_options = [
    ("Strona Główna", "\U0001F3E0"),
    ("Analiza Umowy", "\U0001F4C4"),
    ("Ryzyka", "\u26A0"),
    ("Moje Analizy", "\U0001F4CB")
]
translated_menu = [f"{icon} {translations[label][session_state.language]}" for label, icon in menu_options]
menu_choice = st.sidebar.selectbox("Wybierz opcję", translated_menu)

plain_choice = [label for label, icon in menu_options][translated_menu.index(menu_choice)]

def analyze_risks(text, sensitivity, custom_kw):
    # Przykładowe ryzyka wg kategorii
    base_risks = {
        "Finansowe": ["kara", "opłata", "odszkodowanie", "koszt", "kaucja"],
        "Prawne": ["rozwiązanie", "wypowiedzenie", "kara umowna", "odpowiedzialność", "odstąpienie"],
        "Terminowe": ["zwłoka", "opóźnienie", "termin", "czas", "deadline"]
    }
    # Dodaj custom keywords do kategorii "Niestandardowe"
    if custom_kw:
        base_risks["Niestandardowe"] = custom_kw

    # Modyfikator czułości - wpływa na progi wykrywania
    sensitivity_factor = {"Niski": 0.5, "Średni": 1.0, "Wysoki": 1.5}.get(sensitivity, 1.0)

    found = {}
    text_lower = text.lower()
    for category, keywords in base_risks.items():
        count = 0
        for kw in keywords:
            count += text_lower.count(kw.lower())
        if count * sensitivity_factor >= 1:
            found[category] = int(count * sensitivity_factor)
    return found

def generate_pdf_report(text, summary, risks_found, username):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    c.setFont("Helvetica-Bold", 20)
    c.drawString(72, height - 72, "Raport analizy umowy")

    c.setFont("Helvetica", 12)
    c.drawString(72, height - 100, f"Użytkownik: {username}")
    c.drawString(72, height - 120, f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    c.drawString(72, height - 150, "Podsumowanie:")
    text_object = c.beginText(72, height - 170)
    for line in summary.split('\n'):
        text_object.textLine(line)
    c.drawText(text_object)

    y = height - 300
    c.drawString(72, y, "Wykryte ryzyka:")
    y -= 20
    for cat, count in risks_found.items():
        c.drawString(90, y, f"{cat}: {count}")
        y -= 20

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

def save_analysis_to_db(user, tekst, podsumowanie, score):
    timestamp = datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO analiza (user, tekst, podsumowanie, score, timestamp) 
        VALUES (?, ?, ?, ?, ?)''',
        (user, tekst, podsumowanie, score, timestamp))
    conn.commit()

def load_user_analyses(user):
    cursor.execute('SELECT id, tekst, podsumowanie, score, timestamp FROM analiza WHERE user=? ORDER BY timestamp DESC', (user,))
    return cursor.fetchall()

def summarize_text(text):
    # Proste podsumowanie - wyciąga pierwsze 3 zdania
    sentences = re.split(r'(?<=[.!?]) +', text)
    summary = ' '.join(sentences[:3]) if sentences else ""
    return summary

if plain_choice == "Strona Główna":
    if "start_analysis" not in session_state:
        session_state.start_analysis = False

    if session_state.start_analysis:
        plain_choice = "Analiza Umowy"
        session_state.start_analysis = False
        st.experimental_rerun()

    st.markdown("""
        <div style='text-align: center; padding: 5vh 2vw;'>
            <h1 style='font-size: 4.5em; margin-bottom: 0;'>🤖 UmowaAI</h1>
            <p style='font-size: 1.7em; margin-top: 0;'>Twój osobisty asystent do analizy umów i wykrywania ryzyk</p>
        </div>

        <div class='top-card' style='display: flex; flex-direction: row; justify-content: space-around; flex-wrap: wrap; gap: 2rem; padding: 2rem;'>
            <div style='flex: 1; min-width: 250px; max-width: 400px;'>
                <h2>📄 Analiza Umowy</h2>
                <p>Automatycznie analizujemy umowy PDF i wyciągamy kluczowe informacje.</p>
            </div>
            <div style='flex: 1; min-width: 250px; max-width: 400px;'>
                <h2>⚠️ Wykrywanie Ryzyk</h2>
                <p>Wykrywamy nieoczywiste haczyki i ryzyka w zapisach umownych.</p>
            </div>
            <div style='flex: 1; min-width: 250px; max-width: 400px;'>
                <h2>📊 Twoje Analizy</h2>
                <p>Przeglądaj i porównuj wszystkie swoje wcześniejsze analizy w przejrzysty sposób.</p>
            </div>
        </div>

        <div class='top-card' style='text-align: center; padding: 3rem; margin-top: 3rem;'>
            <h2>🚀 Dlaczego UmowaAI?</h2>
            <ul style='list-style: none; font-size: 1.2em; padding: 0;'>
                <li>✅ Intuicyjny i nowoczesny interfejs</li>
                <li>✅ Wysoka skuteczność wykrywania niekorzystnych zapisów</li>
                <li>✅ Bezpieczeństwo i poufność danych</li>
                <li>✅ Historia wszystkich Twoich analiz</li>
            </ul>
        </div>
    """, unsafe_allow_html=True)

    if st.button("🔍 Rozpocznij analizę teraz"):
        session_state.start_analysis = True
        st.experimental_rerun()

elif plain_choice == "Analiza Umowy":
    st.header("📄 Analiza Umowy")

    # Upload PDF lub wpisanie ręczne
    uploaded_file = st.file_uploader("Wgraj plik PDF z umową", type=["pdf"])
    manual_text = st.text_area("Lub wpisz / wklej treść umowy ręcznie", height=250)

    sensitivity = st.sidebar.selectbox("Czułość wykrywania ryzyk", ["Niski", "Średni", "Wysoki"], index=["Niski", "Średni", "Wysoki"].index(session_state.sensitivity))
    session_state.sensitivity = sensitivity

    custom_kw_input = st.sidebar.text_area("Dodaj własne słowa kluczowe do wykrywania (oddziel przecinkami)", value=", ".join(session_state.custom_keywords))
    if custom_kw_input:
        session_state.custom_keywords = [kw.strip() for kw in custom_kw_input.split(",") if kw.strip()]
    else:
        session_state.custom_keywords = []

    text_to_analyze = ""
    if uploaded_file:
        try:
            pdf = PdfReader(uploaded_file)
            text_to_analyze = ""
            for page in pdf.pages:
                text_to_analyze += page.extract_text() + "\n"
        except Exception as e:
            st.error(f"Błąd podczas odczytu PDF: {e}")

    if manual_text.strip():
        text_to_analyze = manual_text

    if text_to_analyze.strip():
        if st.button("Analizuj umowę"):
            summary = summarize_text(text_to_analyze)
            risks_found = analyze_risks(text_to_analyze, session_state.sensitivity, session_state.custom_keywords)

            # Wyliczenie score jako suma ryzyk
            score = sum(risks_found.values())

            st.subheader("Podsumowanie umowy")
            st.write(summary)

            st.subheader("Wykryte ryzyka")
            if risks_found:
                for cat, count in risks_found.items():
                    st.write(f"- **{cat}:** {count} wystąpień")
                # Wykres słupkowy
                fig, ax = plt.subplots()
                ax.bar(risks_found.keys(), risks_found.values(), color='orange')
                st.pyplot(fig)
            else:
                st.write("Nie wykryto istotnych ryzyk.")

            # Zapis analizy w bazie
            save_analysis_to_db(session_state.username, text_to_analyze, summary, score)
            st.success("Analiza została zapisana.")

            # Eksport PDF i JSON
            pdf_report = generate_pdf_report(text_to_analyze, summary, risks_found, session_state.username)
            st.download_button(label="Pobierz raport PDF", data=pdf_report, file_name="raport_umowa.pdf", mime="application/pdf")

            json_report = json.dumps({
                "user": session_state.username,
                "summary": summary,
                "risks": risks_found,
                "score": score,
                "timestamp": datetime.now().isoformat()
            }, indent=2, ensure_ascii=False)
            st.download_button(label="Pobierz raport JSON", data=json_report, file_name="raport_umowa.json", mime="application/json")
    else:
        st.info("Wgraj plik PDF lub wpisz / wklej tekst umowy, aby rozpocząć analizę.")

elif plain_choice == "Ryzyka":
    st.header("⚠️ Wykrywanie Ryzyk")

    user_text = st.text_area("Wklej tekst umowy do analizy ryzyk", height=300)

    sensitivity = st.sidebar.selectbox("Czułość wykrywania ryzyk", ["Niski", "Średni", "Wysoki"], index=["Niski", "Średni", "Wysoki"].index(session_state.sensitivity))
    session_state.sensitivity = sensitivity

    custom_kw_input = st.sidebar.text_area("Dodaj własne słowa kluczowe do wykrywania (oddziel przecinkami)", value=", ".join(session_state.custom_keywords))
    if custom_kw_input:
        session_state.custom_keywords = [kw.strip() for kw in custom_kw_input.split(",") if kw.strip()]
    else:
        session_state.custom_keywords = []

    if st.button("Analizuj ryzyka"):
        if user_text.strip():
            risks_found = analyze_risks(user_text, session_state.sensitivity, session_state.custom_keywords)
            if risks_found:
                st.write("Wykryte ryzyka wg kategorii:")
                for cat, count in risks_found.items():
                    st.write(f"- **{cat}:** {count} wystąpień")
                # Wykres słupkowy
                fig, ax = plt.subplots()
                ax.bar(risks_found.keys(), risks_found.values(), color='orange')
                st.pyplot(fig)
            else:
                st.write("Nie wykryto istotnych ryzyk.")
        else:
            st.warning("Wprowadź tekst umowy.")

elif plain_choice == "Moje Analizy":
    st.header("📋 Moje Analizy")

    analyses = load_user_analyses(session_state.username)
    if not analyses:
        st.info("Nie masz jeszcze żadnych zapisanych analiz.")
    else:
        for analysis in analyses:
            id_, tekst, podsumowanie, score, timestamp = analysis
            with st.expander(f"Analiza z {timestamp} - Wynik: {score}"):
                st.subheader("Podsumowanie")
                st.write(podsumowanie)
                st.subheader("Treść umowy")
                st.text_area("Umowa", value=tekst, height=200, disabled=True)

    # Prosty sposób na porównanie dwóch analiz
    st.subheader("Porównaj dwie analizy")
    if len(analyses) >= 2:
        options = {f"{a[0]} - {a[4]} (Wynik: {a[3]})": a for a in analyses}
        sel1 = st.selectbox("Wybierz pierwszą analizę", options.keys())
        sel2 = st.selectbox("Wybierz drugą analizę", options.keys())
        if sel1 != sel2:
            a1 = options[sel1]
            a2 = options[sel2]
            st.write("Porównanie wyników:")
            categories = set()
            try:
                risks1 = json.loads(a1[2]) if isinstance(a1[2], str) else {}
            except:
                risks1 = {}
            try:
                risks2 = json.loads(a2[2]) if isinstance(a2[2], str) else {}
            except:
                risks2 = {}
            # Jeśli podsumowanie zawiera ryzyka w JSON to pokazujemy, inaczej puste
            st.write(f"- Analiza 1 wynik: {a1[3]}")
            st.write(f"- Analiza 2 wynik: {a2[3]}")
            # Można rozbudować o wykres porównujący - tutaj tylko liczby
        else:
            st.info("Wybierz dwie różne analizy do porównania.")
    else:
        st.info("Potrzebujesz minimum 2 analizy do porównania.")

# Wylogowanie
with st.sidebar:
    if st.button("🔓 Wyloguj"):
        session_state.logged_in = False
        session_state.username = ""
        st.experimental_rerun()
