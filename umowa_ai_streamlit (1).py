import streamlit as st
import fitz  # PyMuPDF
import re
from fpdf import FPDF
from io import BytesIO

# === KONFIGURACJA STRONY ===
st.set_page_config(page_title="UmowaAI – Legal Risk Detector", layout="wide")

# === TRYB CIEMNY / JASNY ===
dark_mode = st.toggle("🌗 Tryb ciemny/jasny", key="dark_mode_toggle")
if dark_mode:
    st.markdown("""
    <style>
    body { background-color: #0f0f0f; color: #ffffff; }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
    body { background-color: #ffffff; color: #000000; }
    </style>
    """, unsafe_allow_html=True)

# === STAN SESJI (logowanie, historia) ===
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "history" not in st.session_state:
    st.session_state.history = []

# === LOGOWANIE ===
if not st.session_state.logged_in:
    st.subheader("🔐 Logowanie")
    username = st.text_input("Login")
    password = st.text_input("Hasło", type="password")
    if st.button("Zaloguj"):
        if username == "admin" and password == "admin":
            st.session_state.logged_in = True
            st.success("Zalogowano pomyślnie")
        else:
            st.error("Nieprawidłowy login lub hasło")
    st.stop()

# === INTERFEJS MULTI-JĘZYKOWY ===
lang = st.radio("🌐 Wybierz język / Choose language", ["Polski", "English"])
is_pl = lang == "Polski"

# === NAGŁÓWEK ===
st.image("https://cdn.pixabay.com/photo/2022/01/30/11/23/ai-6983455_1280.jpg", use_container_width=True)
st.title("🤖 UmowaAI – " + ("Ekspert od ryzyk prawnych" if is_pl else "AI Legal Risk Analyzer"))
st.markdown("#### " + (
    "Prześlij umowę PDF i AI znajdzie ryzykowne zapisy prawne, finansowe lub inne."
    if is_pl else
    "Upload a PDF and AI will detect legal, financial or other risks."
))
st.markdown("---")

# === OPCJE ===
typ_umowy = st.selectbox("📄 Typ umowy", ["Najmu", "O pracę", "Zlecenie", "Dzieło", "Sprzedaży"])
typ_analizy = st.selectbox("🔍 Typ analizy", ["Prawne", "Finansowe", "Wszystkie"])

# === FUNKCJE ===
def extract_text_from_pdf(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    return "".join(page.get_text() for page in doc)

def find_risks(text, typ_umowy, typ_analizy):
    wspolne = {
        "⚠️ Kaucja": r"kaucj[ae]\s+.*?\d+[\s\w]*z[\u0142l]",
        "⏳ Wypowiedzenie": r"wypowiedze?nie.*?(umowy|kontraktu)?",
        "🚫 Kara umowna": r"kara\s+umowna.*?\d+[\s\w]*z[\u0142l]",
    }
    finansowe = {
        "💸 Brak wynagrodzenia": r"(nie przysługuje|brak)\s+wynagrodzenia",
        "📈 Podwyżki bez zgody": r"(automatyczn[aey]|jednostronn[aey])\s+(zmian[aey]|podwyżk)"
    }
    spec = {
        "Najmu": {"Zakaz podnajmu": r"(zakaz|brak zgody).*?podnajm"},
        "O pracę": {"Nadgodziny niepłatne": r"nadgodzin(y|ach|om).*?nieodpłatn"},
        "Zlecenie": {"Terminy realizacji": r"termin.*?realizacj"},
        "Dzieło": {"Odpowiedzialność za wady": r"odpowiedzialno\w+.*?wady.*?dzie[\u0142l]"},
        "Sprzedaży": {"Reklamacje": r"(reklamacj|odpowiedzialno\w+).*?towar"}
    }
    patterns = wspolne.copy()
    if typ_analizy in ["Wszystkie", "Finansowe"]:
        patterns.update(finansowe)
    if typ_umowy in spec:
        patterns.update(spec[typ_umowy])

    return [(label, m.group()) for label, pat in patterns.items() for m in re.finditer(pat, text, re.IGNORECASE)]

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
uploaded_file = st.file_uploader("📅 Wgraj PDF", type="pdf")
if uploaded_file:
    with st.spinner("🔍 Analiza..."):
        text = extract_text_from_pdf(uploaded_file)
        risks = find_risks(text, typ_umowy, typ_analizy)
        highlighted = highlight_risks(text, risks)

    st.subheader("🚨 Ryzyka:")
    if risks:
        for label, frag in risks:
            st.markdown(f"<div class='risk-box'><b>{label}</b><br>{frag}</div>", unsafe_allow_html=True)
        st.session_state.history.append({"typ": typ_umowy, "analiza": typ_analizy, "risks": risks})
    else:
        st.success("✅ Brak ryzyk.")

    st.subheader("📄 Podgląd umowy:")
    st.markdown(highlighted)

    with st.expander("📂 Eksport analizy"):
        st.download_button("📁 Pobierz TXT", highlighted, file_name="analiza.txt")
        st.download_button("🧾 Pobierz PDF", export_to_pdf(highlighted), file_name="analiza.pdf")

    with st.expander("🔐 Historia analiz"):
        for i, entry in enumerate(st.session_state.history[::-1], 1):
            st.write(f"{i}. {entry['typ']} ({entry['analiza']}): {len(entry['risks'])} ryzyk")
else:
    st.info("✍️ Wgraj PDF umowy, aby zacząć.")
