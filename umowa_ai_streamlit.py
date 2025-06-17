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

selected_lang = st.sidebar.selectbox("\U0001F310 Wybierz język / Select Language / Sprache wählen", list(lang_options.keys()), format_func=lambda x: lang_options[x])
session_state.language = selected_lang

# Kosmiczne animacje i efekty neonów + gwiazdy tło
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
textarea {
    background: rgba(0, 51, 77, 0.9) !important;
    color: #aaffff !important;
    border-radius: 15px !important;
    border: 2px solid #00ffff !important;
    font-size: 1.05em !important;
    padding: 18px !important;
    font-family: 'Consolas', monospace !important;
    box-shadow: 0 0 15px #00ffff inset;
    transition: border-color 0.4s ease;
}

textarea:focus {
    border-color: #33ffff !important;
    outline: none !important;
    box-shadow: 0 0 25px #33ffff inset !important;
}

/* Scrollbar stylization */
::-webkit-scrollbar {
    width: 10px;
}
::-webkit-scrollbar-track {
    background: #001a33;
}
::-webkit-scrollbar-thumb {
    background: #00ffff;
    border-radius: 15px;
}

/* Link style with glow */
a, a:visited {
    color: #00ffff;
    text-decoration: none;
    font-weight: 700;
    transition: color 0.3s ease;
}
a:hover {
    text-decoration: underline;
    color: #33ffff;
}

/* Glow animation for main heading */
@keyframes glow {
    0%, 100% {
        text-shadow:
           0 0 12px #00ffff,
           0 0 25px #00ffff,
           0 0 40px #00ffff,
           0 0 70px #00ffff;
    }
    50% {
        text-shadow:
           0 0 25px #33ffff,
           0 0 50px #33ffff,
           0 0 80px #33ffff,
           0 0 140px #33ffff;
    }
}

h1 {
    animation: glow 3s infinite ease-in-out;
}

/* Futuristic icon container with glow */
.icon-container {
    display: inline-block;
    margin: 0 12px;
    vertical-align: middle;
    filter: drop-shadow(0 0 8px #00ffff);
}

/* Responsive adjustments */
@media (max-width: 768px) {
    .top-card {
        padding: 35px 20px;
        margin: 40px 10px;
        max-width: 95%;
    }
    ul {
        font-size: 1.15em;
    }
}
</style>

<!-- Import Orbitron font for futuristic style -->
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@700&display=swap" rel="stylesheet">

<!-- Background stars container -->
<div class="stars"></div>
""", unsafe_allow_html=True)

if not session_state.logged_in:
    st.sidebar.subheader("\U0001F510 Logowanie / Rejestracja")
    choice = st.sidebar.radio("Wybierz opcję", ["Zaloguj się", "Zarejestruj się"])
    username = st.sidebar.text_input("Nazwa użytkownika")
    password = st.sidebar.text_input("Hasło", type="password")
    if choice == "Zarejestruj się":
        password2 = st.sidebar.text_input("Powtórz hasło", type="password")
        if st.sidebar.button("Zarejestruj się"):
            if not username or not password:
                st.sidebar.error("Uzupełnij wszystkie pola.")
            elif password != password2:
                st.sidebar.error("Hasła nie są takie same.")
            elif username in users:
                st.sidebar.error("Użytkownik już istnieje.")
            else:
                users[username] = hash_password(password)
                save_users(users)
                st.sidebar.success("Zarejestrowano pomyślnie! Zaloguj się.")
    else:
        if st.sidebar.button("Zaloguj się"):
            if username in users and users[username] == hash_password(password):
                session_state.logged_in = True
                session_state.username = username
                st.experimental_rerun()
            else:
                st.sidebar.error("Błędna nazwa użytkownika lub hasło.")
    st.stop()

menu = [translations["Strona Główna"][selected_lang], translations["Analiza Umowy"][selected_lang],
        translations["Ryzyka"][selected_lang], translations["Moje Analizy"][selected_lang]]

choice = st.sidebar.radio("Menu", menu)

def analyze_risks(text, sensitivity, custom_keywords):
    # Prosty przykład analizy ryzyk na podstawie słów kluczowych
    keywords = {
        "kara umowna": 3,
        "odszkodowanie": 2,
        "termin": 1,
        "odpowiedzialność": 2,
        "klauzula poufności": 3,
        "warunki odstąpienia": 3,
        "spory": 2,
    }
    # Dodaj niestandardowe słowa
    for kw in custom_keywords:
        if kw:
            keywords[kw.lower()] = 2

    # Dopasuj czułość
    threshold = {"Niski": 1, "Średni": 2, "Wysoki": 3}.get(sensitivity, 2)

    found = {}
    text_lower = text.lower()
    for k, v in keywords.items():
        count = text_lower.count(k)
        if count * v >= threshold:
            found[k] = count
    return found

def summarize_text(text):
    # Prosta metoda podsumowania: pierwsze 3 zdania
    sentences = re.split(r'(?<=[.!?]) +', text)
    return " ".join(sentences[:3]) if sentences else ""

def generate_pdf_report(text, summary, risks, user):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    p.setFont("Helvetica-Bold", 18)
    p.drawString(30, height - 50, "Raport analizy umowy")
    p.setFont("Helvetica", 12)
    p.drawString(30, height - 80, f"Użytkownik: {user}")
    p.drawString(30, height - 100, f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    p.setFont("Helvetica-Bold", 14)
    p.drawString(30, height - 140, "Podsumowanie:")
    text_object = p.beginText(30, height - 160)
    for line in summary.split('\n'):
        text_object.textLine(line)
    p.drawText(text_object)

    p.setFont("Helvetica-Bold", 14)
    p.drawString(30, height - 220, "Wykryte ryzyka:")
    y = height - 240
    p.setFont("Helvetica", 12)
    if risks:
        for k, v in risks.items():
            p.drawString(40, y, f"- {k}: {v} wystąpień")
            y -= 20
            if y < 50:
                p.showPage()
                y = height - 50
    else:
        p.drawString(40, y, "Brak wykrytych ryzyk.")

    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer

def save_analysis_to_db(user, text, summary, score):
    timestamp = datetime.now().isoformat()
    cursor.execute('INSERT INTO analiza (user, tekst, podsumowanie, score, timestamp) VALUES (?, ?, ?, ?, ?)',
                   (user, text, summary, score, timestamp))
    conn.commit()

def load_user_analyses(user):
    cursor.execute('SELECT id, tekst, podsumowanie, score, timestamp FROM analiza WHERE user=? ORDER BY timestamp DESC', (user,))
    return cursor.fetchall()

# Strona główna - futurystyczna karta powitalna i animacje
if choice == translations["Strona Główna"][selected_lang]:
    st.markdown('<div class="top-card">', unsafe_allow_html=True)
    st.title("\U0001F680 Umowa AI - Twój asystent do analizy umów z przyszłości")
    st.write(translations["Witaj w aplikacji"][selected_lang])
    st.write(translations["Twoim asystencie do analizy umów"][selected_lang])
    st.write(translations["Automatycznie analizujemy dokumenty"][selected_lang])
    st.write(translations["i prezentujemy je w czytelnej formie"][selected_lang])
    st.markdown("""
    <ul>
        <li>⚡ Analiza umów w czasie rzeczywistym z wykorzystaniem AI</li>
        <li>🛸 Kosmiczny, nowoczesny design</li>
        <li>🚀 Eksport raportów do PDF z animowanymi efektami</li>
        <li>✨ Wgrywanie PDF lub wpisywanie umów ręcznie</li>
        <li>🌌 Pełna personalizacja i wielojęzyczność</li>
    </ul>
    <p style="text-align:center; font-size:0.85em; color:#66ffff; margin-top:40px;">
    Jeśli chcesz, mogę zrobić jeszcze bardziej kosmiczne efekty i animacje! 🚀✨
    </p>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

elif choice == translations["Analiza Umowy"][selected_lang]:
    st.header(translations["Analiza Umowy"][selected_lang])

    input_method = st.radio("Wybierz sposób wprowadzenia umowy:", ["Wgraj PDF", "Wpisz ręcznie"])

    contract_text = ""

    if input_method == "Wgraj PDF":
        pdf_file = st.file_uploader("Wgraj plik PDF z umową", type=["pdf"])
        if pdf_file is not None:
            reader = PdfReader(pdf_file)
            contract_text = ""
            for page in reader.pages:
                contract_text += page.extract_text()
            st.success("PDF załadowany pomyślnie!")
    else:
        contract_text = st.text_area("Wpisz lub wklej tekst umowy tutaj", height=300)

    if contract_text:
        sensitivity = st.selectbox("Wybierz czułość analizy", ["Niski", "Średni", "Wysoki"], index=["Niski", "Średni", "Wysoki"].index(session_state.sensitivity))
        session_state.sensitivity = sensitivity
        custom_keywords = st.text_input("Dodaj niestandardowe słowa kluczowe do analizy (oddziel przecinkami)", "")
        if custom_keywords:
            session_state.custom_keywords = [k.strip() for k in custom_keywords.split(",")]
        else:
            session_state.custom_keywords = []

        if st.button("Analizuj umowę"):
            risks_found = analyze_risks(contract_text, sensitivity, session_state.custom_keywords)
            summary = summarize_text(contract_text)
            score = sum(risks_found.values())

            save_analysis_to_db(session_state.username, contract_text, summary, score)

            st.subheader("Podsumowanie umowy:")
            st.write(summary)

            st.subheader("Wykryte ryzyka:")
            if risks_found:
                for k, v in risks_found.items():
                    st.write(f"- **{k}**: {v} wystąpień")
            else:
                st.write("Brak wykrytych ryzyk.")

            # Generowanie raportu PDF
            pdf_buffer = generate_pdf_report(contract_text, summary, risks_found, session_state.username)
            st.download_button("Pobierz raport PDF", pdf_buffer, file_name="raport_umowy.pdf", mime="application/pdf")

elif choice == translations["Ryzyka"][selected_lang]:
    st.header(translations["Ryzyka"][selected_lang])
    st.write("Tutaj można rozbudować wykresy i statystyki dotyczące wykrytych ryzyk w analizowanych umowach.")
    st.write("Funkcjonalność w trakcie rozwoju...")

elif choice == translations["Moje Analizy"][selected_lang]:
    st.header(translations["Moje Analizy"][selected_lang])
    analyses = load_user_analyses(session_state.username)
    if analyses:
        for a_id, tekst, podsumowanie, score, timestamp in analyses:
            with st.expander(f"Analiza z {timestamp[:19]} (Score: {score})"):
                st.write("**Podsumowanie:**")
                st.write(podsumowanie)
                st.write("**Pełny tekst umowy:**")
                st.write(tekst)
    else:
        st.write("Brak zapisanych analiz. Zrób pierwszą analizę!")

