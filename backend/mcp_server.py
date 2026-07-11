"""Read-only MCP bridge for the local AI Job Radar service."""

from __future__ import annotations

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from mcp.server.fastmcp import FastMCP

API_URL = os.getenv("AI_JOB_RADAR_API_URL", "http://127.0.0.1:8000").rstrip("/")
mcp = FastMCP("AI Job Radar")


def _call(path: str, method: str = "GET", payload: dict | None = None) -> dict | list:
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = Request(f"{API_URL}{path}", data=body, method=method, headers={"Content-Type": "application/json"})
    try:
        with urlopen(request, timeout=20) as response:  # nosec B310: local user-configured URL
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        raise RuntimeError(f"Radar API returned {error.code}: {error.read().decode('utf-8', errors='replace')}") from error
    except URLError as error:
        raise RuntimeError(f"Cannot reach local Radar API at {API_URL}: {error.reason}") from error


@mcp.tool()
def list_platforms() -> list[dict]:
    """List vetted marketplaces and compliant intake routes. No account access occurs."""
    return _call("/platforms")  # type: ignore[return-value]


@mcp.tool()
def search_jobs(query: str = "", platforms: list[str] | None = None, max_results: int = 50) -> list[dict]:
    """Search local imported/read-only captured jobs; it never creates platform actions."""
    return _call("/jobs/search", "POST", {"query": query, "platforms": platforms or [], "max_results": max_results})  # type: ignore[return-value]


@mcp.tool()
def recommend_ai_deliverable_jobs(max_minutes: int = 120, minimum_budget_cny: float = 50) -> list[dict]:
    """Find low-risk high-autonomy candidates; all delivery still needs human fact and quality review."""
    return _call("/jobs/recommendations", "POST", {"maxMinutes": max_minutes, "minimumBudgetCny": minimum_budget_cny, "minimumAiAutonomy": 0.85, "maximumManualWorkLevel": 2, "maximumRiskLevel": 2})  # type: ignore[return-value]


@mcp.tool()
def get_job(job_id: str) -> dict:
    """Read a scored job, its draft proposal, and delivery plan. The draft cannot be sent automatically."""
    return _call(f"/jobs/{job_id}")  # type: ignore[return-value]


@mcp.tool()
def generate_proposal(job_id: str, language: str = "auto") -> dict:
    """Generate a proposal draft for human review only; it never submits it to a platform."""
    return _call(f"/jobs/{job_id}/proposal", "POST", {"language": language})  # type: ignore[return-value]


@mcp.tool()
def recent_audit_events(limit: int = 50) -> list[dict]:
    """Read the local audit trail."""
    return _call(f"/audit?limit={min(max(limit, 1), 500)}")  # type: ignore[return-value]


if __name__ == "__main__":
    mcp.run()
