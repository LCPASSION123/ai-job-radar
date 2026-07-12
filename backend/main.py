from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from backend.connectors.catalog import build_connector_catalog
from backend.connectors.freelancer import FreelancerConnector
from backend.connectors.manual_import import ManualImportConnector
from backend.connectors.upwork import UpworkConnector
from backend.database import Database
from backend.exporting import as_csv, as_json, as_markdown
from backend.models import (
    AuditEvent, ConnectorHealth, ConnectorInfo, DomCaptureRequest, HighRiskConfirmation,
    EmbeddedTargetProfile, ImportResult, PasteRequest, PlatformProfile, ProposalRequest, ScoredJob, SearchRequest, TargetProfile, Workspace,
)
from backend.platform_catalog import platform_catalog
from backend.scheduler import RadarScheduler
from backend.llm import provider_status
from backend.scoring import build_proposal, score_job

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
DATABASE_PATH = Path(os.getenv("DATABASE_PATH", str(ROOT / "data" / "ai_job_radar.db")))
SAMPLE_PATH = ROOT / "data" / "sample_jobs.json"
EMBEDDED_SAMPLE_PATH = ROOT / "data" / "sample_embedded_jobs.json"
database = Database(DATABASE_PATH)
manual_connector = ManualImportConnector()
connectors = build_connector_catalog(
    UpworkConnector(os.getenv("UPWORK_CLIENT_ID"), os.getenv("UPWORK_CLIENT_SECRET")),
    FreelancerConnector(os.getenv("FREELANCER_API_TOKEN")),
)
scheduler = RadarScheduler(database)


def _seed_demo_data() -> None:
    for path, workspace in ((SAMPLE_PATH, Workspace.general), (EMBEDDED_SAMPLE_PATH, Workspace.embedded)):
        if database.list_jobs(limit=1, workspace=workspace) or not path.exists():
            continue
        jobs = ManualImportConnector(path).parse_json(path.read_text(encoding="utf-8"))
        for job in jobs:
            job.source = "bundled_embedded_demo" if workspace == Workspace.embedded else "bundled_demo"
            job.workspace = workspace
        database.upsert_jobs(jobs)
        database.audit("demo_seeded", {"workspace": workspace.value, "jobs": len(jobs), "source": jobs[0].source})


@asynccontextmanager
async def lifespan(_: FastAPI):
    database.initialize()
    _seed_demo_data()
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(
    title="AI Job Radar API", version="1.0.0",
    description="Compliant, account-free job intake, scoring, drafting, export, and audit API. It never submits bids or platform actions.",
    lifespan=lifespan,
)
app.add_middleware(CORSMiddleware, allow_origins=[os.getenv("RADAR_CORS_ORIGIN", "http://localhost:5173")], allow_methods=["*"], allow_headers=["*"])


def _scored(request: SearchRequest) -> list[ScoredJob]:
    jobs = database.list_jobs(request.query, request.platforms, request.categories, request.max_results, request.workspace)
    result = sorted((score_job(job) for job in jobs), key=lambda item: item.score, reverse=True)
    database.audit("search", {"workspace": request.workspace.value, "query": request.query, "platforms": request.platforms, "categories": request.categories, "results": len(result)})
    database.audit("score", {"workspace": request.workspace.value, "jobs": len(result), "engine": "deterministic_v2"})
    return result


@app.get("/health")
async def health() -> dict[str, str]:
    return {"ok": "true", "service": "AI Job Radar", "storage": "sqlite"}


@app.get("/llm/status")
async def llm_status() -> dict[str, str | bool]:
    return provider_status()


@app.get("/connectors", response_model=list[ConnectorInfo])
async def connector_list(workspace: Workspace | None = None) -> list[ConnectorInfo]:
    items = []
    for connector in connectors:
        health = await connector.health_check()
        items.append(ConnectorInfo(**health.model_dump(), supportsCsv=connector.platform not in {"Upwork", "Freelancer", "百度众测", "京东众智"}, supportsPaste=True, supportsDomCapture=getattr(connector, "dom_capture", False)))
    return [item for item in items if workspace is None or item.workspace == workspace]


@app.get("/platforms", response_model=list[PlatformProfile])
async def platforms(workspace: Workspace | None = None) -> list[PlatformProfile]:
    """Return the local curated directory; no platform network call is made."""
    return platform_catalog(workspace)


@app.get("/connectors/health", response_model=list[ConnectorHealth])
async def connector_health() -> list[ConnectorHealth]:
    return [await connector.health_check() for connector in connectors]


@app.post("/jobs/search", response_model=list[ScoredJob])
async def search_jobs(request: SearchRequest) -> list[ScoredJob]:
    return _scored(request)


@app.post("/jobs/recommendations", response_model=list[ScoredJob])
async def recommendations(profile: TargetProfile) -> list[ScoredJob]:
    """Strict queue for small, low-risk, high-autonomy work candidates."""
    from backend.scoring import fits_target_profile

    candidates = _scored(SearchRequest(max_results=200, workspace=Workspace.general))
    result = [job for job in candidates if fits_target_profile(job, profile)]
    database.audit("target_recommendations", {"profile": profile.model_dump(), "results": len(result)})
    return result


@app.post("/embedded/jobs/recommendations", response_model=list[ScoredJob])
async def embedded_recommendations(profile: EmbeddedTargetProfile) -> list[ScoredJob]:
    """Strict desk-only embedded queue; never selects work needing real hardware."""
    from backend.scoring import fits_embedded_target_profile

    candidates = _scored(SearchRequest(max_results=200, workspace=Workspace.embedded))
    result = [job for job in candidates if fits_embedded_target_profile(job, profile)]
    database.audit("embedded_target_recommendations", {"profile": profile.model_dump(), "results": len(result)})
    return result


@app.get("/jobs/{job_id}", response_model=ScoredJob)
async def get_job(job_id: str) -> ScoredJob:
    job = database.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return score_job(job)


@app.post("/jobs/{job_id}/proposal", response_model=dict)
async def generate_proposal(job_id: str, request: ProposalRequest) -> dict:
    job = database.get_job(job_id)
    if not job: raise HTTPException(status_code=404, detail="Job not found")
    database.audit("proposal_generated", {"job_id": job_id, "language": request.language})
    return {"job_id": job_id, "proposal": build_proposal(job, request.language), "requires_human_review": True}


@app.post("/jobs/import/json", response_model=ImportResult)
async def import_json(file: UploadFile = File(...)) -> ImportResult:
    try:
        jobs = manual_connector.parse_json((await file.read()).decode("utf-8-sig"))
    except (UnicodeDecodeError, ValueError) as error:
        raise HTTPException(status_code=422, detail=f"Invalid JSON import: {error}") from error
    database.upsert_jobs(jobs); database.audit("import_json", {"filename": file.filename, "jobs": len(jobs)})
    return ImportResult(imported=len(jobs))


@app.post("/jobs/import/csv", response_model=ImportResult)
async def import_csv(file: UploadFile = File(...)) -> ImportResult:
    try:
        jobs = manual_connector.parse_csv((await file.read()).decode("utf-8-sig"))
    except (UnicodeDecodeError, ValueError) as error:
        raise HTTPException(status_code=422, detail=f"Invalid CSV import: {error}") from error
    database.upsert_jobs(jobs); database.audit("import_csv", {"filename": file.filename, "jobs": len(jobs)})
    return ImportResult(imported=len(jobs))


@app.post("/jobs/paste", response_model=ImportResult)
async def paste_job(request: PasteRequest) -> ImportResult:
    job = manual_connector.parse_paste(request.platform, request.text, request.workspace)
    database.upsert_jobs([job]); database.audit("manual_paste", {"workspace": request.workspace.value, "platform": request.platform, "job_id": job.id})
    return ImportResult(imported=1)


@app.post("/jobs/dom-capture", response_model=ImportResult)
async def dom_capture(request: DomCaptureRequest) -> ImportResult:
    """Read-only browser-extension handoff. The extension must capture only visible user-authorized DOM."""
    jobs = [manual_connector.normalize_job({**raw, "workspace": request.workspace.value, "platform": request.platform, "source": "browser_extension_dom_capture"}) for raw in request.jobs]
    database.upsert_jobs(jobs); database.audit("dom_capture", {"workspace": request.workspace.value, "platform": request.platform, "jobs": len(jobs)})
    return ImportResult(imported=len(jobs))


@app.get("/exports/{format_name}")
async def export_report(format_name: str) -> Response:
    jobs = _scored(SearchRequest(max_results=200))
    exporters = {"csv": (as_csv, "text/csv; charset=utf-8", "ai-job-radar.csv"), "json": (as_json, "application/json", "ai-job-radar.json"), "markdown": (as_markdown, "text/markdown; charset=utf-8", "ai-job-radar-report.md")}
    if format_name not in exporters: raise HTTPException(status_code=404, detail="Use csv, json, or markdown")
    export, media_type, filename = exporters[format_name]
    database.audit("export", {"format": format_name, "jobs": len(jobs)})
    return Response(export(jobs), media_type=media_type, headers={"Content-Disposition": f'attachment; filename="{filename}"'})


@app.get("/audit", response_model=list[AuditEvent])
async def audit_log(limit: int = 100) -> list[AuditEvent]:
    return database.list_audit(limit=min(limit, 500))


@app.post("/actions/high-risk/confirm", status_code=202)
async def confirm_high_risk_action(request: HighRiskConfirmation) -> dict[str, str]:
    expected = f"CONFIRM {request.action}"
    if request.confirmation != expected:
        raise HTTPException(status_code=400, detail=f"Second confirmation required: enter exactly '{expected}'. No platform action has occurred.")
    database.audit("high_risk_action_confirmed", {"action": request.action, "job_id": request.job_id, "executed": False})
    return {"status": "recorded", "message": "Confirmation was logged. AI Job Radar intentionally does not submit, message, contract, or pay on your behalf."}
