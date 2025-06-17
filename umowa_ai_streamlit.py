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

# Logowanie
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
                st.rerun()
            else:
                st.sidebar.error("Błędny login lub hasło.")
    st.stop()

# Menu główne
menu_options = [
    ("Strona Główna", "\U0001F3E0"),
    ("Analiza Umowy", "\U0001F4C4"),
    ("Ryzyka", "\u26A0"),
    ("Moje Analizy", "\U0001F4CB")
]
translated_menu = [f"{icon} {translations[label][session_state.language]}" for label, icon in menu_options]
menu_choice = st.sidebar.selectbox("Wybierz opcję", translated_menu)
plain_choice = [label for label, icon in menu_options][translated_menu.index(menu_choice)]

# 💡 NOWA STRONA GŁÓWNA
if plain_choice == "Strona Główna":
    if "start_analysis" not in session_state:
        session_state.start_analysis = False

    if session_state.start_analysis:
        plain_choice = "Analiza Umowy"
        session_state.start_analysis = False
        st.rerun()

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
        st.rerun()
