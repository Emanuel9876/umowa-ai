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

users = load_users()
session_state = st.session_state

if "logged_in" not in session_state:
    session_state.logged_in = False
    session_state.username = ""

if "language" not in session_state:
    session_state.language = "PL"

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
    "Wprowadź lub załaduj tekst umowy.": {"PL": "Wprowadź lub załaduj tekst umowy.", "EN": "Enter or upload contract text.", "DE": "Vertragstext eingeben oder hochladen."},
    "Twój osobisty asystent do analizy umów i wykrywania ryzyk": {
        "PL": "Twój osobisty asystent do analizy umów i wykrywania ryzyk",
        "EN": "Your personal assistant for contract analysis and risk detection",
        "DE": "Ihr persönlicher Assistent zur Vertragsanalyse und Risikobewertung"
    },
    "Co potrafi aplikacja:": {
        "PL": "Co potrafi aplikacja:",
        "EN": "What the app can do:",
        "DE": "Was die App kann:"
    },
    "Analiza tekstu umowy lub pliku PDF": {
        "PL": "Analiza tekstu umowy lub pliku PDF",
        "EN": "Analyze contract text or PDF file",
        "DE": "Analyse des Vertragstextes oder PDF-Datei"
    },
    "Ocena ryzyka w umowie": {
        "PL": "Ocena ryzyka w umowie",
        "EN": "Risk evaluation in the contract",
        "DE": "Risikobewertung im Vertrag"
    },
    "Podsumowanie kluczowych punktów": {
        "PL": "Podsumowanie kluczowych punktów",
        "EN": "Summary of key points",
        "DE": "Zusammenfassung der wichtigsten Punkte"
    },
    "Zarządzanie historią analiz": {
        "PL": "Zarządzanie historią analiz",
        "EN": "Manage analysis history",
        "DE": "Analyseverlauf verwalten"
    },
    "Tłumaczenie interfejsu na 3 języki": {
        "PL": "Tłumaczenie interfejsu na 3 języki",
        "EN": "Interface translation in 3 languages",
        "DE": "Oberfläche in 3 Sprachen übersetzen"
    },
    "Gotowy?": {
        "PL": "Gotowy?",
        "EN": "Ready?",
        "DE": "Bereit?"
    },
    "Metoda:": {"PL": "Metoda:", "EN": "Method:", "DE": "Methode:"},
    "Prześlij plik PDF": {"PL": "Prześlij plik PDF", "EN": "Upload PDF file", "DE": "PDF-Datei hochladen"},
    "Tekst umowy:": {"PL": "Tekst umowy:", "EN": "Contract text:", "DE": "Vertragstext:"},
    "Podsumowanie:": {"PL": "Podsumowanie:", "EN": "Summary:", "DE": "Zusammenfassung:"},
    "Zapisz analizę": {"PL": "Zapisz analizę", "EN": "Save analysis", "DE": "Analyse speichern"},
    "Wybierz język / Select Language / Sprache wählen": {
        "PL": "Wybierz język", "EN": "Select Language", "DE": "Sprache wählen"
    },
    "Wybierz opcję": {"PL": "Wybierz opcję", "EN": "Choose option", "DE": "Option wählen"},
    "Wklej treść umowy tutaj": {"PL": "Wklej treść umowy tutaj", "EN": "Paste contract text here", "DE": "Vertragstext hier einfügen"},
    "Analizuj umowę": {"PL": "Analizuj umowę", "EN": "Analyze contract", "DE": "Vertrag analysieren"},
    "Podsumowanie analizy": {"PL": "Podsumowanie analizy", "EN": "Analysis summary", "DE": "Analysezusammenfassung"},
    "Wykryte ryzyka": {"PL": "Wykryte ryzyka", "EN": "Detected risks", "DE": "Erkannte Risiken"},
    "Poziom czułości wykrywania": {"PL": "Poziom czułości wykrywania", "EN": "Detection sensitivity level", "DE": "Erkennungsempfindlichkeit"},
    "Dodaj własne słowa kluczowe (oddziel przecinkami)": {
        "PL": "Dodaj własne słowa kluczowe (oddziel przecinkami)",
        "EN": "Add custom keywords (comma separated)",
        "DE": "Benutzerdefinierte Schlüsselwörter hinzufügen (Komma getrennt)"
    },
    "Eksportuj raport PDF": {"PL": "Eksportuj raport PDF", "EN": "Export PDF report", "DE": "PDF-Bericht exportieren"},
    "Eksportuj raport JSON": {"PL": "Eksportuj raport JSON", "EN": "Export JSON report", "DE": "JSON-Bericht exportieren"},
    "Wprowadź dwie analizy do porównania": {
        "PL": "Wprowadź dwie analizy do porównania",
        "EN": "Select two analyses to compare",
        "DE": "Wählen Sie zwei Analysen zum Vergleich"
    },
    "Porównanie wyników:": {"PL": "Porównanie wyników:", "EN": "Comparison of results:", "DE": "Ergebnisvergleich:"},
    "Brak analiz do porównania.": {"PL": "Brak analiz do porównania.", "EN": "No analyses to compare.", "DE": "Keine Analysen zum Vergleichen."},
    "Wyloguj": {"PL": "Wyloguj", "EN": "Logout", "DE": "Ausloggen"},
    "Błędny login lub hasło.": {"PL": "Błędny login lub hasło.", "EN": "Incorrect login or password.", "DE": "Falscher Login oder Passwort."},
    "Użytkownik już istnieje.": {"PL": "Użytkownik już istnieje.", "EN": "User already exists.", "DE": "Benutzer existiert bereits."},
    "Rejestracja zakończona sukcesem. Możesz się zalogować.": {
        "PL": "Rejestracja zakończona sukcesem. Możesz się zalogować.",
        "EN": "Registration successful. You can log in now.",
        "DE": "Registrierung erfolgreich. Sie können sich jetzt anmelden."
    }
}

lang_options = {"PL": "Polski", "EN": "English", "DE": "Deutsch"}
selected_lang = st.sidebar.selectbox("🌐 " + translations["Wybierz język / Select Language / Sprache wählen"][session_state.language],
                                    list(lang_options.keys()), format_func=lambda x: lang_options[x])
session_state.language = selected_lang

# Styl nowoczesny z gradientem
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
        h1, h2, h3, h4, h5, h6, p, div, span, label {
            color: #ffffff !important;
        }
        .top-card {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
        }
        ul {
            list-style-type: disc;
            padding-left: 2rem;
        }
    </style>
""", unsafe_allow_html=True)

if not session_state.logged_in:
    st.sidebar.subheader(translations["Logowanie / Rejestracja"][session_state.language])
    choice = st.sidebar.radio("", [translations["Zaloguj się"][session_state.language], translations["Zarejestruj się"][session_state.language]])

    username = st.sidebar.text_input(translations["Login"][session_state.language])
    password = st.sidebar.text_input(translations["Hasło"][session_state.language], type="password")

    if choice == translations["Zarejestruj się"][session_state.language]:
        if st.sidebar.button(translations["Zarejestruj się"][session_state.language]):
            if username in users:
                st.sidebar.warning(translations["Użytkownik już istnieje."][session_state.language])
            else:
                users[username] = hash_password(password)
                save_users(users)
                st.sidebar.success(translations["Rejestracja zakończona sukcesem. Możesz się zalogować."][session_state.language])
    else:
        if st.sidebar.button(translations["Zaloguj się"][session_state.language]):
            if username in users and users[username] == hash_password(password):
                session_state.logged_in = True
                session_state.username = username
                st.experimental_rerun()
            else:
                st.sidebar.error(translations["Błędny login lub hasło."][session_state.language])
else:
    st.sidebar.write(f"{translations['Witaj'][session_state.language] if 'Witaj' in translations else 'Witaj'}, {session_state.username}")
    if st.sidebar.button(translations["Wyloguj"][session_state.language]):
        session_state.logged_in = False
        session_state.username = ""
        st.experimental_rerun()

    menu = [translations["Strona Główna"][session_state.language],
            translations["Analiza Umowy"][session_state.language],
            translations["Ryzyka"][session_state.language],
            translations["Moje Analizy"][session_state.language]]
    choice = st.sidebar.radio(translations["Wybierz opcję"][session_state.language], menu)

    if choice == translations["Strona Główna"][session_state.language]:
        st.markdown(f"# {translations['Twój osobisty asystent do analizy umów i wykrywania ryzyk'][session_state.language]}")
        st.markdown("## " + translations["Co potrafi aplikacja:"][session_state.language])
        st.markdown(f"""
        - {translations['Analiza tekstu umowy lub pliku PDF'][session_state.language]}
        - {translations['Ocena ryzyka w umowie'][session_state.language]}
        - {translations['Podsumowanie kluczowych punktów'][session_state.language]}
        - {translations['Zarządzanie historią analiz'][session_state.language]}
        - {translations['Tłumaczenie interfejsu na 3 języki'][session_state.language]}
        """)
    elif choice == translations["Analiza Umowy"][session_state.language]:
        st.header(translations["Analiza Umowy"][session_state.language])
        method = st.radio(translations["Metoda:"][session_state.language], [translations["Prześlij plik PDF"][session_state.language], translations["Wklej treść umowy tutaj"][session_state.language]])
        
        contract_text = ""
        if method == translations["Prześlij plik PDF"][session_state.language]:
            uploaded_file = st.file_uploader(translations["Prześlij plik PDF"][session_state.language], type=["pdf"])
            if uploaded_file is not None:
                pdf = PdfReader(uploaded_file)
                contract_text = ""
                for page in pdf.pages:
                    contract_text += page.extract_text()
        else:
            contract_text = st.text_area(translations["Wklej treść umowy tutaj"][session_state.language], height=300)
        
        if st.button(translations["Analizuj umowę"][session_state.language]):
            if contract_text.strip() == "":
                st.warning(translations["Wprowadź lub załaduj tekst umowy."][session_state.language])
            else:
                # Prosta analiza: zliczanie wystąpień słów kluczowych ryzyka
                keywords = ["kara", "odszkodowanie", "odpowiedzialność", "karencja", "wygaśnięcie", "zwłoka"]
                found = {k: len(re.findall(k, contract_text, re.IGNORECASE)) for k in keywords}
                summary = f"{translations['Podsumowanie analizy'][session_state.language]}:\n"
                for k, v in found.items():
                    summary += f"- {translations['Ryzyko'][session_state.language]} '{k}': {v}\n"

                # Zapis analizy do bazy
                cursor.execute("INSERT INTO analiza (user, tekst, podsumowanie, score, timestamp) VALUES (?, ?, ?, ?, ?)",
                               (session_state.username, contract_text, summary, sum(found.values()), datetime.now().isoformat()))
                conn.commit()
                st.success(translations["Analiza zapisana."][session_state.language])
                st.text_area(translations["Podsumowanie:"][session_state.language], summary, height=200)

                # Eksport PDF i JSON
                if st.button(translations["Eksportuj raport PDF"][session_state.language]):
                    buffer = io.BytesIO()
                    p = canvas.Canvas(buffer)
                    p.drawString(100, 800, "Raport analizy umowy")
                    p.drawString(100, 780, summary)
                    p.save()
                    buffer.seek(0)
                    st.download_button(label="PDF", data=buffer, file_name="raport.pdf", mime="application/pdf")
                
                if st.button(translations["Eksportuj raport JSON"][session_state.language]):
                    report_json = json.dumps({"contract_text": contract_text, "summary": summary}, ensure_ascii=False, indent=2)
                    st.download_button(label="JSON", data=report_json, file_name="raport.json", mime="application/json")

    elif choice == translations["Ryzyka"][session_state.language]:
        st.header(translations["Ryzyka"][session_state.language])
        # Tutaj można dodać wykres ryzyk itd.

    elif choice == translations["Moje Analizy"][session_state.language]:
        st.header(translations["Moje Analizy"][session_state.language])
        cursor.execute("SELECT id, timestamp, score FROM analiza WHERE user = ?", (session_state.username,))
        rows = cursor.fetchall()
        if not rows:
            st.info(translations["Brak zapisanych analiz."][session_state.language])
        else:
            for r in rows:
                st.write(f"{translations['Analiza z dnia'][session_state.language]} {r[1]} - {translations['Ryzyko'][session_state.language]}: {r[2]}")
                if st.button(f"{translations['Usuń analizę'][session_state.language]} {r[0]}"):
                    cursor.execute("DELETE FROM analiza WHERE id = ?", (r[0],))
                    conn.commit()
                    st.experimental_rerun()

