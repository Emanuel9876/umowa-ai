import streamlit as st
import fitz  # PyMuPDF
import re

# === KONFIGURACJA STRONY ===
st.set_page_config(page_title="UmowaAI – Analiza PDF", layout="wide")

# === NAGŁÓWEK ===
st.title("📄 UmowaAI – Wykrywanie Ryzyk i Analiza PDF")
st.markdown("""
<style>
    .block-container {
        padding-top: 2rem;
    }
    .css-18e3th9 {
        background-color: #f0f4fa;
        border-radius: 12px;
        padding: 2rem;
    }
    .risk-section strong {
        font-size: 1.3em;
        display: block;
        margin-top: 1rem;
    }
    .risk-section p {
        font-size: 1.1em;
    }
</style>
""", unsafe_allow_html=True)

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
        summary += "\n- Możliwe ograniczenia w odstąpieniu od umowy."
    if re.search(r'obowiąz(e|ą)zki|zobowiązany', text, re.IGNORECASE):
        summary += "\n- Dodatkowe obowiązki użytkownika."
    if re.search(r'opłata|koszt|zapłaty', text, re.IGNORECASE):
        summary += "\n- Potencjalne dodatkowe opłaty."
    if re.search(r'nieważn|unieważn', text, re.IGNORECASE):
        summary += "\n- Możliwe zapisy prowadzące do nieważności umowy."
    if re.search(r'kara|odsetki|strata|szkoda', text, re.IGNORECASE):
        summary += "\n- Ryzyko konsekwencji finansowych."
    if re.search(r'prawne|pozew|sąd', text, re.IGNORECASE):
        summary += "\n- Możliwe skutki prawne."
    if re.search(r'niewywiązuje|niewykona|zaniedbanie', text, re.IGNORECASE):
        summary += "\n- Ryzyko niewywiązania się z umowy."
    return summary.strip()

# === FUNKCJA: RYZYKA (stałe opisy) ===
def show_risks():
    st.subheader("🛡️ Możliwe Ryzyka w Umowie")
    st.markdown("""
<div class="risk-section">
<strong>Utrudnione odstąpienie od umowy:</strong>
<p>Umowy często zawierają zapisy, które utrudniają lub uniemożliwiają odstąpienie od umowy, nawet jeśli jej warunki okazują się niekorzystne.</p>

<strong>Dodatkowe obowiązki:</strong>
<p>Możesz być zobowiązany do spełnienia dodatkowych czynności lub płatności, o których nie miałeś pojęcia.</p>

<strong>Dodatkowe opłaty:</strong>
<p>Nieuważne czytanie umowy może prowadzić do konieczności zapłaty dodatkowych opłat, które nie były wliczone w pierwotne koszty.</p>

<strong>Nieważność umowy:</strong>
<p>Niektóre umowy mogą być uznane za nieważne, jeśli zawierają niezgodne z prawem lub zasadami współżycia społecznego postanowienia.</p>

<strong>Konsekwencje finansowe:</strong>
<p>Jeśli w umowie znajdują się niekorzystne zapisy dotyczące płatności, odsetek lub kar umownych, możesz ponieść znaczne straty finansowe.</p>

<strong>Skutki prawne:</strong>
<p>Nieważność umowy może prowadzić do konieczności zwrotu świadczeń lub dochodzenia odszkodowania, jeśli jedna ze stron poniosła szkody w wyniku jej zawarcia.</p>

<strong>Niewywiązanie się z umowy:</strong>
<p>Jeśli nie rozumiesz swoich obowiązków wynikających z umowy, możesz nieświadomie ich nie wykonać, co może skutkować karami umownymi lub innymi konsekwencjami prawnymi.</p>
</div>
""", unsafe_allow_html=True)

# === STRONY ===
if menu == "Strona główna":
    st.markdown("""
### 👋 Witaj w UmowaAI
Twoje narzędzie do analizy PDF i wykrywania ryzyk w umowach.
Zacznij od przesłania pliku lub wklejenia treści.
    """)

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
