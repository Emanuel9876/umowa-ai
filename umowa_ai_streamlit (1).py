import streamlit as st
import fitz  # PyMuPDF
import re

# === KONFIGURACJA STRONY ===
st.set_page_config(page_title="UmowaAI – Legal Risk Detector", layout="wide")

# === STYL STRONY ===
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;800&display=swap');

body {
    background-image: url("https://files.oaiusercontent.com/file-VDXu1R184nwGQa6ocn3h4F");
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
    font-family: 'Poppins', sans-serif;
    color: white;
    margin: 0;
    padding: 0;
}

[data-testid="stAppViewContainer"]::before {
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.6);
    z-index: -1;
}

h1, h2, h3 {
    font-family: 'Poppins', sans-serif;
    font-weight: 800;
    font-size: 2.5rem;
    color: #ffffff;
    text-shadow: 2px 2px 4px #000;
    margin-top: 0.5rem;
}

.stButton > button {
    font-family: 'Poppins', sans-serif;
    font-size: 1.1rem;
}

.nav-title {
    font-size: 2.5rem;
    font-family: 'Poppins', sans-serif;
    font-weight: 800;
    text-shadow: 2px 2px 4px #000;
    text-align: center;
    flex-grow: 1;
}

.nav-left, .nav-right {
    font-size: 1.1rem;
    font-family: 'Poppins', sans-serif;
}
</style>

<style>
@keyframes gradientBG {
  0% {background-position: 0% 50%;}
  50% {background-position: 100% 50%;}
  100% {background-position: 0% 50%;}
}

[data-testid="stAppViewContainer"] > .main {
    background-color: rgba(255, 255, 255, 0.04);
    backdrop-filter: blur(10px);
    padding: 2rem;
    border-radius: 16px;
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

.navbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding: 1rem;
    background: rgba(0, 0, 0, 0.4);
    border-radius: 12px;
    backdrop-filter: blur(5px);
}

.nav-left, .nav-right {
    display: flex;
    align-items: center;
    gap: 1rem;
    color: white;
    font-weight: bold;
    font-size: 1.2rem;
}
</style>
""", unsafe_allow_html=True)

# === INTERFEJS MULTI-JĘZYKOWY ===
st.markdown("""<div class='navbar'>
    <div class='nav-left'>🌐 """, unsafe_allow_html=True)
lang = st.radio("", ["Polski", "English"], horizontal=True, label_visibility="collapsed")
st.markdown("""</div>
    <div class='nav-title'>STRONA GŁÓWNA / Analiza Umów</div>
    <div class='nav-right'>📄 Typ umowy</div>
</div>""", unsafe_allow_html=True)
is_pl = lang == "Polski"

# === OBRAZ NAGŁÓWKA ===
st.image("/mnt/data/84fa4f41-724c-4375-a361-b6416c34eebe.png", use_container_width=True)

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

st.markdown("### 🔎 Wybierz typ analizy ryzyk:")
col1, col2, col3 = st.columns(3)
selected_types = []
if col1.checkbox("📌 Ryzyka prawne", value=True):
    selected_types.append("Prawne")
if col2.checkbox("💰 Ryzyka finansowe", value=True):
    selected_types.append("Finansowe")

if not selected_types:
    st.warning("⚠️ Wybierz przynajmniej jeden typ ryzyka do analizy.")

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
            "🛠️ Odpowiedzialność za wady": r"odpowiedzialno\\w+.*?wady.*?dzie[łl]"
        },
        "Sprzedaży": {
            "🔍 Reklamacje": r"(reklamacj|odpowiedzialno\\w+).*?towar"
        }
    }

    patterns = wspolne.copy()
    if "Finansowe" in typ_analizy:
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
        frag_clean = re.escape(frag)
        highlighted = f"<mark style='background-color:#ff4b2b33;padding:2px 4px;border-radius:4px'><b>{label}</b>: {frag}</mark>"
        text = re.sub(frag_clean, highlighted, text, flags=re.IGNORECASE)
    return text

# === ANALIZA ===
uploaded_file = st.file_uploader("📥 Wgraj PDF umowy / Upload contract PDF", type="pdf")
if uploaded_file and selected_types:
    with st.spinner("🔍 Analiza... / Analyzing..."):
        text = extract_text_from_pdf(uploaded_file)
        risks = find_risks(text, typ_umowy, selected_types)
        highlighted = highlight_risks(text, risks)

    st.subheader("🚨 Wykryte ryzyka:" if is_pl else "🚨 Detected Risks")
    if risks:
        for label, frag in risks:
            st.markdown(f"<div class='risk-box'><b>{label}</b><br>{frag}</div>", unsafe_allow_html=True)
    else:
        st.success("✅ Brak oczywistych ryzyk." if is_pl else "✅ No obvious risks found.")

    st.subheader("📄 Treść umowy z oznaczeniami:" if is_pl else "📄 Contract with highlights")
    preview_len = 3000
    preview = highlighted[:preview_len]
    st.markdown(preview, unsafe_allow_html=True)
    if len(highlighted) > preview_len:
        with st.expander("🔽 Zobacz całą umowę"):
            st.markdown(highlighted, unsafe_allow_html=True)

    with st.expander("💾 Pobierz analizę / Download result"):
        st.download_button("📩 Pobierz jako TXT" if is_pl else "📩 Download as TXT",
                           data=highlighted, file_name="analiza_umowy.txt")
else:
    st.info("✍️ Wgraj umowę PDF, aby rozpocząć analizę." if is_pl else "✍️ Upload a PDF to begin analysis.")
