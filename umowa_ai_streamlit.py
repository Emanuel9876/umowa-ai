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

# === KONFIGURACJA ===
st.set_page_config(page_title="Umowa AI", layout="wide")

# === BAZA DANYCH ===
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

# === UŻYTKOWNICY ===
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
session_state.setdefault("logged_in", False)
session_state.setdefault("username", "")
session_state.setdefault("language", "PL")

# === TŁUMACZENIA ===
lang_options = {"PL": "Polski", "EN": "English", "DE": "Deutsch"}
translations = {
    "Strona Główna": {"PL": "Strona Główna", "EN": "Home", "DE": "Startseite"},
    "Analiza Umowy": {"PL": "Analiza Umowy", "EN": "Contract Analysis", "DE": "Vertragsanalyse"},
    "Ryzyka": {"PL": "Ryzyka", "EN": "Risks", "DE": "Risiken"},
    "Moje Analizy": {"PL": "Moje Analizy", "EN": "My Analyses", "DE": "Meine Analysen"},
    "Logowanie / Rejestracja": {"PL": "Logowanie / Rejestracja", "EN": "Login / Register", "DE": "Anmeldung / Registrierung"},
    "Zaloguj się": {"PL": "Zaloguj się", "EN": "Login", "DE": "Einloggen"},
    "Zarejestruj się": {"PL": "Zarejestruj się", "EN": "Register", "DE": "Registrieren"},
    "Login": {"PL": "Login", "EN": "Username", "DE": "Benutzername"},
    "Hasło": {"PL": "Hasło", "EN": "Password", "DE": "Passwort"},
    "Rozpocznij analizę teraz": {"PL": "Rozpocznij analizę teraz", "EN": "Start analysis now", "DE": "Analyse jetzt starten"},
    "Analiza zapisana.": {"PL": "Analiza zapisana.", "EN": "Analysis saved.", "DE": "Analyse gespeichert."},
    "Brak analiz do pokazania wykresu.": {"PL": "Brak analiz do pokazania wykresu.", "EN": "No analyses to display chart.", "DE": "Keine Analysen zum Anzeigen des Diagramms."},
    "Brak zapisanych analiz.": {"PL": "Brak zapisanych analiz.", "EN": "No saved analyses.", "DE": "Keine gespeicherten Analysen."},
    "Usuń analizę": {"PL": "Usuń analizę", "EN": "Delete analysis", "DE": "Analyse löschen"},
    "Analiza z dnia": {"PL": "Analiza z dnia", "EN": "Analysis from", "DE": "Analyse vom"},
    "Ryzyko": {"PL": "Ryzyko", "EN": "Risk", "DE": "Risiko"},
    "Wprowadź lub załaduj tekst umowy.": {"PL": "Wprowadź lub załaduj tekst umowy.", "EN": "Enter or upload contract text.", "DE": "Vertragstext eingeben oder hochladen."}
}

def t(text):
    return translations.get(text, {}).get(session_state.language, text)

# === WYBÓR JĘZYKA ===
selected_lang = st.sidebar.selectbox("🌍 " + t("Wybierz język / Select Language / Sprache wählen"), list(lang_options.keys()), format_func=lambda x: lang_options[x])
session_state.language = selected_lang

# === STYL ===
st.markdown("""
    <style>
        .stApp {
            background: linear-gradient(to right, #2c3e50, #3498db);
            font-family: 'Segoe UI', sans-serif;
        }
        html, body, [class*="css"] {
            background-color: transparent !important;
            color: #ffffff !important;
        }
        .top-card {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            padding: 2rem;
            margin-bottom: 2rem;
        }
        ul {
            list-style-type: disc;
            padding-left: 2rem;
        }
    </style>
""", unsafe_allow_html=True)

# === AUTORYZACJA ===
if not session_state.logged_in:
    st.sidebar.subheader("🔐 " + t("Logowanie / Rejestracja"))
    choice = st.sidebar.radio(t("Wybierz opcję"), [t("Zaloguj się"), t("Zarejestruj się")])
    username = st.sidebar.text_input(t("Login"))
    password = st.sidebar.text_input(t("Hasło"), type="password")

    if choice == t("Zarejestruj się"):
        if st.sidebar.button(t("Zarejestruj się")):
            if username in users:
                st.sidebar.warning("Użytkownik już istnieje.")
            else:
                users[username] = hash_password(password)
                save_users(users)
                st.sidebar.success("Rejestracja zakończona sukcesem.")
    else:
        if st.sidebar.button(t("Zaloguj się")):
            if username in users and users[username] == hash_password(password):
                session_state.logged_in = True
                session_state.username = username
                st.rerun()
            else:
                st.sidebar.error("Błędny login lub hasło.")
    st.stop()

# === MENU ===
menu_options = [
    ("Strona Główna", "🏠"),
    ("Analiza Umowy", "📄"),
    ("Ryzyka", "⚠️"),
    ("Moje Analizy", "📊")
]
translated_menu = [f"{icon} {t(label)}" for label, icon in menu_options]
menu_choice = st.sidebar.selectbox("📋 " + t("Wybierz opcję"), translated_menu)
plain_choice = [label for label, icon in menu_options][translated_menu.index(menu_choice)]

# === STRONY ===
if plain_choice == "Strona Główna":
    if st.button("🚀 " + t("Rozpocznij analizę teraz")):
        session_state["start_analysis"] = True
        st.experimental_rerun()
    st.title("🤖 UmowaAI")
    st.markdown("### " + t("Twój osobisty asystent do analizy umów i wykrywania ryzyk"))

elif plain_choice == "Analiza Umowy":
    st.header("📄 " + t("Analiza Umowy"))
    option = st.radio("Metoda:", ["PDF", "Tekst"])
    if option == "PDF":
        uploaded_file = st.file_uploader("Prześlij plik PDF", type="pdf")
        if uploaded_file:
            reader = PdfReader(uploaded_file)
            full_text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
    else:
        full_text = st.text_area("Tekst umowy:", height=300)

    if full_text:
        summary = full_text[:500] + "..."
        st.text_area("🔎 Podsumowanie:", summary, height=150)
        score = len(full_text) % 10
        if st.button("💾 " + t("Zapisz analizę")):
            cursor.execute("INSERT INTO analiza (user, tekst, podsumowanie, score, timestamp) VALUES (?, ?, ?, ?, ?)",
                           (session_state.username, full_text, summary, score, datetime.now().isoformat()))
            conn.commit()
            st.success(t("Analiza zapisana."))
    else:
        st.info(t("Wprowadź lub załaduj tekst umowy."))

elif plain_choice == "Ryzyka":
    st.header("⚠️ " + t("Ryzyka"))
    cursor.execute("SELECT score, timestamp FROM analiza WHERE user = ? ORDER BY timestamp DESC LIMIT 5", (session_state.username,))
    data = cursor.fetchall()
    if data:
        scores, times = zip(*data)
        fig, ax = plt.subplots()
        sns.lineplot(x=times, y=scores, marker='o', ax=ax)
        ax.set_title(t("Ryzyko") + " w czasie")
        st.pyplot(fig)
    else:
        st.info(t("Brak analiz do pokazania wykresu."))

elif plain_choice == "Moje Analizy":
    st.header("📊 " + t("Moje Analizy"))
    cursor.execute("SELECT id, podsumowanie, score, timestamp FROM analiza WHERE user = ? ORDER BY timestamp DESC", (session_state.username,))
    for analiza_id, podsumowanie, score, timestamp in cursor.fetchall():
        with st.expander(f"{t('Analiza z dnia')} {timestamp} ({t('Ryzyko')}: {score}/10)"):
            st.write(podsumowanie[:500] + "...")
            buffer = io.BytesIO()
            c = canvas.Canvas(buffer)
            c.drawString(100, 800, f"{t('Analiza z dnia')} {timestamp}")
            c.drawString(100, 780, f"{t('Ryzyko')}: {score}/10")
            c.drawText(c.beginText(100, 760))
            c.save()
            buffer.seek(0)
            st.download_button(label="📄 PDF", data=buffer, file_name=f"analiza_{analiza_id}.pdf", mime="application/pdf")
            if st.button(f"🗑 {t('Usuń analizę')} {analiza_id}", key=f"delete_{analiza_id}"):
                cursor.execute("DELETE FROM analiza WHERE id = ? AND user = ?", (analiza_id, session_state.username))
                conn.commit()
                st.success("Usunięto.")
                st.experimental_rerun()
