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
for key in ["logged_in", "username", "page", "lang"]:
    if key not in st.session_state:
        if key == "logged_in":
            st.session_state[key] = False
        elif key == "lang":
            st.session_state[key] = "PL"
        else:
            st.session_state[key] = "Strona główna"

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
    font-size: 2rem;
    font-family: 'Georgia', serif;
    font-weight: bold;
    color: white;
    text-decoration: none;
}
.header-center {
    font-size: 1.8rem;
    font-weight: bold;
    color: white;
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
st.markdown(f"""
<div class="header-bar">
    <div class="header-left"><a href="/?page=Strona%20g%C5%82%C3%B3wna">Strona główna</a></div>
    <div class="header-center">Ekspert od ryzyk prawnych</div>
    <div class="header-right">
        <a href="/?lang=PL">PL</a> / <a href="/?lang=ENG">ENG</a>
        <a href="/?page=Logowanie">Logowanie</a>
        <a href="/?page=Rejestracja">Rejestracja</a>
        <a href="/?page=UmowaAI">UmowaAI</a>
    </div>
</div>
""", unsafe_allow_html=True)

# === ROUTING ===
params = st.query_params
if "page" in params:
    st.session_state.page = params["page"]
if "lang" in params:
    st.session_state.lang = params["lang"]

# === FUNKCJA TŁUMACZEŃ ===
def _(pl, eng):
    return pl if st.session_state.lang == "PL" else eng

# === PRZEŁĄCZANIE WIDOKÓW ===
page = st.session_state.page

if page == "Strona główna":
    st.title("🏠 " + _("Strona główna", "Home Page"))
    st.markdown(_("""
    ### Witamy w UmowaAI!
    Narzędzie do analizy dokumentów prawnych i wykrywania ryzyk.

    - 🔍 Wykrywanie niekorzystnych zapisów
    - 📊 Historia Twoich analiz
    - 📥 Eksport PDF i TXT

    Aby rozpocząć, wybierz "UmowaAI" w menu.
    """, """
    ### Welcome to UmowaAI!
    A tool for legal document analysis and risk detection.

    - 🔍 Detect unfavorable clauses
    - 📊 Your analysis history
    - 📥 Export to PDF and TXT

    To get started, choose "UmowaAI" from the menu.
    """))

elif page == "Logowanie":
    st.header("🔐 " + _("Logowanie", "Login"))
    user = st.text_input(_("Nazwa użytkownika", "Username"), key="login_user")
    passwd = st.text_input("Hasło", type="password", key="login_pass")
    if st.button(_("Zaloguj", "Login")):
        if authenticate_user(user, passwd):
            st.session_state.logged_in = True
            st.session_state.username = user
            st.success(_("Zalogowano pomyślnie!", "Login successful!"))
            st.session_state.page = "UmowaAI"
            st.rerun()
        else:
            st.error(_("Nieprawidłowy login lub hasło", "Invalid username or password"))

elif page == "Rejestracja":
    st.header("📝 " + _( "Rejestracja", "Register"))
    new_user = st.text_input(_("Nazwa użytkownika", "Username"), key="register_user")
    new_pass = st.text_input("Hasło", type="password", key="register_pass")
    if st.button(_("Zarejestruj", "Register")):
        if register_user(new_user, new_pass):
            st.success(_("Zarejestrowano! Możesz się teraz zalogować.", "Registered! You can now log in."))
            st.session_state.page = "Logowanie"
            st.rerun()
        else:
            st.error(_("Użytkownik już istnieje!", "User already exists!"))

elif page == "UmowaAI":
    if not st.session_state.logged_in:
        st.warning(_("Musisz się zalogować, aby korzystać z analizy umów.", "You must log in to use the contract analysis."))
    else:
        st.title("📄 " + _( "UmowaAI – Analiza umowy", "UmowaAI – Contract Analysis"))

        uploaded_file = st.file_uploader(_("Prześlij plik PDF", "Upload PDF file"), type="pdf")
        input_text = st.text_area(_("Lub wklej treść umowy", "Or paste the contract text"))

        if st.button(_("Analizuj umowę", "Analyze contract")):
            text = ""
            if uploaded_file:
                with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
                    text = "\n".join(page.get_text() for page in doc)
            elif input_text:
                text = input_text

            if text:
                st.success(_("Analiza zakończona pomyślnie.", "Analysis completed successfully."))
                st.download_button("📥 " + _("Eksportuj jako TXT", "Export as TXT"), text, file_name="analiza.txt")

                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=12)
                for line in text.split('\n'):
                    pdf.multi_cell(0, 10, line)
                buf = BytesIO()
                pdf.output(buf)
                st.download_button("📥 " + _("Eksportuj jako PDF", "Export as PDF"), data=buf.getvalue(), file_name="analiza.pdf")
            else:
                st.error(_("Brak tekstu do analizy.", "No text provided for analysis."))
