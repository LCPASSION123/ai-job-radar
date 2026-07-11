from __future__ import annotations

from backend.connectors.base import JobConnector
from backend.models import ConnectorHealth, Job, SearchRequest
from typing import Any


class FreelancerConnector(JobConnector):
    """Official API scaffold for Freelancer.com.

    The official API/SDK supports project search and project detail retrieval. Production code
    should handle auth, pagination, rate limits and normalize the project object into Job.
    """

    platform = "Freelancer"
    mode = "official_api"

    def __init__(self, token: str | None = None):
        self.token = token

    async def health_check(self) -> ConnectorHealth:
        return ConnectorHealth(
            platform=self.platform,
            mode=self.mode,
            ok=bool(self.token),
            message="API token configured" if self.token else "Missing API token; using demo/manual mode",
        )

    def normalize_job(self, raw: dict[str, Any]) -> Job:
        # Keep official API mapping isolated; this does not call Freelancer without user credentials.
        from backend.connectors.manual_import import ManualImportConnector
        raw["platform"] = self.platform
        raw["source"] = "freelancer_official_api"
        return ManualImportConnector().normalize_job(raw)

    async def search_jobs(self, request: SearchRequest) -> list[Job]:
        raise NotImplementedError("Implement with Freelancer official API or SDK.")
