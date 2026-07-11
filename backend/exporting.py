from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone

from backend.models import ScoredJob


def as_json(jobs: list[ScoredJob]) -> str:
    return json.dumps([job.model_dump(mode="json") for job in jobs], ensure_ascii=False, indent=2)


def as_csv(jobs: list[ScoredJob]) -> str:
    output = io.StringIO()
    fields = ["id", "platform", "title", "category", "budget", "score", "verdict", "estimatedMinutes", "reason", "url"]
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    for job in jobs:
        writer.writerow({field: getattr(job, field) for field in fields})
    return output.getvalue()


def as_markdown(jobs: list[ScoredJob]) -> str:
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [f"# AI Job Radar daily report\n\nGenerated: {generated}\n", "| Score | Verdict | Platform | Job | Budget |", "|---:|---|---|---|---|"]
    lines.extend(f"| {job.score} | {job.verdict.value} | {job.platform} | {job.title} | {job.budget or '-'} |" for job in jobs)
    lines.append("\n> This report only supports review and drafting. It does not submit bids, send messages, accept contracts, or make payments.")
    return "\n".join(lines)
