import streamlit as st
import fitz  # PyMuPDF
import re

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

# === NAGŁÓWEK ===
st.title("📄 UmowaAI – Wykrywanie Ryzyk i Analiza PDF")

# === MENU ===
menu = st.sidebar.radio("📌 Nawigacja:", [
    "Strona główna",
    "🔐 Logowanie / Rejestracja",
    "📤 Wgraj PDF",
    "📋 Wklej tekst",
    "🛡️ Ryzyka",
    "📥 Pobierz analizę"
])

# === FUNKCJA: WYCIĄGANIE TEKSTU ===
def extract_text_from_pdf(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

# === FUNKCJA: ANALIZA TEKSTU ===
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

# === FUNKCJA: RYZYKA (stałe opisy) ===
def show_risks():
    st.subheader("🛡️ Możliwe Ryzyka w Umowie")
    st.markdown("""
<div class="risk-section">
<strong style='font-family: Georgia; color: #c62828;'>Utrudnione odstąpienie od umowy:</strong>
<p>Umowy często zawierają zapisy, które utrudniają lub uniemożliwiają odstąpienie od umowy, nawet jeśli jej warunki okazują się niekorzystne.</p>

<strong style='font-family: Georgia; color: #c62828;'>Dodatkowe obowiązki:</strong>
<p>Możesz być zobowiązany do spełnienia dodatkowych czynności lub płatności, o których nie miałeś pojęcia.</p>

<strong style='font-family: Georgia; color: #c62828;'>Dodatkowe opłaty:</strong>
<p>Nieuważne czytanie umowy może prowadzić do konieczności zapłaty dodatkowych opłat, które nie były wliczone w pierwotne koszty.</p>

<strong style='font-family: Georgia; color: #c62828;'>Nieważność umowy:</strong>
<p>Niektóre umowy mogą być uznane za nieważne, jeśli zawierają niezgodne z prawem lub zasadami współżycia społecznego postanowienia.</p>

<strong style='font-family: Georgia; color: #c62828;'>Konsekwencje finansowe:</strong>
<p>Jeśli w umowie znajdują się niekorzystne zapisy dotyczące płatności, odsetek lub kar umownych, możesz ponieść znaczne straty finansowe.</p>

<strong style='font-family: Georgia; color: #c62828;'>Skutki prawne:</strong>
<p>Nieważność umowy może prowadzić do konieczności zwrotu świadczeń lub dochodzenia odszkodowania, jeśli jedna ze stron poniosła szkody w wyniku jej zawarcia.</p>

<strong style='font-family: Georgia; color: #c62828;'>Niewywiązanie się z umowy:</strong>
<p>Jeśli nie rozumiesz swoich obowiązków wynikających z umowy, możesz nieświadomie ich nie wykonać, co może skutkować karami umownymi lub innymi konsekwencjami prawnymi.</p>
</div>
""", unsafe_allow_html=True)

# === STRONY ===
if menu == "Strona główna":
    st.markdown("""
    <div style='text-align: center; padding: 2rem 0;'>
        <h1 style='font-size: 3em;'>🤖 UmowaAI – Twoja Osobista AI do Analizy Umów</h1>
        <p style='font-size: 1.3em; color: #cccccc;'>Pozwól sztucznej inteligencji sprawdzić Twoją umowę zanim ją podpiszesz.</p>
    </div>

    <div style='display: flex; justify-content: space-around; padding: 1.5rem 0;'>
        <div class='home-card' style='flex: 1; margin: 1rem; padding: 1rem; border-radius: 12px;'>
            <h3>📤 Wgraj PDF</h3>
            <p>Automatycznie przetworzymy Twoją umowę i zidentyfikujemy potencjalne zagrożenia.</p>
        </div>
        <div class='home-card' style='flex: 1; margin: 1rem; padding: 1rem; border-radius: 12px;'>
            <h3>🛡️ Sprawdź ryzyka</h3>
            <p>Poznaj najczęstsze pułapki prawne ukryte w dokumentach.</p>
        </div>
        <div class='home-card' style='flex: 1; margin: 1rem; padding: 1rem; border-radius: 12px;'>
            <h3>🔍 Zrozum treść</h3>
            <p>Otrzymaj przejrzyste podsumowanie najważniejszych punktów.</p>
        </div>
    </div>

    <hr style='margin: 2rem 0;'>

    <h2 style='text-align: center;'>📌 Jak to działa?</h2>
    <ol style='font-size: 1.1em; line-height: 1.6; color: #dddddd;'>
        <li>📂 Prześlij plik PDF lub wklej treść umowy</li>
        <li>🤖 AI analizuje dokument i szuka ryzyk</li>
        <li>📋 Otrzymujesz podsumowanie oraz ocenę bezpieczeństwa</li>
    </ol>

    <h2 style='text-align: center; margin-top: 3rem;'>💡 Dlaczego warto?</h2>
    <ul style='font-size: 1.1em; line-height: 1.6; color: #dddddd;'>
        <li>🔎 Wykrywasz ukryte zapisy i dodatkowe obowiązki</li>
        <li>⚖️ Zyskujesz świadomość swoich praw</li>
        <li>⏱️ Oszczędzasz czas – analiza zajmuje kilka sekund</li>
    </ul>

    <div style='text-align: center; margin-top: 2.5rem;'>
        <a href='#' style='background-color: #0073e6; color: white; padding: 1rem 2rem; text-decoration: none; border-radius: 8px; font-size: 1.2em;'>Zacznij analizować</a>
    </div>
    """, unsafe_allow_html=True)

elif menu == "🔐 Logowanie / Rejestracja":
    with st.form("login_form"):
        st.write("Zaloguj się lub zarejestruj:")
        username = st.text_input("Nazwa użytkownika")
        password = st.text_input("Hasło", type="password")
        action = st.radio("Wybierz opcję:", ["Zaloguj", "Zarejestruj"])
        submitted = st.form_submit_button("Dalej")
        if submitted:
            st.success(f"✅ {action} jako {username}")

elif menu == "📤 Wgraj PDF":
    uploaded_file = st.file_uploader("Wgraj plik PDF", type="pdf")
    if uploaded_file:
        text = extract_text_from_pdf(uploaded_file)
        st.text_area("📄 Zawartość pliku:", text, height=300)
        st.markdown("### 📌 Podsumowanie analizy:")
        st.info(analyze_text(text))

elif menu == "📋 Wklej tekst":
    user_text = st.text_area("Wklej tekst umowy:", height=300)
    if user_text:
        st.success("✅ Tekst zapisany do analizy")
        st.markdown("### 📌 Podsumowanie analizy:")
        st.info(analyze_text(user_text))

elif menu == "🛡️ Ryzyka":
    show_risks()

elif menu == "📥 Pobierz analizę":
    st.info("🔧 Funkcja eksportu PDF z analizą w przygotowaniu...")
    st.button("📩 Pobierz jako PDF")
