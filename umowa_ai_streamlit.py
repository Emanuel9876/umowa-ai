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

# === FUNKCJA: RYZYKA (stałe opisy) ===
def show_risks():
    st.subheader("🛡️ Możliwe Ryzyka w Umowie")
    st.markdown("""
**Utrudnione odstąpienie od umowy:**\
Umowy często zawierają zapisy, które utrudniają lub uniemożliwiają odstąpienie od umowy, nawet jeśli jej warunki okazują się niekorzystne.

**Dodatkowe obowiązki:**\
Możesz być zobowiązany do spełnienia dodatkowych czynności lub płatności, o których nie miałeś pojęcia.

**Dodatkowe opłaty:**\
Nieuważne czytanie umowy może prowadzić do konieczności zapłaty dodatkowych opłat, które nie były wliczone w pierwotne koszty.

**Nieważność umowy:**\
Niektóre umowy mogą być uznane za nieważne, jeśli zawierają niezgodne z prawem lub zasadami współżycia społecznego postanowienia.

**Konsekwencje finansowe:**\
Jeśli w umowie znajdują się niekorzystne zapisy dotyczące płatności, odsetek lub kar umownych, możesz ponieść znaczne straty finansowe.

**Skutki prawne:**\
Nieważność umowy może prowadzić do konieczności zwrotu świadczeń lub dochodzenia odszkodowania, jeśli jedna ze stron poniosła szkody w wyniku jej zawarcia.

**Niewywiązanie się z umowy:**\
Jeśli nie rozumiesz swoich obowiązków wynikających z umowy, możesz nieświadomie ich nie wykonać, co może skutkować karami umownymi lub innymi konsekwencjami prawnymi.
""")

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

elif menu == "📋 Wklej tekst":
    user_text = st.text_area("Wklej tekst umowy:", height=300)
    if user_text:
        st.success("✅ Tekst zapisany do analizy")

elif menu == "🛡️ Ryzyka":
    show_risks()

elif menu == "📥 Pobierz analizę":
    st.info("🔧 Funkcja eksportu PDF z analizą w przygotowaniu...")
    st.button("📩 Pobierz jako PDF")
