from .models import PlanStep
from .rules import Analysis


def build_plan(analysis: Analysis, approval_threshold: float) -> list[PlanStep]:
    approval = analysis.risk_score > approval_threshold or bool(analysis.missing)
    steps = [
        PlanStep(tool="validate_case", description="Validar campos e regras do domínio"),
        PlanStep(tool="check_eligibility", description="Consultar elegibilidade em modo simulado"),
    ]
    if analysis.missing:
        steps.append(
            PlanStep(
                tool="request_information",
                description="Solicitar os campos obrigatórios ausentes",
                requires_approval=False,
            )
        )
    else:
        steps.append(
            PlanStep(
                tool="register_decision",
                description="Registrar encaminhamento operacional",
                requires_approval=approval,
            )
        )
    return steps


def deterministic_summary(analysis: Analysis) -> str:
    label = (
        "autorização em saúde"
        if analysis.case_type == "health_authorization"
        else "solicitação geral"
    )
    quality = "com dados mínimos presentes" if not analysis.missing else "com informações pendentes"
    return f"Caso classificado como {label}, {quality}, risco {analysis.risk_score:.0%}."
