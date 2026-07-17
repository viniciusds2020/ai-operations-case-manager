import json
import sqlite3
from pathlib import Path

from .models import Case, Event


class Repository:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self._init()

    def connect(self):
        db = sqlite3.connect(self.path)
        db.row_factory = sqlite3.Row
        return db

    def _init(self):
        with self.connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS cases (
                id TEXT PRIMARY KEY, sha256 TEXT UNIQUE, payload TEXT NOT NULL)""")
            db.execute("""CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT, case_id TEXT NOT NULL,
                event_type TEXT NOT NULL, actor TEXT NOT NULL, detail TEXT NOT NULL,
                created_at TEXT NOT NULL)""")

    def save_case(self, case: Case):
        with self.connect() as db:
            db.execute(
                "INSERT INTO cases(id, sha256, payload) VALUES (?, ?, ?)",
                (case.id, case.sha256, case.model_dump_json()),
            )

    def update_case(self, case: Case):
        with self.connect() as db:
            db.execute(
                "UPDATE cases SET payload = ? WHERE id = ?",
                (case.model_dump_json(), case.id),
            )

    def get_case(self, case_id: str) -> Case | None:
        with self.connect() as db:
            row = db.execute("SELECT payload FROM cases WHERE id = ?", (case_id,)).fetchone()
        return Case.model_validate(json.loads(row["payload"])) if row else None

    def list_cases(self) -> list[Case]:
        with self.connect() as db:
            rows = db.execute("SELECT payload FROM cases ORDER BY rowid DESC").fetchall()
        return [Case.model_validate(json.loads(row["payload"])) for row in rows]

    def add_event(self, event: Event):
        with self.connect() as db:
            cursor = db.execute(
                """INSERT INTO events(case_id, event_type, actor, detail, created_at)
                VALUES (?, ?, ?, ?, ?)""",
                (event.case_id, event.event_type, event.actor, event.detail, event.created_at),
            )
        event.id = cursor.lastrowid

    def events(self, case_id: str) -> list[Event]:
        with self.connect() as db:
            rows = db.execute(
                "SELECT * FROM events WHERE case_id = ? ORDER BY id", (case_id,)
            ).fetchall()
        return [Event.model_validate(dict(row)) for row in rows]
