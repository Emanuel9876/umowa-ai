import streamlit as st
from PyPDF2 import PdfReader

# --- Tłumaczenia ---
translations = {
    "Strona Główna": {"PL": "Strona Główna", "EN": "Home", "DE": "Startseite"},
    "Analiza Umowy": {"PL": "Analiza Umowy", "EN": "Contract Analysis", "DE": "Vertragsanalyse"},
    "Ryzyka": {"PL": "Ryzyka", "EN": "Risks", "DE": "Risiken"},
    "Moje Analizy": {"PL": "Moje Analizy", "EN": "My Analyses", "DE": "Meine Analysen"},
    "Wprowadź lub załaduj tekst umowy.": {
        "PL": "Wprowadź lub załaduj tekst umowy.",
        "EN": "Enter or upload contract text.",
        "DE": "Vertragstext eingeben oder hochladen."
    },
    "Prześlij plik PDF": {"PL": "Prześlij plik PDF", "EN": "Upload PDF file", "DE": "PDF-Datei hochladen"},
    "Twój osobisty asystent do analizy umów i wykrywania ryzyk": {
        "PL": "Twój osobisty asystent do analizy umów i wykrywania ryzyk",
        "EN": "Your personal assistant for contract analysis and risk detection",
        "DE": "Ihr persönlicher Assistent zur Vertragsanalyse und Risikobewertung"
    },
    "Ryzyka": {"PL": "Ryzyka", "EN": "Risks", "DE": "Risiken"},
    "Dlaczego UmowaAI?": {"PL": "Dlaczego UmowaAI?", "EN": "Why UmowaAI?", "DE": "Warum UmowaAI?"},
    "Analiza zapisana.": {"PL": "Analiza zapisana.", "EN": "Analysis saved.", "DE": "Analyse gespeichert."}
}

# --- Inicjalizacja języka ---
if "language" not in st.session_state:
    st.session_state.language = "PL"

lang = st.sidebar.selectbox(
    "Wybierz język / Select Language / Sprache wählen",
    options=["PL", "EN", "DE"],
    index=["PL", "EN", "DE"].index(st.session_state.language),
)
st.session_state.language = lang

# --- Menu główne ---
menu = [
    translations["Strona Główna"][lang],
    translations["Analiza Umowy"][lang],
    translations["Ryzyka"][lang],
    translations["Moje Analizy"][lang]
]

choice = st.sidebar.radio("Menu", menu)

# --- STRONA GŁÓWNA ---
if choice == translations["Strona Główna"][lang]:
    st.markdown("""
    <div style="text-align:center; margin: 4vh 0 4vh 0;">
        <h1 style="font-size: 5em;">🤖 UmowaAI</h1>
        <p style="font-size: 1.7em;">""" + translations["Twój osobisty asystent do analizy umów i wykrywania ryzyk"][lang] + """</p>
    </div>

    <div style="display: flex; justify-content: space-around; flex-wrap: wrap; gap: 2rem; padding: 2rem;">
        <div style="flex:1; min-width: 250px; max-width: 350px; border-radius: 20px; background-color: #f5f5f5; padding: 1rem; box-shadow: 0 0 5px #aaa;">
            <h2>📄 """ + translations["Analiza Umowy"][lang] + """</h2>
            <p>Automatyczna analiza dokumentów PDF i tekstów umów.</p>
        </div>
        <div style="flex:1; min-width: 250px; max-width: 350px; border-radius: 20px; background-color: #f5f5f5; padding: 1rem; box-shadow: 0 0 5px #aaa;">
            <h2>⚠️ """ + translations["Ryzyka"][lang] + """</h2>
            <p>Wykrywanie potencjalnych ryzyk i niekorzystnych zapisów w umowach.</p>
        </div>
        <div style="flex:1; min-width: 250px; max-width: 350px; border-radius: 20px; background-color: #f5f5f5; padding: 1rem; box-shadow: 0 0 5px #aaa;">
            <h2>📋 """ + translations["Moje Analizy"][lang] + """</h2>
            <p>Przeglądanie historii wszystkich wykonanych analiz.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- ANALIZA UMOWY ---
elif choice == translations["Analiza Umowy"][lang]:
    st.header(translations["Analiza Umowy"][lang])

    contract_text = st.text_area(
        translations["Wprowadź lub załaduj tekst umowy."][lang],
        height=200
    )

    uploaded_file = st.file_uploader(
        translations["Prześlij plik PDF"][lang],
        type=["pdf"]
    )

    # Jeśli użytkownik załadował plik PDF, wczytaj tekst
    if uploaded_file:
        try:
            pdf = PdfReader(uploaded_file)
            contract_text = ""
            for page in pdf.pages:
                contract_text += page.extract_text() or ""
        except Exception as e:
            st.error(f"Błąd podczas odczytu pliku PDF: {e}")

    if contract_text.strip() != "":
        # Funkcja analizująca tekst - przykładowa, zamień na własną logikę
        def analyze_contract(text):
            # Przykładowe ryzyka z "czułością"
            return {
                "Niejasne klauzule": 0.89,
                "Ryzyko kar umownych": 0.75,
                "Nadmierna odpowiedzialność": 0.62
            }

        risks = analyze_contract(contract_text)

        st.subheader(translations["Ryzyka"][lang])
        for risk, sensitivity in risks.items():
            st.markdown(f"- **{risk}**: {sensitivity*100:.0f}%")

# --- RYZYKA ---
elif choice == translations["Ryzyka"][lang]:
    st.header(translations["Ryzyka"][lang])
    st.write("Tutaj możesz dodać więcej informacji o ryzykach.")

# --- MOJE ANALIZY ---
elif choice == translations["Moje Analizy"][lang]:
    st.header(translations["Moje Analizy"][lang])
    st.write("Tutaj możesz wyświetlić zapisane analizy.")

