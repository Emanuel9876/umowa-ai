import streamlit as st
import fitz  # PyMuPDF
import re
from PIL import Image
from io import BytesIO
from fpdf import FPDF
import datetime

st.set_page_config(page_title="UmowaAI – Ekspert od umów", layout="wide")

# === STYL STRONY ===
st.markdown("""
<style>
body {
    background-color: #0f2027;
    background-image: linear-gradient(315deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
    color: white;
}
[data-testid="stAppViewContainer"] > .main {
    background-color: rgba(0, 0, 0, 0);
    padding: 2rem;
}
h1, h2, h3, h4 {
    color: #ffffff;
    text-shadow: 1px 1px 2px #000000;
}
.stButton > button {
    border-radius: 1rem;
    padding: 0.75rem 1.5rem;
    background-color: #ff4b1f;
    background-image: linear-gradient(to right, #ff416c, #ff4b2b);
    color: white;
    border: none;
    font-weight: bold;
}
.stSelectbox > div > div {
    background-color: #ffffff11;
    color: #ffffff;
}
.block-container {
    padding-top: 2rem;
}
.risk-box {
    background-color: rgba(255, 255, 255, 0.1);
    border-left: 5px solid #ff4b2b;
    padding: 1rem;
    margin: 1rem 0;
    border-radius: 10px;
    color: white;
    font-size: 1rem;
}
</style>
""", unsafe_allow_html=True)

# === NAGŁÓWEK Z OBRAZKIEM ===
st.image("https://cdn.pixabay.com/photo/2017/08/10/07/32/law-2619305_1280.jpg", use_container_width=True)
st.title("🧠 UmowaAI – Ekspert od ryzyk prawnych")
st.markdown("""
##### Wybierz typ umowy, prześlij plik PDF i pozwól AI wskazać wszystkie potencjalne zagrożenia prawne w przejrzysty i zrozumiały sposób.
---
""")

# === OPCJE UŻYTKOWNIKA ===
dark_mode = st.toggle("🌗 Tryb ciemny/jasny")
lang = st.radio("🌐 Język interfejsu", ["Polski", "English"])
dodatkowa_analiza = st.checkbox("💸 Włącz analizę finansową i niezgodności")

# === WYBÓR TYPÓW UMÓW ===
typ_umowy = st.selectbox("📄 Wybierz typ umowy", ["Najmu", "O pracę", "Zlecenie", "Dzieło", "Sprzedaży"])

# === FUNKCJE ===
def extract_text_from_pdf(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def find_risks(text, typ):
    wspolne = {
        "⚠️ Kaucja": r"kaucj[ae]\s+.*?\d+[\s\w]*z[łl]",
        "⏳ Wypowiedzenie": r"wypowiedze?nie.*?(umowy|kontraktu)?",
        "🚫 Kara umowna": r"kara\s+umowna.*?\d+[\s\w]*z[łl]",
        "📉 Brak odpowiedzialności": r"nie ponosi odpowiedzialn",
    }
    if dodatkowa_analiza:
        wspolne["💸 Ukryte koszty"] = r"dodatkowe opłaty|ukryte koszty"
    typowe = {
        "Najmu": {
            "❌ Zakaz podnajmu": r"(zakaz|brak zgody).*?podnajm",
            "🧾 Odpowiedzialność za szkody": r"odpowiedzialn[oó]\w+.*?(najemc[aę]|wynajmuj[aą]cego)"
        },
        "O pracę": {
            "⛔ Okres próbny": r"okres\s+pr[óo]bny.*?\d+\s+(dni|miesi[ąa]c)",
            "💼 Nadgodziny niepłatne": r"nadgodzin(y|ach|om).*?nieodpłatn"
        },
        "Zlecenie": {
            "💸 Brak wynagrodzenia": r"(nie przysługuje|brak)\s+wynagrodzenia",
            "📆 Terminy realizacji": r"termin.*?realizacj"
        },
        "Dzieło": {
            "🛠️ Odpowiedzialność za wady": r"odpowiedzialno\w+.*?wady.*?dzie[łl]",
            "📉 Kara za opóźnienie": r"kara.*?op[oó]\w+nienia"
        },
        "Sprzedaży": {
            "🔍 Reklamacje": r"(reklamacj|odpowiedzialno\w+).*?towar",
            "📅 Termin dostawy": r"termin.*?dostaw[yie]"
        }
    }
    patterns = wspolne.copy()
    patterns.update(typowe.get(typ, {}))

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
uploaded_file = st.file_uploader("📥 Prześlij plik PDF z umową", type="pdf")
if uploaded_file:
    with st.spinner("🔎 Trwa analiza dokumentu..."):
        text = extract_text_from_pdf(uploaded_file)
        risks = find_risks(text, typ_umowy)
        highlighted = highlight_risks(text, risks)

    st.subheader("🚨 Wykryte ryzyka:")
    if risks:
        for label, frag in risks:
            st.markdown(f"<div class='risk-box'><b>{label}</b><br>{frag}</div>", unsafe_allow_html=True)
    else:
        st.success("✅ Nie znaleziono oczywistych ryzyk w umowie.")

    st.subheader("📄 Treść umowy z oznaczeniami:")
    st.markdown(highlighted)

    with st.expander("💾 Pobierz wynik analizy"):
        st.download_button("📩 Pobierz analizę jako TXT", data=highlighted, file_name="analiza_umowy.txt")
        pdf_bytes = export_to_pdf(highlighted)
        st.download_button("🧾 Pobierz jako PDF", data=pdf_bytes, file_name="analiza_umowy.pdf")

    st.info("🕓 Historia i logowanie dostępne w wersji premium (wkrótce)")
else:
    st.info("✍️ Wgraj umowę w formacie PDF, aby rozpocząć analizę.")
