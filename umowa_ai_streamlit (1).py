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

# === TRYB JASNY/CIEMNY ===
dark_mode = st.toggle("🌗 Tryb ciemny/jasny", value=True)
if dark_mode:
    st.markdown("""
    <style>
    body {
        background: #0f2027;
        color: white;
    }
    .risk-box {
        background-color: #2c2c2c;
        padding: 10px;
        margin: 10px 0;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
    body {
        background: #f5f5f5;
        color: black;
    }
    .risk-box {
        background-color: #e0e0e0;
        padding: 10px;
        margin: 10px 0;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# === LOGOWANIE/REJESTRACJA ===
if not st.session_state.logged_in:
    st.image("https://images.unsplash.com/photo-1581091226825-b156c7ff8cde", use_column_width=True)
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
if st.session_state.logged_in:
    st.title("🤖 UmowaAI – Ekspert od ryzyk prawnych")
    lang = st.radio("🌐 Język", ["Polski", "English"])
    is_pl = lang == "Polski"

    typ_umowy = st.selectbox("📄 Typ umowy", ["Najmu", "O pracę", "Zlecenie", "Dzieło", "Sprzedaży"])
    analiza = st.selectbox("🔍 Typ analizy", ["Prawne", "Finansowe", "Wszystkie"])

    def extract_text_from_pdf(file):
        doc = fitz.open(stream=file.read(), filetype="pdf")
        return "".join([page.get_text() for page in doc])

    def find_risks(text, typ_umowy, analiza):
        wspolne = {
            "⚠️ Kaucja": r"kaucj[ae]\s+.*?\d+[\s\w]*z[łl]",
            "⏳ Wypowiedzenie": r"wypowiedze?nie.*?(umowy|kontraktu)?",
            "🚫 Kara umowna": r"kara\s+umowna.*?\d+[\s\w]*z[łl]",
            "❗ Penalty clause": r"penalty clause.*?",
            "📬 Termination notice": r"termination notice.*?",
        }
        finansowe = {
            "💸 Brak wynagrodzenia": r"(nie przysługuje|brak)\s+wynagrodzenia",
            "📈 Podwyżki bez zgody": r"(automatyczn[aey]|jednostronn[aey])\s+(zmian[aey]|podwyżk)",
            "📉 Automatic deductions": r"automatic deductions.*?",
        }
        spec = {
            "Najmu": {"🔐 Zakaz podnajmu": r"(zakaz|brak zgody).*?podnajm"},
            "O pracę": {"💼 Nadgodziny niepłatne": r"nadgodzin(y|ach|om).*?nieodpłatn"},
            "Zlecenie": {"📆 Terminy realizacji": r"termin.*?realizacj"},
            "Dzieło": {"🛠️ Odpowiedzialność za wady": r"odpowiedzialno\w+.*?wady.*?dzie[łl]"},
            "Sprzedaży": {"🔍 Reklamacje": r"(reklamacj|odpowiedzialno\w+).*?towar"}
        }

        patterns = wspolne.copy()
        if analiza in ["Finansowe", "Wszystkie"]:
            patterns.update(finansowe)
        if typ_umowy in spec:
            patterns.update(spec[typ_umowy])

        results = []
        for label, pattern in patterns.items():
            for match in re.finditer(pattern, text, re.IGNORECASE):
                results.append((label, match.group()))
        return results

    def highlight_risks(text, risks):
        for label, frag in risks:
            text = text.replace(frag, f"**[{label}]** {frag}")
        return text

    def export_to_pdf(text):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_font("Arial", size=12)
        for line in text.split('\n'):
            pdf.multi_cell(0, 10, line)
        buf = BytesIO()
        pdf.output(buf)
        return buf.getvalue()

    uploaded_file = st.file_uploader("📥 Wgraj PDF umowy", type="pdf")
    if uploaded_file:
        with st.spinner("🔎 Analiza..."):
            text = extract_text_from_pdf(uploaded_file)
            risks = find_risks(text, typ_umowy, analiza)
            highlighted = highlight_risks(text, risks)
            save_analysis(st.session_state.username, typ_umowy, analiza, lang, highlighted)

        st.subheader("🚨 Wykryte ryzyka:")
        if risks:
            for label, frag in risks:
                st.markdown(f"<div class='risk-box'><b>{label}</b><br>{frag}</div>", unsafe_allow_html=True)
        else:
            st.success("✅ Brak oczywistych ryzyk.")

        st.subheader("📄 Treść umowy z oznaczeniami:")
        st.markdown(highlighted)

        with st.expander("💾 Pobierz analizę"):
            st.download_button("📩 TXT", data=highlighted, file_name="analiza_umowy.txt")
            st.download_button("🧾 PDF", data=export_to_pdf(highlighted), file_name="analiza_umowy.pdf")

    st.subheader("🗂️ Historia analiz")
    for fname in list_user_analyses(st.session_state.username):
        with st.expander(fname):
            content = load_analysis_file(fname)
            st.text(content)

