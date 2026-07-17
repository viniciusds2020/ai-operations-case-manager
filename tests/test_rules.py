from case_manager.agent import build_plan
from case_manager.rules import analyze

COMPLETE = """Autorização
Beneficiário: Maria Exemplo
Carteira: DEMO-001
Procedimento: Exame sintético
Médico: Dr. Teste
CRM: RS 12345
"""


def test_extracts_health_case_fields():
    result = analyze(COMPLETE)
    assert result.case_type == "health_authorization"
    assert result.fields["carteira"] == "DEMO-001"
    assert not result.missing


def test_missing_fields_raise_risk_and_add_information_step():
    result = analyze("Autorização para beneficiário: Maria. Procedimento: Exame urgente")
    plan = build_plan(result, 0.25)
    assert result.missing
    assert result.risk_score > 0.25
    assert any(step.tool == "request_information" for step in plan)


def test_general_request_has_low_confidence_reason():
    result = analyze("Preciso atualizar meu endereço cadastral.")
    assert result.case_type == "general_request"
    assert "Baixa confiança na classificação" in result.reasons
