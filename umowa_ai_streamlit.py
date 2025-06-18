import streamlit as st
import re
import io
import os
import json
import hashlib
import sqlite3
from datetime import datetime
from PyPDF2 import PdfReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from docx import Document

# --- Konfiguracja strony ---
st.set_page_config(page_title="Umowa AI 2.0", layout="wide")

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
)
''')
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

# --- Stan sesji ---
if "logged_in" not in session_state:
    session_state.logged_in = False
    session_state.username = ""

if "custom_keywords" not in session_state:
    session_state.custom_keywords = []

# --- Pomocnicze funkcje do plików ---
def extract_text_from_pdf(file):
    try:
        pdf = PdfReader(file)
        text = ""
        for page in pdf.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        return ""

def extract_text_from_docx(file):
    try:
        doc = Document(file)
        fullText = []
        for para in doc.paragraphs:
            fullText.append(para.text)
        return "\n".join(fullText)
    except Exception as e:
        return ""

# --- Analiza tekstu ---
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

# --- Logowanie / Rejestracja / Wylogowanie ---
def login():
    st.sidebar.markdown("<h2>🔑 Logowanie</h2>", unsafe_allow_html=True)
    username = st.sidebar.text_input("Nazwa użytkownika")
    password = st.sidebar.text_input("Hasło", type="password")
    if st.sidebar.button("Zaloguj"):
        if username in users and users[username]["password"] == hash_password(password):
            session_state.logged_in = True
            session_state.username = username
            st.sidebar.success(f"Zalogowano jako {username}")
            st.experimental_rerun()
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

# --- Generowanie PDF z podsumowaniem ---
def generate_pdf(user, summary, score):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.setFont("Helvetica-Bold", 16)
    c.setFillColorRGB(0, 1, 1)
    c.drawString(72, 750, "Podsumowanie analizy umowy")
    c.setFont("Helvetica", 12)
    c.setFillColorRGB(0.5, 1, 1)
    c.drawString(72, 730, f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    c.drawString(72, 710, f"Użytkownik: {user}")
    c.drawString(72, 690, f"Wskaźnik ryzyka: {score}")
    c.drawString(72, 670, "Podsumowanie:")
    text_object = c.beginText(72, 650)
    text_object.setFont("Helvetica", 12)
    text_object.setFillColorRGB(0.5, 1, 1)
    for line in summary.split(", "):
        text_object.textLine("- " + line)
    c.drawText(text_object)
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

# --- Strona główna ---
def show_home():
    st.markdown("""
    <div style="max-width:900px; margin: 40px auto; background: rgba(0,30,40,0.9); border-radius: 30px; padding: 40px 60px; color:#aaffff; font-family: 'Orbitron', sans-serif; line-height:1.7;">
        <h1 style="font-size:3.8em; letter-spacing:5px; text-align:center; text-shadow: 0 0 15px #00ffff, 0 0 40px #00ffff;">Strona Główna</h1>
        <h3 style="text-align:center; font-weight:600; font-size:1.8em; text-shadow: 0 0 10px #33ffff;">Witaj w aplikacji - Twoim asystencie do analizy umów</h3>
        <p>Ta aplikacja pozwala na szybkie i automatyczne analizowanie dokumentów prawnych, wykrywanie potencjalnych ryzyk oraz ich wizualizację.</p>
        <p>Funkcje aplikacji:</p>
        <ul style="font-size:1.4em; max-width:650px; margin: 0 auto; list-style:none; padding-left:0;">
            <li style="position:relative; padding-left:35px; margin: 15px 0;">
                <span style="position:absolute; left:0; color:#00ffff; font-weight:900; font-size:1.6em;">▸</span>
                Wczytaj dokumenty w formatach PDF oraz DOCX
            </li>
            <li style="position:relative; padding-left:35px; margin: 15px 0;">
                <span style="position:absolute; left:0; color:#00ffff; font-weight:900; font-size:1.6em;">▸</span>
                Skonfiguruj czułość i słowa kluczowe dla analizy
            </li>
            <li style="position:relative; padding-left:35px; margin: 15px 0;">
                <span style="position:absolute; left:0; color:#00ffff; font-weight:900; font-size:1.6em;">▸</span>
                Przeglądaj wyniki analizy i pobieraj podsumowania w PDF
            </li>
            <li style="position:relative; padding-left:35px; margin: 15px 0;">
                <span style="position:absolute; left:0; color:#00ffff; font-weight:900; font-size:1.6em;">▸</span>
                Zapisuj i przeglądaj historię swoich analiz
            </li>
        </ul>
        <p style="text-align:center; margin-top:40px;">
            <em>Analizuj umowy szybko, łatwo i bezpiecznie z Umowa AI 2.0!</em>
        </p>
    </div>
    """, unsafe_allow_html=True)

# --- Strona analizy ---
def show_analysis():
    st.title("Analiza Umowy")

    col1, col2 = st.columns([1,1])
    uploaded_text = ""

    with col1:
        st.write("📄 Wczytaj plik PDF lub DOCX do analizy:")
        uploaded_file = st.file_uploader("Wybierz plik PDF lub DOCX", type=["pdf", "docx"])
        if uploaded_file:
            if uploaded_file.type == "application/pdf":
                uploaded_text = extract_text_from_pdf(uploaded_file)
            elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                uploaded_text = extract_text_from_docx(uploaded_file)
            else:
                st.error("Nieobsługiwany format pliku.")
            if uploaded_text:
                session_state.uploaded_text = uploaded_text
                st.success("Plik załadowany poprawnie!")

    with col2:
        st.write("📝 Edytuj tekst (opcjonalnie):")
        text_to_analyze = st.text_area("Tekst umowy", value=session_state.get("uploaded_text", ""), height=300)

    st.markdown("---")
    st.subheader("Konfiguracja analizy")

    keywords_input = st.text_input("Słowa kluczowe (oddzielone przecinkami)", value="ryzyko, kara, odpowiedzialność, zobowiązanie, umowa")
    custom_keywords = [kw.strip() for kw in keywords_input.split(",") if kw.strip()]
    session_state.custom_keywords = custom_keywords

    if st.button("Przeprowadź analizę"):
        if not text_to_analyze.strip():
            st.warning("Wprowadź tekst do analizy!")
        else:
            found = analyze_text(text_to_analyze, custom_keywords)
            score = calculate_score(found)
            summary = generate_summary(found)
            st.success(f"Wykryto {len(found)} kluczowych ryzyk.")
            st.markdown(f"**Podsumowanie:** {summary}")
            st.markdown(f"**Wskaźnik ryzyka:** {score}")

            # Zapis do bazy
            save_analysis(session_state.username, text_to_analyze, summary, score)

            # Pobieranie PDF
            pdf_buffer = generate_pdf(session_state.username, summary, score)
            st.download_button("📥 Pobierz podsumowanie PDF", data=pdf_buffer, file_name="podsumowanie.pdf", mime="application/pdf")

# --- Historia analiz ---
def show_history():
    st.title("Historia Twoich analiz")
    cursor.execute('SELECT id, tekst, podsumowanie, score, timestamp FROM analiza WHERE user = ? ORDER BY timestamp DESC', (session_state.username,))
    rows = cursor.fetchall()

    if not rows:
        st.info("Brak historii analiz.")
        return

    for row in rows:
        st.markdown(f"### Analiza z {row[4]}")
        st.markdown(f"**Wskaźnik ryzyka:** {row[3]}")
        st.markdown(f"**Podsumowanie:** {row[2]}")
        with st.expander("Pokaż pełny tekst umowy"):
            st.write(row[1])
        st.markdown("---")

# --- Główna logika aplikacji ---
def main():
    st.sidebar.title("Umowa AI 2.0")
    if not session_state.logged_in:
        login()
        st.sidebar.markdown("---")
        register()
    else:
        st.sidebar.markdown(f"Witaj, **{session_state.username}**!")
        logout()

        page = st.sidebar.selectbox("Wybierz stronę", ["Strona Główna", "Analiza umowy", "Historia analiz"])
        if page == "Strona Główna":
            show_home()
        elif page == "Analiza umowy":
            show_analysis()
        elif page == "Historia analiz":
            show_history()

if __name__ == "__main__":
    main()
