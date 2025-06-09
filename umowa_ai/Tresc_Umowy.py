import streamlit as st
import re

st.set_page_config(page_title="📄 UmowaAI – Treść umowy", layout="wide")
st.title("📄 Treść umowy z podświetleniem")

if "uploaded_text" not in st.session_state:
    st.warning("Najpierw wgraj PDF w zakładce 🗓️ Wgraj PDF.")
else:
    text = st.session_state["uploaded_text"]

    highlights = {
        "⚠️ Kaucja": r"kaucj[ae]\s+.*?\d+[\s\w]*z[\u0142l]",
        "🚫 Kara umowna": r"kara\s+umowna.*?\d+[\s\w]*z[\u0142l]",
    }

    def highlight(text, highlights):
        for label, pattern in highlights.items():
            text = re.sub(pattern, lambda m: f"<mark><b>{label}</b>: {m.group()}</mark>", text, flags=re.IGNORECASE)
        return text

    st.markdown(highlight(text, highlights), unsafe_allow_html=True)
