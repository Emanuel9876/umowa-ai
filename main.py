import streamlit as st
import fitz  # PyMuPDF
import re

# === KONFIGURACJA STRONY ===
st.set_page_config(page_title="UmowaAI – Legal Risk Detector", layout="wide")

# === INTERFEJS MULTI-JĘZYKOWY ===
lang = st.sidebar.radio("🌐 Wybierz język / Select language:", ["Polski", "English"])
is_pl = lang == "Polski"

# === MENU NAWIGACYJNE ===
page = st.sidebar.radio("📚 Nawigacja:", [
    "🏠 Strona główna",
    "🗓️ Wgraj PDF",
    "🚨 Ryzyka",
    "📄 Wklej treść umowy",
    "💾 Pobierz"
])
if page == "🏠 Strona główna":
    st.title("🏠 Strona główna")
    st.markdown("Witaj w UmowaAI!")

elif page == "🗓️ Wgraj PDF":
    st.title("🗓️ Wgraj PDF")
    uploaded_file = st.file_uploader("📄 Wgraj umowę (PDF)", type="pdf")
    if uploaded_file:
        text = extract_text_from_pdf(uploaded_file)
        st.success("✅ Umowa została wczytana.")
        st.text_area("📜 Tekst umowy:", text, height=300)

elif page == "🚨 Ryzyka":
    st.title("🚨 Analiza ryzyk")
    st.markdown("Tu będą wykryte ryzyka, np. kara umowna, wypowiedzenie itd.")
    # Możesz tu wykorzystać funkcję find_risks(text, typ_umowy, selected_types)

elif page == "📄 Wklej treść umowy":
    st.title("📄 Wklej treść umowy")
    pasted_text = st.text_area("Wklej tekst do analizy:", height=300)
    if pasted_text:
        risks = find_risks(pasted_text, typ_umowy, selected_types)
        highlighted = highlight_risks(pasted_text, risks)
        st.markdown(highlighted, unsafe_allow_html=True)

elif page == "💾 Pobierz":
    st.title("💾 Pobierz analizę")
    st.markdown("Tutaj możesz pobrać analizę w formacie TXT.")
    if uploaded_file:
        st.download_button("📩 Pobierz analizę", data=text, file_name="analiza.txt")

# === OPCJE: TYP UMOWY I ANALIZY ===
typ_umowy = st.sidebar.selectbox("📄 Typ umowy", ["Najmu", "O pracę", "Zlecenie", "Dzieło", "Sprzedaży"])
selected_types = []
if st.sidebar.checkbox("📌 Ryzyka prawne", value=True):
    selected_types.append("Prawne")
if st.sidebar.checkbox("💰 Ryzyka finansowe", value=True):
    selected_types.append("Finansowe")
if not selected_types:
    st.sidebar.warning("⚠️ Wybierz przynajmniej jeden typ ryzyka.")

# === FUNKCJE ===
def extract_text_from_pdf(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def find_risks(text, typ_umowy, typ_analizy):
    wspolne = {
        "⚠️ Kaucja": r"kaucj[ae]\s+.*?\d+[\s\w]*zł",
        "⏳ Wypowiedzenie": r"wypowiedze?nie.*?(umowy|kontraktu)?",
        "🚫 Kara umowna": r"kara\s+umowna.*?\d+[\s\w]*zł",
    }
    finansowe = {
        "💸 Brak wynagrodzenia": r"(nie przysługuje|brak)\s+wynagrodzenia",
        "📈 Podwyżki bez zgody": r"(automatyczn[aey]|jednostronn[aey])\s+(zmian[aey]|podwyżk)"
    }
    spec = {
        "Najmu": {"🔐 Zakaz podnajmu": r"(zakaz|brak zgody).*?podnajm"},
        "O pracę": {"💼 Nadgodziny niepłatne": r"nadgodzin(y|ach|om).*?nieodpłatn"},
        "Zlecenie": {"🗖️ Terminy realizacji": r"termin.*?realizacj"},
        "Dzieło": {"🛠️ Odpowiedzialność za wady": r"odpowiedzialno\w+.*?wady.*?dzieło"},
        "Sprzedaży": {"🔍 Reklamacje": r"(reklamacj|odpowiedzialno\w+).*?towar"}
    }

    patterns = wspolne.copy()
    if "Finansowe" in typ_analizy:
        patterns.update(finansowe)
    if typ_umowy in spec:
        patterns.update(spec[typ_umowy])

    results = []
    for label, pattern in patterns.items():
        for match in re.finditer(pattern, text, re.IGNORECASE):
            results.append((label, match.group()))
    return results

def highlight_risks(text, risks):
    for label, frag in risks:
        frag_clean = re.escape(frag)
        highlighted = f"<mark style='background-color:#ff4b2b33;padding:2px 4px;border-radius:4px'><b>{label}</b>: {frag}</mark>"
        text = re.sub(frag_clean, highlighted, text, flags=re.IGNORECASE)
    return text

# === STRONY APLIKACJI ===

# 🏠 STRONA GŁÓWNA
if page == "🏠 Strona główna":
    st.title("🤖 UmowaAI – " + ("Ekspert od ryzyk prawnych" if is_pl else "AI Legal Risk Analyzer"))
    st.image("https://files.oaiusercontent.com/file-VDXu1R184nwGQa6ocn3h4F", use_container_width=True)
    st.markdown("#### " + (
        "Prześlij umowę PDF i AI znajdzie ryzykowne zapisy prawne, finansowe lub inne – automatycznie i zrozumiale."
        if is_pl else
        "Upload a contract PDF and AI will detect legal, financial, or other risk clauses – clearly and automatically."
    ))
    st.markdown("---")
    st.info("📂 Użyj menu po lewej stronie, aby przejść do wgrywania pliku lub analizy.")

# 🗓️ WGRAJ PDF
elif page == "🗓️ Wgraj PDF":
    st.header("📂 Wgraj PDF umowy")
    uploaded_file = st.file_uploader("📄 Prześlij plik PDF", type="pdf")
    if uploaded_file and selected_types:
        with st.spinner("🔍 Analiza..."):
            text = extract_text_from_pdf(uploaded_file)
            risks = find_risks(text, typ_umowy, selected_types)
            highlighted = highlight_risks(text, risks)

        st.subheader("🚨 Wykryte ryzyka:")
        if risks:
            for label, frag in risks:
                st.markdown(f"<b>{label}</b><br>{frag}", unsafe_allow_html=True)
        else:
            st.success("✅ Brak oczywistych ryzyk.")
        
        st.subheader("📄 Treść z oznaczeniami:")
        st.markdown(highlighted[:3000], unsafe_allow_html=True)
        if len(highlighted) > 3000:
            with st.expander("🔽 Pokaż całość"):
                st.markdown(highlighted, unsafe_allow_html=True)
        
        st.session_state["highlighted"] = highlighted

# 🚨 RYZYKA
elif page == "🚨 Ryzyka":
    st.header("🛡️ Lista wykrywanych ryzyk")
    st.write("Przykładowe reguły wykrywania:")
    st.code(r"kaucj[ae]\s+.*?\d+[\s\w]*zł", language="regex")
    st.code(r"kara\s+umowna.*?\d+[\s\w]*zł", language="regex")
    st.info("W przyszłości możesz tu dodawać własne reguły!")

# 📄 TREŚĆ WKLEJONA
elif page == "📄 Wklej treść umowy":
    st.header("✍️ Wklej treść umowy")
    manual_text = st.text_area("Wklej tutaj umowę", height=300)
    if manual_text and selected_types:
        with st.spinner("🔍 Analiza..."):
            risks = find_risks(manual_text, typ_umowy, selected_types)
            highlighted = highlight_risks(manual_text, risks)

        st.subheader("🚨 Wykryte ryzyka:")
        if risks:
            for label, frag in risks:
                st.markdown(f"<b>{label}</b><br>{frag}", unsafe_allow_html=True)
        else:
            st.success("✅ Brak oczywistych ryzyk.")

        st.subheader("📄 Tekst z oznaczeniami:")
        st.markdown(highlighted[:3000], unsafe_allow_html=True)
        st.session_state["highlighted"] = highlighted

# 💾 POBIERZ
elif page == "💾 Pobierz":
    st.header("💾 Pobierz analizę")
    if "highlighted" in st.session_state:
        st.download_button(
            "📩 Pobierz analizę jako TXT",
            data=st.session_state["highlighted"],
            file_name="analiza_umowy.txt"
        )
    else:
        st.warning("⚠️ Najpierw wykonaj analizę pliku PDF lub wklejonego tekstu.")
