import streamlit as st
import re
from PyPDF2 import PdfReader
from reportlab.pdfgen import canvas
import io

# Ustawienia aplikacji
st.set_page_config(page_title="Umowa AI", layout="wide")

# Styl — ciemniejsze tło + lepszy kontrast
st.markdown("""
    <style>
        .stApp {
            background-color: #f0f4f8;
            font-family: 'Segoe UI', sans-serif;
        }
        .content-text {
            font-size: 18px;
            color: #0f172a;
            line-height: 1.6;
        }
        .highlight {
            font-weight: bold;
            color: #1e3a8a;
        }
    </style>
""", unsafe_allow_html=True)

# Funkcja analizy treści
def analyze_text(text):
    summary = ""
    if re.search(r'odstąpienie|rozwiązanie.*umow', text, re.IGNORECASE):
        summary += "\n- **Trudność w odstąpieniu**: zapisy ograniczające możliwość wypowiedzenia umowy."
    if re.search(r'obowiąz(e|ą)zki|zobowiązany', text, re.IGNORECASE):
        summary += "\n- **Zobowiązania stron**: konieczność wykonania obowiązków dodatkowych."
    if re.search(r'opłata|koszt|zapłaty', text, re.IGNORECASE):
        summary += "\n- **Dodatkowe opłaty**: możliwe koszty nieujęte w głównej treści."
    if re.search(r'nieważn|unieważn', text, re.IGNORECASE):
        summary += "\n- **Ryzyko nieważności**: umowa może zawierać zapisy niezgodne z prawem."
    if re.search(r'kara|odsetki|strata|szkoda', text, re.IGNORECASE):
        summary += "\n- **Kary finansowe**: niekorzystne zapisy finansowe."
    if re.search(r'prawne|pozew|sąd', text, re.IGNORECASE):
        summary += "\n- **Konsekwencje prawne**: możliwość postępowań sądowych."
    if re.search(r'niewywiązuje|niewykona|zaniedbanie', text, re.IGNORECASE):
        summary += "\n- **Naruszenie obowiązków**: ryzyko niezrealizowania zobowiązań."

    score = summary.count('- **')
    return summary.strip(), score

# Funkcja ekstrakcji tekstu z PDF
def extract_text_from_pdf(uploaded_file):
    reader = PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

# Generowanie PDF z analizą
def generate_pdf(text):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer)
    text_object = c.beginText(40, 800)
    for line in text.split('\n'):
        text_object.textLine(line)
    c.drawText(text_object)
    c.save()
    buffer.seek(0)
    return buffer

# MENU
st.sidebar.title("📁 Nawigacja")
menu = st.sidebar.selectbox("Wybierz opcję", ["Strona Główna", "Analiza Umowy", "Ryzyka"])

# STRONA GŁÓWNA
if menu == "Strona Główna":
    st.title("🤖 UmowaAI – Twój asystent do analizy umów")
    st.markdown("""
        <div class="content-text">
        Nasza aplikacja wspiera Cię w bezpiecznym przeglądaniu, analizie i rozumieniu treści umów cywilnoprawnych.<br><br>

        <span class="highlight">🔍 Co potrafi aplikacja?</span><br>
        • Przeskanuj umowę i sprawdź, czy zawiera niebezpieczne zapisy.<br>
        • Wykryj kluczowe ryzyka prawne, finansowe i operacyjne.<br>
        • Pobierz PDF z raportem, który możesz wykorzystać jako załącznik lub archiwum.<br><br>

        <span class="highlight">📂 Jak to działa?</span><br>
        • Prześlij plik PDF lub wklej tekst umowy.<br>
        • Algorytmy językowe sprawdzą treść pod kątem ryzyk.<br>
        • Zobaczysz podsumowanie oraz liczbę wykrytych ryzyk.<br><br>

        <span class="highlight">🔐 Dlaczego warto?</span><br>
        • Aplikacja pomaga chronić Twoje interesy przed nieuczciwymi zapisami.<br>
        • Oszczędzasz czas – nie musisz czytać całej umowy samodzielnie.<br>
        • Możesz podejmować świadome decyzje przy zawieraniu umowy.<br><br>
        </div>
    """, unsafe_allow_html=True)

# ANALIZA
elif menu == "Analiza Umowy":
    st.title("📑 Prześlij umowę do analizy")
    uploaded_file = st.file_uploader("Wgraj plik PDF", type="pdf")
    text_input = st.text_area("Lub wklej treść umowy:", height=300)

    if st.button("🔍 Analizuj"):
        if uploaded_file:
            contract_text = extract_text_from_pdf(uploaded_file)
        else:
            contract_text = text_input

        if contract_text:
            summary, score = analyze_text(contract_text)
            st.subheader("📌 Wykryte ryzyka:")
            st.markdown(summary)
            st.metric("Liczba ryzyk", score)
            pdf_data = generate_pdf(summary)
            st.download_button("📥 Pobierz raport PDF", pdf_data, "analiza_umowy.pdf")

# RYZYKA
elif menu == "Ryzyka":
    st.title("⚠️ Typowe ryzyka w umowach")
    st.markdown("""
        <div class="content-text">
        Zebraliśmy najczęstsze ryzyka, które pojawiają się w umowach:<br><br>

        <span class="highlight">🛑 Utrudnione odstąpienie:</span> brak możliwości rozwiązania umowy w razie problemów.<br><br>

        <span class="highlight">📄 Dodatkowe obowiązki:</span> ukryte zapisy zmuszające Cię do działań, których się nie spodziewasz.<br><br>

        <span class="highlight">💸 Ukryte opłaty:</span> zapisy wymagające dodatkowych płatności lub opłat manipulacyjnych.<br><br>

        <span class="highlight">⚖️ Konsekwencje prawne:</span> groźba pozwów lub innych sankcji prawnych.<br><br>

        <span class="highlight">🧾 Kara umowna:</span> zapisy przewidujące wysokie kary za niewielkie uchybienia.<br><br>

        <span class="highlight">⛔ Nieważność umowy:</span> błędy formalne, które mogą skutkować nieważnością całego dokumentu.<br><br>

        <span class="highlight">📉 Utrata kontroli:</span> przeniesienie pełnej odpowiedzialności na jedną stronę.
        </div>
    """, unsafe_allow_html=True)
