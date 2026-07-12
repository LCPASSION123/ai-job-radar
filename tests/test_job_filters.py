from datetime import datetime, timedelta, timezone

from backend.main import _matches_extra_filters
from backend.models import Job, SearchRequest


def job(**changes):
    defaults = {
        "id": "filter-1", "platform": "Manual", "title": "ESP32 UART parser", "category": "embedded_firmware",
        "description": "Fix a UART protocol parser with supplied host test.", "requiredSkills": ["ESP-IDF", "C"],
        "constraints": ["simulation"], "posted": datetime.now(timezone.utc).isoformat(),
    }
    return Job(**(defaults | changes))


def test_posted_range_and_custom_tags_must_match():
    assert _matches_extra_filters(job(), SearchRequest(tags=["ESP32", "simulation"], postedWithinHours=24))
    assert not _matches_extra_filters(job(), SearchRequest(tags=["Zephyr"], postedWithinHours=24))
    old = job(id="old", posted=(datetime.now(timezone.utc) - timedelta(days=8)).isoformat())
    assert not _matches_extra_filters(old, SearchRequest(postedWithinHours=168))
