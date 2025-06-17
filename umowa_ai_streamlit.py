import streamlit as st
import re
from PyPDF2 import PdfReader
import io
import sqlite3
import json
import hashlib
import os
from datetime import datetime
import plotly.graph_objects as go
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

st.set_page_config(page_title="Umowa AI", layout="wide")

# --- Baza danych SQLite ---
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
)''')
conn.commit()

# --- Użytkownicy ---
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

# --- Proste tłumaczenia ---
lang_options = {"PL": "Polski", "EN": "English", "DE": "Deutsch"}
translations = {
    "Strona Główna": {"PL": "Strona Główna", "EN": "Home", "DE": "Startseite"},
    "Analiza Umowy": {"PL": "Analiza Umowy", "EN": "Contract Analysis", "DE": "Vertragsanalyse"},
    "Ryzyka": {"PL": "Ryzyka", "EN": "Risks", "DE": "Risiken"},
    "Moje Analizy": {"PL": "Moje Analizy", "EN": "My Analyses", "DE": "Meine Analysen"},
}

selected_lang = st.sidebar.selectbox("\U0001F310 Wybierz język", list(lang_options.keys()), format_func=lambda x: lang_options[x])
session_state.language = selected_lang

# --- Logowanie/Rejestracja ---
if not session_state.logged_in:
    st.sidebar.subheader("\U0001F510 Logowanie / Rejestracja")
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
                st.experimental_rerun()
            else:
                st.sidebar.error("Błędny login lub hasło.")
    st.stop()

# --- Funkcje ---
def analyze_risks_advanced(text, sensitivity, custom_kw):
    # Bardziej inteligentna analiza - wykrywanie ryzyk z ważeniem TF-IDF
    base_risks = {
        "Finansowe": ["kara", "opłata", "odszkodowanie", "koszt", "kaucja"],
        "Prawne": ["rozwiązanie", "wypowiedzenie", "kara umowna", "odpowiedzialność", "odstąpienie"],
        "Terminowe": ["zwłoka", "opóźnienie", "termin", "czas", "deadline"]
    }
    if custom_kw:
        base_risks["Niestandardowe"] = custom_kw

    sensitivity_factor = {"Niski": 0.5, "Średni": 1.0, "Wysoki": 1.5}.get(sensitivity, 1.0)

    # Przygotuj tekst i słowa kluczowe
    text_lower = text.lower()
    found = {}
    for category, keywords in base_risks.items():
        count = 0
        for kw in keywords:
            # Proste liczenie wystąpień i ważenie
            count += text_lower.count(kw.lower())
        score = count * sensitivity_factor
        if score >= 1:
            found[category] = int(score)

    return found

def summarize_text(text):
    sentences = re.split(r'(?<=[.!?]) +', text)
    return ' '.join(sentences[:3]) if sentences else ""

def save_analysis_to_db(user, tekst, podsumowanie, score):
    timestamp = datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO analiza (user, tekst, podsumowanie, score, timestamp)
        VALUES (?, ?, ?, ?, ?)''', (user, tekst, podsumowanie, score, timestamp))
    conn.commit()

def load_user_analyses(user):
    cursor.execute('SELECT id, tekst, podsumowanie, score, timestamp FROM analiza WHERE user=? ORDER BY timestamp DESC', (user,))
    return cursor.fetchall()

def plot_risks_interactive(risks_found):
    fig = go.Figure(data=[go.Bar(
        x=list(risks_found.keys()),
        y=list(risks_found.values()),
        marker_color='orange'
    )])
    fig.update_layout(title_text='Wykryte ryzyka wg kategorii', yaxis_title='Liczba wystąpień')
    return fig

def compare_text_similarity(text1, text2):
    vectorizer = TfidfVectorizer().fit_transform([text1, text2])
    vectors = vectorizer.toarray()
    sim = cosine_similarity([vectors[0]], [vectors[1]])[0][0]
    return sim

# --- Menu ---
menu_options = [
    ("Strona Główna", "\U0001F3E0"),
    ("Analiza Umowy", "\U0001F4C4"),
    ("Ryzyka", "\u26A0"),
    ("Moje Analizy", "\U0001F4CB")
]

translated_menu = [f"{icon} {translations[label][session_state.language]}" for label, icon in menu_options]
menu_choice = st.sidebar.selectbox("Wybierz opcję", translated_menu)
plain_choice = [label for label, icon in menu_options][translated_menu.index(menu_choice)]

# --- Strona Główna ---
if plain_choice == "Strona Główna":
    st.markdown("""
        <div style='text-align: center; padding: 5vh 2vw;'>
            <h1 style='font-size: 4.5em; margin-bottom: 0;'>🤖 UmowaAI</h1>
            <p style='font-size: 1.7em; margin-top: 0;'>Twój osobisty asystent do analizy umów i wykrywania ryzyk</p>
        </div>

        <div style='display: flex; flex-direction: row; justify-content: space-around; flex-wrap: wrap; gap: 2rem; padding: 2rem; background: rgba(255,255,255,0.1); border-radius: 20px; margin-bottom: 2rem;'>
            <div style='flex: 1; min-width: 250px; max-width: 400px;'>
                <h2>📄 Analiza Umowy</h2>
                <p>Automatycznie analizujemy umowy PDF i wyciągamy kluczowe informacje.</p>
            </div>
            <div style='flex: 1; min-width: 250px; max-width: 400px;'>
                <h2>⚠️ Wykrywanie Ryzyk</h2>
                <p>Wykrywamy nieoczywiste haczyki i ryzyka w zapisach umownych.</p>
            </div>
            <div style='flex: 1; min-width: 250px; max-width: 400px;'>
                <h2>📊 Twoje Analizy</h2>
                <p>Przeglądaj i porównuj swoje poprzednie analizy w przejrzystym dashboardzie.</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

# --- Analiza Umowy ---
elif plain_choice == "Analiza Umowy":
    st.header(translations["Analiza Umowy"][session_state.language])

    uploaded_file = st.file_uploader("Wgraj plik PDF z umową", type=["pdf"])
    if uploaded_file:
        pdf = PdfReader(uploaded_file)
        full_text = ""
        for page in pdf.pages:
            full_text += page.extract_text() + " "

        st.text_area("Tekst umowy:", full_text, height=300)

        sensitivity = st.selectbox("Wybierz czułość analizy ryzyk", ["Niski", "Średni", "Wysoki"], index=1)
        session_state.sensitivity = sensitivity

        custom_kw = st.text_input("Dodaj własne słowa kluczowe (oddziel przecinkami)").strip()
        custom_kw_list = [kw.strip() for kw in custom_kw.split(",")] if custom_kw else []
        session_state.custom_keywords = custom_kw_list

        if st.button("Analizuj umowę"):
            risks_found = analyze_risks_advanced(full_text, sensitivity, custom_kw_list)
            summary = summarize_text(full_text)
            score = sum(risks_found.values())
            save_analysis_to_db(session_state.username, full_text, summary, score)

            st.success("Analiza zakończona!")
            st.subheader("Podsumowanie umowy")
            st.write(summary)

            st.subheader("Wykryte ryzyka")
            st.plotly_chart(plot_risks_interactive(risks_found), use_container_width=True)

# --- Ryzyka ---
elif plain_choice == "Ryzyka":
    st.header(translations["Ryzyka"][session_state.language])
    st.write("Przegląd wszystkich ryzyk z Twoich analiz.")

    user_analyses = load_user_analyses(session_state.username)
    if not user_analyses:
        st.info("Brak zapisanych analiz.")
    else:
        # Lista analiz
        choices = {f"{a[4][:16]} - {a[2][:50]}...": a for a in user_analyses}
        selected = st.selectbox("Wybierz analizę do szczegółów", list(choices.keys()))

        chosen_analysis = choices[selected]
        st.write("Podsumowanie:")
        st.write(chosen_analysis[2])
        st.write(f"Ryzyka (ocena): {chosen_analysis[3]}")

# --- Moje Analizy ---
elif plain_choice == "Moje Analizy":
    st.header(translations["Moje Analizy"][session_state.language])
    analyses = load_user_analyses(session_state.username)

    if not analyses:
        st.info("Brak zapisanych analiz.")
    else:
        for i, (id_, tekst, podsumowanie, score, timestamp) in enumerate(analyses):
            with st.expander(f"Analiza z {timestamp[:16]} - Ryzyka: {score}"):
                st.write(podsumowanie)
                st.write("Podgląd fragmentu umowy:")
                st.text(tekst[:500] + " ...")

        if len(analyses) > 1:
            st.subheader("Porównaj dwie analizy")
            ids = [str(a[0]) for a in analyses]
            a1 = st.selectbox("Wybierz pierwszą analizę", ids)
            a2 = st.selectbox("Wybierz drugą analizę", ids, index=1)

            text1 = next(a[1] for a in analyses if str(a[0]) == a1)
            text2 = next(a[1] for a in analyses if str(a[0]) == a2)
            similarity = compare_text_similarity(text1, text2)
            st.write(f"Podobieństwo tekstów: {similarity:.2%}")

st.sidebar.markdown("---")
st.sidebar.write(f"Zalogowany jako: **{session_state.username}**")
if st.sidebar.button("Wyloguj się"):
    session_state.logged_in = False
    session_state.username = ""
    st.experimental_rerun()
