import streamlit as st
import fitz  # PyMuPDF

st.set_page_config(page_title="📤 UmowaAI – Wgraj PDF", layout="wide")
st.title("🗓️ Wgraj umowę PDF")

uploaded_file = st.file_uploader("Wgraj plik PDF", type="pdf")

if uploaded_file:
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    full_text = ""
    for page in doc:
        full_text += page.get_text()

    st.session_state["uploaded_text"] = full_text
    st.success("✅ Plik załadowany i tekst zapisany do sesji.")
else:
    st.info("✍️ Wgraj plik PDF, aby przejść dalej.")
