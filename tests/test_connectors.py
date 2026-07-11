import asyncio

from backend.connectors.catalog import ImportOnlyConnector
from backend.connectors.manual_import import ManualImportConnector
from backend.models import SearchRequest


def test_import_connector_contract_health_and_empty_search():
    connector = ImportOnlyConnector("Fiverr", "csv_manual_paste", "manual only")
    health = asyncio.run(connector.health_check())
    assert health.platform == "Fiverr"
    assert health.ok is True
    assert asyncio.run(connector.search_jobs(SearchRequest())) == []


def test_normalize_job_preserves_required_contract_fields():
    job = ManualImportConnector().normalize_job({"platform": "Fiverr", "title": "Write captions", "description": "Ten short captions", "deliverables": "captions|hashtags", "estimated_minutes": "30", "ai_autonomy": "0.8"})
    assert job.platform == "Fiverr"
    assert job.deliverables == ["captions", "hashtags"]
    assert job.estimatedMinutes == 30
