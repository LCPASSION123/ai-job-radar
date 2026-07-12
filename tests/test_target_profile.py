from backend.models import Job, TargetProfile
from backend.scoring import fits_target_profile


def test_target_profile_accepts_small_clear_low_risk_job():
    job = Job(id="ok", platform="Manual", title="PPT outline", description="Create a short deck from supplied notes.", budgetAmount=80, currency="CNY", estimatedMinutes=90, aiAutonomy=0.9, manualWorkLevel=1, riskLevel=1)
    assert fits_target_profile(job, TargetProfile())


def test_target_profile_rejects_under_budget_or_high_touch_work():
    too_cheap = Job(id="cheap", platform="Manual", title="Copy", description="Write from supplied brief.", budgetAmount=20, currency="CNY", estimatedMinutes=30, aiAutonomy=0.9, manualWorkLevel=1, riskLevel=1)
    high_touch = too_cheap.model_copy(update={"id": "touch", "budgetAmount": 100, "manualWorkLevel": 4})
    assert not fits_target_profile(too_cheap, TargetProfile())
    assert not fits_target_profile(high_touch, TargetProfile())


def test_target_profile_supports_week_and_unlimited_time_windows():
    week_job = Job(id="week", platform="Manual", title="Bounded documentation", description="Document a supplied repository.", budgetAmount=100, currency="CNY", estimatedMinutes=9000, aiAutonomy=0.9, manualWorkLevel=1, riskLevel=1)
    assert fits_target_profile(week_job, TargetProfile(maxMinutes=10080))
    assert fits_target_profile(week_job, TargetProfile(maxMinutes=525600))
