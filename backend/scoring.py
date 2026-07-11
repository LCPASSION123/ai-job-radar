from __future__ import annotations

import re

from backend.models import Job, ScoreBreakdown, ScoredJob, TargetProfile, Verdict

HIGH_AUTONOMY_CATEGORIES = {"copywriting", "video_script", "ppt", "technical_writing", "image"}
REJECT_KEYWORDS = {
    "fake review", "review manipulation", "刷评", "刷量", "论文代写", "代写作业",
    "deepfake", "换脸", "impersonat", "production payment", "生产支付", "stripe production",
    "gambling", "博彩", "adult content",
}


def _budget_score(job: Job) -> int:
    if job.budgetAmount is None:
        return 55
    hourly_target = 20.0
    expected_cost = max(1, job.estimatedMinutes) / 60 * hourly_target
    return max(0, min(100, round(job.budgetAmount / expected_cost * 65)))


def is_high_risk(job: Job) -> bool:
    blob = " ".join([job.title, job.description, *job.constraints]).lower()
    return any(keyword in blob for keyword in REJECT_KEYWORDS)


def score_job(job: Job) -> ScoredJob:
    """Score a job deterministically so recommendations remain explainable and testable."""
    breakdown = ScoreBreakdown(
        aiAutonomy=round(job.aiAutonomy * 100),
        timeFit=max(0, min(100, round(100 - max(job.estimatedMinutes - 30, 0) * 0.55))),
        manualEffort=round((6 - job.manualWorkLevel) / 5 * 100),
        risk=round((6 - job.riskLevel) / 5 * 100),
        budgetFit=_budget_score(job),
        clientReputation=round(job.clientReputation / 5 * 100),
        deliverableClarity=round(job.deliverableClarity / 5 * 100),
    )

    if is_high_risk(job):
        score, verdict = min(25, breakdown.aiAutonomy), Verdict.reject
        reason = "Rejected: the request contains a prohibited or high-risk pattern. Do not automate or accept it."
    else:
        score = round(
            breakdown.aiAutonomy * 0.26
            + breakdown.timeFit * 0.16
            + breakdown.manualEffort * 0.13
            + breakdown.risk * 0.18
            + breakdown.budgetFit * 0.08
            + breakdown.clientReputation * 0.08
            + breakdown.deliverableClarity * 0.11
            + (4 if job.category in HIGH_AUTONOMY_CATEGORIES else 0)
        )
        score = max(0, min(100, score))
        if score >= 75 and job.estimatedMinutes <= 120 and job.riskLevel <= 2 and job.manualWorkLevel <= 2:
            verdict = Verdict.recommend
            reason = "Clear deliverables, high AI autonomy, and low operational risk make this a good candidate for a human-reviewed delivery."
        elif score >= 50 and job.riskLevel <= 3:
            verdict = Verdict.caution
            reason = "Potentially suitable, but validate scope, source material, platform rules, and quality requirements before proceeding."
        else:
            verdict = Verdict.reject
            reason = "The time, manual effort, risk, or unclear scope does not fit a low-risk AI-assisted delivery."

    return ScoredJob(
        **job.model_dump(), score=score, verdict=verdict, reason=reason,
        scoreBreakdown=breakdown, proposalDraft=build_proposal(job), deliveryPlan=build_delivery_plan(job),
    )


def fits_target_profile(job: Job, profile: TargetProfile) -> bool:
    """Eligibility check for a low-touch AI-assisted queue.

    This does not claim a model can complete work without a final human quality
    review; it only identifies candidates with a small, clear, low-risk scope.
    """
    exchange_floor = {"CNY": 1.0, "RMB": 1.0, "USD": 6.0, "EUR": 6.0, "GBP": 7.0}
    budget_cny = (job.budgetAmount or 0) * exchange_floor.get((job.currency or "").upper(), 0)
    return (
        not is_high_risk(job)
        and job.estimatedMinutes <= profile.maxMinutes
        and job.aiAutonomy >= profile.minimumAiAutonomy
        and job.manualWorkLevel <= profile.maximumManualWorkLevel
        and job.riskLevel <= profile.maximumRiskLevel
        and budget_cny >= profile.minimumBudgetCny
    )


def build_proposal(job: Job, language: str = "auto") -> str:
    wants_zh = language == "zh" or (language == "auto" and bool(re.search(r"[\u4e00-\u9fff]", job.description)))
    deliverables = "\n".join(f"- {item}" for item in job.deliverables) or "- A scoped first draft\n- One light revision"
    if wants_zh:
        return (f"您好，我可以协助完成「{job.title}」。\n\n我会交付：\n{deliverables}\n\n"
                "我会基于您提供的资料完成工作，不虚构事实、资历或使用体验；交付前会进行人工核对。\n\n"
                f"预计用时：{'当天' if job.estimatedMinutes <= 60 else '24–48 小时内'}。开始前请提供源材料、目标受众和参考样例。")
    return (f"Hello, I can help with “{job.title}”.\n\nI will deliver:\n{deliverables}\n\n"
            "I will work from your source materials, preserve the facts, and review the result before delivery. "
            "I will not claim experience or results I cannot verify.\n\n"
            f"Estimated turnaround: {'same day' if job.estimatedMinutes <= 60 else 'within 24–48 hours'}. "
            "Please share the source materials, audience, and preferred examples.")


def build_delivery_plan(job: Job) -> list[str]:
    category_steps = {
        "copywriting": ["Confirm audience, claims, and banned wording.", "Draft variations from supplied facts.", "Review for unsupported claims and tone."],
        "ppt": ["Outline each slide from supplied notes.", "Apply a consistent layout and hierarchy.", "Export PPTX/PDF and visually review."],
        "video_script": ["Create hook, scene, dialogue, and CTA options.", "Check claims and third-party material rights."],
        "image": ["Confirm original/non-person subject and usage rights.", "Prepare prompts and generate options.", "Human-review images for likeness and IP issues."],
        "technical_writing": ["Map supplied source material to a document outline.", "Draft examples without inventing API behavior.", "Validate terminology and examples."],
    }.get(job.category, [])
    return category_steps + [
        "Confirm delivery format, revision limit, and deadline.",
        "Create the first draft with GPT/Codex assistance.",
        "Perform human fact, quality, copyright, and platform-rule review.",
        "Package the requested files and a concise delivery note.",
    ]
