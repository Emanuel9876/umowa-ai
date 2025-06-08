import streamlit as st
import fitz  # PyMuPDF
import re
from fpdf import FPDF
from io import BytesIO
import datetime

# === KONFIGURACJA STRONY ===
st.set_page_config(page_title="UmowaAI – Legal Risk Detector", layout="wide")

# === SESJA UŻYTKOWNIKA ===
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True

# === FUNKCJE LOGOWANIA ===
users = {"admin": "haslo123"}  # Przykładowi użytkownicy, zamień na bazę danych w wersji produkcyjnej


def login(username, password):
    return users.get(username) == password


def register(username, password):
    if username in users:
        return False
    users[username] = password
    return True

# === TRYB JASNY/CIEMNY ===
dark_mode = st.toggle("🌗 Tryb ciemny/jasny", value=st.session_state.dark_mode)
st.session_state.dark_mode = dark_mode

# === STYL ===
st.markdown(f"""
<style>
body {{
    background: {'#1f1c2c' if dark_mode else '#f5f5f5'};
    color: {'white' if dark_mode else 'black'};
}}
[data-testid="stAppViewContainer"] > .main {{
    background-color: {'rgba(255, 255, 255, 0.03)' if dark_mode else '#ffffff'};
    backdrop-filter: blur(6px);
    padding: 2rem;
    border-radius: 16px;
}}
h1, h2, h3 {{
    color: {'#ffffff' if dark_mode else '#000000'};
}}
.risk-box {{
    background-color: rgba(255, 0, 0, 0.1);
    border-left: 4px solid #ff4b2b;
    padding: 1rem;
    margin: 1rem 0;
    border-radius: 12px;
    font-size: 1rem;
    backdrop-filter: blur(3px);
    box-shadow: 0 0 10px rgba(255, 75, 43, 0.3);
}}
</style>
""", unsafe_allow_html=True)

# === LOGOWANIE ===
if not st.session_state.logged_in:
    st.header("🔐 Logowanie / Login")
    username = st.text_input("Login")
    password = st.text_input("Hasło / Password", type="password")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Zaloguj / Login"):
            if login(username, password):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success("Zalogowano!")
            else:
                st.error("Błędny login lub hasło.")
    with col2:
        if st.button("Zarejestruj / Register"):
            if register(username, password):
                st.success("Zarejestrowano! Możesz się teraz zalogować.")
            else:
                st.warning("Użytkownik już istnieje.")
    st.stop()

# === INTERFEJS ===
st.image("https://cdn.pixabay.com/photo/2022/01/30/11/23/ai-6983455_1280.jpg", use_container_width=True)
lang = st.radio("🌐 Język / Language", ["Polski", "English"])
is_pl = lang == "Polski"
st.title("🤖 UmowaAI – " + ("Ekspert od ryzyk prawnych" if is_pl else "AI Legal Risk Analyzer"))

st.markdown("#### " + (
    "Prześlij umowę PDF i AI znajdzie ryzykowne zapisy prawne, finansowe lub inne – automatycznie i zrozumiale."
    if is_pl else
    "Upload a contract PDF and AI will detect legal, financial, or other risk clauses – clearly and automatically."
))

st.markdown("---")

# === OPCJE ===
typ_umowy = st.selectbox("📄 Typ umowy / Contract type", ["Najmu", "O pracę", "Zlecenie", "Dzieło", "Sprzedaży"])
typ_analizy = st.selectbox("🔍 Co analizować? / Type of risks to detect", ["Prawne", "Finansowe", "Wszystkie"])

# === FUNKCJE ===
def extract_text_from_pdf(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def find_risks(text, typ_umowy, typ_analizy):
    wspolne = {
        "⚠️ Kaucja": r"kaucj[ae]\s+.*?\d+[\s\w]*z[łl]",
        "⏳ Wypowiedzenie": r"wypowiedze?nie.*?(umowy|kontraktu)?",
        "🚫 Kara umowna": r"kara\s+umowna.*?\d+[\s\w]*z[łl]",
    }
    finansowe = {
        "💸 Brak wynagrodzenia": r"(nie przysługuje|brak)\s+wynagrodzenia",
        "📈 Podwyżki bez zgody": r"(automatyczn[aey]|jednostronn[aey])\s+(zmian[aey]|podwyżk)"
    }
    spec = {
        "Najmu": {"🔐 Zakaz podnajmu": r"(zakaz|brak zgody).*?podnajm"},
        "O pracę": {"💼 Nadgodziny niepłatne": r"nadgodzin(y|ach|om).*?nieodpłatn"},
        "Zlecenie": {"📆 Terminy realizacji": r"termin.*?realizacj"},
        "Dzieło": {"🛠️ Odpowiedzialność za wady": r"odpowiedzialno\w+.*?wady.*?dzie[łl]"},
        "Sprzedaży": {"🔍 Reklamacje": r"(reklamacj|odpowiedzialno\w+).*?towar"}
    }
    patterns = wspolne.copy()
    if typ_analizy in ["Wszystkie", "Finansowe"]:
        patterns.update(finansowe)
    if typ_umowy in spec:
        patterns.update(spec[typ_umowy])

    results = []
    for label, pattern in patterns.items():
        for match in re.finditer(pattern, text, re.IGNORECASE):
            results.append((label, match.group()))
    return results

def highlight_risks(text, risks):
    for label, frag in risks:
        text = text.replace(frag, f"**[{label}]** {frag}")
    return text

def export_to_pdf(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)
    for line in text.split('\n'):
        pdf.multi_cell(0, 10, line)
    buf = BytesIO()
    pdf.output(buf)
    return buf.getvalue()

# === ANALIZA ===
uploaded_file = st.file_uploader("📥 Wgraj PDF umowy / Upload contract PDF", type="pdf")
if uploaded_file:
    with st.spinner("🔍 Analiza... / Analyzing..."):
        text = extract_text_from_pdf(uploaded_file)
        risks = find_risks(text, typ_umowy, typ_analizy)
        highlighted = highlight_risks(text, risks)

    st.subheader("🚨 Wykryte ryzyka:" if is_pl else "🚨 Detected Risks")
    if risks:
        for label, frag in risks:
            st.markdown(f"<div class='risk-box'><b>{label}</b><br>{frag}</div>", unsafe_allow_html=True)
    else:
        st.success("✅ Brak oczywistych ryzyk." if is_pl else "✅ No obvious risks found.")

    st.subheader("📄 Treść umowy z oznaczeniami:" if is_pl else "📄 Contract with highlights")
    st.markdown(highlighted)

    with st.expander("💾 Pobierz analizę / Download result"):
        st.download_button("📩 Pobierz jako TXT" if is_pl else "📩 Download as TXT",
                           data=highlighted, file_name="analiza_umowy.txt")
        st.download_button("🧾 Pobierz jako PDF" if is_pl else "🧾 Download as PDF",
                           data=export_to_pdf(highlighted), file_name="analiza_umowy.pdf")

    st.info("🔐 Historia analiz dostępna w wersji premium – wkrótce." if is_pl else "🔐 Analysis history coming soon in premium version.")
else:
    st.info("✍️ Wgraj umowę PDF, aby rozpocząć analizę." if is_pl else "✍️ Upload a PDF to begin analysis.")
