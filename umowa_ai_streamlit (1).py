import datetime

# === Historia analiz ===
history_file = "analizy.json"

if not os.path.exists(history_file):
    with open(history_file, "w") as f:
        json.dump({}, f)

def load_analysis_history():
    with open(history_file, "r") as f:
        return json.load(f)

def save_analysis_history(history):
    with open(history_file, "w") as f:
        json.dump(history, f, indent=4)

def add_analysis_entry(username, filename, typ_umowy, analiza, risks):
    history = load_analysis_history()
    if username not in history:
        history[username] = []
    entry = {
        "plik": filename,
        "typ_umowy": typ_umowy,
        "typ_analizy": analiza,
        "ryzyka": len(risks),
        "data": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    history[username].append(entry)
    save_analysis_history(history)

# Zapisz analizę do historii
add_analysis_entry(
    username=st.session_state.username,
    filename=uploaded_file.name,
    typ_umowy=typ_umowy,
    analiza=analiza,
    risks=risks
)

# Wyświetl historię analiz
st.subheader("📚 Historia analiz")
history = load_analysis_history()
user_history = history.get(st.session_state.username, [])

if user_history:
    for h in reversed(user_history[-5:]):  # ostatnie 5 analiz
        st.markdown(f"🗂️ **{h['plik']}** ({h['typ_umowy']}, {h['typ_analizy']}) – {h['ryzyka']} ryzyk – _{h['data']}_")
else:
    st.write("Brak zapisanych analiz.")
