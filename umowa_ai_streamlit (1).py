import streamlit as st
import fitz  # PyMuPDF
import re

st.set_page_config(page_title="UmowaAI - Wykrywanie ryzyk w umowach", layout="centered")
st.title("📄 UmowaAI – wykrywanie ryzyk prawnych w umowach")
st.write("Wgraj plik PDF z umową najmu, a AI wykryje potencjalne ryzyka (np. kaucje, kary, wypowiedzenia)")

# === Funkcje pomocnicze ===
def extract_text_from_pdf(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def find_risks(text):
    patterns = {
        "Kaucja": r"kaucj[ae]\s+.*?\d+[\s\w]*z[łl]",
        "Kara umowna": r"kara\s+umowna.*?\d+[\s\w]*z[łl]",
        "Wypowiedzenie": r"wypowiedze?nie.*?(umowy|kontraktu)?",
        "Zakaz podnajmu": r"(zakaz|brak zgody).*?podnajm",
        "Odpowiedzialność": r"odpowiedzialn[oó]\w+.*?(najemc[aę]|wynajmuj[aą]cego)"
    }
    results = []
    for label, pattern in patterns.items():
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            results.append((label, match.group()))
    return results

def highlight_risks(text, risks):
    for label, fragment in risks:
        highlighted = f"**[{label.upper()}]** {fragment}"
        text = text.replace(fragment, highlighted)
    return text

# === Interfejs ===
uploaded_file = st.file_uploader("Wgraj plik PDF z umową", type="pdf")

if uploaded_file:
    with st.spinner("Analizuję dokument..."):
        text = extract_text_from_pdf(uploaded_file)
        risks = find_risks(text)
        highlighted_text = highlight_risks(text, risks)

    st.subheader("📌 Wykryte ryzyka:")
    if risks:
        for label, fragment in risks:
            st.markdown(f"- **{label}**: _{fragment}_")
    else:
        st.success("Nie wykryto istotnych ryzyk.")

    st.subheader("📄 Podgląd umowy z zaznaczeniami:")
    st.markdown(highlighted_text)

    with st.expander("📥 Zapisz wynik jako TXT"):
        st.download_button("Pobierz analizę", data=highlighted_text, file_name="analiza_umowy.txt")
