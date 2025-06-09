import streamlit as st
import fitz
import re
from io import BytesIO
from fpdf import FPDF
import json, os

# Konfiguracja strony
st.set_page_config(page_title="UmowaAI", layout="wide")

# Baza logowania
if not os.path.exists("users.json"):
    with open("users.json","w") as f: json.dump({}, f)
def load_users(): return json.load(open("users.json"))
def save_users(u): json.dump(u, open("users.json","w"))
def register(u,p):
    users = load_users()
    if u in users: return False
    users[u]=p; save_users(users); return True
def auth(u,p):
    users = load_users()
    return u in users and users[u]==p

# Stan sesji
if "page" not in st.session_state: st.session_state.page="home"
if "logged" not in st.session_state: st.session_state.logged=False
if "user" not in st.session_state: st.session_state.user=""

# Sidebar - logowanie/rejestracja
st.sidebar.title("🔒 Konto")
if not st.session_state.logged:
    mode = st.sidebar.radio("Mode", ["Login", "Register"])
    user = st.sidebar.text_input("Username", key="usr_inp")
    pwd = st.sidebar.text_input("Password", type="password", key="pwd_inp")
    if st.sidebar.button("Submit"):
        if mode=="Register":
            if register(user,pwd):
                st.sidebar.success("Registered! You can now login.")
            else:
                st.sidebar.error("User exists.")
        else:
            if auth(user,pwd):
                st.session_state.logged=True
                st.session_state.user=user
                st.sidebar.success("Logged in!")
            else:
                st.sidebar.error("Invalid credentials.")
else:
    st.sidebar.write(f"✅ Logged in as **{st.session_state.user}**")
    if st.sidebar.button("Logout"):
        st.session_state.logged=False

# Sidebar - menu (tylko po zalogowaniu)
if st.session_state.logged:
    st.sidebar.markdown("---")
    if st.sidebar.button("🏠 Strona główna"): st.session_state.page="home"
    if st.sidebar.button("🗓️ Wgraj PDF"): st.session_state.page="upload"
    if st.sidebar.button("🚨 Ryzyka"): st.session_state.page="risks"
    if st.sidebar.button("📄 Treść umowy"): st.session_state.page="content"
    if st.sidebar.button("💾 Pobierz"): st.session_state.page="download"

# Podstrony
st.header({
    "home": "🏠 Strona główna",
    "upload": "🗓️ Wgraj PDF",
    "risks": "🚨 Ryzyka",
    "content": "📄 Treść umowy",
    "download": "💾 Pobierz analizę"
}[st.session_state.page])

if st.session_state.page=="home":
    st.write("Witaj w UmowaAI!")
elif st.session_state.page=="upload":
    uploaded = st.file_uploader("Wgraj PDF", type="pdf")
    if uploaded:
        doc = fitz.open(stream=uploaded.read(), filetype="pdf")
        txt="".join(page.get_text() for page in doc)
        st.session_state.pdf_text = txt
        st.success("PDF wczytany!")
elif st.session_state.page=="risks":
    if "pdf_text" not in st.session_state:
        st.info("Najpierw wgraj PDF.")
    else:
        patterns = {
            "⚠️ Kaucja": r"kaucj[ae]\s+.*?\d+[\s\w]*zł",
            "⏳ Wypowiedzenie": r"wypowiedze?nie",
            "🚫 Kara umowna": r"kara\s+umowna",
            "💸 Brak wynagrodzenia": r"brak\s+wynagrodzenia"
        }
        st.write("Wykryte ryzyka:")
        forlbl,pat in patterns.items():
            for m in re.finditer(pat, st.session_state.pdf_text, re.IGNORECASE):
                st.write(f"- **{lbl}**: {m.group()}")
elif st.session_state.page=="content":
    if "pdf_text" not in st.session_state:
        st.info("Najpierw wgraj PDF.")
    else:
        t = st.session_state.pdf_text
        highlighted = re.sub(r"(kaucj[ae]\s+.*?\d+[\s\w]*zł)", "<mark>⚠️ \\1</mark>", t, flags=re.IGNORECASE)
        st.markdown(highlighted, unsafe_allow_html=True)
elif st.session_state.page=="download":
    if "pdf_text" not in st.session_state:
        st.info("Najpierw wgraj PDF.")
    else:
        txt = st.session_state.pdf_text
        st.download_button("📥 Pobierz jako TXT", data=txt, file_name="analiza.txt")
