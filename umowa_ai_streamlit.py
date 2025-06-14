import streamlit as st
import re
from PyPDF2 import PdfReader
from reportlab.pdfgen import canvas
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
    "Logowanie / Rejestracja": {"PL": "Logowanie / Rejestracja", "EN": "Login / Register", "DE": "Anmelden / Registrieren"},
    "Zaloguj się": {"PL": "Zaloguj się", "EN": "Login", "DE": "Anmelden"},
    "Zarejestruj się": {"PL": "Zarejestruj się", "EN": "Register", "DE": "Registrieren"},
    "Login": {"PL": "Login", "EN": "Login", "DE": "Login"},
    "Hasło": {"PL": "Hasło", "EN": "Password", "DE": "Passwort"},
    "Rejestracja zakończona sukcesem. Możesz się zalogować.": {"PL": "Rejestracja zakończona sukcesem. Możesz się zalogować.", "EN": "Registration successful. You can now log in.", "DE": "Registrierung erfolgreich. Sie können sich jetzt anmelden."},
    "Użytkownik już istnieje.": {"PL": "Użytkownik już istnieje.", "EN": "User already exists.", "DE": "Benutzer existiert bereits."},
    "Błędny login lub hasło.": {"PL": "Błędny login lub hasło.", "EN": "Invalid login or password.", "DE": "Ungültiger Benutzername oder Passwort."},
    "Wybierz opcję": {"PL": "Wybierz opcję", "EN": "Choose option", "DE": "Option wählen"},
    "Rozpocznij analizę teraz": {"PL": "Rozpocznij analizę teraz", "EN": "Start analysis now", "DE": "Analyse jetzt starten"}
}

def t(key):
    return translations.get(key, {}).get(session_state.language, key)

selected_lang = st.sidebar.selectbox("\U0001F310 Wybierz język / Select Language / Sprache wählen", list(lang_options.keys()), format_func=lambda x: lang_options[x])
session_state.language = selected_lang

# Dalej używaj t("Klucz") zamiast dosłownych tekstów
# Przykład: st.sidebar.subheader(t("Logowanie / Rejestracja"))
# Dla każdego tekstu użyj t("..."), aby zapewnić tłumaczenie w całej aplikacji
