import streamlit as st

st.set_page_config(page_title="💾 UmowaAI – Pobierz analizę", layout="wide")
st.title("💾 Pobierz analizę")

if "uploaded_text" not in st.session_state:
    st.warning("Najpierw wgraj PDF w zakładce 🗓️ Wgraj PDF.")
else:
    text = st.session_state["uploaded_text"]
    st.download_button("📥 Pobierz treść umowy jako TXT", data=text, file_name="umowa.txt")
