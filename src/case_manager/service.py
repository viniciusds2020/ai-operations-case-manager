import hashlib
import uuid
from datetime import UTC, datetime
from pathlib import Path

from .agent import build_plan, deterministic_summary
from .config import Settings
from .ingestion import extract_text
from .models import Case, Event
from .provider import groq_summary
from .repository import Repository
from .rules import analyze


def now() -> str:
    return datetime.now(UTC).isoformat()


class CaseService:
    def __init__(self, repository: Repository, settings: Settings):
        self.repository = repository
        self.settings = settings

    def create(self, filename: str, content: bytes, requester: str) -> Case:
        text = extract_text(filename, content, self.settings.max_upload_mb * 1024 * 1024)
        analysis = analyze(text)
        plan = build_plan(analysis, self.settings.auto_execute_max_risk)
        case_id = uuid.uuid4().hex[:12]
        upload_dir = self.settings.data_dir / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        (upload_dir / f"{case_id}{Path(filename).suffix.lower()}").write_bytes(content)
        base_summary = deterministic_summary(analysis)
        summary = (
            groq_summary(text, base_summary)
            if self.settings.llm_provider == "groq"
            else base_summary
        )
        timestamp = now()
        needs_review = any(step.requires_approval for step in plan) or bool(analysis.missing)
        case = Case(
            id=case_id,
            title=analysis.fields.get(
                "procedimento", Path(filename).stem.replace("_", " ").title()
            ),
            requester=requester.strip() or "Não informado",
            filename=Path(filename).name,
            sha256=hashlib.sha256(content).hexdigest(),
            case_type=analysis.case_type,
            confidence=analysis.confidence,
            status="pending_review" if needs_review else "ready",
            risk_score=analysis.risk_score,
            risk_reasons=analysis.reasons,
            extracted_fields=analysis.fields,
            missing_fields=analysis.missing,
            plan=plan,
            summary=summary,
            created_at=timestamp,
            updated_at=timestamp,
        )
        self.repository.save_case(case)
        self._event(case.id, "case_created", "system", "Caso recebido, analisado e planejado")
        return case

    def review(self, case: Case, decision: str, actor: str, reason: str) -> Case:
        if case.status != "pending_review":
            raise ValueError("Somente casos pendentes podem ser revisados.")
        case.status = "approved" if decision == "approve" else "rejected"
        case.updated_at = now()
        self.repository.update_case(case)
        self._event(case.id, f"case_{case.status}", actor, reason)
        return case

    def execute(self, case: Case, actor: str) -> Case:
        if case.status == "executed":
            return case
        if case.status not in {"approved", "ready"}:
            raise ValueError("O caso não está autorizado para execução.")
        case.status = "executed"
        case.updated_at = now()
        self.repository.update_case(case)
        self._event(case.id, "plan_executed", actor, "Ferramentas executadas em modo simulado")
        return case

    def _event(self, case_id: str, event_type: str, actor: str, detail: str):
        self.repository.add_event(
            Event(
                case_id=case_id,
                event_type=event_type,
                actor=actor,
                detail=detail,
                created_at=now(),
            )
        )
