import streamlit as st
import fitz  # PyMuPDF
import re

# Konfiguracja strony
st.set_page_config(
    page_title="UmowaAI – Analiza ryzyk",
    layout="centered",
    page_icon="📄"
)

# Styl nagłówka
st.markdown("""
    <style>
        .title {
            text-align: center;
            font-size: 2.4em;
            font-weight: bold;
            color: #3b82f6;
        }
        .subtitle {
            text-align: center;
            font-size: 1.2em;
            color: gray;
        }
        .risk {
            background-color: #fff7e6;
            padding: 10px;
            margin-bottom: 10px;
            border-left: 5px solid #f59e0b;
            border-radius: 8px;
        }
    </style>
""", unsafe_allow_html=True)

# Nagłówek
st.markdown('<div class="title">📄 UmowaAI</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Automatyczne wykrywanie ryzyk w umowach PDF</div>', unsafe_allow_html=True)
st.write("")

# === Funkcje ===
def extract_text_from_pdf(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def find_risks(text):
    patterns = {
        "Kaucja": r"kaucj[ae]\s+.*?\d+[\s\w]*z[łl]",
        "Kara umowna": r"kara\s+umowna.*?\d+[\s\w]*z[łl]",
        "Wypowiedzenie": r"wypowiedze?nie.*?(umowy|kontraktu)?",
        "Zakaz podnajmu": r"(zakaz|brak zgody).*?podnajm",
        "Odpowiedzialność": r"odpowiedzialn[oó]\w+.*?(najemc[aę]|wynajmuj[aą]cego)"
    }
    results = []
    for label, pattern in patterns.items():
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            results.append((label, match.group()))
    return results

def highlight_risks(text, risks):
    for label, fragment in risks:
        highlighted = f"**[{label.upper()}]** {fragment}"
        text = text.replace(fragment, highlighted)
    return text

# === Interfejs ===
uploaded_file = st.file_uploader("📥 Wgraj plik PDF z umową", type="pdf")

if uploaded_file:
    with st.spinner("🔍 Analizuję dokument..."):
        text = extract_text_from_pdf(uploaded_file)
        risks = find_risks(text)
        highlighted_text = highlight_risks(text, risks)

    st.subheader("🚨 Wykryte ryzyka:")
    if risks:
        for label, fragment in risks:
            st.markdown(f'<div class="risk"><b>{label}</b>: {fragment}</div>', unsafe_allow_html=True)
    else:
        st.success("✅ Nie wykryto istotnych ryzyk.")

    st.subheader("📄 Podgląd umowy z zaznaczeniami:")
    st.markdown(highlighted_text)

    with st.expander("📥 Pobierz analizę jako TXT"):
        st.download_button("💾 Pobierz analizę", data=highlighted_text, file_name="analiza_umowy.txt")

else:
    st.info("📂 Wgraj plik PDF, aby rozpocząć analizę.")

