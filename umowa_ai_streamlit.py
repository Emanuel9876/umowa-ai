import streamlit as st
import re
from PyPDF2 import PdfReader
from reportlab.pdfgen import canvas
import io
import sqlite3
import json
import hashlib
import os
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib
import openai
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
matplotlib.use('Agg')

# Konfiguracja GPT i emaili
openai.api_key = os.getenv("OPENAI_API_KEY")
EMAIL_SENDER = "twoj@email.com"
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

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

def is_premium(user):
    premium_until = users.get(user, {}).get("premium_until")
    if premium_until:
        return datetime.fromisoformat(premium_until) > datetime.now()
    return False

def can_analyze(user):
    cursor.execute("SELECT COUNT(*) FROM analiza WHERE user = ? AND timestamp > ?", (user, (datetime.now() - timedelta(days=30)).isoformat()))
    count = cursor.fetchone()[0]
    return is_premium(user) or count < 3

def send_email(to, subject, body):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = to
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        print(f"Błąd wysyłki maila: {e}")

def analyze_with_gpt(text):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Jesteś prawnikiem. Rozpoznaj typ umowy, analizuj ryzyka, podsumuj umowę."},
                {"role": "user", "content": text}
            ],
            max_tokens=1000,
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Błąd analizy AI: {e}"

users = load_users()
session_state = st.session_state

if "logged_in" not in session_state:
    session_state.logged_in = False
    session_state.username = ""

if "language" not in session_state:
    session_state.language = "PL"

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
                users[username] = {
                    "password": hash_password(password),
                    "premium_until": (datetime.now() + timedelta(days=7)).isoformat()
                }
                save_users(users)
                st.sidebar.success("Rejestracja zakończona sukcesem. Możesz się zalogować.")

    else:
        if st.sidebar.button("Zaloguj"):
            user = users.get(username)
            if user and user.get("password") == hash_password(password):
                session_state.logged_in = True
                session_state.username = username
                st.rerun()
            else:
                st.sidebar.error("Błędny login lub hasło.")
    st.stop()

# STRONA GŁÓWNA (przywrócony oryginalny wygląd)
st.markdown("""
    <style>
    body {
        background: linear-gradient(to right, #0f2027, #203a43, #2c5364);
        color: white;
    }
    .main-title {
        font-size: 48px;
        font-weight: bold;
        text-align: center;
        margin-top: 30px;
    }
    .subtitle {
        font-size: 24px;
        text-align: center;
        margin-bottom: 50px;
    }
    .card {
        background-color: rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        padding: 20px;
        margin: 20px;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-title">🤖 <span style='color:white'>UmowaAI</span></div>
<div class="subtitle">Twój osobisty asystent do analizy umów i wykrywania ryzyk</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("""
    <div class="card">
        <h3>📄 Analiza Umowy</h3>
        <p>Automatycznie analizujemy umowy PDF i wyciągamy kluczowe informacje.</p>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown("""
    <div class="card">
        <h3>⚠️ Wykrywanie Ryzyk</h3>
        <p>Wykrywamy nieoczywiste haczyki i ryzyka w zapisach umownych.</p>
    </div>
    """, unsafe_allow_html=True)
with col3:
    st.markdown("""
    <div class="card">
        <h3>📊 Twoje Analizy</h3>
        <p>Przeglądaj i porównuj wszystkie swoje wcześniejsze analizy w przejrzysty sposób.</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("""
<div class="card">
    <h3>🚀 Dlaczego UmowaAI?</h3>
    <ul>
        <li>✅ Intuicyjny i nowoczesny interfejs</li>
        <li>✅ Wysoka skuteczność wykrywania niekorzystnych zapisów</li>
        <li>✅ Bezpieczeństwo i poufność danych</li>
        <li>✅ Historia wszystkich Twoich analiz</li>
    </ul>
</div>
""", unsafe_allow_html=True)
