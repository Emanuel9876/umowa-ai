import streamlit as st
import re
from PyPDF2 import PdfReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import io
import sqlite3
import json
import hashlib
import os
from datetime import datetime

st.set_page_config(page_title="Umowa AI", layout="wide")

# Połączenie z bazą danych
conn = sqlite3.connect("umowa_ai.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS analiza (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT,
    tekst TEXT,
    podsumowanie TEXT,
    score INTEGER,
    timestamp TEXT
)
''')
conn.commit()

# Funkcje do obsługi użytkowników
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

# Inicjalizacja session_state
if "logged_in" not in session_state:
    session_state.logged_in = False
    session_state.username = ""

if "language" not in session_state:
    session_state.language = "PL"

if "sensitivity" not in session_state:
    session_state.sensitivity = "Średni"

if "custom_keywords" not in session_state:
    session_state.custom_keywords = []

# Tłumaczenia i języki
lang_options = {"PL": "Polski", "EN": "English", "DE": "Deutsch"}
translations = {
    "Strona Główna": {"PL": "Strona Główna", "EN": "Home", "DE": "Startseite"},
    "Analiza Umowy": {"PL": "Analiza Umowy", "EN": "Contract Analysis", "DE": "Vertragsanalyse"},
    "Ryzyka": {"PL": "Ryzyka", "EN": "Risks", "DE": "Risiken"},
    "Moje Analizy": {"PL": "Moje Analizy", "EN": "My Analyses", "DE": "Meine Analysen"},
    "Witaj w aplikacji": {"PL": "Witaj w aplikacji", "EN": "Welcome to the app", "DE": "Willkommen in der App"},
    "Twoim asystencie do analizy umów": {"PL": "Twoim asystencie do analizy umów", "EN": "Your contract analysis assistant", "DE": "Ihr Vertragsanalyse-Assistent"},
    "Automatycznie analizujemy dokumenty": {"PL": "Automatycznie analizujemy dokumenty", "EN": "We automatically analyze documents", "DE": "Wir analysieren automatisch Dokumente"},
    "i prezentujemy je w czytelnej formie": {"PL": "i prezentujemy je w czytelnej formie", "EN": "and present them in a clear form", "DE": "und präsentieren sie in klarer Form"},
}

# Wybór języka w sidebarze
selected_lang = st.sidebar.selectbox(
    "\U0001F310 Wybierz język / Select Language / Sprache wählen",
    list(lang_options.keys()),
    format_func=lambda x: lang_options[x]
)
session_state.language = selected_lang

# Styl CSS i efekty neonów + gwiazdy
st.markdown("""
<style>
/* Body gradient + dark cosmic background */
.stApp {
    background: radial-gradient(circle at top left, #00ffff 10%, #001a33 90%);
    color: #e0f7fa;
    font-family: 'Orbitron', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    min-height: 100vh;
    padding-bottom: 3rem;
    overflow-x: hidden;
    position: relative;
}

/* Animate stars in background */
@keyframes star-blink {
    0%, 100% {opacity: 1;}
    50% {opacity: 0.3;}
}

.stars {
    position: fixed;
    width: 100%;
    height: 100%;
    pointer-events: none;
    top: 0;
    left: 0;
    z-index: 0;
    background:
      radial-gradient(2px 2px at 10% 20%, #00ffff, transparent),
      radial-gradient(1.5px 1.5px at 50% 30%, #00ffff, transparent),
      radial-gradient(2px 2px at 80% 25%, #33ffff, transparent),
      radial-gradient(1px 1px at 30% 50%, #00ffff, transparent),
      radial-gradient(1.7px 1.7px at 60% 60%, #33ffff, transparent),
      radial-gradient(1.2px 1.2px at 85% 70%, #00ffff, transparent);
    animation: star-blink 5s infinite ease-in-out;
}

/* Sidebar style */
.css-1d391kg {
    background-color: #002f4b !important;
    color: white !important;
    font-weight: 600;
}

/* Sidebar font color white */
.css-1d391kg * {
    color: white !important;
}

/* Menu selectbox items font white */
div[role="listbox"] div {
    color: white !important;
}

/* Headers neon glow and pulsate */
h1, h2, h3, h4, h5, h6 {
    color: #00ffff;
    text-shadow:
       0 0 10px #00ffff,
       0 0 30px #00ffff,
       0 0 50px #00ffff,
       0 0 80px #00ffff;
    animation: pulse-glow 4s infinite ease-in-out;
}

/* Pulse glow animation */
@keyframes pulse-glow {
    0%, 100% {
        text-shadow:
           0 0 10px #00ffff,
           0 0 30px #00ffff,
           0 0 50px #00ffff,
           0 0 80px #00ffff;
    }
    50% {
        text-shadow:
           0 0 20px #33ffff,
           0 0 50px #33ffff,
           0 0 80px #33ffff,
           0 0 120px #33ffff;
    }
}

/* Futuristic card with animated border */
.top-card {
    background: rgba(0, 30, 40, 0.85);
    border-radius: 20px;
    padding: 50px 60px;
    margin: 60px auto;
    max-width: 800px;
    text-align: center;
    line-height: 1.7;
    position: relative;
    color: #aaffff;
    box-shadow:
        0 0 15px #00ffff,
        inset 0 0 15px #00ffff;
    border: 2px solid transparent;
    animation: border-glow 6s linear infinite;
    backdrop-filter: blur(8px);
}

/* Animated glowing border */
@keyframes border-glow {
    0% {
        border-color: #00ffff;
        box-shadow:
          0 0 10px #00ffff,
          inset 0 0 10px #00ffff;
    }
    50% {
        border-color: #33ffff;
        box-shadow:
          0 0 30px #33ffff,
          inset 0 0 30px #33ffff;
    }
    100% {
        border-color: #00ffff;
        box-shadow:
          0 0 10px #00ffff,
          inset 0 0 10px #00ffff;
    }
}

/* List style with glowing bullets */
ul {
    list-style-type: none;
    padding-left: 0;
    max-width: 600px;
    margin: 30px auto 0 auto;
    font-size: 1.3em;
    color: #00ffff;
}

ul li {
    margin: 12px 0;
    position: relative;
    padding-left: 25px;
}

ul li::before {
    content: "▸";
    position: absolute;
    left: 0;
    color: #00ffff;
    text-shadow: 0 0 12px #00ffff;
    font-weight: bold;
    font-size: 1.3em;
}

/* Neon glowing buttons with hover animation */
div.stButton > button:first-child {
    background: linear-gradient(90deg, #00ffff, #006677);
    color: #003344;
    border-radius: 15px;
    padding: 0.8em 2.4em;
    border: none;
    font-weight: 800;
    font-size: 1.15em;
    box-shadow:
        0 0 15px #00ffff,
        0 0 40px #00ffff inset;
    transition: all 0.4s ease;
    text-transform: uppercase;
    letter-spacing: 1.5px;
}

div.stButton > button:first-child:hover {
    background: linear-gradient(90deg, #33ffff, #0099aa);
    color: #001922;
    box-shadow:
        0 0 30px #33ffff,
        0 0 80px #33ffff inset;
    cursor: pointer;
    transform: scale(1.05);
}

/* Text area futuristic style */
textarea, input[type="text"], input[type="password"], select {
    background: rgba(0, 30, 40, 0.75);
    border: 1.8px solid #00ffff;
    border-radius: 12px;
    color: #aaffff;
    font-size: 1em;
    padding: 12px 15px;
    width: 100%;
    box-sizing: border-box;
    margin-bottom: 15px;
    transition: border-color 0.3s ease;
}

textarea:focus, input[type="text"]:focus, input[type="password"]:focus, select:focus {
    outline: none;
    border-color: #33ffff;
    box-shadow: 0 0 12px #33ffff;
}

/* Scrollbar for main area */
::-webkit-scrollbar {
    width: 10px;
}

::-webkit-scrollbar-track {
    background: #001a33;
}

::-webkit-scrollbar-thumb {
    background: #00ffff;
    border-radius: 5px;
}

</style>

<div class="stars"></div>
""", unsafe_allow_html=True)

# --- FUNKCJE ANALIZY ---

# Funkcja do ekstrakcji tekstu z PDF
def extract_text_from_pdf(file):
    try:
        pdf = PdfReader(file)
        text = ""
        for page in pdf.pages:
            text += page.extract_text() + "\n"
        return text
    except:
        return ""

# Funkcja do analizy tekstu i wykrywania słów kluczowych
def analyze_text(text, keywords):
    results = []
    text_lower = text.lower()
    for kw in keywords:
        if kw.lower() in text_lower:
            results.append(kw)
    return results

# Prosty scoring na podstawie liczby trafień słów kluczowych
def calculate_score(found_keywords):
    return len(found_keywords) * 10

# Generowanie podsumowania (proste, na podstawie znalezionych słów)
def generate_summary(found_keywords):
    if not found_keywords:
        return "Brak wykrytych kluczowych ryzyk."
    return "Wykryte ryzyka: " + ", ".join(found_keywords)

# Funkcja do zapisu analizy do bazy
def save_analysis(user, tekst, podsumowanie, score):
    timestamp = datetime.now().isoformat(timespec='seconds')
    cursor.execute('INSERT INTO analiza (user, tekst, podsumowanie, score, timestamp) VALUES (?, ?, ?, ?, ?)', (user, tekst, podsumowanie, score, timestamp))
    conn.commit()

# --- LOGOWANIE i REJESTRACJA ---

def login():
    st.sidebar.header("🔑 Logowanie")
    username = st.sidebar.text_input("Nazwa użytkownika")
    password = st.sidebar.text_input("Hasło", type="password")
    if st.sidebar.button("Zaloguj"):
        if username in users and users[username]["password"] == hash_password(password):
            session_state.logged_in = True
            session_state.username = username
            st.sidebar.success(f"Zalogowano jako {username}")
        else:
            st.sidebar.error("Nieprawidłowa nazwa użytkownika lub hasło")

def register():
    st.sidebar.header("📝 Rejestracja")
    new_user = st.sidebar.text_input("Nazwa użytkownika", key="reg_user")
    new_pass = st.sidebar.text_input("Hasło", type="password", key="reg_pass")
    new_pass2 = st.sidebar.text_input("Powtórz hasło", type="password", key="reg_pass2")
    if st.sidebar.button("Zarejestruj"):
        if not new_user or not new_pass:
            st.sidebar.error("Wypełnij wszystkie pola")
        elif new_user in users:
            st.sidebar.error("Użytkownik już istnieje")
        elif new_pass != new_pass2:
            st.sidebar.error("Hasła nie są takie same")
        else:
            users[new_user] = {"password": hash_password(new_pass)}
            save_users(users)
            st.sidebar.success("Rejestracja udana! Zaloguj się.")
            # Czyszczenie pól
            st.experimental_rerun()

def logout():
    if st.sidebar.button("🚪 Wyloguj się"):
        session_state.logged_in = False
        session_state.username = ""
        st.sidebar.success("Wylogowano")
        st.experimental_rerun()

# --- MENU GŁÓWNE ---

menu = {
    "main": translations["Strona Główna"][session_state.language],
    "analysis": translations["Analiza Umowy"][session_state.language],
    "risks": translations["Ryzyka"][session_state.language],
    "my_analyses": translations["Moje Analizy"][session_state.language],
}

selected_page = st.sidebar.radio("Menu", list(menu.values()))

# --- STRONA GŁÓWNA ---

def show_home():
    st.markdown('<div class="top-card">', unsafe_allow_html=True)
    st.title(translations["Strona Główna"][session_state.language])
    st.header(translations["Witaj w aplikacji"][session_state.language])
    st.subheader(translations["Twoim asystencie do analizy umów"][session_state.language])
    st.write(translations["Automatycznie analizujemy dokumenty"][session_state.language])
    st.write(translations["i prezentujemy je w czytelnej formie"][session_state.language])
    st.markdown("""
    <ul>
        <li>Wczytaj dokument PDF</li>
        <li>Skonfiguruj czułość analizy</li>
        <li>Dodaj własne słowa kluczowe</li>
        <li>Przeglądaj wyniki i zapisuj analizy</li>
    </ul>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- STRONA ANALIZY ---

def show_analysis():
    st.title(menu["analysis"])

    st.write("Wczytaj plik PDF do analizy:")
    uploaded_file = st.file_uploader("Wybierz plik PDF", type=["pdf"])
    if uploaded_file is not None:
        text = extract_text_from_pdf(uploaded_file)
        if not text.strip():
            st.error("Nie udało się wyodrębnić tekstu z pliku PDF.")
            return
        st.text_area("Wyodrębniony tekst", text, height=200, max_chars=None, key="extracted_text")

        # Czułość analizy
        sensitivity = st.selectbox("Wybierz czułość analizy", ["Niski", "Średni", "Wysoki"], index=1)
        session_state.sensitivity = sensitivity

        # Słowa kluczowe domyślne i niestandardowe
        default_keywords = ["kara umowna", "odszkodowanie", "odpowiedzialność", "kara", "termin", "rozwiązanie", "kara umowna"]
        keywords = default_keywords + session_state.custom_keywords

        st.write("Dodaj własne słowa kluczowe (oddzielone przecinkami):")
        custom_kw_input = st.text_input("", value=", ".join(session_state.custom_keywords))
        if custom_kw_input:
            session_state.custom_keywords = [kw.strip() for kw in custom_kw_input.split(",") if kw.strip()]

        if st.button("Analizuj"):
            found = analyze_text(text, keywords)
            score = calculate_score(found)
            summary = generate_summary(found)

            st.success(summary)
            st.write(f"Wskaźnik ryzyka: {score}")

            save_analysis(session_state.username, text, summary, score)

            # Pobieranie podsumowania PDF
            buffer = io.BytesIO()
            c = canvas.Canvas(buffer, pagesize=letter)
            c.setFont("Helvetica-Bold", 16)
            c.setFillColorRGB(0, 1, 1)
            c.drawString(72, 720, "Podsumowanie analizy umowy")
            c.setFont("Helvetica", 12)
            c.setFillColorRGB(0.5, 1, 1)
            c.drawString(72, 690, f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            c.drawString(72, 670, f"Użytkownik: {session_state.username}")
            c.drawString(72, 640, "Podsumowanie:")
            text_object = c.beginText(72, 620)
            text_object.setFont("Helvetica", 12)
            text_object.setFillColorRGB(0.5, 1, 1)
            for line in summary.split(", "):
                text_object.textLine("- " + line)
            c.drawText(text_object)
            c.showPage()
            c.save()
            buffer.seek(0)
            st.download_button("Pobierz podsumowanie PDF", buffer, file_name="podsumowanie_umowy.pdf", mime="application/pdf")

# --- STRONA RYZYKA ---

def show_risks():
    st.title(menu["risks"])
    st.write("Strona z analizą i wykresami ryzyk (do implementacji).")

# --- STRONA MOICH ANALIZ ---

def show_my_analyses():
    st.title(menu["my_analyses"])
    cursor.execute("SELECT id, timestamp, podsumowanie, score FROM analiza WHERE user=?", (session_state.username,))
    rows = cursor.fetchall()
    if not rows:
        st.info("Brak zapisanych analiz.")
    else:
        for r in rows:
            st.markdown(f"**ID:** {r[0]} | **Data:** {r[1]} | **Wskaźnik ryzyka:** {r[3]}")
            st.write(r[2])
            st.markdown("---")

# --- GŁÓWNA LOGIKA ---

if not session_state.logged_in:
    login()
    st.sidebar.markdown("---")
    register()
else:
    st.sidebar.markdown(f"**Zalogowany jako:** {session_state.username}")
    logout()

    if selected_page == menu["main"]:
        show_home()
    elif selected_page == menu["analysis"]:
        show_analysis()
    elif selected_page == menu["risks"]:
        show_risks()
    elif selected_page == menu["my_analyses"]:
        show_my_analyses()
