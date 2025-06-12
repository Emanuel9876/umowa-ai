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

selected_lang = st.sidebar.selectbox("🌐 Wybierz język / Select Language / Sprache wählen", list(lang_options.keys()), format_func=lambda x: lang_options[x])
session_state.language = selected_lang

if not session_state.logged_in:
    st.sidebar.subheader("🔐 Logowanie / Rejestracja")
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
        body { background-color: #dbeafe; font-family: 'Segoe UI', sans-serif; }
        .stApp { background-color: #dbeafe; }
        .highlight { font-weight: bold; font-size: 20px; color: #0c0c0c; font-family: 'Georgia', serif; }
        .content-text { font-size: 18px; color: #0c0c0c; }
        .custom-label { font-size: 20px; color: #1d4ed8; font-weight: bold; margin-top: 20px; }
        .summary-section { text-align: center; }
        .block-container { padding: 3rem 4rem 3rem 4rem; }
        h1, h2, h3 { text-align: center; color: #1e293b; }
        .element-container p, .element-container div {
            color: #0c0c0c !important;
        }
    </style>
""", unsafe_allow_html=True)

# (pozostała część kodu zostaje bez zmian – logika analizy itd.)

# Menu główne
st.sidebar.title("Menu")
menu = st.sidebar.selectbox("Wybierz opcję", ["Strona Główna", "Analiza Umowy", "Ryzyka", "Moje Analizy"])

# (reszta jak w poprzednim kodzie – strony główna, analiza, ryzyka, historia)
