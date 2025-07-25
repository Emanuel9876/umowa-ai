# Dodane elementy premium i limity użytkowników do Twojej aplikacji

import streamlit as st
import re
import io
import os
import json
import hashlib
import sqlite3
from datetime import datetime, date
from PyPDF2 import PdfReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from docx import Document

# --- Konfiguracja strony ---
st.set_page_config(page_title="Umowa AI 2.0", layout="wide")

# --- Baza danych SQLite ---
conn = sqlite3.connect("umowa_ai.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS analiza (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT,
    tekst TEXT,
    podsumowanie TEXT,
    score INTEGER,
    timestamp TEXT
)
''')
conn.commit()

# --- Użytkownicy ---
def load_users():
    if os.path.exists("users.json"):
        with open("users.json", "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open("users.json", "w") as f:
        json.dump(users, f, indent=4)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

users = load_users()
session_state = st.session_state

# --- Stan sesji ---
if "logged_in" not in session_state:
    session_state.logged_in = False
    session_state.username = ""
if "custom_keywords" not in session_state:
    session_state.custom_keywords = []

# --- Ograniczenia kont ---
def user_can_analyze(user):
    plan = users[user].get("plan", "free")
    today = date.today().isoformat()
    last = users[user].get("last_analysis", "")

    if plan == "premium":
        return True
    elif plan == "free":
        return last != today
    return False

def update_last_analysis(user):
    users[user]["last_analysis"] = date.today().isoformat()
    save_users(users)

# --- Pomocnicze funkcje do plików ---
# (pozostawiam bez zmian, jak w Twoim kodzie)

# --- Logowanie / Rejestracja / Wylogowanie ---
def login():
    st.sidebar.markdown("<h2>🔑 Logowanie</h2>", unsafe_allow_html=True)
    username = st.sidebar.text_input("Nazwa użytkownika")
    password = st.sidebar.text_input("Hasło", type="password")
    if st.sidebar.button("Zaloguj"):
        if username in users and users[username]["password"] == hash_password(password):
            session_state.logged_in = True
            session_state.username = username
            st.sidebar.success(f"Zalogowano jako {username}")
            st.experimental_rerun()
        else:
            st.sidebar.error("Nieprawidłowa nazwa użytkownika lub hasło")

def register():
    st.sidebar.markdown("<h2>📝 Rejestracja</h2>", unsafe_allow_html=True)
    new_user = st.sidebar.text_input("Nazwa użytkownika", key="reg_user")
    new_pass = st.sidebar.text_input("Hasło", type="password", key="reg_pass")
    new_pass2 = st.sidebar.text_input("Powtórz hasło", type="password", key="reg_pass2")
    if st.sidebar.button("Zarejestruj"):
        if not new_user or not new_pass:
            st.sidebar.error("Wypełnij wszystkie pola")
        elif new_user in users:
            st.sidebar.error("Użytkownik już istnieje")
        elif new_pass != new_pass2:
            st.sidebar.error("Hasła nie są takie same")
        else:
            users[new_user] = {
                "password": hash_password(new_pass),
                "plan": "free",
                "last_analysis": ""
            }
            save_users(users)
            st.sidebar.success("Rejestracja udana! Zaloguj się.")
            st.experimental_rerun()

def logout():
    if st.sidebar.button("🚪 Wyloguj się"):
        session_state.logged_in = False
        session_state.username = ""
        st.sidebar.success("Wylogowano")
        st.experimental_rerun()

# --- Dodanie cennika ---
def show_pricing():
    st.title("💳 Cennik")
    st.markdown("""
    | Plan | Cena | Funkcje |
    |------|------|---------|
    | **Free** | 0 zł | 1 analiza dziennie, max 5 słów kluczowych, brak PDF |
    | **Premium** | 29 zł / mies. | Bez limitu analiz, PDF, historia, własne słowa kluczowe |
    """)
    st.info("Integracja z Stripe/PayPal do dodania. Tymczasem zmieniaj plan manualnie w users.json")

# --- Wybór strony ---
def main():
    st.sidebar.title("Umowa AI 2.0")
    if not session_state.logged_in:
        login()
        st.sidebar.markdown("---")
        register()
    else:
        st.sidebar.markdown(f"Witaj, **{session_state.username}**!")
        logout()
        page = st.sidebar.selectbox("Strona", ["Strona Główna", "Analiza umowy", "Historia analiz", "Cennik"])

        if page == "Cennik":
            show_pricing()
        # inne strony bez zmian

if __name__ == "__main__":
    main()
