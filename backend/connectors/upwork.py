from __future__ import annotations

from backend.connectors.base import JobConnector
from backend.models import ConnectorHealth, Job, SearchRequest
from typing import Any


class UpworkConnector(JobConnector):
    """Official-API-first scaffold.

    Production implementation should use Upwork OAuth credentials and GraphQL queries.
    Keep proposal submission/manual account actions outside automation unless the user explicitly confirms.
    """

    platform = "Upwork"
    mode = "official_api_oauth"

    def __init__(self, client_id: str | None = None, client_secret: str | None = None):
        self.client_id = client_id
        self.client_secret = client_secret

    async def health_check(self) -> ConnectorHealth:
        configured = bool(self.client_id and self.client_secret)
        return ConnectorHealth(
            platform=self.platform,
            mode=self.mode,
            ok=configured,
            message="OAuth credentials configured" if configured else "Missing OAuth credentials; using demo/manual mode",
        )

    def normalize_job(self, raw: dict[str, Any]) -> Job:
        # Keep official API mapping isolated; this does not call Upwork or bypass OAuth.
        from backend.connectors.manual_import import ManualImportConnector
        raw["platform"] = self.platform
        raw["source"] = "upwork_official_api"
        return ManualImportConnector().normalize_job(raw)

    async def search_jobs(self, request: SearchRequest) -> list[Job]:
        raise NotImplementedError("Implement with official Upwork GraphQL API after OAuth setup.")
