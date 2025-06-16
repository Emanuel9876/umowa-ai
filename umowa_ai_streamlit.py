import streamlit as st
import re
from PyPDF2 import PdfReader
from reportlab.pdfgen import canvas
import io
import sqlite3
import json
import hashlib
import os
from datetime import datetime, date
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib
matplotlib.use('Agg')

st.set_page_config(page_title="Umowa AI", layout="wide")

# Funkcja tłumacząca
translations = {
    "Login": {"PL": "Login", "EN": "Username", "DE": "Benutzername"},
    "Hasło": {"PL": "Hasło", "EN": "Password", "DE": "Passwort"},
    "Zaloguj się": {"PL": "Zaloguj się", "EN": "Log In", "DE": "Anmelden"},
    "Zarejestruj się": {"PL": "Zarejestruj się", "EN": "Register", "DE": "Registrieren"},
    "Rozpocznij analizę teraz": {"PL": "Rozpocznij analizę teraz", "EN": "Start analysis now", "DE": "Analyse jetzt starten"},
    "Wybierz sposób analizy:": {"PL": "Wybierz sposób analizy:", "EN": "Choose analysis method:", "DE": "Analysemethode wählen:"},
    "Prześlij PDF": {"PL": "Prześlij PDF", "EN": "Upload PDF", "DE": "PDF hochladen"},
    "Wklej tekst": {"PL": "Wklej tekst", "EN": "Paste text", "DE": "Text einfügen"},
    "Podsumowanie:": {"PL": "Podsumowanie:", "EN": "Summary:", "DE": "Zusammenfassung:"},
    "Zapisz analizę": {"PL": "Zapisz analizę", "EN": "Save analysis", "DE": "Analyse speichern"},
    "Usuń analizę": {"PL": "Usuń analizę", "EN": "Delete analysis", "DE": "Analyse löschen"},
    "Pozostało analiz dzisiaj:": {"PL": "Pozostało analiz dzisiaj:", "EN": "Analyses remaining today:", "DE": "Verbleibende Analysen heute:"},
    "Osiągnięto dzienny limit 2 analiz. Spróbuj jutro.": {
        "PL": "Osiągnięto dzienny limit 2 analiz. Spróbuj jutro.",
        "EN": "Daily limit of 2 analyses reached. Try again tomorrow.",
        "DE": "Tägliches Limit von 2 Analysen erreicht. Versuche es morgen erneut."
    },
    "Wprowadź lub załaduj tekst umowy.": {
        "PL": "Wprowadź lub załaduj tekst umowy.",
        "EN": "Enter or upload the contract text.",
        "DE": "Vertragstext eingeben oder hochladen."
    },
    "Logowanie / Rejestracja": {"PL": "Logowanie / Rejestracja", "EN": "Login / Register", "DE": "Anmeldung / Registrierung"},
    "Wybierz opcję": {"PL": "Wybierz opcję", "EN": "Choose option", "DE": "Option wählen"}
}

def tr(phrase):
    return translations.get(phrase, {}).get(session_state.language, phrase)

# Stan sesji i język
session_state = st.session_state
if "language" not in session_state:
    session_state.language = "PL"
lang_options = {"PL": "Polski", "EN": "English", "DE": "Deutsch"}
selected_lang = st.sidebar.selectbox("\U0001F310 Wybierz język / Select Language / Sprache wählen", list(lang_options.keys()), format_func=lambda x: lang_options[x])
session_state.language = selected_lang

# Baza danych
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

# Zarządzanie użytkownikami
users = {}
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
if "logged_in" not in session_state:
    session_state.logged_in = False
    session_state.username = ""

if not session_state.logged_in:
    st.sidebar.subheader(tr("Logowanie / Rejestracja"))
    choice = st.sidebar.radio(tr("Wybierz opcję"), [tr("Zaloguj się"), tr("Zarejestruj się")])

    username = st.sidebar.text_input(tr("Login"))
    password = st.sidebar.text_input(tr("Hasło"), type="password")

    if choice == tr("Zarejestruj się"):
        if st.sidebar.button(tr("Zarejestruj się")):
            if username in users:
                st.sidebar.warning("Użytkownik już istnieje.")
            else:
                users[username] = hash_password(password)
                save_users(users)
                st.sidebar.success("Rejestracja zakończona sukcesem. Możesz się zalogować.")
    else:
        if st.sidebar.button(tr("Zaloguj się")):
            if username in users and users[username] == hash_password(password):
                session_state.logged_in = True
                session_state.username = username
                st.rerun()
            else:
                st.sidebar.error("Błędny login lub hasło.")
    st.stop()

# --- ANALIZA ---

st.header(tr("Rozpocznij analizę teraz"))

# Sprawdzenie dziennego limitu analiz
cursor.execute("SELECT COUNT(*) FROM analiza WHERE user=? AND date(timestamp)=?", (session_state.username, str(date.today())))
count_today = cursor.fetchone()[0]
limit_left = max(0, 2 - count_today)
st.info(f"{tr('Pozostało analiz dzisiaj:')} {limit_left}")
if limit_left == 0:
    st.warning(tr("Osiągnięto dzienny limit 2 analiz. Spróbuj jutro."))
    st.stop()

# Wybór metody analizy
method = st.radio(tr("Wybierz sposób analizy:"), [tr("Wklej tekst"), tr("Prześlij PDF")])
text = ""

if method == tr("Wklej tekst"):
    text = st.text_area(tr("Wprowadź lub załaduj tekst umowy."))
elif method == tr("Prześlij PDF"):
    uploaded_file = st.file_uploader(tr("Prześlij PDF"), type="pdf")
    if uploaded_file:
        reader = PdfReader(uploaded_file)
        text = "\n".join(page.extract_text() for page in reader.pages if page.extract_text())

# Analiza
if text:
    summary = ""
    risk_keywords = ["kara", "odpowiedzialność", "ryzyko", "opóźnienie", "grzywna"]
    score = sum(1 for word in risk_keywords if word in text.lower())
    summary = f"Zidentyfikowano {score} potencjalnych punktów ryzyka."

    st.subheader(tr("Podsumowanie:"))
    st.write(summary)

    if st.button(tr("Zapisz analizę")):
        timestamp = datetime.now().isoformat()
        cursor.execute("INSERT INTO analiza (user, tekst, podsumowanie, score, timestamp) VALUES (?, ?, ?, ?, ?)",
                       (session_state.username, text, summary, score, timestamp))
        conn.commit()
        st.success("Analiza została zapisana.")
