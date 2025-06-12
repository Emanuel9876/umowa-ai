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
        .highlight { font-weight: bold; font-size: 20px; color: #111827; font-family: 'Georgia', serif; }
        .content-text { font-size: 18px; color: #1e293b; }
        .custom-label { font-size: 20px; color: #1e3a8a; font-weight: bold; margin-top: 20px; }
        .summary-section { text-align: center; }
    </style>
""", unsafe_allow_html=True)

def analyze_text(text):
    summary = ""
    if re.search(r'odstąpienie|rozwiązanie.*umow', text, re.IGNORECASE):
        summary += "\n- **Utrudnione odstąpienie od umowy**: możliwe ograniczenia."
    if re.search(r'obowiąz(e|ą)zki|zobowiązany', text, re.IGNORECASE):
        summary += "\n- **Dodatkowe obowiązki**: potencjalne zobowiązania."
    if re.search(r'opłata|koszt|zapłaty', text, re.IGNORECASE):
        summary += "\n- **Dodatkowe opłaty**: możliwe ukryte koszty."
    if re.search(r'nieważn|unieważn', text, re.IGNORECASE):
        summary += "\n- **Nieważność umowy**: zapisy mogą być nieważne."
    if re.search(r'kara|odsetki|strata|szkoda', text, re.IGNORECASE):
        summary += "\n- **Konsekwencje finansowe**: ryzyko kosztów."
    if re.search(r'prawne|pozew|sąd', text, re.IGNORECASE):
        summary += "\n- **Skutki prawne**: możliwe działania prawne."
    if re.search(r'niewywiązuje|niewykona|zaniedbanie', text, re.IGNORECASE):
        summary += "\n- **Niewywiązanie się z umowy**: ryzyko naruszeń."
    score = summary.count('- **')
    return summary.strip(), score

def ocena_poziomu_ryzyka(score):
    if score <= 1:
        return "Niskie", "🟢", "Umowa wygląda bezpiecznie."
    elif 2 <= score <= 3:
        return "Średnie", "🟡", "Warto zwrócić uwagę na kilka zapisów."
    else:
        return "Wysokie", "🔴", "Zalecamy konsultację z prawnikiem."

def extract_text_from_pdf(uploaded_file):
    reader = PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

def generate_pdf(text):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer)
    text_object = c.beginText(40, 800)
    for line in text.split('\n'):
        text_object.textLine(line)
    c.drawText(text_object)
    c.save()
    buffer.seek(0)
    return buffer

st.sidebar.title("Menu")
menu = st.sidebar.selectbox("Wybierz opcję", ["Strona Główna", "Analiza Umowy", "Ryzyka", "Moje Analizy"])

if menu == "Strona Główna":
    st.title("🤖 UmowaAI – Twój inteligentny doradca od umów")
    st.markdown("""
    ### Co potrafimy?
    - Analiza treści umów
    - Wykrywanie ryzyk
    - Pobieranie raportów
    - Interfejs wielojęzyczny
    - Historia Twoich analiz (tylko dla zalogowanych)
    """)

elif menu == "Analiza Umowy":
    st.title("🔍 Analiza treści umowy")
    uploaded_file = st.file_uploader("Wgraj plik PDF umowy:", type="pdf")
    text_input = st.text_area("Lub wklej treść umowy:", height=300)

    if st.button("Analizuj"):
        contract_text = extract_text_from_pdf(uploaded_file) if uploaded_file else text_input
        if contract_text:
            summary, score = analyze_text(contract_text)
            level, icon, comment = ocena_poziomu_ryzyka(score)

            st.subheader("📌 Podsumowanie ryzyk")
            st.markdown(summary)
            st.metric("Liczba wykrytych ryzyk", score)
            st.markdown(f"### {icon} Poziom ryzyka: {level}")
            st.info(comment)

            if score >= 4:
                st.error("⚠️ Duże ryzyko! Zalecamy konsultację z prawnikiem.")

            pdf_data = generate_pdf(summary)
            st.download_button(label="📥 Pobierz PDF", data=pdf_data, file_name="analiza_umowy.pdf")

            cursor.execute("INSERT INTO analiza (user, tekst, podsumowanie, score, timestamp) VALUES (?, ?, ?, ?, ?)",
                           (session_state.username, contract_text, summary, score, datetime.now().isoformat()))
            conn.commit()

elif menu == "Ryzyka":
    st.title("⚠️ Możliwe ryzyka w umowach")
    st.markdown("""
    - Utrudnione odstąpienie od umowy
    - Dodatkowe obowiązki
    - Dodatkowe opłaty
    - Nieważność umowy
    - Konsekwencje finansowe
    - Skutki prawne
    - Niewywiązanie się z umowy
    """)

elif menu == "Moje Analizy":
    st.title("📂 Historia analiz")
    cursor.execute("SELECT timestamp, score, podsumowanie FROM analiza WHERE user = ? ORDER BY timestamp DESC", (session_state.username,))
    rows = cursor.fetchall()
    for ts, sc, summ in rows:
        st.markdown(f"### 📅 {ts}  —  🎯 Ryzyk: {sc}")
        st.markdown(summ)
        st.markdown("---")
