from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from backend.models import ConnectorHealth, Job, SearchRequest


class JobConnector(ABC):
    platform: str
    mode: str

    @abstractmethod
    async def health_check(self) -> ConnectorHealth: ...

    @abstractmethod
    async def search_jobs(self, request: SearchRequest) -> list[Job]: ...

    @abstractmethod
    def normalize_job(self, raw: dict[str, Any]) -> Job: ...
