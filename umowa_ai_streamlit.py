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
    "Strona G\u0142\u00f3wna": {"PL": "Strona G\u0142\u00f3wna", "EN": "Home", "DE": "Startseite"},
    "Analiza Umowy": {"PL": "Analiza Umowy", "EN": "Contract Analysis", "DE": "Vertragsanalyse"},
    "Ryzyka": {"PL": "Ryzyka", "EN": "Risks", "DE": "Risiken"},
    "Moje Analizy": {"PL": "Moje Analizy", "EN": "My Analyses", "DE": "Meine Analysen"},
    "Witaj w aplikacji": {"PL": "Witaj w aplikacji", "EN": "Welcome to the app", "DE": "Willkommen in der App"},
    "Twoim asystencie do analizy um\u00f3w": {"PL": "Twoim asystencie do analizy um\u00f3w", "EN": "Your contract analysis assistant", "DE": "Ihr Vertragsanalyse-Assistent"},
    "Automatycznie analizujemy dokumenty": {"PL": "Automatycznie analizujemy dokumenty", "EN": "We automatically analyze documents", "DE": "Wir analysieren automatisch Dokumente"},
    "i prezentujemy je w czytelnej formie": {"PL": "i prezentujemy je w czytelnej formie", "EN": "and present them in a clear form", "DE": "und pr\u00e4sentieren sie in klarer Form"},
    "Zaloguj si\u0119": {"PL": "Zaloguj si\u0119", "EN": "Log in", "DE": "Anmelden"},
    "Zarejestruj si\u0119": {"PL": "Zarejestruj si\u0119", "EN": "Register", "DE": "Registrieren"},
    "Login": {"PL": "Login", "EN": "Username", "DE": "Benutzername"},
    "Has\u0142o": {"PL": "Has\u0142o", "EN": "Password", "DE": "Passwort"},
    "Wybierz opcj\u0119": {"PL": "Wybierz opcj\u0119", "EN": "Choose option", "DE": "Option ausw\u00e4hlen"},
    "Rozpocznij analiz\u0119 teraz": {"PL": "Rozpocznij analiz\u0119 teraz", "EN": "Start analysis now", "DE": "Analyse jetzt starten"},
    "Prze\u015blij PDF": {"PL": "Prze\u015blij PDF", "EN": "Upload PDF", "DE": "PDF hochladen"},
    "Wklej tekst": {"PL": "Wklej tekst", "EN": "Paste text", "DE": "Text einf\u00fcgen"},
    "Podsumowanie:": {"PL": "Podsumowanie:", "EN": "Summary:", "DE": "Zusammenfassung:"},
    "Zapisz analiz\u0119": {"PL": "Zapisz analiz\u0119", "EN": "Save analysis", "DE": "Analyse speichern"},
    "Wprowad\u017a lub za\u0142aduj tekst umowy.": {"PL": "Wprowad\u017a lub za\u0142aduj tekst umowy.", "EN": "Enter or upload contract text.", "DE": "Vertragstext eingeben oder hochladen."},
    "Historia Twoich analiz": {"PL": "Historia Twoich analiz", "EN": "Your analysis history", "DE": "Analyseverlauf"},
    "Usu\u0144 analiz\u0119": {"PL": "Usu\u0144 analiz\u0119", "EN": "Delete analysis", "DE": "Analyse l\u00f6schen"},
    "Brak zapisanych analiz.": {"PL": "Brak zapisanych analiz.", "EN": "No saved analyses.", "DE": "Keine gespeicherten Analysen."},
    "Pobierz PDF": {"PL": "Pobierz PDF", "EN": "Download PDF", "DE": "PDF herunterladen"},
    "Wybierz j\u0119zyk / Select Language / Sprache w\u00e4hlen": {"PL": "Wybierz j\u0119zyk", "EN": "Select Language", "DE": "Sprache w\u00e4hlen"},
    "Logowanie / Rejestracja": {"PL": "Logowanie / Rejestracja", "EN": "Login / Register", "DE": "Anmelden / Registrieren"}
}

def t(key):
    return translations.get(key, {}).get(session_state.language, key)

# Dalej kod powinien używać t("nazwa") dla każdego tłumaczonego tekstu np. st.header(t("Historia Twoich analiz"))
# Zamień wszystkie literalne stringi w UI na ich odpowiedniki przez t()
