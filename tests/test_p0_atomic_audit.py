import sqlite3

import pytest

from case_manager.config import Settings
from case_manager.repository import Repository
from case_manager.service import CaseService

from .test_rules import COMPLETE


def test_case_transition_rolls_back_when_audit_insert_fails(tmp_path):
    repo = Repository(tmp_path / "cases.db")
    service = CaseService(repo, Settings(data_dir=tmp_path, auto_execute_max_risk=0.05))
    case = service.create("case.md", COMPLETE.encode(), "Portal")
    with repo.connect() as db:
        db.execute(
            """CREATE TRIGGER reject_approval BEFORE INSERT ON events
            WHEN NEW.event_type='case_approved'
            BEGIN SELECT RAISE(ABORT, 'audit unavailable'); END;"""
        )
        db.commit()
    with pytest.raises(sqlite3.IntegrityError):
        service.review(case, "approve", "Reviewer", "Verified details")
    persisted = repo.get_case(case.id)
    assert persisted.status == "pending_review"
    assert [e.event_type for e in repo.events(case.id)] == ["case_created"]
