import streamlit as st
import fitz  # PyMuPDF
import re
from fpdf import FPDF
from io import BytesIO

# === KONFIGURACJA STRONY ===
st.set_page_config(page_title="UmowaAI – Legal Risk Detector", layout="wide")

# === STYL PODSTAWOWY ===
st.markdown("""
<style>
body {
    font-family: 'Segoe UI', sans-serif;
}
[data-testid="stAppViewContainer"] > .main {
    padding: 2rem;
}
h1, h2, h3 {
    color: #ffffff;
    text-shadow: 1px 1px 2px #000;
}
.risk-box {
    background-color: rgba(255, 0, 0, 0.1);
    border-left: 4px solid #ff4b2b;
    padding: 1rem;
    margin: 1rem 0;
    border-radius: 12px;
    font-size: 1rem;
    backdrop-filter: blur(3px);
    box-shadow: 0 0 10px rgba(255, 75, 43, 0.3);
}
</style>
""", unsafe_allow_html=True)

# === TRYB CIEMNY / JASNY ===
dark_mode = st.toggle("🌗 Tryb ciemny/jasny")
if dark_mode:
    st.markdown("""
    <style>
    body { background-color: #0f0f0f; color: #ffffff; }
    </style>
    """, unsafe_allow_html=True)

# === LOGOWANIE ===
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def login():
    username = st.text_input("Login")
    password = st.text_input("Hasło", type="password")
    if st.button("Zaloguj"):
        if username == "admin" and password == "haslo123":
            st.session_state.logged_in = True
            st.success("✅ Zalogowano!")
        else:
            st.error("❌ Błędny login lub hasło.")

if not st.session_state.logged_in:
    st.warning("🔐 Zaloguj się, aby korzystać z pełnych funkcji.")
    login()
    st.stop()

# === INTERFEJS JĘZYKOWY ===
lang = st.radio("🌐 Wybierz język / Choose language", ["Polski", "English"])
is_pl = lang == "Polski"

# === TYTUŁ I OBRAZEK ===
st.image("https://cdn.pixabay.com/photo/2022/01/30/11/23/ai-6983455_1280.jpg", use_container_width=True)
st.title("🤖 UmowaAI – " + ("Ekspert od ryzyk prawnych" if is_pl else "AI Legal Risk Analyzer"))
st.markdown("#### " + (
    "Prześlij umowę PDF i AI znajdzie ryzykowne zapisy prawne, finansowe lub inne – automatycznie i zrozumiale."
    if is_pl else
    "Upload a contract PDF and AI will detect legal, financial, or other risk clauses – clearly and automatically."
))
st.markdown("---")

# === WYBORY ===
typ_umowy = st.selectbox("📄 Wybierz typ umowy / Select contract type", [
    "Najmu", "O pracę", "Zlecenie", "Dzieło", "Sprzedaży"
])
typ_analizy = st.selectbox("🔍 Co analizować? / Type of risks to detect", [
    "Prawne", "Finansowe", "Wszystkie"
])

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

    # === STATYSTYKI ===
    st.metric("📌 Ilość wykrytych ryzyk", len(risks))
    if text:
        percent = round((len(risks) / max(1, len(text.split()))) * 10000, 2)
        st.progress(min(100, int(percent)), text="Poziom ryzyka (szacunkowy)")

    # === HISTORIA ANALIZ ===
    if "history" not in st.session_state:
        st.session_state.history = []
    st.session_state.history.append({
        "file": uploaded_file.name,
        "risks": len(risks),
        "type": typ_umowy,
        "analysis": typ_analizy
    })

    with st.expander("🕓 Historia analiz"):
        for entry in st.session_state.history:
            st.markdown(f"**{entry['file']}** – {entry['type']}, ryzyka: {entry['risks']} ({entry['analysis']})")

    # === WYNIKI ===
    st.subheader("🚨 Wykryte ryzyka:" if is_pl else "🚨 Detected Risks")
    if risks:
        for label, frag in risks:
            st.markdown(f"<div class='risk-box'><b>{label}</b><br>{frag}</div>", unsafe_allow_html=True)
    else:
        st.success("✅ Brak oczywistych ryzyk." if is_pl else "✅ No obvious risks found.")

    st.subheader("📄 Treść umowy z oznaczeniami:" if is_pl else "📄 Contract with highlights")
    st.markdown(highlighted)

    # === EKSPORT ===
    with st.expander("💾 Pobierz analizę / Download result"):
        st.download_button("📩 TXT", data=highlighted, file_name="analiza_umowy.txt")
        st.download_button("🧾 PDF", data=export_to_pdf(highlighted), file_name="analiza_umowy.pdf")
else:
    st.info("✍️ Wgraj umowę PDF, aby rozpocząć analizę." if is_pl else "✍️ Upload a PDF to begin analysis.")
