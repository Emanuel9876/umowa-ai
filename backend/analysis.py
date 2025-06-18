import re

def analyze_contract(text: str) -> dict:
    """
    Analiza umowy pod kątem wykrywania ryzyk i podsumowania.
    - Szuka potencjalnych ryzyk (np. klauzule o karach, wypowiedzeniu, zobowiązaniach)
    - Tworzy podsumowanie
    """
    risks_patterns = {
        "kary umowne": r"(kara umowna|kary umowne|odszkodowanie|penalti)",
        "wypowiedzenie": r"(wypowiedzenie|termin wypowiedzenia|rozwiązanie umowy)",
        "zobowiązania": r"(zobowiązanie|obowiązek|odpowiedzialność)",
        "płatności": r"(płatność|termin płatności|opłata)",
    }

    found_risks = []
    for risk_name, pattern in risks_patterns.items():
        if re.search(pattern, text, re.IGNORECASE):
            found_risks.append(risk_name)

    summary = f"Tekst ma {len(text)} znaków. Znaleziono potencjalne ryzyka: {', '.join(found_risks) if found_risks else 'Brak wyraźnych ryzyk.'}"

    return {
        "summary": summary,
        "risks": found_risks,
        "full_text": text
    }
