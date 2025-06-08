import streamlit as st
import fitz  # PyMuPDF
import re
from fpdf import FPDF
from io import BytesIO
import json
import os
from datetime import datetime

st.set_page_config(layout="centered")

# === BAZA UŻYTKOWNIKÓW ===
if not os.path.exists("users.json"):
    with open("users.json", "w") as f:
        json.dump({}, f)

def load_users():
    with open("users.json", "r") as f:
        return json.load(f)

def save_users(users):
    with open("users.json", "w") as f:
        json.dump(users, f)

def register_user(username, password):
    users = load_users()
    if username in users:
        return False
    users[username] = password
    save_users(users)
    return True

def authenticate_user(username, password):
    users = load_users()
    return username in users and users[username] == password

# === HISTORIA ANALIZ ===
HISTORIA_DIR = "historie"
os.makedirs(HISTORIA_DIR, exist_ok=True)

def save_analysis(username, typ_umowy, analiza, lang, content):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{HISTORIA_DIR}/{username}_{timestamp}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"Typ umowy: {typ_umowy}\nTyp analizy: {analiza}\nJęzyk: {lang}\n\n{content}")

def list_user_analyses(username):
    return sorted([f for f in os.listdir(HISTORIA_DIR) if f.startswith(username)], reverse=True)

def load_analysis_file(filename):
    with open(f"{HISTORIA_DIR}/{filename}", "r", encoding="utf-8") as f:
        return f.read()

# === STAN SESJI ===
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "register_mode" not in st.session_state:
    st.session_state.register_mode = False

# === TRYB JASNY/CIEMNY + TŁO ===
dark_mode = st.toggle("🌗 Tryb ciemny/jasny", value=True)
background_url = "https://images.unsplash.com/photo-1603575448361-18c1e4d5ecb3"
if dark_mode:
    st.markdown(f"""
    <style>
    body {{
        background: url('{background_url}') no-repeat center center fixed;
        background-size: cover;
        color: white;
    }}
    .risk-box {{
        background-color: rgba(44, 44, 44, 0.85);
        padding: 10px;
        margin: 10px 0;
        border-radius: 10px;
    }}
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
    <style>
    body {{
        background: url('{background_url}') no-repeat center center fixed;
        background-size: cover;
        color: black;
    }}
    .risk-box {{
        background-color: rgba(255, 255, 255, 0.85);
        padding: 10px;
        margin: 10px 0;
        border-radius: 10px;
    }}
    </style>
    """, unsafe_allow_html=True)

# === LOGOWANIE/REJESTRACJA ===
if not st.session_state.logged_in:
    st.image("https://images.unsplash.com/photo-1581091226825-b156c7ff8cde", use_container_width=True)
    if st.session_state.register_mode:
        st.header("📝 Rejestracja")
        new_user = st.text_input("Nazwa użytkownika")
        new_pass = st.text_input("Hasło", type="password")
        if st.button("Zarejestruj"):
            if register_user(new_user, new_pass):
                st.success("Zarejestrowano! Możesz się teraz zalogować.")
                st.session_state.register_mode = False
            else:
                st.error("Użytkownik już istnieje!")
        if st.button("← Masz już konto? Zaloguj się"):
            st.session_state.register_mode = False
    else:
        st.header("🔐 Logowanie")
        user = st.text_input("Nazwa użytkownika")
        passwd = st.text_input("Hasło", type="password")
        if st.button("Zaloguj"):
            if authenticate_user(user, passwd):
                st.session_state.logged_in = True
                st.session_state.username = user
                st.success("Zalogowano jako " + user)
            else:
                st.error("Nieprawidłowy login lub hasło")
        if st.button("Nie masz konta? Zarejestruj się →"):
            st.session_state.register_mode = True

# === APLIKACJA PO ZALOGOWANIU ===
# (reszta kodu pozostaje bez zmian)
