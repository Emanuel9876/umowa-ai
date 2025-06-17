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

# Nowy styl jasnoniebieski z gradientem i nowoczesny układ dla strony głównej
st.markdown("""
    <style>
        /* Body and background gradient */
        .stApp {
            background: linear-gradient(135deg, #a1c4fd, #c2e9fb);
            color: #0a1e3f;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            min-height: 100vh;
            padding-bottom: 3rem;
        }
        /* Sidebar background */
        .css-1d391kg {
            background-color: #f0f8ff !important;
            color: #0a1e3f !important;
        }
        /* Headers and text */
        h1, h2, h3, h4, h5, h6, p, div, span, label {
            color: #0a1e3f !important;
        }
        /* Card style for homepage */
        .top-card {
            background: white;
            border-radius: 15px;
            padding: 40px 50px;
            margin: 40px auto;
            max-width: 700px;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
            text-align: center;
            line-height: 1.6;
        }
        /* List style */
        ul {
            list-style-type: disc;
            padding-left: 1.5rem;
            text-align: left;
            max-width: 600px;
            margin: 20px auto 0 auto;
            font-size: 1.2em;
            color: #0a1e3f;
        }
        /* Stronger buttons style */
        div.stButton > button:first-child {
            background-color: #3a86ff;
            color: white;
            border-radius: 8px;
            padding: 0.5em 1.5em;
            border: none;
            font-weight: 600;
            transition: background-color 0.3s ease;
        }
        div.stButton > button:first-child:hover {
            background-color: #265ecf;
            cursor: pointer;
        }
        /* Text area styling */
        textarea {
            background-color: #e8f0fe !important;
            color: #0a1e3f !important;
            border-radius: 8px !important;
            border: 1px solid #a1c4fd !important;
            font-size: 1em !important;
            padding: 10px !important;
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

# Menu główne z ikonami
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
    st.markdown(f"""
        <div class="top-card">
            <h1 style='font-size: 4.5em; margin-bottom: 0;'>🤖 UmowaAI</h1>
            <p style='font-size: 1.7em; margin-top: 0; font-weight: 600;'>Twój asystent do analizy umów</p>
            <ul>
                <li>Automatycznie analizujemy dokumenty</li>
                <li>Prezentujemy najważniejsze informacje w czytelnej formie</li>
                <li>Pomagamy identyfikować ryzyka i pułapki prawne</li>
                <li>Przechowujemy historię Twoich analiz</li>
            </ul>
        </div>
    """, unsafe_allow_html=True)

elif plain_choice == "Analiza Umowy":
    st.header(translations["Analiza Umowy"][session_state.language])
    uploaded_file = st.file_uploader("Wgraj plik PDF z umową", type=["pdf"])
    if uploaded_file is not None:
        pdf_reader = PdfReader(uploaded_file)
        full_text = ""
        for page in pdf_reader.pages:
            full_text += page.extract_text() + "\n"

        st.text_area("Tekst umowy", full_text, height=300)

        sensitivity = st.selectbox("Wybierz czułość analizy", ["Niski", "Średni", "Wysoki"], index=1)
        session_state.sensitivity = sensitivity

        custom_kw = st.text_input("Dodaj własne słowa kluczowe (oddziel przecinkami)", "")

        if st.button("Analizuj umowę"):
            keywords = [kw.strip() for kw in custom_kw.split(",")] if custom_kw else []
            risks_found = analyze_risks(full_text, sensitivity, keywords)
            summary = summarize_text(full_text)

            score = sum(risks_found.values())
            st.subheader("Podsumowanie analizy")
            st.write(summary)

            st.subheader("Wykryte ryzyka")
            if risks_found:
                for cat, count in risks_found.items():
                    st.write(f"- **{cat}:** {count}")
            else:
                st.write("Nie wykryto istotnych ryzyk.")

            save_analysis_to_db(session_state.username, full_text, summary, score)

            buffer = generate_pdf_report(full_text, summary, risks_found, session_state.username)
            st.download_button("Pobierz raport PDF", buffer, file_name="raport_umowy.pdf", mime="application/pdf")

elif plain_choice == "Ryzyka":
    st.header(translations["Ryzyka"][session_state.language])
    st.write("Tutaj możesz ustawić czułość wykrywania ryzyk oraz dodać własne słowa kluczowe.")

    sensitivity = st.selectbox("Czułość wykrywania", ["Niski", "Średni", "Wysoki"], index=["Niski", "Średni", "Wysoki"].index(session_state.sensitivity))
    session_state.sensitivity = sensitivity

    custom_kw = st.text_area("Własne słowa kluczowe (oddziel przecinkami)", ", ".join(session_state.custom_keywords))
    if st.button("Zapisz słowa kluczowe"):
        session_state.custom_keywords = [kw.strip() for kw in custom_kw.split(",") if kw.strip()]
        st.success("Słowa kluczowe zapisane.")

elif plain_choice == "Moje Analizy":
    st.header(translations["Moje Analizy"][session_state.language])
    analyses = load_user_analyses(session_state.username)
    if analyses:
        for (id_, tekst, podsumowanie, score, timestamp) in analyses:
            with st.expander(f"Analiza z {timestamp[:19]} (Ocena ryzyka: {score})"):
                st.write(podsumowanie)
                st.write("Fragment umowy:")
                st.text_area("Tekst umowy", tekst[:1000] + ("..." if len(tekst) > 1000 else ""), height=200)
    else:
        st.info("Brak zapisanych analiz.")
