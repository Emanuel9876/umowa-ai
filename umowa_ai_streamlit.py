import streamlit as st
import fitz  # PyMuPDF
import re
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from datetime import datetime

# === KONFIGURACJA STRONY ===
st.set_page_config(page_title="UmowaAI – Analiza PDF", layout="wide")

# === STYL GLOBALNY ===
st.markdown("""
<style>
    body {
        background-color: #0f1117;
        font-family: 'Segoe UI', sans-serif;
    }
    .block-container {
        padding-top: 2rem;
    }
    .css-18e3th9 {
        background-color: #1c1f26;
        border-radius: 12px;
        padding: 2rem;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    .risk-section strong {
        font-size: 1.6em;
        display: block;
        margin-top: 1.5rem;
        font-family: 'Verdana', sans-serif;
        color: #ff4b4b;
        text-decoration: underline;
    }
    .risk-section p {
        font-size: 1.3em;
        line-height: 1.7;
        text-align: justify;
    }
    h1, h2, h3, h4 {
        color: #ffffff;
    }
    .stButton > button {
        background-color: #0073e6;
        color: white;
        font-weight: bold;
        border-radius: 6px;
        padding: 0.5rem 1.2rem;
    }
    .home-card {
        background: linear-gradient(135deg, #1f2a3a, #2f3e4f);
        color: #ffffff;
        transition: transform 0.3s ease;
        border: 1px solid #3c4f64;
    }
    .home-card:hover {
        transform: scale(1.03);
    }
</style>
""", unsafe_allow_html=True)

st.title("📄 UmowaAI – Wykrywanie Ryzyk i Analiza PDF")

menu = st.sidebar.radio("📌 Nawigacja:", [
    "Strona główna",
    "🔐 Logowanie / Rejestracja",
    "📄 Wgraj PDF",
    "📋 Wklej tekst",
    "🛡️ Ryzyka",
    "📅 Pobierz analizę",
    "📚 Dodatkowe Funkcje"
])

def extract_text_from_pdf(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def analyze_text(text):
    summary = ""
    if re.search(r'odstąpienie|rozwiązanie.*umow', text, re.IGNORECASE):
        summary += "\n- **Utrudnione odstąpienie od umowy**: możliwe ograniczenia w odstąpieniu od umowy."
    if re.search(r'obowiąz(e|ą)zki|zobowiązany', text, re.IGNORECASE):
        summary += "\n- **Dodatkowe obowiązki**: możliwe zobowiązania użytkownika."
    if re.search(r'opłata|koszt|zapłaty', text, re.IGNORECASE):
        summary += "\n- **Dodatkowe opłaty**: potencjalne ukryte koszty."
    if re.search(r'nieważn|unieważn', text, re.IGNORECASE):
        summary += "\n- **Nieważność umowy**: zapisy mogą prowadzić do nieważności."
    if re.search(r'kara|odsetki|strata|szkoda', text, re.IGNORECASE):
        summary += "\n- **Konsekwencje finansowe**: ryzyko dodatkowych kosztów."
    if re.search(r'prawne|pozew|sąd', text, re.IGNORECASE):
        summary += "\n- **Skutki prawne**: potencjalne problemy prawne."
    if re.search(r'niewywiązuje|niewykona|zaniedbanie', text, re.IGNORECASE):
        summary += "\n- **Niewywiązanie się z umowy**: ryzyko niewykonania obowiązków."
    return summary.strip()

def generate_pdf(summary):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    textobject = c.beginText(40, 750)
    textobject.setFont("Helvetica", 12)
    textobject.textLine("Raport analizy umowy – UmowaAI")
    textobject.textLine(f"Data analizy: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    textobject.textLine("\nWykryte ryzyka:")
    for line in summary.split("\n"):
        textobject.textLine(line)
    c.drawText(textobject)
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

def show_risks():
    st.subheader("🛡️ Możliwe Ryzyka w Umowie")
    st.markdown("""
    <div class="risk-section">
    <strong>1. Utrudnione odstąpienie od umowy</strong>
    <p>Nieprecyzyjne lub rygorystyczne warunki odstąpienia mogą utrudnić rezygnację z umowy.</p>

    <strong>2. Ukryte koszty</strong>
    <p>Wzmianki o dodatkowych opłatach, karach umownych lub kosztach mogą nie być widoczne na pierwszy rzut oka.</p>

    <strong>3. Niekorzystne warunki finansowe</strong>
    <p>Zbyt wysokie odsetki, opłaty za opóźnienie lub niejasne warunki finansowe mogą narazić użytkownika na straty.</p>

    <strong>4. Ograniczenie odpowiedzialności drugiej strony</strong>
    <p>Zapisy ograniczające odpowiedzialność kontrahenta za błędy lub szkody.</p>

    <strong>5. Wymuszone zobowiązania</strong>
    <p>Postanowienia mogą nakładać na użytkownika obowiązki, które nie są oczywiste przy podpisywaniu umowy.</p>

    <strong>6. Klauzule niedozwolone (abuzywne)</strong>
    <p>Nieuczciwe postanowienia, które mogą być niezgodne z prawem konsumenckim.</p>

    <strong>7. Brak możliwości negocjacji</strong>
    <p>Umowy "take-it-or-leave-it", w których jedna strona nie ma realnego wpływu na treść dokumentu.</p>
    </div>
    """, unsafe_allow_html=True)

if menu == "Strona główna":
    st.markdown("""
    ### Witaj w UmowaAI!
    
    Aplikacja do automatycznej analizy umów i wykrywania potencjalnych zagrożeń. 
    
    - 🔹 Wgraj plik PDF lub wklej tekst umowy
    - 🔹 Skanuj dokument w poszukiwaniu ryzyk
    - 🔹 Generuj raport w formacie PDF
    
    **Dlaczego warto?**

    🔗 Łatwa obsługa · 🔍 Inteligentna analiza · 📈 Szybkie wyniki
    
    ---
    """, unsafe_allow_html=True)

elif menu == "🔐 Logowanie / Rejestracja":
    with st.form("login_form"):
        ...

elif menu == "📄 Wgraj PDF":
    uploaded_file = st.file_uploader("Wgraj plik PDF", type="pdf")
    if uploaded_file:
        text = extract_text_from_pdf(uploaded_file)
        st.text_area("📄 Zawartość pliku:", text, height=300)
        summary = analyze_text(text)
        st.markdown("### 📌 Podsumowanie analizy:")
        st.info(summary)
        if st.button("📄 Pobierz raport PDF"):
            pdf_file = generate_pdf(summary)
            st.download_button("📩 Pobierz PDF", data=pdf_file, file_name="raport_umowaAI.pdf")

elif menu == "📋 Wklej tekst":
    user_text = st.text_area("Wklej tekst umowy:", height=300)
    if user_text:
        summary = analyze_text(user_text)
        st.success("✅ Tekst zapisany do analizy")
        st.markdown("### 📌 Podsumowanie analizy:")
        st.info(summary)
        if st.button("📄 Pobierz raport PDF"):
            pdf_file = generate_pdf(summary)
            st.download_button("📩 Pobierz PDF", data=pdf_file, file_name="raport_umowaAI.pdf")

elif menu == "🛡️ Ryzyka":
    show_risks()

elif menu == "📅 Pobierz analizę":
    st.info("🔧 Funkcja eksportu PDF z analizą dostępna w zakładce 'Wgraj PDF' lub 'Wklej tekst'.")

elif menu == "📚 Dodatkowe Funkcje":
    st.header("🚀 Rozszerzone Funkcje Aplikacji")
    st.markdown("""
    1. 🔍 **Podświetlanie ryzyk w tekście** – już wkrótce zobaczysz dokładnie, które fragmenty umowy są ryzykowne.
    2. 📄 **Profesjonalny raport PDF** – z logo, datą, listą ryzyk i podsumowaniem.
    3. 📈 **Wskaźnik ryzyka** – ocena procentowa ryzyka w umowie.
    4. 🤖 **Tryb Smart Advisor** – porozmawiaj z AI na temat konkretnej umowy.
    5. �\udce...
