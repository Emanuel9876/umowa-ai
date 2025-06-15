import streamlit as st
import re
from PyPDF2 import PdfReader
from reportlab.pdfgen import canvas
import io
import sqlite3
import json
import hashlib
import os
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib
import openai
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
matplotlib.use('Agg')

# Konfiguracja GPT i emaili
openai.api_key = os.getenv("OPENAI_API_KEY")
EMAIL_SENDER = "twoj@email.com"
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

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

def is_premium(user):
    premium_until = users.get(user, {}).get("premium_until")
    if premium_until:
        return datetime.fromisoformat(premium_until) > datetime.now()
    return False

def can_analyze(user):
    cursor.execute("SELECT COUNT(*) FROM analiza WHERE user = ? AND timestamp > ?", (user, (datetime.now() - timedelta(days=30)).isoformat()))
    count = cursor.fetchone()[0]
    return is_premium(user) or count < 3

def send_email(to, subject, body):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = to
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        print(f"Błąd wysyłki maila: {e}")

def analyze_with_gpt(text):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Jesteś prawnikiem. Rozpoznaj typ umowy, analizuj ryzyka, podsumuj umowę."},
                {"role": "user", "content": text}
            ],
            max_tokens=1000,
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Błąd analizy AI: {e}"

users = load_users()
session_state = st.session_state

if "logged_in" not in session_state:
    session_state.logged_in = False
    session_state.username = ""

if "language" not in session_state:
    session_state.language = "PL"

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
                users[username] = {
                    "password": hash_password(password),
                    "premium_until": (datetime.now() + timedelta(days=7)).isoformat()
                }
                save_users(users)
                st.sidebar.success("Rejestracja zakończona sukcesem. Możesz się zalogować.")

    else:
        if st.sidebar.button("Zaloguj"):
            user = users.get(username)
            if user and user.get("password") == hash_password(password):
                session_state.logged_in = True
                session_state.username = username
                st.rerun()
            else:
                st.sidebar.error("Błędny login lub hasło.")
    st.stop()

menu_options = [
    ("Strona Główna", "\U0001F3E0"),
    ("Analiza Umowy", "\U0001F4C4"),
    ("Ryzyka", "\u26A0"),
    ("Moje Analizy", "\U0001F4CB")
]
translated_menu = [f"{icon} {translations[label][session_state.language]}" for label, icon in menu_options]
menu_choice = st.sidebar.selectbox("Wybierz opcję", translated_menu)
plain_choice = [label for label, icon in menu_options][translated_menu.index(menu_choice)]

if plain_choice == "Analiza Umowy":
    st.header("Analiza AI")
    option = st.radio("Wybierz sposób analizy:", ["Prześlij PDF", "Wklej tekst"])

    if option == "Prześlij PDF":
        uploaded_file = st.file_uploader("Prześlij plik PDF do analizy", type="pdf")
        if uploaded_file:
            reader = PdfReader(uploaded_file)
            full_text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
    else:
        full_text = st.text_area("Wklej tekst umowy tutaj:", height=300)

    if (option == "Wklej tekst" or uploaded_file) and full_text.strip():
        if not can_analyze(session_state.username):
            st.error("Limit darmowych analiz miesięcznych został wyczerpany. Przejdź na wersję premium.")
        else:
            if st.checkbox("Użyj analizy GPT-4 (AI)"):
                with st.spinner("Analizuję z pomocą GPT-4..."):
                    ai_summary = analyze_with_gpt(full_text)
                st.text_area("AI Podsumowanie:", ai_summary, height=200)
            else:
                ai_summary = full_text[:500] + "..."
                st.text_area("Podsumowanie:", ai_summary, height=150)

            score = len(full_text) % 10
            if st.button("Zapisz analizę"):
                cursor.execute("INSERT INTO analiza (user, tekst, podsumowanie, score, timestamp) VALUES (?, ?, ?, ?, ?)",
                               (session_state.username, full_text, ai_summary, score, datetime.now().isoformat()))
                conn.commit()
                st.success("Analiza zapisana.")
                send_email("adres@usera.com", "Twoja analiza AI", ai_summary)
