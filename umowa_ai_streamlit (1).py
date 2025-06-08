import streamlit as st
import fitz  # PyMuPDF
import re
from io import BytesIO
from fpdf import FPDF

# === KONFIGURACJA STRONY ===
st.set_page_config(page_title="UmowaAI – Ekspert od umów", layout="wide")

# === OPCJE INTERFEJSU ===
col1, col2, col3 = st.columns(3)
with col1:
    dark_mode = st.toggle("🌗 Tryb ciemny/jasny")
with col2:
    lang = st.radio("🌐 Język interfejsu", ["Polski", "English"])
with col3:
    dodatkowa_analiza = st.checkbox("💸 Zaawansowane wykrywanie", help="Wykrywa np. ukryte koszty")

# === STYL DYNAMICZNY ===
if dark_mode:
    st.markdown("""
    <style>
    body {
        background-color: #0f2027;
        background-image: linear-gradient(315deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
        color: white;
    }
    [data-testid="stAppViewContainer"] > .main {
        background-color: rgba(0, 0, 0, 0);
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
    .risk-box {
        background-color: rgba(255, 255, 255, 0.1);
        border-left: 5px solid #ff4b2b;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 10px;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# === NAGŁÓWEK ===
st.image("https://cdn.pixabay.com/photo/2017/08/10/07/32/law-2619305_1280.jpg", use_container_width=True)
st.title("🧠 UmowaAI – Ekspert od ryzyk prawnych")
st.markdown("""
##### Prześlij plik PDF i pozwól AI wskazać potencjalne zagrożenia prawne w zrozumiały sposób.
---
""")

# === WYBÓR UMOWY ===
typ_umowy = st.selectbox("📄 Wybierz typ umowy", ["Najmu", "O pracę", "Zlecenie", "Dzieło", "Sprzedaży"])

# === FUNKCJE ===
def extract_text_from_pdf(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    return "".join([page.get_text() for page in doc])

def find_risks(text, typ):
    wspolne = {
        "⚠️ Kaucja": r"kaucj[ae]\s+.*?\d+[\s\w]*z[łl]",
        "⏳ Wypowiedzenie": r"wypowiedze?nie.*?(umowy|kontraktu)?",
        "🚫 Kara umowna": r"kara\s+umowna.*?\d+[\s\w]*z[łl]",
        "📉 Brak odpowiedzialności": r"nie ponosi odpowiedn",
    }
    if dodatkowa_analiza:
        wspolne["💸 Ukryte koszty"] = r"dodatkowe opłaty|ukryte koszty"
    typowe = {
        "Najmu": {
            "❌ Zakaz podnajmu": r"(zakaz|brak zgody).*?podnajm",
            "🧾 Odpowiedzialność za szkody": r"odpowiedzialn[oó].*?(najemc[aę]|wynajmuj[aą]cego)"
        },
        "O pracę": {
            "⛔ Okres próbny": r"okres\s+pr[óo]bny.*?\d+\s+(dni|miesi[ąa]c)",
            "💼 Nadgodziny niepłatne": r"nadgodzin.*?nieodpłatn"
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
    patterns = wspolne | typowe.get(typ, {})
    results = []
    for label, pattern in patterns.items():
        for match in re.finditer(pattern, text, re.IGNORECASE):
            results.append((label, match.group()))
    return results

def highlight_risks(text, risks):
    for label, fragment in risks:
        text = text.replace(fragment, f"**[{label}]** {fragment}")
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

# === UPLOAD I ANALIZA ===
uploaded_file = st.file_uploader("📥 Prześlij umowę (PDF)", type="pdf")
if uploaded_file:
    with st.spinner("🔎 Analiza dokumentu..."):
        text = extract_text_from_pdf(uploaded_file)
        risks = find_risks(text, typ_umowy)
        highlighted = highlight_risks(text, risks)

    st.subheader("🚨 Wykryte ryzyka:")
    if risks:
        for label, frag in risks:
            st.markdown(f"<div class='risk-box'><b>{label}</b><br>{frag}</div>", unsafe_allow_html=True)
    else:
        st.success("✅ Nie wykryto istotnych ryzyk.")

    st.subheader("📄 Umowa z oznaczeniami:")
    st.markdown(highlighted)

    with st.expander("💾 Pobierz analizę"):
        st.download_button("📩 TXT", data=highlighted, file_name="analiza_umowy.txt")
        st.download_button("🧾 PDF", data=export_to_pdf(highlighted), file_name="analiza_umowy.pdf")

    st.info("🔐 Historia analiz i logowanie dostępne w wersji premium – już wkrótce!")
else:
    st.info("✍️ Prześlij dokument PDF, aby rozpocząć analizę.")
