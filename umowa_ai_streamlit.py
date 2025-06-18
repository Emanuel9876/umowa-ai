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
        0 0 30px #00ffff,
        0 0 80px #00ffff inset;
    margin-top: 50px;
    cursor: pointer;
    transition: all 0.4s ease;
    letter-spacing: 2px;
}

.main-container button:hover {
    background: linear-gradient(90deg, #33ffff, #0099aa);
    color: #001922;
    box-shadow:
        0 0 50px #33ffff,
        0 0 120px #33ffff inset;
    transform: scale(1.05);
}

/* Analysis page layout */
.analysis-container {
    max-width: 900px;
    margin: 60px auto 80px auto;
    background: rgba(0, 30, 40, 0.85);
    border-radius: 30px;
    padding: 40px 60px;
    box-shadow:
        0 0 40px #00ffffcc,
        inset 0 0 25px #00ffffaa;
    color: #aaffff;
    font-family: 'Orbitron', sans-serif;
}

.analysis-container h1 {
    font-size: 3em;
    margin-bottom: 20px;
    letter-spacing: 3px;
    text-align: center;
    background: -webkit-linear-gradient(#00ffff, #33ffff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-shadow:
        0 0 10px #00ffff,
        0 0 30px #33ffff;
}

.analysis-row {
    display: flex;
    gap: 30px;
    margin-top: 30px;
    flex-wrap: wrap;
    justify-content: space-between;
}

.analysis-column {
    flex: 1 1 45%;
    min-width: 320px;
}

.analysis-column textarea {
    font-family: 'Courier New', Courier, monospace;
    font-size: 1em;
    border-radius: 15px;
    padding: 15px;
    background: #001a33;
    color: #00ffff;
    border: 2px solid #00cccc;
    resize: vertical;
    min-height: 160px;
}

.analysis-column select, .analysis-column input {
    font-family: 'Orbitron', sans-serif;
    font-size: 1.1em;
    border-radius: 12px;
    background: #002244;
    color: #00ffff;
    border: 2px solid #00cccc;
    padding: 8px 12px;
    width: 100%;
    margin-top: 10px;
    margin-bottom: 20px;
    outline: none;
}

.analysis-column label {
    font-weight: 700;
    font-size: 1.2em;
    display: block;
    margin-bottom: 6px;
}

.analysis-button {
    display: block;
    margin: 0 auto;
    background: linear-gradient(90deg, #00ffff, #006677);
    color: #003344;
    border-radius: 20px;
    padding: 15px 40px;
    border: none;
    font-weight: 900;
    font-size: 1.5em;
    box-shadow:
        0 0 30px #00ffff,
        0 0 80px #00ffff inset;
    cursor: pointer;
    transition: all 0.4s ease;
    letter-spacing: 2px;
}

.analysis-button:hover {
    background: linear-gradient(90deg, #33ffff, #0099aa);
    color: #001922;
    box-shadow:
        0 0 50px #33ffff,
        0 0 120px #33ffff inset;
    transform: scale(1.05);
}

</style>
""", unsafe_allow_html=True)

# Gwiazdy w tle
st.markdown('<div class="stars"></div>', unsafe_allow_html=True)


def show_home():
    st.markdown(f"""
    <div class="main-container">
        <h1 style="font-size:4em; background: -webkit-linear-gradient(#00ffff, #33ffff); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
            {translations["Strona Główna"][session_state.language]}
        </h1>
        <h3 style="font-size:2em; color:#66ffff;">{translations["Witaj w aplikacji"][session_state.language]}</h3>
        <p style="font-size:1.3em; margin-top:1.5em;">
            {translations["Twoim asystencie do analizy umów"][session_state.language]}
        </p>
        <p style="font-size:1.3em;">
            {translations["Automatycznie analizujemy dokumenty"][session_state.language]}<br>
            {translations["i prezentujemy je w czytelnej formie"][session_state.language]}
        </p>
        <ul style="margin-top:2em;">
            <li>📥 Wczytaj dokument PDF</li>
            <li>🎯 Skonfiguruj czułość analizy</li>
            <li>🧠 Dodaj własne słowa kluczowe</li>
            <li>📊 Przeglądaj wyniki i zapisuj analizy</li>
        </ul>
        <button onclick="window.scrollTo(0, document.body.scrollHeight);" style="margin-top:50px;">
            Rozpocznij analizę
        </button>
    </div>
    """, unsafe_allow_html=True)


def show_analysis():
    st.markdown("""
    <div class="analysis-container">
        <h1>Analiza Umowy</h1>
        <div class="analysis-row">
            <div class="analysis-column">
                <label for="pdf_input">Wczytaj PDF z umową</label>
                uploaded_file = st.file_uploader("", type=["pdf"])
            </div>
            <div class="analysis-column">
                <label for="sensitivity_select">Wybierz czułość analizy</label>
                sensitivity = st.selectbox("", ["Niski", "Średni", "Wysoki"], index=1)
                
                <label for="custom_keywords_input">Dodaj własne słowa kluczowe (oddziel przecinkami)</label>
                custom_keywords = st.text_input("", placeholder="np. kara umowna, odszkodowanie, termin zapłaty")
            </div>
        </div>
        <button class="analysis-button">Rozpocznij analizę</button>
    </div>
    """, unsafe_allow_html=True)

    # Poniżej dodajemy działanie formularza Streamlit, bo powyższy HTML to tylko stylizacja
    # Nie da się bezpośrednio mieszać streamlitowych inputów w raw HTML, więc trzeba wywołać Streamlit inputy w Pythonie

    col1, col2 = st.columns(2)

    with col1:
        uploaded_file = st.file_uploader(translations["Wczytaj PDF z umową"][session_state.language] if "Wczytaj PDF z umową" in translations else "Wczytaj PDF z umową", type=["pdf"])
    with col2:
        sensitivity = st.selectbox(
            translations["Wybierz czułość analizy"][session_state.language] if "Wybierz czułość analizy" in translations else "Wybierz czułość analizy",
            ["Niski", "Średni", "Wysoki"],
            index=["Niski", "Średni", "Wysoki"].index(session_state.sensitivity)
        )
        custom_keywords = st.text_input(
            translations["Dodaj własne słowa kluczowe (oddziel przecinkami)"][session_state.language] if "Dodaj własne słowa kluczowe (oddziel przecinkami)" in translations else "Dodaj własne słowa kluczowe (oddziel przecinkami)",
            value=",".join(session_state.custom_keywords)
        )
    if st.button(translations["Rozpocznij analizę"][session_state.language] if "Rozpocznij analizę" in translations else "Rozpocznij analizę"):
        session_state.sensitivity = sensitivity
        session_state.custom_keywords = [kw.strip() for kw in custom_keywords.split(",") if kw.strip()]
        if uploaded_file is not None:
            text = extract_text_from_pdf(uploaded_file)
            st.success("PDF został wczytany i przetworzony.")
            # Tutaj możesz wywołać funkcję analizy umowy
            st.write("Treść umowy:")
            st.write(text)
        else:
            st.error("Proszę wczytać plik PDF.")


def extract_text_from_pdf(pdf_file):
    pdf_reader = PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() + "\n"
    return text


def main():
    st.sidebar.title("Umowa AI")

    pages = {
        "home": show_home,
        "analysis": show_analysis,
        # Dodaj inne podstrony tutaj
    }

    page = st.sidebar.radio(
        "Nawigacja",
        options=["home", "analysis"],
        format_func=lambda x: {
            "home": translations["Strona Główna"][session_state.language],
            "analysis": translations["Analiza Umowy"][session_state.language],
        }[x]
    )

    pages[page]()


if __name__ == "__main__":
    main()
