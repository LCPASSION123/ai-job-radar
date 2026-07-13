from backend.models import Job, Verdict
from backend.scoring import score_job


def job(**changes):
    defaults = dict(id="test-1", platform="Manual", title="Polish product copy", category="copywriting", description="Rewrite supplied product copy without new claims.", deliverables=["copy"], manualWorkLevel=1, riskLevel=1, estimatedMinutes=45, aiAutonomy=0.92, budgetAmount=40, clientReputation=4, deliverableClarity=5)
    return Job(**(defaults | changes))


def test_low_risk_clear_job_is_recommended():
    result = score_job(job())
    assert result.verdict == Verdict.recommend
    assert result.score >= 75
    assert result.scoreBreakdown.deliverableClarity == 100


def test_prohibited_request_is_rejected_even_with_good_metrics():
    result = score_job(job(title="Write fake reviews", description="Need fake review manipulation"))
    assert result.verdict == Verdict.reject
    assert result.score <= 25
    assert "不建议接" in result.reason


def test_proposal_defaults_to_chinese_for_an_english_job():
    result = score_job(job(title="Rewrite product copy", description="Rewrite supplied product copy without new claims."))
    assert "您好" in result.proposalDraft
