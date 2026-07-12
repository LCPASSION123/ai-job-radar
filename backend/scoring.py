from __future__ import annotations

import re

from backend.models import EmbeddedAssessment, EmbeddedTargetProfile, Job, ScoreBreakdown, ScoredJob, TargetProfile, Verdict, Workspace

HIGH_AUTONOMY_CATEGORIES = {"copywriting", "video_script", "ppt", "technical_writing", "image"}
REJECT_KEYWORDS = {
    "fake review", "review manipulation", "刷评", "刷量", "论文代写", "代写作业",
    "deepfake", "换脸", "impersonat", "production payment", "生产支付", "stripe production",
    "gambling", "博彩", "adult content",
}

EMBEDDED_DESK_ONLY = {
    "unit test", "host test", "simulation", "simulator", "mock", "documentation", "readme",
    "protocol parser", "code review", "static analysis", "build fix", "ci", "zephyr", "qemu",
    "仿真", "模拟", "单元测试", "协议解析", "代码审查", "文档", "静态分析", "编译修复",
}
EMBEDDED_HARDWARE_BLOCKERS = {
    "on-site", "onsite", "travel", "solder", "scope measurement", "logic analyzer", "bring-up",
    "flash device", "production flash", "factory", "physical prototype", "ship hardware", "现场", "焊接",
    "示波器", "逻辑分析仪", "板卡调试", "量产烧录", "工厂", "寄送硬件", "实物样机",
}
EMBEDDED_SAFETY_KEYWORDS = {
    "medical device", "automotive safety", "brake", "battery management", "high voltage", "medical",
    "医疗器械", "汽车安全", "刹车", "电池管理", "高压", "安全关键",
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


def assess_embedded_job(job: Job) -> EmbeddedAssessment:
    """Assess whether an embedded task is desk-only and reproducible.

    This deliberately gives no credit for a task which sounds easy but requires
    a board, lab equipment, production flashing, or safety-critical validation.
    """
    facts = job.embedded
    blob = " ".join([job.title, job.description, *job.constraints, *job.deliverables]).lower()
    contains = lambda words: any(word in blob for word in words)
    hardware_required = bool(facts.get("hardwareAccessRequired")) or contains(EMBEDDED_HARDWARE_BLOCKERS)
    physical_delivery = bool(facts.get("physicalDeliveryRequired")) or any(word in blob for word in {"ship", "寄送", "deliver board", "交付板卡"})
    on_device_language = any(word in blob for word in {"on device", "on-device"}) and not any(word in blob for word in {"no on-device", "no on device", "无需真机", "不需要真机"})
    on_device = bool(facts.get("onDeviceTestingRequired")) or on_device_language or any(word in blob for word in {"真机", "实机", "板上测试"})
    production = bool(facts.get("productionFlashOrDeploy")) or any(word in blob for word in {"production flash", "量产烧录", "deploy to fleet", "生产部署"})
    safety = bool(facts.get("safetyCritical")) or contains(EMBEDDED_SAFETY_KEYWORDS)
    source = bool(facts.get("sourceFilesProvided")) or any(word in blob for word in {"source code provided", "repo provided", "提供源码", "提供仓库"})
    toolchain = bool(facts.get("toolchainKnown")) or any(word in blob for word in {"cmake", "platformio", "esp-idf", "zephyr", "gcc", "toolchain"})
    fixtures = bool(facts.get("testFixturesProvided")) or contains(EMBEDDED_DESK_ONLY)
    blockers: list[str] = []
    if hardware_required: blockers.append("Requires physical hardware or lab access.")
    if physical_delivery: blockers.append("Requires shipping or a physical device deliverable.")
    if on_device: blockers.append("Requires on-device verification that an agent cannot perform.")
    if production: blockers.append("Requests production flashing or deployment.")
    if safety: blockers.append("Safety-critical domain requires a qualified human validation process.")
    if not source: blockers.append("Source files or an equivalent reproducible input are not confirmed.")
    if not toolchain: blockers.append("Build toolchain is not confirmed.")
    readiness = 100
    readiness -= 40 if hardware_required else 0
    readiness -= 25 if physical_delivery else 0
    readiness -= 30 if on_device else 0
    readiness -= 40 if production else 0
    readiness -= 35 if safety else 0
    readiness -= 18 if not source else 0
    readiness -= 12 if not toolchain else 0
    readiness -= 8 if not fixtures else 0
    if contains(EMBEDDED_DESK_ONLY): readiness += 8
    readiness = max(0, min(100, readiness))
    artifacts = ["Patch/diff with concise changelog", "Build command and reproducible test notes"]
    if fixtures or contains(EMBEDDED_DESK_ONLY): artifacts.append("Host-side/unit-test or simulator result")
    if not blockers: artifacts.append("Human review checklist for target-hardware verification")
    return EmbeddedAssessment(
        target=str(facts.get("target") or "embedded target"), scope=str(facts.get("scope") or "firmware / protocol / tooling"),
        sourceFilesProvided=source, toolchainKnown=toolchain, testFixturesProvided=fixtures,
        hardwareAccessRequired=hardware_required, physicalDeliveryRequired=physical_delivery,
        onDeviceTestingRequired=on_device, productionFlashOrDeploy=production, safetyCritical=safety,
        agentReadiness=readiness, blockers=blockers, recommendedArtifacts=artifacts,
    )


def score_job(job: Job) -> ScoredJob:
    """Score a job deterministically so recommendations remain explainable and testable."""
    assessment = assess_embedded_job(job) if job.workspace == Workspace.embedded else None
    breakdown = ScoreBreakdown(
        aiAutonomy=round(job.aiAutonomy * 100),
        timeFit=max(0, min(100, round(100 - max(job.estimatedMinutes - 30, 0) * 0.55))),
        manualEffort=round((6 - job.manualWorkLevel) / 5 * 100),
        risk=round((6 - job.riskLevel) / 5 * 100),
        budgetFit=_budget_score(job),
        clientReputation=round(job.clientReputation / 5 * 100),
        deliverableClarity=round(job.deliverableClarity / 5 * 100),
        embeddedReadiness=assessment.agentReadiness if assessment else None,
    )

    if is_high_risk(job):
        score, verdict = min(25, breakdown.aiAutonomy), Verdict.reject
        reason = "Rejected: the request contains a prohibited or high-risk pattern. Do not automate or accept it."
    elif assessment and (assessment.hardwareAccessRequired or assessment.physicalDeliveryRequired or assessment.onDeviceTestingRequired or assessment.productionFlashOrDeploy or assessment.safetyCritical):
        score, verdict = min(45, round((breakdown.aiAutonomy + assessment.agentReadiness) / 2)), Verdict.reject
        reason = "Not recommended: this embedded scope needs physical hardware, device validation, production deployment, or safety-critical sign-off."
    else:
        score = round(
            breakdown.aiAutonomy * 0.26
            + breakdown.timeFit * 0.16
            + breakdown.manualEffort * 0.13
            + breakdown.risk * 0.18
            + breakdown.budgetFit * 0.08
            + breakdown.clientReputation * 0.08
            + breakdown.deliverableClarity * 0.11
            + (assessment.agentReadiness * 0.15 if assessment else 0)
            + (4 if job.category in HIGH_AUTONOMY_CATEGORIES else 0)
        )
        score = max(0, min(100, score))
        threshold = 78 if assessment else 75
        if score >= threshold and job.estimatedMinutes <= 120 and job.riskLevel <= 2 and job.manualWorkLevel <= 2 and (not assessment or assessment.agentReadiness >= 80):
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
        scoreBreakdown=breakdown, proposalDraft=build_proposal(job), deliveryPlan=build_delivery_plan(job), embeddedAssessment=assessment,
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


def fits_embedded_target_profile(job: Job, profile: EmbeddedTargetProfile) -> bool:
    if job.workspace != Workspace.embedded or not fits_target_profile(job, profile):
        return False
    assessment = assess_embedded_job(job)
    no_physical_work = not any((assessment.hardwareAccessRequired, assessment.physicalDeliveryRequired, assessment.onDeviceTestingRequired, assessment.productionFlashOrDeploy, assessment.safetyCritical))
    return no_physical_work and assessment.agentReadiness >= profile.minimumAgentReadiness


def build_proposal(job: Job, language: str = "auto") -> str:
    wants_zh = language == "zh" or (language == "auto" and bool(re.search(r"[\u4e00-\u9fff]", job.description)))
    deliverables = "\n".join(f"- {item}" for item in job.deliverables) or "- A scoped first draft\n- One light revision"
    if job.workspace == Workspace.embedded:
        assessment = assess_embedded_job(job)
        boundaries = "I can prepare a desk-only patch, build/test notes, and a verification checklist. I cannot claim on-device, production, safety, or physical-hardware validation."
        if wants_zh:
            return (f"您好，我可以先处理「{job.title}」中可在桌面环境复现的部分。\n\n交付范围：\n{deliverables}\n\n"
                    "我会基于您提供的源码、构建方式和测试样例完成修改，并附上 diff、构建命令和测试记录。"
                    "不承诺真机测试、现场调试、量产烧录、物理交付或安全认证。\n\n"
                    f"开始前请确认：目标平台（{assessment.target}）、源码/仓库、工具链、可复现测试，以及验收边界。")
        return (f"Hello, I can handle the desk-reproducible portion of “{job.title}”.\n\nDeliverables:\n{deliverables}\n\n"
                f"{boundaries}\n\nBefore starting, please confirm the target, source/repository, toolchain, reproducible test fixture, and acceptance boundary.")
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
    if job.workspace == Workspace.embedded:
        assessment = assess_embedded_job(job)
        return [
            "Confirm target MCU/SoC, SDK version, toolchain, source access, and a reproducible local test command.",
            "Reproduce the issue in a host-side test, simulator, mock transport, or provided fixture.",
            "Implement a minimal patch with comments and a focused diff.",
            "Run static checks plus the supplied host/simulation test and record commands/results.",
            "Package patch, changelog, limitations, and a human target-hardware verification checklist.",
            *( ["Stop before physical-hardware, production, or safety validation; these are explicitly outside agent delivery."] if assessment.blockers else [] ),
        ]
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
