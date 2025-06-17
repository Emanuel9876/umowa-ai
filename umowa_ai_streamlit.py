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

# MENU - bez "Strona Główna"
menu_options = [
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

if plain_choice == "Analiza Umowy":
    st.header("📄 Analiza Umowy")

    uploaded_file = st.file_uploader("Wgraj plik PDF z umową", type=["pdf"])
    manual_text = st.text_area("Lub wpisz / wklej treść umowy ręcznie", height=250)

    sensitivity = st.sidebar.selectbox("Czułość wykrywania ryzyk", ["Niski", "Średni", "Wysoki"], index=["Niski", "Średni", "Wysoki"].index(session_state.sensitivity))
    session_state.sensitivity = sensitivity

    custom_keywords_input = st.sidebar.text_area("Dodatkowe słowa kluczowe (oddzielone przecinkami)")
    if custom_keywords_input:
        session_state.custom_keywords = [kw.strip() for kw in custom_keywords_input.split(",") if kw.strip()]
    else:
        session_state.custom_keywords = []

    # Pobierz tekst z PDF jeśli wgrany
    if uploaded_file:
        pdf_reader = PdfReader(uploaded_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() or ""
    else:
        text = manual_text

    if text.strip():
        st.subheader("Wykryte ryzyka:")
        risks_found = analyze_risks(text, sensitivity, session_state.custom_keywords)

        if risks_found:
            for category, count in risks_found.items():
                st.markdown(f"- **{category}**: {count} razy")
        else:
            st.info("Nie wykryto istotnych ryzyk.")

        podsumowanie = summarize_text(text)
        st.subheader("Podsumowanie umowy:")
        st.write(podsumowanie)

        score = sum(risks_found.values())

        # Zapisz analizę
        save_analysis_to_db(session_state.username, text, podsumowanie, score)

        # Pobierz PDF do pobrania
        pdf_buffer = generate_pdf_report(text, podsumowanie, risks_found, session_state.username)
        st.download_button("Pobierz raport PDF", pdf_buffer, file_name="raport_umowa.pdf", mime="application/pdf")

elif plain_choice == "Ryzyka":
    st.header("⚠️ Ryzyka")

    # Przykładowy wykres kołowy ryzyk
    example_data = {"Finansowe": 10, "Prawne": 5, "Terminowe": 7}
    fig, ax = plt.subplots()
    ax.pie(example_data.values(), labels=example_data.keys(), autopct='%1.1f%%', startangle=90)
    ax.axis('equal')
    st.pyplot(fig)

elif plain_choice == "Moje Analizy":
    st.header("🗂️ Moje Analizy")

    analyses = load_user_analyses(session_state.username)
    if not analyses:
        st.info("Nie znaleziono żadnych analiz.")
    else:
        for id_, tekst, podsumowanie, score, timestamp in analyses:
            with st.expander(f"Analiza z {timestamp[:19]} - Ryzyka: {score}"):
                st.write("**Podsumowanie:**")
                st.write(podsumowanie)
                st.write("**Treść umowy:**")
                st.write(tekst)

