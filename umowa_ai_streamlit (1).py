import streamlit as st
import fitz  # PyMuPDF
import re

# === KONFIGURACJA STRONY ===
st.set_page_config(page_title="UmowaAI – Legal Risk Detector", layout="wide")

# === STYL STRONY ===
st.markdown("""
<style>
@keyframes gradientBG {
  0% {background-position: 0% 50%;}
  50% {background-position: 100% 50%;}
  100% {background-position: 0% 50%;}
}
body {
    background: linear-gradient(135deg, #1f1c2c, #928dab);
    background-size: 400% 400%;
    animation: gradientBG 15s ease infinite;
    font-family: 'Segoe UI', sans-serif;
    color: white;
}
[data-testid="stAppViewContainer"] > .main {
    background-color: rgba(255, 255, 255, 0.03);
    backdrop-filter: blur(8px);
    padding: 2rem;
    border-radius: 16px;
}
h1, h2, h3 {
    color: #ffffff;
    text-shadow: 1px 1px 2px #000;
}
.stButton > button {
    border-radius: 0.75rem;
    padding: 0.8rem 1.6rem;
    background: linear-gradient(to right, #ff416c, #ff4b2b);
    color: white;
    font-weight: bold;
    border: none;
    transition: 0.3s ease;
}
.stButton > button:hover {
    background: linear-gradient(to right, #ff4b2b, #ff416c);
    transform: scale(1.02);
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
.stSelectbox > div > div {
    background-color: #22222255;
    color: white;
}
.block-container {
    padding-top: 1rem;
}
</style>
""", unsafe_allow_html=True)

# === INTERFEJS MULTI-JĘZYKOWY ===
lang = st.radio("🌐 Wybierz język / Choose language", ["Polski", "English"])
is_pl = lang == "Polski"

# === OBRAZ NAGŁÓWKA ===
st.image("https://cdn.pixabay.com/photo/2022/01/30/11/23/ai-6983455_1280.jpg", use_container_width=True)

# === TYTUŁ I OPIS ===
st.title("🤖 UmowaAI – " + ("Ekspert od ryzyk prawnych" if is_pl else "AI Legal Risk Analyzer"))
st.markdown("#### " + (
    "Prześlij umowę PDF i AI znajdzie ryzykowne zapisy prawne, finansowe lub inne – automatycznie i zrozumiale."
    if is_pl else
    "Upload a contract PDF and AI will detect legal, financial, or other risk clauses – clearly and automatically."
))
st.markdown("---")

# === OPCJE: TYP UMOWY I TYP ANALIZY ===
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
        "Najmu": {
            "🔐 Zakaz podnajmu": r"(zakaz|brak zgody).*?podnajm",
        },
        "O pracę": {
            "💼 Nadgodziny niepłatne": r"nadgodzin(y|ach|om).*?nieodpłatn"
        },
        "Zlecenie": {
            "📆 Terminy realizacji": r"termin.*?realizacj"
        },
        "Dzieło": {
            "🛠️ Odpowiedzialność za wady": r"odpowiedzialno\w+.*?wady.*?dzie[łl]"
        },
        "Sprzedaży": {
            "🔍 Reklamacje": r"(reklamacj|odpowiedzialno\w+).*?towar"
        }
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
else:
    st.info("✍️ Wgraj umowę PDF, aby rozpocząć analizę." if is_pl else "✍️ Upload a PDF to begin analysis.")
