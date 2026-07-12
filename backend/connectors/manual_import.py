from __future__ import annotations

import csv
import io
import json
import re
from pathlib import Path
from typing import Any
from uuid import uuid4

from backend.connectors.base import JobConnector
from backend.models import ConnectorHealth, Job, SearchRequest, Workspace


def _list_value(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if not value:
        return []
    try:
        decoded = json.loads(str(value))
        if isinstance(decoded, list):
            return [str(item).strip() for item in decoded if str(item).strip()]
    except json.JSONDecodeError:
        pass
    return [part.strip() for part in re.split(r"[|;\n]", str(value)) if part.strip()]


def _budget_fields(raw: dict[str, Any]) -> tuple[float | None, str | None]:
    """Extract a displayed fixed budget without guessing a foreign-exchange rate."""
    explicit_amount = raw.get("budgetAmount") or raw.get("budget_amount")
    explicit_currency = raw.get("currency")
    if explicit_amount not in (None, ""):
        try:
            return float(explicit_amount), str(explicit_currency).upper() if explicit_currency else None
        except (TypeError, ValueError):
            return None, str(explicit_currency).upper() if explicit_currency else None
    text = str(raw.get("budget") or "")
    # Platform listings often place the amount before the ISO code: "35 USD fixed".
    trailing_match = re.search(r"(\d+(?:\.\d+)?)\s*(CNY|RMB|USD|GBP|EUR|¥|￥|\$|£|€)\b", text, re.I)
    if trailing_match:
        amount, marker = trailing_match.groups()
        marker = marker.upper()
        currency = (
            "CNY" if marker in {"CNY", "RMB", "¥", "￥"}
            else "USD" if marker in {"USD", "$"}
            else "GBP" if marker in {"GBP", "£"}
            else "EUR" if marker in {"EUR", "€"}
            else None
        )
        return float(amount), currency
    match = re.search(r"(?:CNY|RMB|USD|GBP|EUR|¥|\$|£|€)?\s*(\d+(?:\.\d+)?)", text, re.I)
    if not match:
        return None, str(explicit_currency).upper() if explicit_currency else None
    marker = match.group(0).upper()
    currency = "CNY" if ("CNY" in marker or "RMB" in marker or "¥" in marker) else "USD" if ("USD" in marker or "$" in marker) else "GBP" if ("GBP" in marker or "£" in marker) else "EUR" if ("EUR" in marker or "€" in marker) else None
    return float(match.group(1)), currency


class ManualImportConnector(JobConnector):
    platform = "ManualImport"
    mode = "json_csv_paste"

    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path else None

    async def health_check(self) -> ConnectorHealth:
        return ConnectorHealth(platform=self.platform, mode=self.mode, ok=True, message="CSV, JSON, paste, and extension capture are available locally.")

    def normalize_job(self, raw: dict[str, Any]) -> Job:
        budget_amount, currency = _budget_fields(raw)
        normalized = {
            "id": str(raw.get("id") or f"import-{uuid4().hex[:12]}"),
            "workspace": raw.get("workspace") or ("embedded" if raw.get("embedded") else Workspace.general.value),
            "platform": str(raw.get("platform") or "Manual"),
            "title": str(raw.get("title") or "Untitled job"),
            "category": str(raw.get("category") or "other"),
            "budget": raw.get("budget"), "budgetAmount": budget_amount,
            "currency": currency, "client": raw.get("client"),
            "clientReputation": raw.get("clientReputation") or raw.get("client_reputation") or 3,
            "posted": raw.get("posted"), "url": raw.get("url"),
            "description": str(raw.get("description") or raw.get("details") or raw.get("title") or "No description supplied."),
            "deliverables": _list_value(raw.get("deliverables")),
            "deliverableClarity": raw.get("deliverableClarity") or raw.get("deliverable_clarity") or 3,
            "constraints": _list_value(raw.get("constraints")), "requiredSkills": _list_value(raw.get("requiredSkills") or raw.get("required_skills")),
            "manualWorkLevel": raw.get("manualWorkLevel") or raw.get("manual_work_level") or 3,
            "riskLevel": raw.get("riskLevel") or raw.get("risk_level") or 3,
            "estimatedMinutes": raw.get("estimatedMinutes") or raw.get("estimated_minutes") or 120,
            "aiAutonomy": raw.get("aiAutonomy") or raw.get("ai_autonomy") or 0.5,
            "embedded": raw.get("embedded") or {},
            "source": str(raw.get("source") or "import"), "raw": raw,
        }
        return Job(**normalized)

    def parse_json(self, content: str) -> list[Job]:
        raw = json.loads(content)
        if isinstance(raw, dict): raw = raw.get("jobs", [raw])
        if not isinstance(raw, list): raise ValueError("JSON must be a job object or an array of jobs")
        return [self.normalize_job(item) for item in raw]

    def parse_csv(self, content: str) -> list[Job]:
        return [self.normalize_job(dict(row)) for row in csv.DictReader(io.StringIO(content))]

    def parse_paste(self, platform: str, text: str, workspace: Workspace = Workspace.general) -> Job:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return self.normalize_job({"platform": platform, "title": lines[0][:200], "description": text, "source": "manual_paste", "workspace": workspace.value})

    async def search_jobs(self, request: SearchRequest) -> list[Job]:
        if not self.path or not self.path.exists(): return []
        jobs = self.parse_json(self.path.read_text(encoding="utf-8"))
        q = request.query.lower().strip()
        return [job for job in jobs if (not q or q in f"{job.title} {job.description} {job.platform} {job.category}".lower()) and (not request.platforms or job.platform in request.platforms) and (not request.categories or job.category in request.categories)][:request.max_results]
