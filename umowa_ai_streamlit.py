# Analiza Umowy
if plain_choice == "Analiza Umowy":
    st.subheader("📄 Prześlij plik PDF do analizy")
    uploaded_file = st.file_uploader("Wybierz plik PDF", type="pdf")

    if uploaded_file and st.button("🔍 Analizuj dokument"):
        reader = PdfReader(uploaded_file)
        full_text = ""
        for page in reader.pages:
            if page.extract_text():
                full_text += page.extract_text()

        # Prosta analiza: liczba wystąpień słowa „ryzyko”
        score = full_text.lower().count("ryzyko")
        summary = "⚠️ Wykryto potencjalne ryzyka" if score > 0 else "✅ Nie wykryto ryzykownych zapisów"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("INSERT INTO analiza (user, tekst, podsumowanie, score, timestamp) VALUES (?, ?, ?, ?, ?)",
                       (session_state.username, full_text, summary, score, timestamp))
        conn.commit()

        st.success("Analiza zakończona!")
        st.markdown(f"**📌 Podsumowanie:** {summary}")
        st.markdown(f"**📈 Wystąpienia słowa 'ryzyko':** {score}")

# Ryzyka
elif plain_choice == "Ryzyka":
    st.subheader("⚠️ Szczegóły wykrytych ryzyk")
    cursor.execute("SELECT tekst FROM analiza WHERE user = ? ORDER BY id DESC LIMIT 1", (session_state.username,))
    result = cursor.fetchone()
    if result:
        text = result[0]
        ryzykowne_zapisy = re.findall(r"(.*?ryzyko.*?[\.!])", text, flags=re.IGNORECASE)
        if ryzykowne_zapisy:
            st.warning("Zidentyfikowano następujące fragmenty zawierające ryzyka:")
            for fragment in ryzykowne_zapisy:
                st.markdown(f"- {fragment}")
        else:
            st.success("Nie znaleziono fragmentów zawierających słowo 'ryzyko'.")
    else:
        st.info("Brak wyników — najpierw przeprowadź analizę dokumentu.")

# Moje Analizy
elif plain_choice == "Moje Analizy":
    st.subheader("📊 Historia Twoich analiz")
    cursor.execute("SELECT timestamp, podsumowanie, score FROM analiza WHERE user = ? ORDER BY id DESC", (session_state.username,))
    rows = cursor.fetchall()

    if rows:
        timestamps, summaries, scores = zip(*rows)
        st.dataframe({
            "Data": timestamps,
            "Podsumowanie": summaries,
            "Ryzykowność": scores
        })

        # Wykres trendu
        fig, ax = plt.subplots(figsize=(10, 4))
        sns.lineplot(x=list(timestamps), y=list(scores), marker="o", ax=ax)
        ax.set_title("Trend wykrytych ryzyk")
        ax.set_xlabel("Data analizy")
        ax.set_ylabel("Liczba ryzykownych zapisów")
        plt.xticks(rotation=45)
        st.pyplot(fig)
    else:
        st.info("Nie przeprowadzono jeszcze żadnych analiz.")
