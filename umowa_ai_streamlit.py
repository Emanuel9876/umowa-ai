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

if "sensitivity" not in session_state:
    session_state.sensitivity = "Średni"

if "custom_keywords" not in session_state:
    session_state.custom_keywords = []

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

selected_lang = st.sidebar.selectbox(
    "\U0001F310 Wybierz język / Select Language / Sprache wählen",
    list(lang_options.keys()),
    format_func=lambda x: lang_options[x]
)
session_state.language = selected_lang

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

/* Sidebar styling */
[data-testid="stSidebar"] {
    background-color: #001f33 !important;
    color: #00ffff !important;
    font-weight: 700;
    border-top-right-radius: 25px;
    border-bottom-right-radius: 25px;
    padding: 25px 20px 30px 20px;
    box-shadow: 0 0 15px #00ffffaa;
    font-family: 'Orbitron', sans-serif;
}

[data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
    color: #33ffff !important;
    text-align: center;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 20px;
    text-shadow:
        0 0 10px #00ffff,
        0 0 20px #00ffff;
}

[data-testid="stSidebar"] label {
    color: #66ffff !important;
    font-weight: 600;
}

[data-testid="stSidebar"] .stRadio > label {
    font-size: 1.1em;
    margin-bottom: 15px;
}

[data-testid="stSidebar"] .stButton > button {
    background: linear-gradient(90deg, #00ffff, #006677);
    color: #003344;
    border-radius: 15px;
    padding: 0.7em 2em;
    border: none;
    font-weight: 800;
    font-size: 1.1em;
    box-shadow:
        0 0 15px #00ffff,
        0 0 40px #00ffff inset;
    transition: all 0.4s ease;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-top: 20px;
    width: 100%;
}

[data-testid="stSidebar"] .stButton > button:hover {
    background: linear-gradient(90deg, #33ffff, #0099aa);
    color: #001922;
    box-shadow:
        0 0 30px #33ffff,
        0 0 80px #33ffff inset;
    cursor: pointer;
    transform: scale(1.05);
}

/* Main content container for home page */
.main-container {
    max-width: 900px;
    margin: 60px auto 80px auto;
    background: rgba(0, 30, 40, 0.9);
    border-radius: 30px;
    padding: 50px 70px;
    box-shadow:
        0 0 40px #00ffffcc,
        inset 0 0 25px #00ffffaa;
    color: #aaffff;
    text-align: center;
    font-family: 'Orbitron', sans-serif;
    line-height: 1.8;
}

/* Large centered heading */
.main-container h1 {
    font-size: 3.8em;
    margin-bottom: 10px;
    letter-spacing: 5px;
    text-shadow:
        0 0 15px #00ffff,
        0 0 40px #00ffff;
}

/* Subtitle */
.main-container h3 {
    font-size: 1.8em;
    margin-bottom: 35px;
    font-weight: 600;
    text-shadow:
        0 0 10px #33ffff;
}

/* Neon styled list */
.main-container ul {
    list-style-type: none;
    padding-left: 0;
    font-size: 1.4em;
    max-width: 650px;
    margin: 0 auto;
}

.main-container ul li {
    margin: 18px 0;
    position: relative;
    padding-left: 35px;
    text-align: left;
}

.main-container ul li::before {
    content: "▸";
    position: absolute;
    left: 0;
    color: #00ffff;
    text-shadow: 0 0 14px #00ffff;
    font-weight: 900;
    font-size: 1.6em;
}

/* Button large on main container */
.main-container button {
    background: linear-gradient(90deg, #00ffff, #006677);
    color: #003344;
    border-radius: 20px;
    padding: 15px 40px;
    border: none;
    font-weight: 900;
    font-size: 1.6em;
    box-shadow:
        0 0 25px #00ffff,
        0 0 60px #00ffff inset;
    margin-top: 40px;
    cursor: pointer;
    transition: all 0.5s ease;
    text-transform: uppercase;
    letter-spacing: 3px;
}

.main-container button:hover {
    background: linear-gradient(90deg, #33ffff, #0099aa);
    color: #001922;
    box-shadow:
        0 0 45px #33ffff,
        0 0 100px #33ffff inset;
    transform: scale(1.1);
}
</style>

<div class="stars"></div>
""", unsafe_allow_html=True)

def extract_text_from_pdf(file):
    try:
        pdf = PdfReader(file)
        text = ""
        for page in pdf.pages:
            text += page.extract_text() + "\n"
        return text
    except:
        return ""

def analyze_text(text, keywords):
    results = []
    text_lower = text.lower()
    for kw in keywords:
        if kw.lower() in text_lower:
            results.append(kw)
    return results

def calculate_score(found_keywords):
    return len(found_keywords) * 10

def generate_summary(found_keywords):
    if not found_keywords:
        return "Brak wykrytych kluczowych ryzyk."
    return "Wykryte ryzyka: " + ", ".join(found_keywords)

def save_analysis(user, tekst, podsumowanie, score):
    timestamp = datetime.now().isoformat(timespec='seconds')
    cursor.execute('INSERT INTO analiza (user, tekst, podsumowanie, score, timestamp) VALUES (?, ?, ?, ?, ?)', (user, tekst, podsumowanie, score, timestamp))
    conn.commit()

def login():
    st.sidebar.markdown("<h2>🔑 Logowanie</h2>", unsafe_allow_html=True)
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
    st.sidebar.markdown("<h2>📝 Rejestracja</h2>", unsafe_allow_html=True)
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
            st.experimental_rerun()

def logout():
    if st.sidebar.button("🚪 Wyloguj się"):
        session_state.logged_in = False
        session_state.username = ""
        st.sidebar.success("Wylogowano")
        st.experimental_rerun()

menu = {
    "main": translations["Strona Główna"][session_state.language],
    "analysis": translations["Analiza Umowy"][session_state.language],
    "risks": translations["Ryzyka"][session_state.language],
    "my_analyses": translations["Moje Analizy"][session_state.language],
}

selected_page = st.sidebar.radio("Menu", list(menu.values()))

def show_home():
    st.markdown("""
    <div class="main-container">
        <h1>{title}</h1>
        <h3>{subtitle}</h3>
        <p>{desc1}</p>
        <p>{desc2}</p>
        <ul>
            <li>Wczytaj dokument PDF</li>
            <li>Skonfiguruj czułość analizy</li>
            <li>Dodaj własne słowa kluczowe</li>
            <li>Przeglądaj wyniki i zapisuj analizy</li>
        </ul>
    </div>
    """.format(
        title=translations["Strona Główna"][session_state.language],
        subtitle=translations["Witaj w aplikacji"][session_state.language],
        desc1=translations["Twoim asystencie do analizy umów"][session_state.language],
        desc2=translations["Automatycznie analizujemy dokumenty"][session_state.language] + "<br>" + translations["i prezentujemy je w czytelnej formie"][session_state.language]
    ), unsafe_allow_html=True)

def show_analysis():
    st.title(menu["analysis"])
    col1, col2 = st.columns([1,1])

    with col1:
        st.write("📄 Wczytaj plik PDF do analizy:")
        uploaded_file = st.file_uploader("Wybierz plik PDF", type=["pdf"])
        pdf_text = ""
        if uploaded_file is not None:
            pdf_text = extract_text_from_pdf(uploaded_file)
            if not pdf_text.strip():
                st.error("Nie udało się wyodrębnić tekstu z pliku PDF.")
                return
            st.text_area("Wyodrębniony tekst z PDF", pdf_text, height=200, max_chars=None)

    with col2:
        st.write("✍️ Wpisz / wklej treść umowy ręcznie do analizy:")
        manual_text = st.text_area("Treść umowy ręcznie", height=350)

    # Ustawienia
    sensitivity = st.selectbox("Wybierz czułość analizy", ["Niski", "Średni", "Wysoki"], index=1)
    session_state.sensitivity = sensitivity

    default_keywords = ["kara umowna", "odszkodowanie", "odpowiedzialność", "kara", "termin", "rozwiązanie", "odpowiedzialność"]
    keywords = default_keywords + session_state.custom_keywords

    st.write("Dodaj własne słowa kluczowe (oddzielone przecinkami):")
    custom_kw_input = st.text_input("", value=", ".join(session_state.custom_keywords))
    if custom_kw_input:
        session_state.custom_keywords = [kw.strip() for kw in custom_kw_input.split(",") if kw.strip()]

    # Połącz tekst z PDF i tekst ręczny do analizy
    combined_text = (pdf_text or "") + "\n" + (manual_text or "")

    if st.button("Analizuj"):
        if not combined_text.strip():
            st.error("Proszę wczytać plik PDF lub wpisać tekst umowy ręcznie.")
            return

        found = analyze_text(combined_text, keywords)
        score = calculate_score(found)
        summary = generate_summary(found)

        st.success(summary)
        st.write(f"Wskaźnik ryzyka: {score}")

        save_analysis(session_state.username, combined_text, summary, score)

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

def show_risks():
    st.title(menu["risks"])
    st.write("Strona z analizą i wykresami ryzyk (do implementacji).")

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
