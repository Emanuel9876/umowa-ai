import streamlit as st
import fitz  # PyMuPDF
import re
from fpdf import FPDF
from io import BytesIO
import json
import os

st.set_page_config(layout="wide", page_title="UmowaAI")

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

# === STAN SESJI ===
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "register_mode" not in st.session_state:
    st.session_state.register_mode = False
if "analysis_count" not in st.session_state:
    st.session_state.analysis_count = 0

# === STYL STRONY ===
st.markdown("""
<style>
body {
    background: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.8)), url('https://cdn.pixabay.com/photo/2016/12/10/07/13/law-1890714_1280.jpg') no-repeat center center fixed;
    background-size: cover;
    color: white;
}
.risk-box {
    background-color: rgba(255, 255, 255, 0.15);
    padding: 1rem;
    margin: 1rem 0;
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

# === LOGOWANIE/REJESTRACJA ===
if not st.session_state.logged_in and st.session_state.analysis_count >= 1:
    st.warning("🔐 Aby kontynuować, musisz się zalogować lub zarejestrować.")

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

# === APLIKACJA ===
if st.session_state.logged_in or st.session_state.analysis_count < 1:
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
        }
        finansowe = {
            "💸 Brak wynagrodzenia": r"(nie przysługuje|brak)\s+wynagrodzenia",
            "📈 Podwyżki bez zgody": r"(automatyczn[aey]|jednostronn[aey])\s+(zmian[aey]|podwyżk)"
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

        st.session_state.analysis_count += 1

        st.info("🕓 Historia analiz wkrótce dostępna.")
