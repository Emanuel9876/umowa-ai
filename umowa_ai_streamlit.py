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
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib
matplotlib.use('Agg')

# Konfiguracja strony
st.set_page_config(page_title="Umowa AI", layout="wide")

# Baza danych
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

# Zarządzanie użytkownikami
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
translations = {
    "Strona Główna": {"PL": "Strona Główna", "EN": "Home", "DE": "Startseite"},
    "Analiza Umowy": {"PL": "Analiza Umowy", "EN": "Contract Analysis", "DE": "Vertragsanalyse"},
    "Ryzyka": {"PL": "Ryzyka", "EN": "Risks", "DE": "Risiken"},
    "Moje Analizy": {"PL": "Moje Analizy", "EN": "My Analyses", "DE": "Meine Analysen"},
}

selected_lang = st.sidebar.selectbox("🌐 Język / Language", list(lang_options.keys()), format_func=lambda x: lang_options[x])
session_state.language = selected_lang

# Stylizacja
st.markdown("""
    <style>
        .stApp {background: linear-gradient(to right, #2c3e50, #3498db);}
        html, body, [class*="css"] {
            background-color: transparent !important;
            color: #ffffff !important;
        }
        .top-card {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
        }
        h1, h2, h3, h4, h5, h6, p, div, span, label {
            color: #ffffff !important;
        }
    </style>
""", unsafe_allow_html=True)

# Logowanie / Rejestracja
if not session_state.logged_in:
    st.sidebar.subheader("🔐 Logowanie / Rejestracja")
    choice = st.sidebar.radio("Opcja", ["Zaloguj się", "Zarejestruj się"])
    username = st.sidebar.text_input("Login")
    password = st.sidebar.text_input("Hasło", type="password")

    if choice == "Zarejestruj się":
        if st.sidebar.button("Zarejestruj"):
            if username in users:
                st.sidebar.warning("Użytkownik już istnieje.")
            else:
                users[username] = hash_password(password)
                save_users(users)
                st.sidebar.success("Zarejestrowano pomyślnie.")
    else:
        if st.sidebar.button("Zaloguj"):
            if username in users and users[username] == hash_password(password):
                session_state.logged_in = True
                session_state.username = username
                st.rerun()
            else:
                st.sidebar.error("Błędne dane logowania.")
    st.stop()

# Menu główne
menu = [
    ("Strona Główna", "🏠"),
    ("Analiza Umowy", "📄"),
    ("Ryzyka", "⚠️"),
    ("Moje Analizy", "📊")
]
menu_labels = [f"{icon} {translations[label][session_state.language]}" for label, icon in menu]
selection = st.sidebar.selectbox("📌 Menu", menu_labels)
selected_option = menu[menu_labels.index(selection)][0]

# Strona Główna
if selected_option == "Strona Główna":
    st.markdown("""
        <div style='text-align: center; padding: 5vh 2vw;'>
            <h1 style='font-size: 4.5em;'>🤖 UmowaAI</h1>
            <p style='font-size: 1.7em;'>Twój osobisty asystent do analizy umów i wykrywania ryzyk</p>
        </div>
    """, unsafe_allow_html=True)

# Analiza Umowy
elif selected_option == "Analiza Umowy":
    st.subheader("📄 Prześlij plik PDF do analizy")
    uploaded_file = st.file_uploader("Wybierz plik PDF", type="pdf")

    if uploaded_file and st.button("🔍 Analizuj"):
        reader = PdfReader(uploaded_file)
        text = "\n".join(page.extract_text() for page in reader.pages if page.extract_text())
        score = text.lower().count("ryzyko")
        summary = "Wykryto potencjalne zagrożenia" if score > 0 else "Nie wykryto niebezpiecznych zapisów"
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("INSERT INTO analiza (user, tekst, podsumowanie, score, timestamp) VALUES (?, ?, ?, ?, ?)",
                       (session_state.username, text, summary, score, now))
        conn.commit()

        st.success("Analiza zakończona!")
        st.write("📑 Podsumowanie:", summary)
        st.write("📈 Liczba wystąpień słowa 'ryzyko':", score)

# Ryzyka
elif selected_option == "Ryzyka":
    st.subheader("⚠️ Wykrywanie ryzyk")
    cursor.execute("SELECT tekst FROM analiza WHERE user = ? ORDER BY id DESC LIMIT 1", (session_state.username,))
    result = cursor.fetchone()
    if result:
        text = result[0]
        ryzykowne_zapisy = re.findall(r"(ryzyko.*?\\.)", text, re.IGNORECASE)
        if ryzykowne_zapisy:
            st.warning("Znaleziono ryzykowne zapisy:")
            for r in ryzykowne_zapisy:
                st.markdown(f"- {r}")
        else:
            st.success("Brak oczywistych ryzyk w ostatnim dokumencie.")
    else:
        st.info("Nie wykonano jeszcze żadnej analizy.")

# Moje Analizy
elif selected_option == "Moje Analizy":
    st.subheader("📊 Historia Twoich analiz")
    cursor.execute("SELECT podsumowanie, score, timestamp FROM analiza WHERE user = ? ORDER BY id DESC", (session_state.username,))
    records = cursor.fetchall()

    if records:
        df = {
            "Data": [r[2] for r in records],
            "Ryzykowność": [r[1] for r in records],
            "Podsumowanie": [r[0] for r in records]
        }

        st.table(df)

        fig, ax = plt.subplots()
        sns.lineplot(x=df["Data"], y=df["Ryzykowność"], marker="o", ax=ax)
        plt.xticks(rotation=45)
        st.pyplot(fig)
    else:
        st.info("Brak zapisanych analiz.")
