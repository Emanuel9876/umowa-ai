import streamlit as st
import re
from PyPDF2 import PdfReader
from reportlab.pdfgen import canvas
import io

# Ustawienia strony
st.set_page_config(page_title="Umowa AI", layout="wide")
st.markdown("""
    <style>
        .stApp {
            background-color: #f0f4f8;
            font-family: 'Segoe UI', sans-serif;
        }
        .highlight {
            font-weight: bold;
            font-size: 20px;
            color: #0f172a;
            font-family: 'Georgia', serif;
        }
        .content-text {
            font-size: 18px;
            color: #1e293b;
        }
        .risk-bar {
            height: 20px;
            background: linear-gradient(90deg, #22c55e, #facc15, #ef4444);
            border-radius: 5px;
            margin-top: 10px;
        }
    </style>
""", unsafe_allow_html=True)

# Analiza tekstu
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

    score = summary.count('- **')
    return summary.strip(), score

def extract_text_from_pdf(uploaded_file):
    reader = PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

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
st.sidebar.title("Menu")
menu = st.sidebar.selectbox("Wybierz opcję", ["Strona Główna", "Analiza Umowy", "Ryzyka"])

if menu == "Strona Główna":
    st.title("📄 Umowa AI – Twój osobisty analityk umów")
    st.markdown("""
        <div class="content-text">
        Nasza aplikacja wspierana sztuczną inteligencją pomaga identyfikować ryzykowne zapisy w umowach cywilnoprawnych.<br><br>
        ✅ Zastosowanie:<br>
        - Analiza zapisów umów (PDF / tekst)<br>
        - Wykrywanie kluczowych ryzyk<br>
        - Automatyczne podsumowanie z możliwością pobrania PDF<br><br>

        📌 Jak korzystać:<br>
        - Przejdź do zakładki "Analiza Umowy"<br>
        - Wgraj plik lub wklej tekst<br>
        - Otrzymasz raport ryzyk oraz ich liczbę<br><br>

        🛡️ Zadbaj o swoje bezpieczeństwo prawne z pomocą AI!
        </div>
    """, unsafe_allow_html=True)

elif menu == "Analiza Umowy":
    st.title("🔍 Analiza treści umowy")
    uploaded_file = st.file_uploader("Wgraj plik PDF umowy", type="pdf")
    text_input = st.text_area("Lub wklej treść umowy:", height=300)

    if st.button("Analizuj"):
        if uploaded_file:
            contract_text = extract_text_from_pdf(uploaded_file)
        else:
            contract_text = text_input

        if contract_text:
            summary, score = analyze_text(contract_text)
            st.subheader("📌 Podsumowanie ryzyk:")
            st.markdown(summary, unsafe_allow_html=True)
            st.metric("Liczba wykrytych ryzyk", score)

            # Pasek ryzyka
            st.markdown("##### Poziom ryzyka:")
            risk_color = "#22c55e" if score <= 2 else "#facc15" if score <= 4 else "#ef4444"
            st.markdown(f"""
                <div style="background-color:{risk_color}; width:{score*14+10}%; height:20px; border-radius:6px;"></div>
            """, unsafe_allow_html=True)

            pdf_data = generate_pdf(summary)
            st.download_button(label="📥 Pobierz analizę jako PDF", data=pdf_data, file_name="analiza_umowy.pdf")

elif menu == "Ryzyka":
    st.title("⚠️ Możliwe ryzyka w umowach")
    st.markdown("""
        <div class="content-text">
        <span class="highlight">Utrudnione odstąpienie od umowy:</span><br>
        Umowy często zawierają zapisy, które utrudniają lub uniemożliwiają odstąpienie od umowy.<br><br>

        <span class="highlight">Dodatkowe obowiązki:</span><br>
        Możesz być zobowiązany do spełnienia dodatkowych czynności lub płatności, o których nie miałeś pojęcia.<br><br>

        <span class="highlight">Dodatkowe opłaty:</span><br>
        Możesz być obciążony kosztami, które nie są jasno przedstawione.<br><br>

        <span class="highlight">Nieważność umowy:</span><br>
        Niektóre postanowienia mogą być sprzeczne z prawem i powodować nieważność całej umowy.<br><br>

        <span class="highlight">Konsekwencje finansowe:</span><br>
        Niektóre zapisy mogą wiązać się z karami, odsetkami lub stratami finansowymi.<br><br>

        <span class="highlight">Skutki prawne:</span><br>
        Możliwość procesów sądowych lub innych komplikacji prawnych.<br><br>

        <span class="highlight">Niewywiązanie się z umowy:</span><br>
        Możliwe konsekwencje wynikające z nieznajomości własnych obowiązków.<br><br>
        </div>
    """, unsafe_allow_html=True)
