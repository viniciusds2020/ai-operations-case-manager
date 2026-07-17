import re
from dataclasses import dataclass


@dataclass
class Analysis:
    case_type: str
    confidence: float
    fields: dict[str, str]
    missing: list[str]
    risk_score: float
    reasons: list[str]


PATTERNS = {
    "beneficiario": r"benefici[aá]rio\s*:\s*([^\n]+)",
    "carteira": r"carteira\s*:\s*([A-Z0-9.-]+)",
    "procedimento": r"procedimento\s*:\s*([^\n]+)",
    "codigo": r"c[oó]digo\s*:\s*([A-Z0-9.-]+)",
    "medico": r"m[eé]dico\s*:\s*([^\n]+)",
    "crm": r"crm\s*:\s*([A-Z]{0,2}\s*\d+)",
}
REQUIRED = ["beneficiario", "carteira", "procedimento", "medico", "crm"]


def analyze(text: str) -> Analysis:
    lowered = text.lower()
    health_hits = sum(
        term in lowered for term in ["beneficiário", "procedimento", "crm", "autorização"]
    )
    if health_hits >= 2:
        case_type = "health_authorization"
        confidence = min(0.55 + health_hits * 0.1, 0.95)
    else:
        case_type = "general_request"
        confidence = 0.55
    fields = {}
    for name, pattern in PATTERNS.items():
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            fields[name] = match.group(1).strip()
    missing = [field for field in REQUIRED if field not in fields] if health_hits >= 2 else []
    reasons = []
    risk = 0.1
    if missing:
        risk += min(0.1 * len(missing), 0.4)
        reasons.append(f"Campos obrigatórios ausentes: {', '.join(missing)}")
    if any(term in lowered for term in ["urgente", "emergência", "alto custo"]):
        risk += 0.3
        reasons.append("Caso urgente ou de alto impacto identificado")
    if confidence < 0.7:
        risk += 0.25
        reasons.append("Baixa confiança na classificação")
    risk = round(min(risk, 1.0), 2)
    return Analysis(case_type, confidence, fields, missing, risk, reasons)
