import streamlit as st
import fitz  # PyMuPDF
import re

# === STRONA ===
st.set_page_config(
    page_title="UmowaAI – Przyszłość Prawa",
    layout="centered",
    page_icon="🤖"
)

# === STYL: FUTURYSTYCZNY ===
st.markdown("""
<style>
/* Tło strony */
[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
    color: #FFFFFF;
}

/* Tytuł */
.big-title {
    font-size: 48px;
    font-weight: bold;
    text-align: center;
    background: linear-gradient(to right, #00c6ff, #0072ff);
    -webkit-background-clip: text;
    color: transparent;
    margin-top: 2rem;
}

/* Opis */
.subtitle {
    text-align: center;
    font-size: 18px;
    color: #c0c0c0;
    margin-bottom: 2rem;
}

/* Ryzyko = futurystyczna karta */
.risk-box {
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 12px;
    padding: 15px;
    margin-bottom: 10px;
    box-shadow: 0 0 20px rgba(0,255,255,0.2);
}

.download {
    background-color: #0072ff;
    color: white;
    font-weight: bold;
    border-radius: 8px;
    padding: 10px 16px;
}

a {
    color: #0ff;
}
</style>
""", unsafe_allow_html=True)

# === NAGŁÓWEK ===
st.markdown('<div class="big-title">🤖 UmowaAI</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Analiza umów PDF z wykrywaniem ryzyk prawnych — jak z przyszłości</div>', unsafe_allow_html=True)

# === FUNKCJE ===
def extract_text_from_pdf(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def find_risks(text):
    patterns = {
        "⚠️ Kaucja": r"kaucj[ae]\s+.*?\d+[\s\w]*z[łl]",
        "🚫 Kara umowna": r"kara\s+umowna.*?\d+[\s\w]*z[łl]",
        "⏳ Wypowiedzenie": r"wypowiedze?nie.*?(umowy|kontraktu)?",
        "❌ Zakaz podnajmu": r"(zakaz|brak zgody).*?podnajm",
        "🧾 Odpowiedzialność": r"odpowiedzialn[oó]\w+.*?(najemc[aę]|wynajmuj[aą]cego)"
    }
    results = []
    for label, pattern in patterns.items():
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            results.append((label, match.group()))
    return results

def highlight_risks(text, risks):
    for label, fragment in risks:
        highlighted = f"**[{label}]** {fragment}"
        text = text.replace(fragment, highlighted)
    return text

# === INTERFEJS ===
uploaded_file = st.file_uploader("📂 Wgraj umowę (PDF)", type="pdf")

if uploaded_file:
    with st.spinner("🧠 Analiza w toku..."):
        text = extract_text_from_pdf(uploaded_file)
        risks = find_risks(text)
        highlighted_text = highlight_risks(text, risks)

    st.subheader("📌 Wykryte ryzyka:")
    if risks:
        for label, fragment in risks:
            st.markdown(f'<div class="risk-box"><b>{label}</b><br>{fragment}</div>', unsafe_allow_html=True)
    else:
        st.success("✅ Umowa wygląda bezpiecznie (nie wykryto ryzyk).")

    st.subheader("📄 Podgląd treści z podświetleniami:")
    st.markdown(highlighted_text)

    with st.expander("💾 Pobierz analizę jako TXT"):
        st.download_button("📥 Pobierz analizę", data=highlighted_text, file_name="analiza_umowy.txt", use_container_width=True)
else:
    st.info("🔽 Wgraj umowę PDF, aby rozpocząć analizę.")

