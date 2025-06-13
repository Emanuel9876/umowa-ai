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

# Stylizacja
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
        .highlight {
            font-weight: bold;
            font-size: 22px;
            font-family: 'Georgia', serif;
        }
        .content-text {
            font-size: 18px;
        }
        .custom-label {
            font-size: 20px;
            font-weight: bold;
            margin-top: 20px;
        }
        .summary-section {
            text-align: center;
        }
        .block-container {
            padding: 3rem 4rem;
        }
    </style>
""", unsafe_allow_html=True)

# Menu główne
st.sidebar.title("Menu")
menu_options = ["Strona Główna", "Analiza Umowy", "Ryzyka", "Moje Analizy"]
translated_menu = [translations[opt][session_state.language] for opt in menu_options]
menu_choice = st.sidebar.selectbox("Wybierz opcję", translated_menu)

# Treści stron
if menu_choice == translations["Strona Główna"][session_state.language]:
    st.title("\U0001F916 UmowaAI")
    st.markdown("## Witaj w aplikacji do analizy umów")
    st.markdown("""
        **Czym jest UmowaAI?**

        UmowaAI to Twój inteligentny asystent, który:
        - automatycznie analizuje przesłane pliki PDF,
        - ocenia ryzyko zawarte w dokumentach,
        - prezentuje podsumowanie i historię Twoich analiz.
    """)
    st.markdown("---")
    st.markdown("### Rozpocznij od przesłania swojej pierwszej umowy w zakładce *Analiza Umowy*.")

elif menu_choice == translations["Analiza Umowy"][session_state.language]:
    st.header("Analiza AI")
    uploaded_file = st.file_uploader("Prześlij plik PDF do analizy", type="pdf")
    if uploaded_file:
        reader = PdfReader(uploaded_file)
        full_text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
        summary = full_text[:500] + "..."
        st.text_area("Treść umowy:", full_text, height=300)
        st.text_area("Podsumowanie:", summary, height=150)
        score = len(full_text) % 10  # przykład: analiza punktowa
        cursor.execute("INSERT INTO analiza (user, tekst, podsumowanie, score, timestamp) VALUES (?, ?, ?, ?, ?)",
                       (session_state.username, full_text, summary, score, datetime.now().isoformat()))
        conn.commit()
        st.success("Analiza zapisana.")

elif menu_choice == translations["Ryzyka"][session_state.language]:
    st.header("Wykrywanie Ryzyk")
    cursor.execute("SELECT score, timestamp FROM analiza WHERE user = ? ORDER BY timestamp DESC LIMIT 5", (session_state.username,))
    data = cursor.fetchall()
    if data:
        scores, times = zip(*data)
        fig, ax = plt.subplots()
        ax.plot(times, scores, marker='o', color='red')
        ax.set_title("Ocena ryzyk w czasie")
        ax.set_xlabel("Data")
        ax.set_ylabel("Ryzyko (0-10)")
        st.pyplot(fig)
    else:
        st.info("Brak analiz do pokazania wykresu.")

elif menu_choice == translations["Moje Analizy"][session_state.language]:
    st.header("Historia Twoich analiz")
    cursor.execute("SELECT tekst, podsumowanie, score, timestamp FROM analiza WHERE user = ? ORDER BY timestamp DESC", (session_state.username,))
    rows = cursor.fetchall()
    for tekst, podsumowanie, score, timestamp in rows:
        st.markdown("---")
        st.markdown(f"**Data:** {timestamp}")
        st.markdown(f"**Ocena ryzyka:** {score}/10")
        st.markdown(f"**Podsumowanie:** {podsumowanie[:300]}...")
