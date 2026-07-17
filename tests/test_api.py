from fastapi.testclient import TestClient

from case_manager import api
from case_manager.config import Settings
from case_manager.repository import Repository
from case_manager.service import CaseService

from .test_rules import COMPLETE


def test_api_workflow(tmp_path, monkeypatch):
    repository = Repository(tmp_path / "api.db")
    config = Settings(data_dir=tmp_path, auto_execute_max_risk=0.05)
    monkeypatch.setattr(api, "repository", repository)
    monkeypatch.setattr(api, "service", CaseService(repository, config))
    client = TestClient(api.app)
    response = client.post(
        "/api/cases",
        files={"file": ("request.md", COMPLETE.encode())},
        data={"requester": "Teste"},
    )
    assert response.status_code == 201
    case_id = response.json()["id"]
    reviewed = client.post(
        f"/api/cases/{case_id}/review",
        json={"decision": "approve", "actor": "Analista", "reason": "Caso validado"},
    )
    assert reviewed.json()["status"] == "approved"
    assert client.get(f"/api/cases/{case_id}").json()["events"]


def test_metrics_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(api, "repository", Repository(tmp_path / "empty.db"))
    assert TestClient(api.app).get("/api/metrics").json()["total"] == 0
