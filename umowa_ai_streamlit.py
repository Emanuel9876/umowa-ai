import streamlit as st
from PyPDF2 import PdfReader

# Przykładowe tłumaczenia (wyciąg, dodaj więcej jeśli potrzebujesz)
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

# Inicjalizacja języka (domyślnie PL)
if "language" not in st.session_state:
    st.session_state.language = "PL"

# Pasek boczny wyboru języka (możesz rozszerzyć)
lang = st.sidebar.selectbox(
    "Wybierz język / Select Language / Sprache wählen",
    options=["PL", "EN", "DE"],
    index=["PL", "EN", "DE"].index(st.session_state.language),
)
st.session_state.language = lang

# Menu wyboru głównych stron
menu = [
    translations["Strona Główna"][st.session_state.language],
    translations["Analiza Umowy"][st.session_state.language],
    translations["Ryzyka"][st.session_state.language],
    translations["Moje Analizy"][st.session_state.language]
]

choice = st.sidebar.radio("Menu", menu)

# --- STRONA GŁÓWNA ---
if choice == translations["Strona Główna"][st.session_state.language]:
    st.markdown(f"""
    <div style='text-align: center; padding: 5vh 2vw;'>
        <h1 style='font-size: 4.5em; margin-bottom: 0;'>🤖 UmowaAI</h1>
        <p style='font-size: 1.7em; margin-top: 0;'>{translations['Twój osobisty asystent do analizy umów i wykrywania ryzyk'][st.session_state.language]}</p>
    </div>

    <div class='top-card' style='display: flex; flex-direction: row; justify-content: space-around; flex-wrap: wrap; gap: 2rem; padding: 2rem;'>
        <div style='flex: 1; min-width: 250px; max-width: 400px;'>
            <h2>📄 {translations['Analiza Umowy'][st.session_state.language]}</h2>
            <p>Automatyczna analiza dokumentów PDF i tekstów umów.</p>
        </div>
        <div style='flex: 1; min-width: 250px; max-width: 400px;'>
            <h2>⚠️ {translations['Ryzyka'][st.session_state.language]}</h2>
            <p>Wykrywanie potencjalnych ryzyk i niekorzystnych zapisów w umowach.</p>
        </div>
        <div style='flex: 1; min-width: 250px; max-width: 400px;'>
            <h2>📊 {translations['Moje Analizy'][st.session_state.language]}</h2>
            <p>Przeglądanie historii wszystkich wykonanych analiz.</p>
        </div>
    </div>

    <div class='top-card' style='text-align: center; padding: 3rem; margin-top: 3rem;'>
        <h2>🚀 {translations['Dlaczego UmowaAI?'][st.session_state.language]}</h2>
        <ul style='list-style: none; font-size: 1.2em; padding: 0;'>
            <li>✅ Intuicyjny i nowoczesny interfejs</li>
            <li>✅ Wysoka skuteczność wykrywania niekorzystnych zapisów</li>
            <li>✅ Bezpieczeństwo i poufność danych</li>
            <li>✅ Historia wszystkich Twoich analiz</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# --- ANALIZA UMOWY ---
elif choice == translations["Analiza Umowy"][st.session_state.language]:
    st.header(translations["Analiza Umowy"][st.session_state.language])

    contract_text = st.text_area(
        translations["Wprowadź lub załaduj tekst umowy."][st.session_state.language],
        height=200
    )

    uploaded_file = st.file_uploader(
        translations["Prześlij plik PDF"][st.session_state.language],
        type=["pdf"]
    )

    if uploaded_file:
        try:
            pdf = PdfReader(uploaded_file)
            contract_text = ""
            for page in pdf.pages:
                contract_text += page.extract_text() or ""
        except Exception as e:
            st.error(f"Błąd podczas odczytu pliku PDF: {e}")

    if contract_text.strip() != "":
        # Funkcja symulująca analizę i wykrywanie ryzyk z czułością
        def analyze_contract(text):
            # Tutaj podmień na rzeczywistą analizę
            return {
                "Niejasne klauzule": 0.9,
                "Ryzyko kar umownych": 0.75,
                "Nadmierna odpowiedzialność": 0.6
            }

        risks = analyze_contract(contract_text)

        st.subheader(translations["Ryzyka"][st.session_state.language])
        for risk_name, sensitivity in risks.items():
            st.write(f"- {risk_name}: {sensitivity*100:.0f}%")

# --- RYZYKA ---
elif choice == translations["Ryzyka"][st.session_state.language]:
    st.header(translations["Ryzyka"][st.session_state.language])
    st.write("Tu możesz wyświetlić dodatkowe informacje o ryzykach.")

# --- MOJE ANALIZY ---
elif choice == translations["Moje Analizy"][st.session_state.language]:
    st.header(translations["Moje Analizy"][st.session_state.language])
    st.write("Tu możesz wyświetlić zapisane analizy.")

