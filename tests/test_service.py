import pytest

from case_manager.config import Settings
from case_manager.repository import Repository
from case_manager.service import CaseService

from .test_rules import COMPLETE


@pytest.fixture
def service(tmp_path):
    config = Settings(data_dir=tmp_path, auto_execute_max_risk=0.05)
    return CaseService(Repository(tmp_path / "cases.db"), config)


def test_review_execute_and_audit(service):
    case = service.create("case.md", COMPLETE.encode(), "Portal")
    assert case.status == "pending_review"
    approved = service.review(case, "approve", "Analista", "Documentação validada")
    executed = service.execute(approved, "Operador")
    assert executed.status == "executed"
    assert [event.event_type for event in service.repository.events(case.id)] == [
        "case_created",
        "case_approved",
        "plan_executed",
    ]


def test_execution_is_idempotent(service):
    case = service.create("case.md", COMPLETE.encode(), "Portal")
    service.review(case, "approve", "Analista", "Documentação validada")
    first = service.execute(case, "Operador")
    assert service.execute(first, "Operador").status == "executed"


def test_rejected_case_cannot_execute(service):
    case = service.create("case.md", COMPLETE.encode(), "Portal")
    service.review(case, "reject", "Analista", "Necessária correção documental")
    with pytest.raises(ValueError, match="não está autorizado"):
        service.execute(case, "Operador")
