import streamlit as st
import fitz  # PyMuPDF
import re
from fpdf import FPDF
from io import BytesIO
import json
import os
from datetime import datetime

# === KONFIGURACJA STRONY ===
st.set_page_config(layout="wide", page_title="UmowaAI", page_icon="🤖")

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
if not os.path.exists("history.json"):
    with open("history.json", "w") as f:
        json.dump({}, f)

def load_history():
    with open("history.json", "r") as f:
        return json.load(f)

def save_history(history):
    with open("history.json", "w") as f:
        json.dump(history, f)

def add_analysis_to_history(username, filename, typ_umowy, analiza, risks):
    history = load_history()
    if username not in history:
        history[username] = []
    history[username].append({
        "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "plik": filename,
        "typ_umowy": typ_umowy,
        "analiza": analiza,
        "ryzyka": [label for label, _ in risks]
    })
    save_history(history)

# === STAN SESJI ===
for key in ["logged_in", "username", "page"]:
    if key not in st.session_state:
        st.session_state[key] = False if key == "logged_in" else "Strona główna"

# === STYL STRONY ===
st.markdown("""
<style>
html, body, [class*="css"]  {
    height: 100%;
    margin: 0;
    background: linear-gradient(rgba(0,0,0,0.85), rgba(0,0,0,0.85)), url('https://cdn.pixabay.com/photo/2016/12/10/07/13/law-1890714_1280.jpg') no-repeat center center fixed;
    background-size: cover;
    color: white;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}
.block-container {
    padding: 2rem 3rem;
    background-color: rgba(255,255,255,0.06);
    border-radius: 20px;
    max-width: 900px;
    margin: auto;
    box-shadow: 0 0 30px rgba(255, 255, 255, 0.05);
}
.risk-box {
    background-color: rgba(255, 255, 255, 0.1);
    padding: 1rem;
    margin: 1rem 0;
    border-radius: 10px;
    border-left: 4px solid #f39c12;
}
.header-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 2rem;
    background-color: rgba(255, 255, 255, 0.05);
    border-radius: 10px;
    margin-bottom: 1rem;
}
.header-left a {
    font-size: 1.8rem;
    font-family: 'Georgia', serif;
    font-weight: bold;
    color: white;
    text-decoration: none;
}
.header-center {
    font-size: 1.5rem;
}
.header-right a {
    margin-left: 1rem;
    color: white;
    text-decoration: none;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# === HEADER BAR ===
st.markdown("""
<div class="header-bar">
    <div class="header-left"><a href="/?page=Strona%20g%C5%82%C3%B3wna">🏠 Strona główna</a></div>
    <div class="header-center">Ekspert od ryzyk prawnych</div>
    <div class="header-right">
        <a href="/?page=PL">PL/ENG</a>
        <a href="/?page=Logowanie">Logowanie</a>
        <a href="/?page=Rejestracja">Rejestracja</a>
    </div>
</div>
""", unsafe_allow_html=True)

# === ROUTING NA PODSTAWIE QUERY PARAMS ===
params = st.query_params
if "page" in params:
    st.session_state.page = params["page"]

# === PRZEŁĄCZANIE WIDOKÓW ===
page = st.session_state.page

if page == "Strona główna":
    st.title("🏠 Strona główna")
    st.markdown("""
    ### Witamy w UmowaAI!
    Narzędzie do analizy dokumentów prawnych i wykrywania ryzyk.

    - 🔍 Wykrywanie niekorzystnych zapisów
    - 📊 Historia Twoich analiz
    - 📥 Eksport PDF i TXT

    Aby rozpocząć, wybierz "UmowaAI" w menu.
    """)

elif page == "Logowanie":
    st.header("🔐 Logowanie")
    user = st.text_input("Nazwa użytkownika")
    passwd = st.text_input("Hasło", type="password")
    if st.button("Zaloguj"):
        if authenticate_user(user, passwd):
            st.session_state.logged_in = True
            st.session_state.username = user
            st.success("Zalogowano pomyślnie!")
            st.query_params.page = "UmowaAI"
        else:
            st.error("Nieprawidłowy login lub hasło")

elif page == "Rejestracja":
    st.header("📝 Rejestracja")
    new_user = st.text_input("Nazwa użytkownika")
    new_pass = st.text_input("Hasło", type="password")
    if st.button("Zarejestruj"):
        if register_user(new_user, new_pass):
            st.success("Zarejestrowano! Możesz się teraz zalogować.")
            st.query_params.page = "Logowanie"
        else:
            st.error("Użytkownik już istnieje!")

elif page == "UmowaAI":
    if not st.session_state.logged_in:
        st.warning("Musisz się zalogować, aby korzystać z analizy umów.")
    else:
        st.title("📄 UmowaAI – Analiza umowy")
        # --- tutaj dalszy kod analizy (upload, analiza, wyniki itd.)
