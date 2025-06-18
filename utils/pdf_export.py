from fpdf import FPDF

def export_to_pdf(analysis_result: dict) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=14)
    pdf.cell(0, 10, "Podsumowanie analizy umowy", ln=True, align='C')

    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, analysis_result.get("summary", "Brak podsumowania"))

    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Wykryte ryzyka:", ln=True)

    pdf.set_font("Arial", size=12)
    risks = analysis_result.get("risks", [])
    if risks:
        for risk in risks:
            pdf.cell(0, 8, f"- {risk}", ln=True)
    else:
        pdf.cell(0, 8, "Brak wykrytych ryzyk.", ln=True)

    return pdf.output(dest='S').encode('latin1')
