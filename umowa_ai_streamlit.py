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

if "theme" not in session_state:
    session_state.theme = "dark"

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

# Theme switch
if st.sidebar.checkbox("\U0001F319 Tryb ciemny / jasny"):
    session_state.theme = "light" if session_state.theme == "dark" else "dark"

if session_state.theme == "dark":
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
        </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
        <style>
            .stApp {
                background: #f9f9f9;
                font-family: 'Segoe UI', sans-serif;
            }
            html, body, [class*="css"] {
                background-color: transparent !important;
                color: #000000 !important;
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
                st.rerun()
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

# Rozpoznawanie wyboru bez ikon
plain_choice = [label for label, icon in menu_options][translated_menu.index(menu_choice)]

# Treści stron
if plain_choice == "Strona Główna":
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

elif plain_choice == "Analiza Umowy":
    st.header("Analiza AI")
    uploaded_file = st.file_uploader("Prześlij plik PDF do analizy", type="pdf")
    if uploaded_file:
        reader = PdfReader(uploaded_file)
        full_text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
        summary = full_text[:500] + "..."
        st.text_area("Treść umowy:", full_text, height=300)
        st.text_area("Podsumowanie:", summary, height=150)
        score = len(full_text) % 10
        cursor.execute("INSERT INTO analiza (user, tekst, podsumowanie, score, timestamp) VALUES (?, ?, ?, ?, ?)",
                       (session_state.username, full_text, summary, score, datetime.now().isoformat()))
        conn.commit()
        st.success("Analiza zapisana.")

elif plain_choice == "Ryzyka":
    st.header("Wykrywanie Ryzyk")
    cursor.execute("SELECT score, timestamp FROM analiza WHERE user = ? ORDER BY timestamp DESC LIMIT 5", (session_state.username,))
    data = cursor.fetchall()
    if data:
        scores, times = zip(*data)
        fig, ax = plt.subplots(figsize=(10, 4))
        sns.set_style("darkgrid")
        sns.lineplot(x=times, y=scores, marker='o', color='crimson', ax=ax)
        ax.set_title("Ocena ryzyk w czasie")
        ax.set_xlabel("Data")
        ax.set_ylabel("Ryzyko (0-10)")
        plt.xticks(rotation=30)
        st.pyplot(fig)
    else:
        st.info("Brak analiz do pokazania wykresu.")

elif plain_choice == "Moje Analizy":
    st.header("Historia Twoich analiz")
    cursor.execute("SELECT id, tekst, podsumowanie, score, timestamp FROM analiza WHERE user = ? ORDER BY timestamp DESC", (session_state.username,))
    rows = cursor.fetchall()

    if not rows:
        st.info("Brak zapisanych analiz.")
    else:
        for row in rows:
            analiza_id, tekst, podsumowanie, score, timestamp = row
            with st.expander(f"Analiza z dnia {timestamp} (Ryzyko: {score}/10)"):
                st.markdown(f"**Podsumowanie:** {podsumowanie[:500]}...")
                if st.button(f"🗑️ Usuń analizę {analiza_id}", key=f"delete_{analiza_id}"):
                    cursor.execute("DELETE FROM analiza WHERE id = ? AND user = ?", (analiza_id, session_state.username))
                    conn.commit()
                    st.success(f"Usunięto analizę z {timestamp}.")
                    st.experimental_rerun()
