import sqlite3
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .ingestion import IngestionError
from .models import ExecuteRequest, ReviewRequest
from .repository import Repository
from .service import CaseService

STATIC = Path(__file__).parent / "static"
app = FastAPI(title="AI Operations Case Manager", version="0.1.0")
app.mount("/static", StaticFiles(directory=STATIC), name="static")
repository = Repository(settings.database_path)
service = CaseService(repository, settings)


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(STATIC / "index.html")


@app.get("/api/health")
def health():
    return {"status": "ok", "llm_provider": settings.llm_provider}


@app.post("/api/cases", status_code=201)
async def create_case(file: UploadFile = File(...), requester: str = Form("Portal")):
    try:
        return service.create(file.filename or "request.md", await file.read(), requester)
    except IngestionError as exc:
        raise HTTPException(422, str(exc)) from exc
    except sqlite3.IntegrityError as exc:
        raise HTTPException(409, "Este documento já possui um caso.") from exc


@app.get("/api/cases")
def list_cases():
    return repository.list_cases()


@app.get("/api/cases/{case_id}")
def get_case(case_id: str):
    case = repository.get_case(case_id)
    if not case:
        raise HTTPException(404, "Caso não encontrado.")
    return {"case": case, "events": repository.events(case_id)}


@app.post("/api/cases/{case_id}/review")
def review_case(case_id: str, request: ReviewRequest):
    case = repository.get_case(case_id)
    if not case:
        raise HTTPException(404, "Caso não encontrado.")
    try:
        return service.review(case, request.decision, request.actor, request.reason)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc


@app.post("/api/cases/{case_id}/execute")
def execute_case(case_id: str, request: ExecuteRequest):
    case = repository.get_case(case_id)
    if not case:
        raise HTTPException(404, "Caso não encontrado.")
    try:
        return service.execute(case, request.actor)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc


@app.get("/api/metrics")
def metrics():
    cases = repository.list_cases()
    total = len(cases)
    executed = sum(case.status == "executed" for case in cases)
    pending = sum(case.status == "pending_review" for case in cases)
    return {
        "total": total,
        "pending_review": pending,
        "executed": executed,
        "automation_rate": round(sum(case.status == "ready" for case in cases) / total, 3)
        if total
        else 0,
        "average_risk": round(sum(case.risk_score for case in cases) / total, 3) if total else 0,
    }
