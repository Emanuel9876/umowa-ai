import streamlit as st
import re

st.set_page_config(page_title="🚨 UmowaAI – Ryzyka", layout="wide")
st.title("🚨 Wykryte ryzyka")

if "uploaded_text" not in st.session_state:
    st.warning("Najpierw wgraj PDF w zakładce 🗓️ Wgraj PDF.")
else:
    text = st.session_state["uploaded_text"]
    
    patterny = {
        "⚠️ Kaucja": r"kaucj[ae]\s+.*?\d+[\s\w]*z[\u0142l]",
        "⏳ Wypowiedzenie": r"wypowiedze?nie.*?(umowy|kontraktu)?",
        "🚫 Kara umowna": r"kara\s+umowna.*?\d+[\s\w]*z[\u0142l]",
        "💸 Brak wynagrodzenia": r"(nie przysługuje|brak)\s+wynagrodzenia",
        "📈 Podwyżki bez zgody": r"(automatyczn[aey]|jednostronn[aey])\s+(zmian[aey]|podwyżk)"
    }

    found = []
    for label, pattern in patterny.items():
        matches = list(re.finditer(pattern, text, re.IGNORECASE))
        for m in matches:
            found.append((label, m.group()))

    if found:
        for label, fragment in found:
            st.markdown(f"**{label}**: {fragment}")
    else:
        st.success("✅ Nie znaleziono ryzyk.")
