from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from backend.models import AuditEvent, Job, Workspace


class Database:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def initialize(self) -> None:
        with self.connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    platform TEXT NOT NULL,
                    category TEXT NOT NULL,
                    title TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS audit_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event TEXT NOT NULL,
                    details TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
            """)

    def upsert_jobs(self, jobs: list[Job]) -> None:
        with self.connection() as conn:
            conn.executemany(
                """INSERT INTO jobs(id, platform, category, title, payload) VALUES(?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET platform=excluded.platform, category=excluded.category,
                title=excluded.title, payload=excluded.payload, updated_at=CURRENT_TIMESTAMP""",
                [(job.id, job.platform, job.category, job.title, json.dumps(job.model_dump(), ensure_ascii=False)) for job in jobs],
            )

    def list_jobs(self, query: str = "", platforms: list[str] | None = None, categories: list[str] | None = None, limit: int = 50, workspace: Workspace | None = None) -> list[Job]:
        clauses, params = [], []
        if query:
            clauses.append("(lower(title) LIKE ? OR lower(payload) LIKE ?)")
            params.extend([f"%{query.lower()}%", f"%{query.lower()}%"])
        if platforms:
            clauses.append(f"platform IN ({','.join('?' for _ in platforms)})")
            params.extend(platforms)
        if categories:
            clauses.append(f"category IN ({','.join('?' for _ in categories)})")
            params.extend(categories)
        sql = "SELECT payload FROM jobs" + (" WHERE " + " AND ".join(clauses) if clauses else "") + " ORDER BY updated_at DESC LIMIT ?"
        params.append(limit)
        with self.connection() as conn:
            records = [Job(**json.loads(row["payload"])) for row in conn.execute(sql, params)]
        return [job for job in records if workspace is None or job.workspace == workspace]

    def get_job(self, job_id: str) -> Job | None:
        with self.connection() as conn:
            row = conn.execute("SELECT payload FROM jobs WHERE id = ?", (job_id,)).fetchone()
        return Job(**json.loads(row["payload"])) if row else None

    def audit(self, event: str, details: dict[str, Any]) -> None:
        with self.connection() as conn:
            conn.execute("INSERT INTO audit_events(event, details) VALUES (?, ?)", (event, json.dumps(details, ensure_ascii=False)))

    def list_audit(self, limit: int = 100) -> list[AuditEvent]:
        with self.connection() as conn:
            rows = conn.execute("SELECT id, event, details, created_at FROM audit_events ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [AuditEvent(id=row["id"], event=row["event"], details=json.loads(row["details"]), created_at=row["created_at"]) for row in rows]
