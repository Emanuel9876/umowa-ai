import streamlit as st
from PyPDF2 import PdfReader
import hashlib
import json
import sqlite3
import os
from datetime import datetime

st.set_page_config(page_title="Umowa AI", layout="wide")

# --- Baza danych i użytkownicy (szkielet) ---
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

# --- Stan sesji ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

if "language" not in st.session_state:
    st.session_state.language = "PL"

if "sensitivity" not in st.session_state:
    st.session_state.sensitivity = "Średni"

if "custom_keywords" not in st.session_state:
    st.session_state.custom_keywords = []

# --- Tłumaczenia ---
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
    "Wczytaj PDF z umową": {"PL": "Wczytaj PDF z umową", "EN": "Upload contract PDF", "DE": "Vertrags-PDF hochladen"},
    "Wybierz czułość analizy": {"PL": "Wybierz czułość analizy", "EN": "Choose analysis sensitivity", "DE": "Analyseempfindlichkeit wählen"},
    "Dodaj własne słowa kluczowe (oddziel przecinkami)": {"PL": "Dodaj własne słowa kluczowe (oddziel przecinkami)", "EN": "Add custom keywords (comma separated)", "DE": "Eigene Schlüsselwörter hinzufügen (kommagetrennt)"},
    "Rozpocznij analizę": {"PL": "Rozpocznij analizę", "EN": "Start analysis", "DE": "Analyse starten"},
    "Zaloguj się": {"PL": "Zaloguj się", "EN": "Log In", "DE": "Anmelden"},
    "Zarejestruj się": {"PL": "Zarejestruj się", "EN": "Sign Up", "DE": "Registrieren"},
    "Wyloguj się": {"PL": "Wyloguj się", "EN": "Log Out", "DE": "Abmelden"},
    "Login": {"PL": "Login", "EN": "Login", "DE": "Benutzername"},
    "Hasło": {"PL": "Hasło", "EN": "Password", "DE": "Passwort"},
    "Nie masz konta?": {"PL": "Nie masz konta?", "EN": "Don't have an account?", "DE": "Kein Konto?"},
    "Zarejestruj się teraz": {"PL": "Zarejestruj się teraz", "EN": "Sign up now", "DE": "Jetzt registrieren"},
}

# --- Styl CSS ---

st.markdown("""
<style>
.stApp {
    background: radial-gradient(circle at top left, #001a33 10%, #000d1a 90%);
    color: #aaffff;
    font-family: 'Orbitron', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    min-height: 100vh;
    padding-bottom: 3rem;
}

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

.main-container h1 {
    font-size: 4em;
    margin-bottom: 10px;
    letter-spacing: 5px;
    text-shadow:
        0 0 15px #00ffff,
        0 0 40px #00ffff;
}

.main-container h3 {
    font-size: 2em;
    margin-bottom: 25px;
    font-weight: 600;
    text-shadow:
        0 0 10px #33ffff;
}

.main-container p {
    font-size: 1.3em;
    max-width: 800px;
    margin-left: auto;
    margin-right: auto;
    margin-bottom: 1.5em;
    color: #88eeffcc;
}

.main-container ul {
    list-style-type: none;
    padding-left: 0;
    font-size: 1.3em;
    max-width: 650px;
    margin: 0 auto 2.5em auto;
    text-align: left;
}

.main-container ul li {
    margin: 15px 0;
    position: relative;
    padding-left: 35px;
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

.main-container button {
    background: linear-gradient(90deg, #00ffff, #006677);
    color: #003344;
    border-radius: 20px;
    padding: 15px 50px;
    border: none;
    font-weight: 900;
    font-size: 1.6em;
    box-shadow:
        0 0 30px #00ffff,
        0 0 80px #00ffff inset;
    margin-top: 40px;
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
    margin-bottom: 25px;
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

.login-container {
    max-width: 400px;
    margin: 80px auto;
    background: rgba(0, 30, 40, 0.9);
    border-radius: 25px;
    padding: 40px 50px;
    box-shadow:
        0 0 35px #00ffffcc,
        inset 0 0 20px #00ffffaa;
    color: #aaffff;
    font-family: 'Orbitron', sans-serif;
    text-align: center;
}

.login-container h2 {
    margin-bottom: 25px;
    font-size: 2.5em;
    letter-spacing: 3px;
    text-shadow:
        0 0 10px #00ffff,
        0 0 30px #33ffff;
}

.login-container label {
    display: block;
    text-align: left;
    font-weight: 700;
    margin-bottom: 10px;
    font-size: 1.1em;
    color: #66ffff;
}

.login-container input {
    width: 100%;
    padding: 10px 15px;
    margin-bottom: 25px;
    font-size: 1.1em;
    border-radius: 12px;
    border: 2px solid #00cccc;
    background: #002244;
    color: #00ffff;
    outline: none;
    font-family: 'Orbitron', sans-serif;
}

.login-container button {
    width: 100%;
    padding: 12px 0;
    background: linear-gradient(90deg, #00ffff, #006677);
    border: none;
    border-radius: 20px;
    color: #003344;
    font-weight: 900;
    font-size: 1.3em;
    box-shadow:
        0 0 30px #00ffff,
        0 0 80px #00ffff inset;
    cursor: pointer;
    letter-spacing: 2px;
    transition: all 0.4s ease;
}

.login-container button:hover {
    background: linear-gradient(90deg, #33ffff, #0099aa);
    color: #001922;
    box-shadow:
        0 0 50px #33ffff,
        0 0 120px #33ffff inset;
    transform: scale(1.05);
}

</style>
""", unsafe_allow_html=True)

# --- Funkcje ---

def extract_text_from_pdf(pdf_file):
    pdf_reader = PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted + "\n"
    return text

# --- UI Funkcje ---

def login_page():
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown(f"<h2>{translations['Zaloguj się'][st.session_state.language]}</h2>", unsafe_allow_html=True)
    username = st.text_input(translations["Login"][st.session_state.language])
    password = st.text_input(translations["Hasło"][st.session_state.language], type="password")
    if st.button(translations["Zaloguj się"][st.session_state.language]):
        if username in users and users[username] == hash_password(password):
            st.session_state.logged_in = True
            st.session_state.username = username
            st.success(f"Zalogowano jako {username}")
        else:
            st.error("Nieprawidłowy login lub hasło.")
    st.markdown(f"<p>{translations['Nie masz konta?'][st.session_state.language]} <a href='#' onclick='window.location.reload();'>{translations['Zarejestruj się teraz'][st.session_state.language]}</a></p>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

def signup_page():
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown(f"<h2>{translations['Zarejestruj się'][st.session_state.language]}</h2>", unsafe_allow_html=True)
    new_username = st.text_input(translations["Login"][st.session_state.language], key="signup_user")
    new_password = st.text_input(translations["Hasło"][st.session_state.language], type="password", key="signup_pass")
    if st.button(translations["Zarejestruj się"][st.session_state.language]):
        if new_username in users:
            st.error("Użytkownik już istnieje.")
        elif len(new_password) < 5:
            st.error("Hasło jest za krótkie (min 5 znaków).")
        elif new_username.strip() == "":
            st.error("Login nie może być pusty.")
        else:
            users[new_username] = hash_password(new_password)
            save_users(users)
            st.success("Rejestracja zakończona pomyślnie! Możesz się teraz zalogować.")
    st.markdown('</div>', unsafe_allow_html=True)

def show_home():
    st.markdown("""
    <div class="main-container">
        <h1>Umowa AI</h1>
        <h3>Twoim asystencie do analizy umów</h3>
        <p>Witaj w naszej aplikacji, która wspiera Cię w szybkiej i precyzyjnej analizie umów. Dzięki nowoczesnym technologiom automatycznie przetwarzamy dokumenty, identyfikując kluczowe zagadnienia i potencjalne ryzyka.</p>
        <p>Naszym celem jest ułatwienie Twojej pracy prawniczej lub biznesowej poprzez:</p>
        <ul>
            <li>📥 Proste wczytywanie dokumentów PDF</li>
            <li>🎯 Regulację czułości analizy dla optymalnych wyników</li>
            <li>🧠 Możliwość dodania własnych słów kluczowych do wyszukiwania</li>
            <li>📊 Intuicyjne prezentowanie wyników oraz eksport raportów</li>
            <li>🔒 Bezpieczeństwo Twoich danych i analiz dzięki logowaniu</li>
        </ul>
        <p>Przekonaj się sam, jak łatwo możesz zoptymalizować analizę umów i minimalizować ryzyka.</p>
        <button onclick="window.scrollTo(0, document.body.scrollHeight);">Rozpocznij analizę</button>
    </div>
    """, unsafe_allow_html=True)

def show_analysis():
    st.markdown('<div class="analysis-container">', unsafe_allow_html=True)
    st.markdown(f"<h1>{translations['Analiza Umowy'][st.session_state.language]}</h1>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        uploaded_file = st.file_uploader(translations["Wczytaj PDF z umową"][st.session_state.language], type=["pdf"])
    with col2:
        sensitivity = st.selectbox(
            translations["Wybierz czułość analizy"][st.session_state.language],
            ["Niski", "Średni", "Wysoki"],
            index=["Niski", "Średni", "Wysoki"].index(st.session_state.sensitivity)
        )
        custom_keywords = st.text_input(
            translations["Dodaj własne słowa kluczowe (oddziel przecinkami)"][st.session_state.language],
            value=",".join(st.session_state.custom_keywords)
        )

    if st.button(translations["Rozpocznij analizę"][st.session_state.language]):
        if uploaded_file is None:
            st.error("Proszę wczytać plik PDF.")
            return

        st.session_state.sensitivity = sensitivity
        st.session_state.custom_keywords = [kw.strip() for kw in custom_keywords.split(",") if kw.strip()]
        text = extract_text_from_pdf(uploaded_file)
        st.success("PDF został wczytany i przetworzony.")

        # Prosty przykład analizy: liczymy wystąpienia słów kluczowych
        keywords = {
            "Niski": ["opłata", "termin", "odpowiedzialność"],
            "Średni": ["kara", "odstąpienie", "zobowiązanie"],
            "Wysoki": ["kara umowna", "odszkodowanie", "wypowiedzenie", "niezgodność"]
        }
        keywords_to_search = keywords[sensitivity] + st.session_state.custom_keywords

        found = {}
        text_lower = text.lower()
        for kw in keywords_to_search:
            found[kw] = text_lower.count(kw.lower())

        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("### Wyniki analizy:")
        for kw, count in found.items():
            st.write(f"🔹 Słowo kluczowe '{kw}': znaleziono {count} razy")

        # Tutaj można dodać generowanie podsumowania, wykrywanie ryzyk itp.

    st.markdown('</div>', unsafe_allow_html=True)

def main():
    st.sidebar.title("Umowa AI")
    lang = st.sidebar.radio("Język / Language / Sprache", options=list(lang_options.keys()), index=list(lang_options.keys()).index(st.session_state.language))
    st.session_state.language = lang

    if not st.session_state.logged_in:
        auth_action = st.sidebar.radio("", ["Zaloguj się", "Zarejestruj się"])
        if auth_action == "Zaloguj się":
            login_page()
        else:
            signup_page()
    else:
        st.sidebar.markdown(f"👤 Zalogowany jako: **{st.session_state.username}**")
        if st.sidebar.button(translations["Wyloguj się"][st.session_state.language]):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.experimental_rerun()

        menu = st.sidebar.radio(
            "Nawigacja",
            [
                translations["Strona Główna"][lang],
                translations["Analiza Umowy"][lang],
                translations["Moje Analizy"][lang]
            ]
        )

        if menu == translations["Strona Główna"][lang]:
            show_home()
        elif menu == translations["Analiza Umowy"][lang]:
            show_analysis()
        elif menu == translations["Moje Analizy"][lang]:
            st.markdown("""
            <div class="main-container">
                <h1>Twoje poprzednie analizy</h1>
                <p>Ta funkcja zostanie wkrótce dodana.</p>
            </div>
            """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
