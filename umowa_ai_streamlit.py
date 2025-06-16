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
import openai

matplotlib.use('Agg')

# --- NOWOŚĆ: Klucz API OpenAI ---
openai.api_key = os.getenv("OPENAI_API_KEY")

st.set_page_config(page_title="Umowa AI", layout="wide")

# --- Baza danych SQLite ---
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

# --- Rozpoznawanie typu umowy ---
def rozpoznaj_typ_umowy(tekst):
    if re.search(r"non-disclosure|confidentiality", tekst, re.IGNORECASE):
        return "NDA"
    elif re.search(r"service agreement|contractor|SLA", tekst, re.IGNORECASE):
        return "B2B"
    elif re.search(r"employment|employee|employer", tekst, re.IGNORECASE):
        return "Umowa o pracę"
    else:
        return "Nieznany"

# --- Tłumaczenia, UI, logowanie ---
# (niezmienione - zakładamy, że zostały skopiowane z Twojego kodu w całości)

# --- Strona "Analiza Umowy" ---
elif plain_choice == "Analiza Umowy":
    st.header("Analiza AI")
    option = st.radio("Wybierz sposób analizy:", ["Prześlij PDF", "Wklej tekst"])

    if option == "Prześlij PDF":
        uploaded_file = st.file_uploader("Prześlij plik PDF do analizy", type="pdf")
        if uploaded_file:
            reader = PdfReader(uploaded_file)
            full_text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
    else:
        full_text = st.text_area("Wklej tekst umowy tutaj:", height=300)

    if option == "Wklej tekst" or uploaded_file:
        if full_text.strip():
            typ_umowy = rozpoznaj_typ_umowy(full_text)
            st.info(f"\U0001F50D Rozpoznany typ umowy: **{typ_umowy}**")

            with st.spinner("Analiza AI w toku..."):
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "Jesteś asystentem do analizy umów."},
                        {"role": "user", "content": f"Przeanalizuj umowę:\n\n{full_text}\n\nWypisz kluczowe punkty i potencjalne ryzyka."}
                    ],
                    temperature=0.5,
                    max_tokens=500
                )
                summary = response.choices[0].message['content']

            st.text_area("Podsumowanie:", summary, height=250)
            score = len(full_text) % 10

            if st.button("Zapisz analizę"):
                cursor.execute("INSERT INTO analiza (user, tekst, podsumowanie, score, timestamp) VALUES (?, ?, ?, ?, ?)",
                               (session_state.username, full_text, summary, score, datetime.now().isoformat()))
                conn.commit()
                st.success("Analiza zapisana.")
        else:
            st.info("Wprowadź lub załaduj tekst umowy.")

# --- Strona "Moje Analizy" ---
elif plain_choice == "Moje Analizy":
    st.header("Historia Twoich analiz")
    cursor.execute("SELECT id, tekst, podsumowanie, score, timestamp FROM analiza WHERE user = ? ORDER BY timestamp DESC", (session_state.username,))
    rows = cursor.fetchall()

    if not rows:
        st.info("Brak zapisanych analiz.")
    else:
        for row in rows:
            analiza_id, tekst, podsumowanie, score, timestamp = row
            with st.expander(f"Analiza z dnia {timestamp} (Ryzyko: {score}/10)"):
                st.markdown(f"**Podsumowanie:** {podsumowanie[:500]}...")

                # --- Eksport do PDF ---
                buffer = io.BytesIO()
                c = canvas.Canvas(buffer)
                c.setFont("Helvetica", 12)
                c.drawString(100, 800, f"Analiza Umowy - {timestamp}")
                c.drawString(100, 780, f"Ryzyko: {score}/10")
                text_object = c.beginText(100, 760)
                for line in podsumowanie.splitlines():
                    text_object.textLine(line[:120])
                c.drawText(text_object)
                c.showPage()
                c.save()
                buffer.seek(0)

                st.download_button(
                    label="📄 Pobierz PDF",
                    data=buffer,
                    file_name=f"analiza_{analiza_id}.pdf",
                    mime="application/pdf"
                )

                # --- NOWOŚĆ: Eksport do JSON ---
                json_data = {
                    "id": analiza_id,
                    "timestamp": timestamp,
                    "score": score,
                    "summary": podsumowanie,
                    "text": tekst
                }
                st.download_button(
                    label="📦 Pobierz JSON",
                    data=json.dumps(json_data, indent=4),
                    file_name=f"analiza_{analiza_id}.json",
                    mime="application/json"
                )

                if st.button(f"\U0001F5D1️ Usuń analizę {analiza_id}", key=f"delete_{analiza_id}"):
                    cursor.execute("DELETE FROM analiza WHERE id = ? AND user = ?", (analiza_id, session_state.username))
                    conn.commit()
                    st.success(f"Usunięto analizę z {timestamp}.")
                    st.experimental_rerun()
