import streamlit as st
import re
from PyPDF2 import PdfReader
from reportlab.pdfgen import canvas
import io

st.set_page_config(page_title="Umowa AI", layout="wide")
st.markdown("""
    <style>
        body {
            background-color: #dbeafe;
            font-family: 'Segoe UI', sans-serif;
        }
        .stApp {
            background-color: #dbeafe;
        }
        .highlight {
            font-weight: bold;
            font-size: 20px;
            color: #111827;
            font-family: 'Georgia', serif;
        }
        .content-text {
            font-size: 18px;
            color: #1e293b;
        }
        .custom-label {
            font-size: 20px;
            color: #1e3a8a;
            font-weight: bold;
            margin-top: 20px;
        }
        .summary-section {
            text-align: center;
        }
    </style>
""", unsafe_allow_html=True)

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

def ocena_poziomu_ryzyka(score):
    if score <= 1:
        return "Niskie", "🟢", "Umowa wydaje się bezpieczna. Zalecamy jednak przeczytanie całego dokumentu."
    elif 2 <= score <= 3:
        return "Średnie", "🟡", "Zidentyfikowano kilka potencjalnych ryzyk. Warto skonsultować się z doradcą."
    else:
        return "Wysokie", "🔴", "Umowa zawiera wiele niepokojących zapisów. Zalecamy ostrożność i konsultację prawną."

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

st.sidebar.title("Menu")
menu = st.sidebar.selectbox("Wybierz opcję", ["Strona Główna", "Analiza Umowy", "Ryzyka"])

if menu == "Strona Główna":
    st.markdown("""
        <style>
            .hero {
                background-color: #e0f2fe;
                padding: 4rem 2rem;
                border-radius: 12px;
                text-align: center;
                margin: auto;
                max-width: 1000px;
                box-shadow: 0 8px 24px rgba(0,0,0,0.15);
            }
            .hero h1 {
                font-size: 3rem;
                color: #1e3a8a;
                margin-bottom: 1.5rem;
                font-family: 'Segoe UI', sans-serif;
            }
            .hero p {
                font-size: 1.25rem;
                color: #1e293b;
                line-height: 1.8;
            }
            .benefits {
                margin-top: 3rem;
                background-color: #dbeafe;
                border-left: 8px solid #3b82f6;
                padding: 2rem;
                border-radius: 12px;
                max-width: 900px;
                margin-left: auto;
                margin-right: auto;
            }
            .benefits h2 {
                color: #1e3a8a;
                font-size: 1.75rem;
                margin-bottom: 1rem;
            }
            .benefits ul {
                text-align: left;
                padding-left: 1.5rem;
                font-size: 1.1rem;
                line-height: 1.8;
                color: #0f172a;
            }
        </style>

        <div class="hero">
            <h1>🤖 UmowaAI – Twój inteligentny doradca od umów</h1>
            <p>
                Witaj w aplikacji, która pomoże Ci bezpiecznie analizować treść umów cywilnoprawnych, zanim je podpiszesz. <br><br>
                Dzięki technologii AI sprawdzisz w kilka sekund, czy dokument zawiera ryzykowne zapisy.
                <br><br>
                🔹 Wgraj plik PDF lub wklej tekst<br>
                🔹 Otrzymaj podsumowanie zagrożeń<br>
                🔹 Pobierz raport PDF
            </p>
        </div>

        <div class="benefits">
            <h2>💼 Dlaczego warto zaufać UmowieAI?</h2>
            <ul>
                <li>✅ Oszczędzasz czas – analiza trwa kilka sekund</li>
                <li>✅ Bezpieczne dane – nic nie jest zapisywane</li>
                <li>✅ Intuicyjny interfejs – nawet dla osób bez wiedzy prawniczej</li>
                <li>✅ Wsparcie sztucznej inteligencji i reguł języka prawniczego</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

elif menu == "Analiza Umowy":
    st.title("🔍 Analiza treści umowy")
    st.markdown('<p class="custom-label">Wgraj plik PDF umowy:</p>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("", type="pdf")

    st.markdown('<p class="custom-label">Lub wklej treść umowy:</p>', unsafe_allow_html=True)
    text_input = st.text_area("", height=300)

    if st.button("Analizuj"):
        if uploaded_file:
            contract_text = extract_text_from_pdf(uploaded_file)
        else:
            contract_text = text_input

        if contract_text:
            summary, score = analyze_text(contract_text)
            ocena, kolor, komentarz = ocena_poziomu_ryzyka(score)
            st.markdown('<div class="summary-section">', unsafe_allow_html=True)
            st.subheader("📌 Podsumowanie ryzyk:")
            st.markdown(summary)
            st.metric("Liczba wykrytych ryzyk", score)
            st.subheader(f"🎯 Ocena poziomu ryzyka: {kolor} {ocena}")
            st.info(komentarz)
            st.progress(min(score / 6, 1.0))
            st.markdown('</div>', unsafe_allow_html=True)
            pdf_data = generate_pdf(summary)
            st.download_button(label="📥 Pobierz analizę jako PDF", data=pdf_data, file_name="analiza_umowy.pdf")

elif menu == "Ryzyka":
    st.title("⚠️ Możliwe ryzyka w umowach")
    st.markdown("""
        <div class="content-text">
        <span class="highlight">Utrudnione odstąpienie od umowy:</span><br>
        Umowy często zawierają zapisy, które utrudniają lub uniemożliwiają odstąpienie od umowy, nawet jeśli jej warunki okazują się niekorzystne.<br><br>

        <span class="highlight">Dodatkowe obowiązki:</span><br>
        Możesz być zobowiązany do spełnienia dodatkowych czynności lub płatności, o których nie miałeś pojęcia.<br><br>

        <span class="highlight">Dodatkowe opłaty:</span><br>
        Nieuważne czytanie umowy może prowadzić do konieczności zapłaty dodatkowych opłat, które nie były wliczone w pierwotne koszty.<br><br>

        <span class="highlight">Nieważność umowy:</span><br>
        Niektóre umowy mogą być uznane za nieważne, jeśli zawierają niezgodne z prawem lub zasadami współżycia społecznego postanowienia.<br><br>

        <span class="highlight">Konsekwencje finansowe:</span><br>
        Jeśli w umowie znajdują się niekorzystne zapisy dotyczące płatności, odsetek lub kar umownych, możesz ponieść znaczne straty finansowe.<br><br>

        <span class="highlight">Skutki prawne:</span><br>
        Nieważność umowy może prowadzić do konieczności zwrotu świadczeń lub dochodzenia odszkodowania, jeśli jedna ze stron poniosła szkody w wyniku jej zawarcia.<br><br>

        <span class="highlight">Niewywiązanie się z umowy:</span><br>
        Jeśli nie rozumiesz swoich obowiązków wynikających z umowy, możesz nieświadomie ich nie wykonać, co może skutkować karami umownymi lub innymi konsekwencjami prawnymi.
        </div>
    """, unsafe_allow_html=True)
