from __future__ import annotations

from typing import Any

from backend.connectors.base import JobConnector
from backend.models import ConnectorHealth, SearchRequest, Workspace


class ImportOnlyConnector(JobConnector):
    def __init__(self, platform: str, mode: str, message: str, dom_capture: bool = False, workspace: Workspace = Workspace.general):
        self.platform, self.mode, self.message, self.dom_capture, self.workspace = platform, mode, message, dom_capture, workspace

    async def health_check(self) -> ConnectorHealth:
        return ConnectorHealth(platform=self.platform, mode=self.mode, ok=True, message=self.message, workspace=self.workspace)

    def normalize_job(self, raw: dict[str, Any]):
        from backend.connectors.manual_import import ManualImportConnector
        raw["platform"] = self.platform
        return ManualImportConnector().normalize_job(raw)

    async def search_jobs(self, request: SearchRequest):
        return []


def build_connector_catalog(upwork: JobConnector, freelancer: JobConnector) -> list[JobConnector]:
    return [
        upwork, freelancer,
        ImportOnlyConnector("Fiverr", "csv_manual_paste", "Import a user export or paste visible job details; no unofficial scraping."),
        ImportOnlyConnector("PeoplePerHour", "csv_dom_capture", "Use a user export, paste, or read-only extension capture.", True),
        ImportOnlyConnector("猪八戒", "csv_dom_capture", "Use a user export, paste, or read-only extension capture.", True),
        ImportOnlyConnector("一品威客", "csv_dom_capture", "Use a user export, paste, or read-only extension capture.", True),
        ImportOnlyConnector("百度众测", "manual_candidate_only", "Candidate tracking only; never automate task submission."),
        ImportOnlyConnector("京东众智", "manual_candidate_only", "Candidate tracking only; never automate task submission."),
        ImportOnlyConnector("猪八戒·硬件开发", "csv_dom_capture", "Read-only import for embedded opportunities; physical work is rejected by the embedded gate.", True, Workspace.embedded),
        ImportOnlyConnector("一品威客·硬件开发", "csv_dom_capture", "Read-only import for embedded opportunities; physical work is rejected by the embedded gate.", True, Workspace.embedded),
        ImportOnlyConnector("程序员客栈·IoT", "csv_dom_capture", "Import or user-clicked visible DOM capture only.", True, Workspace.embedded),
        ImportOnlyConnector("码市·物联网", "csv_dom_capture", "Import or user-clicked visible DOM capture only.", True, Workspace.embedded),
        ImportOnlyConnector("电子发烧友·工程机会", "manual_dom_capture", "Discovery-only engineering lead source; never send messages automatically.", True, Workspace.embedded),
        ImportOnlyConnector("EEWorld·工程机会", "manual_dom_capture", "Discovery-only engineering lead source; never send messages automatically.", True, Workspace.embedded),
        ImportOnlyConnector("21IC·工程机会", "manual_dom_capture", "Discovery-only engineering lead source; never send messages automatically.", True, Workspace.embedded),
    ]
