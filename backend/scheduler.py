from __future__ import annotations

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from backend.database import Database


class RadarScheduler:
    """Schedules local maintenance only; it never logs in, scrapes, bids, or contacts clients."""

    def __init__(self, database: Database):
        self.database = database
        self.scheduler = AsyncIOScheduler()

    def start(self) -> None:
        self.scheduler.add_job(self._heartbeat, "interval", minutes=30, id="local-heartbeat", replace_existing=True)
        self.scheduler.start()

    def shutdown(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)

    def _heartbeat(self) -> None:
        self.database.audit("scheduler_heartbeat", {"purpose": "local maintenance only"})
