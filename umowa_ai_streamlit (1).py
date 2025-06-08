import streamlit as st
import fitz  # PyMuPDF
import re
from PIL import Image
import base64

st.set_page_config(page_title="UmowaAI – Ekspert od umów", layout="wide")

# === STYL STRONY ===
st.markdown("""
<style>
[data-testid="stAppViewContainer"] {
    background-image: url('https://images.unsplash.com/photo-1554224155-6726b3ff858f');
    background-size: cover;
    background-repeat: no-repeat;
    background-attachment: fixed;
    color: #fff;
}

.title {
    font-size: 45px;
    font-weight: bold;
    text-align: center;
    margin-top: 1rem;
    color: #fff;
    text-shadow: 1px 1px 3px #000;
}

.subtitle {
    text-align: center;
    font-size: 18px;
    color: #e0e0e0;
    margin-bottom: 1rem;
}

.risk-box {
    background: rgba(255, 255, 255, 0.15);
    border-radius: 12px;
    padding: 10px;
    margin-bottom: 10px;
    box-shadow: 0 0 10px rgba(255,255,255,0.2);
}
</style>
""", unsafe_allow_html=True)

# === NAGŁÓWEK ===
st.markdown('<div class="title">🧠 UmowaAI – Ekspert od umów</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Analizuj PDF-y różnych umów: najmu, o pracę, zlecenia i wykrywaj ryzyka prawne</div>', unsafe_allow_html=True)

# === WYBÓR RODZAJU UMOWY ===
umowa_typ = st.selectbox("📑 Wybierz typ umowy do analizy:", ["Najmu", "O pracę", "Zlecenie"])

# === FUNKCJE ===
def extract_text_from_pdf(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def find_risks(text, typ):
    common = {
        "⚠️ Kaucja": r"kaucj[ae]\s+.*?\d+[\s\w]*z[łl]",
        "⏳ Wypowiedzenie": r"wypowiedze?nie.*?(umowy|kontraktu)?",
        "🚫 Kara umowna": r"kara\s+umowna.*?\d+[\s\w]*z[łl]",
    }

    najem = {
        "❌ Zakaz podnajmu": r"(zakaz|brak zgody).*?podnajm",
        "🧾 Odpowiedzialność": r"odpowiedzialn[oó]\w+.*?(najemc[aę]|wynajmuj[aą]cego)"
    }

    praca = {
        "⛔ Okres próbny": r"okres\s+pr[óo]bny.*?\d+\s+(dni|miesi[ąa]c)",
        "💼 Nadgodziny": r"nadgodzin(y|ach|om).*?(płatne|nieodpłatne)"
    }

    zlecenie = {
        "💸 Odpłatność": r"wynagrodzen[iea].*?(brutto|netto)?",
        "📆 Terminy": r"termin.*?realizacj"
    }

    risks = common.copy()
    if typ == "Najmu":
        risks.update(najem)
    elif typ == "O pracę":
        risks.update(praca)
    elif typ == "Zlecenie":
        risks.update(zlecenie)

    results = []
    for label, pattern in risks.items():
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            results.append((label, match.group()))
    return results

def highlight_risks(text, risks):
    for label, fragment in risks:
        highlighted = f"**[{label}]** {fragment}"
        text = text.replace(fragment, highlighted)
    return text

# === WGRANIE PDF ===
uploaded_file = st.file_uploader("📂 Wgraj plik PDF", type="pdf")

if uploaded_file:
    with st.spinner("🔍 Analizuję..."):
        text = extract_text_from_pdf(uploaded_file)
        risks = find_risks(text, umowa_typ)
        highlighted_text = highlight_risks(text, risks)

    st.subheader("📌 Wykryte ryzyka:")
    if risks:
        for label, fragment in risks:
            st.markdown(f'<div class="risk-box"><b>{label}</b><br>{fragment}</div>', unsafe_allow_html=True)
    else:
        st.success("✅ Umowa wygląda dobrze. Brak wykrytych ryzyk.")

    st.subheader("📄 Podgląd z oznaczeniami:")
    st.markdown(highlighted_text)

    with st.expander("💾 Pobierz jako TXT"):
        st.download_button("📥 Pobierz analizę", data=highlighted_text, file_name="analiza_umowy.txt")
else:
    st.info("📤 Wgraj plik PDF, by rozpocząć analizę.")

