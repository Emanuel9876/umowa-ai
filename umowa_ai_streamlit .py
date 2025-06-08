import streamlit as st

st.set_page_config(layout="wide", page_title="UmowaAI", page_icon="🤖")

import fitz  # PyMuPDF
import re
from fpdf import FPDF
from io import BytesIO
import json
import os
from datetime import datetime

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
for key in ["logged_in", "register_mode", "analysis_count", "page"]:
    if key not in st.session_state:
        st.session_state[key] = "home" if key == "page" else (False if key != "analysis_count" else 0)

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
</style>
""", unsafe_allow_html=True)

# === MENU ===
menu = st.sidebar.radio("📂 Menu", ["Strona główna", "UmowaAI", "Logowanie", "Rejestracja"])

if menu == "Strona główna":
    st.title("🏠 Strona główna")
    st.markdown("""
    ### Witamy w UmowaAI!
    Narzędzie do analizy dokumentów prawnych i wykrywania ryzyk.

    - 🔍 Wykrywanie niekorzystnych zapisów
    - 📊 Historia Twoich analiz
    - 📥 Eksport PDF i TXT

    Aby rozpocząć, wybierz "UmowaAI" w menu.
    """)

elif menu == "Logowanie":
    st.title("🔐 Logowanie")
    user = st.text_input("Nazwa użytkownika")
    passwd = st.text_input("Hasło", type="password")
    if st.button("Zaloguj"):
        if authenticate_user(user, passwd):
            st.session_state.logged_in = True
            st.session_state.username = user
            st.success("Zalogowano jako " + user)
        else:
            st.error("Nieprawidłowy login lub hasło")

elif menu == "Rejestracja":
    st.title("📝 Rejestracja")
    new_user = st.text_input("Nazwa użytkownika")
    new_pass = st.text_input("Hasło", type="password")
    if st.button("Zarejestruj"):
        if register_user(new_user, new_pass):
            st.success("Zarejestrowano! Możesz się teraz zalogować.")
        else:
            st.error("Użytkownik już istnieje!")

elif menu == "UmowaAI":
    if not st.session_state.logged_in:
        st.warning("🔒 Zaloguj się, aby korzystać z UmowaAI.")
    else:
        st.title("🤖 UmowaAI – Ekspert od ryzyk prawnych")
        lang = st.radio("🌐 Język", ["Polski", "English"], horizontal=True)
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

            if st.session_state.logged_in:
                add_analysis_to_history(st.session_state.username, uploaded_file.name, typ_umowy, analiza, risks)

        if st.session_state.logged_in:
            with st.expander("📚 Historia Twoich analiz"):
                history = load_history().get(st.session_state.username, [])
                if not history:
                    st.info("Brak zapisanych analiz.")
                else:
                    for entry in reversed(history[-10:]):
                        st.markdown(f"""
                        <div class='risk-box'>
                            <b>📅 {entry["data"]}</b><br>
                            📄 Plik: {entry["plik"]}<br>
                            📝 Umowa: {entry["typ_umowy"]}, Analiza: {entry["analiza"]}<br>
                            🚨 Ryzyka: {', '.join(entry["ryzyka"])}
                        </div>
                        """, unsafe_allow_html=True)
