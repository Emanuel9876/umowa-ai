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
    base_risks = {
        "Finansowe": ["kara", "opłata", "odszkodowanie", "koszt", "kaucja"],
        "Prawne": ["rozwiązanie", "wypowiedzenie", "kara umowna", "odpowiedzialność", "odstąpienie"],
        "Terminowe": ["zwłoka", "opóźnienie", "termin", "czas", "deadline"]
    }
    if custom_kw:
        base_risks["Niestandardowe"] = custom_kw

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
    sentences = re.split(r'(?<=[.!?]) +', text)
    summary = ' '.join(sentences[:3]) if sentences else ""
    return summary

if plain_choice == "Strona Główna":
    # PRZYWRÓCONA STRONA GŁÓWNA, ale bez przycisku "Rozpocznij analizę teraz"
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
                <h2>📊 Statystyki i Historia</h2>
                <p>Przeglądaj swoje wcześniejsze analizy i monitoruj trendy ryzyk.</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

elif plain_choice == "Analiza Umowy":
    st.header(translations["Analiza Umowy"][session_state.language])

    uploaded_file = st.file_uploader("Wgraj plik PDF lub wklej tekst umowy", type=["pdf", "txt"], accept_multiple_files=False)

    input_text = ""
    if uploaded_file is not None:
        if uploaded_file.type == "application/pdf":
            pdf_reader = PdfReader(uploaded_file)
            for page in pdf_reader.pages:
                input_text += page.extract_text() + "\n"
        else:
            input_text = uploaded_file.getvalue().decode("utf-8")

    if not input_text:
        input_text = st.text_area("Lub wklej tekst umowy tutaj", height=300)

    session_state.sensitivity = st.selectbox("Wybierz czułość wykrywania ryzyk", ["Niski", "Średni", "Wysoki"], index=["Niski", "Średni", "Wysoki"].index(session_state.sensitivity))
    custom_kw_input = st.text_input("Dodaj własne słowa kluczowe (oddziel przecinkami)", value=",".join(session_state.custom_keywords))
    session_state.custom_keywords = [x.strip() for x in custom_kw_input.split(",") if x.strip()]

    if input_text:
        summary = summarize_text(input_text)
        risks_found = analyze_risks(input_text, session_state.sensitivity, session_state.custom_keywords)
        score = sum(risks_found.values())

        st.subheader("Podsumowanie umowy")
        st.write(summary)

        st.subheader("Wykryte ryzyka")
        if risks_found:
            for k, v in risks_found.items():
                st.write(f"- {k}: {v}")
        else:
            st.write("Nie wykryto istotnych ryzyk.")

        if st.button("Pobierz raport PDF"):
            pdf_buffer = generate_pdf_report(input_text, summary, risks_found, session_state.username)
            st.download_button("Pobierz raport PDF", pdf_buffer, file_name="raport_umowa.pdf", mime="application/pdf")

        # Zapis analizy w bazie
        save_analysis_to_db(session_state.username, input_text, summary, score)

elif plain_choice == "Ryzyka":
    st.header(translations["Ryzyka"][session_state.language])
    user_analyses = load_user_analyses(session_state.username)
    if not user_analyses:
        st.write("Brak wcześniejszych analiz.")
    else:
        scores = [a[3] for a in user_analyses]
        timestamps = [datetime.fromisoformat(a[4]) for a in user_analyses]
        plt.figure(figsize=(10, 5))
        sns.lineplot(x=timestamps, y=scores)
        plt.title("Trend wykrytych ryzyk w czasie")
        plt.xlabel("Data")
        plt.ylabel("Liczba ryzyk")
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(plt)

elif plain_choice == "Moje Analizy":
    st.header(translations["Moje Analizy"][session_state.language])
    analyses = load_user_analyses(session_state.username)
    if not analyses:
        st.write("Nie znaleziono żadnych analiz.")
    else:
        for a in analyses:
            st.markdown(f"### Analiza z {a[4][:19]}")
            st.write(f"Podsumowanie: {a[2]}")
            st.write(f"Liczba ryzyk: {a[3]}")
            if st.button(f"Pokaż pełny tekst #{a[0]}"):
                st.write(a[1])

# Zamknięcie połączenia z bazą przy zamknięciu aplikacji
# (Streamlit sam kończy proces, więc nie jest to konieczne)
