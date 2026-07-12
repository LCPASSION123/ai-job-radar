from backend.models import EmbeddedTargetProfile, Job, Verdict, Workspace
from backend.scoring import fits_embedded_target_profile, score_job


def embedded_job(**changes):
    defaults = dict(
        id="embedded-ok", workspace=Workspace.embedded, platform="Manual", title="ESP32 parser host-test fix",
        category="embedded_firmware", description="Source repository provided. Fix protocol parser with host test simulation.",
        deliverables=["patch", "host test"], constraints=["no on-device test"], budgetAmount=300, currency="CNY",
        manualWorkLevel=1, riskLevel=1, estimatedMinutes=90, aiAutonomy=0.91, clientReputation=4,
        deliverableClarity=5, embedded={"target": "ESP32", "sourceFilesProvided": True, "toolchainKnown": True, "testFixturesProvided": True},
    )
    return Job(**(defaults | changes))


def test_desk_only_embedded_job_is_recommended_and_eligible():
    result = score_job(embedded_job())
    assert result.verdict == Verdict.recommend
    assert result.embeddedAssessment is not None
    assert result.embeddedAssessment.agentReadiness >= 80
    assert fits_embedded_target_profile(result, EmbeddedTargetProfile())


def test_physical_or_production_embedded_work_is_rejected():
    result = score_job(embedded_job(
        id="embedded-no", title="Production flash BMS board", description="Flash device in factory and validate high voltage battery.",
        embedded={"hardwareAccessRequired": True, "onDeviceTestingRequired": True, "productionFlashOrDeploy": True, "safetyCritical": True},
    ))
    assert result.verdict == Verdict.reject
    assert result.embeddedAssessment is not None
    assert result.embeddedAssessment.productionFlashOrDeploy is True
    assert not fits_embedded_target_profile(result, EmbeddedTargetProfile())
