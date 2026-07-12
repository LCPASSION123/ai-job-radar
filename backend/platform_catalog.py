"""Curated marketplace directory.

The catalog is intentionally informational.  A platform record never grants an
agent an account, and every listing has an explicit import route instead of an
unofficial scraper.
"""

from backend.models import PlatformProfile, Workspace


def _platform(
    name: str, region: str, url: str, work_model: str, intake: str,
    best_for: list[str], suitability: str, note: str, *, workspace: Workspace,
    access: str = "Read-only import/capture; every external action needs a human confirmation.",
) -> PlatformProfile:
    return PlatformProfile(
        workspace=workspace, name=name, region=region, url=url,
        workModel=work_model, intakeMode=intake, bestFor=best_for,
        suitability=suitability, note=note, agentAccess=access,
    )


def general_platform_catalog() -> list[PlatformProfile]:
    """General AI-deliverable marketplaces retained as a separate workspace."""
    import_only = "CSV export, manual paste, or user-clicked read-only DOM capture"
    return [
        _platform("Upwork", "Global", "https://www.upwork.com/nx/search/jobs/", "Project bidding", "Official read-only API after your OAuth authorization; otherwise " + import_only, ["technical writing", "scripts", "small automation", "presentations"], "Priority", "Use only account-authorized official access. Proposals are always manually submitted.", workspace=Workspace.general),
        _platform("Freelancer", "Global", "https://www.freelancer.com/jobs/", "Project bidding", "Official read-only API after your authorization; otherwise " + import_only, ["copy", "data cleanup", "small development", "design assets"], "Priority", "Good for clearly-scoped fixed-price work.", workspace=Workspace.general),
        _platform("Fiverr", "Global", "https://www.fiverr.com/", "Packaged services and requests", import_only, ["standardized presentations", "video scripts", "copywriting", "image assets"], "Priority", "Package repeatable deliverables; no automated client messaging.", workspace=Workspace.general),
        _platform("PeoplePerHour", "UK / Global", "https://www.peopleperhour.com/", "Project bidding and offers", import_only, ["copy", "design", "web fixes", "marketing assets"], "Observe", "Prefer complete source materials and a finite revision limit.", workspace=Workspace.general),
        _platform("Workana", "Latin America / Global", "https://www.workana.com/jobs", "Project search and quotation", import_only, ["content", "design", "development"], "Observe", "Verify language and payout availability yourself.", workspace=Workspace.general),
        _platform("猪八戒", "China", "https://www.zbj.com/", "Service store and requirements marketplace", import_only, ["copywriting", "design", "PPT", "website assets"], "Priority", "Follow on-platform communication and transaction rules.", workspace=Workspace.general),
        _platform("一品威客", "China", "https://www.epwk.com/", "Service provider storefront and crowdsourcing", import_only, ["brand assets", "copywriting", "design", "marketing content"], "Priority", "Suitable for clear, reusable service packages.", workspace=Workspace.general),
        _platform("程序员客栈", "China", "https://www.proginn.com/", "Developer project matching", import_only, ["small development", "documentation", "automation"], "Observe", "Screen scope carefully; do not accept production access through the tool.", workspace=Workspace.general),
        _platform("码市", "China", "https://codemart.com/", "Software project marketplace", import_only, ["software prototypes", "automation", "technical documentation"], "Observe", "Only consider clearly bounded tasks without production deployment.", workspace=Workspace.general),
    ]


def embedded_platform_catalog() -> list[PlatformProfile]:
    """Embedded-specific opportunity sources, kept separate from general jobs.

    Some entries are engineering communities/job boards rather than transaction
    marketplaces.  They are labeled as discovery-only so users do not mistake a
    forum post for a guaranteed contract channel.
    """
    capture = "CSV export, manual paste, or user-clicked read-only DOM capture"
    embedded_access = "Read visible opportunities only. Never post, message, quote, flash hardware, or deploy without human confirmation."
    return [
        _platform("猪八戒·硬件开发", "China", "https://www.zbj.com/", "Hardware/firmware service requirements", capture, ["MCU firmware", "PCB review", "embedded Linux", "technical documentation"], "Priority", "Search with MCU, ESP32, STM32, RTOS, driver, and embedded Linux keywords.", workspace=Workspace.embedded, access=embedded_access),
        _platform("一品威客·硬件开发", "China", "https://www.epwk.com/", "Hardware and engineering service requirements", capture, ["firmware prototypes", "BOM/documentation", "device integration"], "Priority", "Only recommend desk-only deliverables with source files and test fixtures.", workspace=Workspace.embedded, access=embedded_access),
        _platform("程序员客栈·IoT", "China", "https://www.proginn.com/", "Developer project matching", capture, ["IoT backend", "ESP32", "embedded Linux", "device protocol"], "Observe", "Treat firmware tasks as candidates only until hardware access is clarified.", workspace=Workspace.embedded, access=embedded_access),
        _platform("码市·物联网", "China", "https://codemart.com/", "Software project marketplace", capture, ["device protocol", "simulation", "tooling", "documentation"], "Observe", "Favor protocol simulators, tests, docs, and supplied-repo bug fixes.", workspace=Workspace.embedded, access=embedded_access),
        _platform("电子发烧友·工程机会", "China", "https://www.elecfans.com/", "Engineering community / discovery", "Manual paste or user-clicked read-only DOM capture", ["electronics design", "firmware", "technical content"], "Discovery", "Community lead source, not a confirmed transaction marketplace; verify the counterparty and terms manually.", workspace=Workspace.embedded, access=embedded_access),
        _platform("EEWorld·工程机会", "China", "https://www.eeworld.com.cn/", "Engineering community / discovery", "Manual paste or user-clicked read-only DOM capture", ["MCU", "RTOS", "embedded Linux", "driver"], "Discovery", "Use as a lead board only; avoid sharing private source code in public threads.", workspace=Workspace.embedded, access=embedded_access),
        _platform("21IC·工程机会", "China", "https://www.21ic.com/", "Engineering community / discovery", "Manual paste or user-clicked read-only DOM capture", ["hardware", "firmware", "IoT"], "Discovery", "Use as a lead board only; platform rules and counterparty verification remain manual.", workspace=Workspace.embedded, access=embedded_access),
        _platform("Upwork·Embedded Systems", "Global", "https://www.upwork.com/nx/search/jobs/", "Project bidding", "Official read-only API after your OAuth authorization; otherwise " + capture, ["C/C++", "Zephyr", "ESP-IDF", "embedded Linux"], "Priority", "Search only. A human must review every scope and submit any proposal.", workspace=Workspace.embedded, access=embedded_access),
        _platform("Freelancer·Electronics", "Global", "https://www.freelancer.com/jobs/electronics/", "Project bidding", "Official read-only API after your authorization; otherwise " + capture, ["firmware", "Arduino", "PCB documentation", "IoT"], "Priority", "Use imported listings; no automatic quotation or message sending.", workspace=Workspace.embedded, access=embedded_access),
        _platform("Guru·Engineering", "Global", "https://www.guru.com/d/jobs/", "Project marketplace", capture, ["firmware", "electronics", "IoT"], "Observe", "Choose work that can be verified in a simulator or supplied test fixture.", workspace=Workspace.embedded, access=embedded_access),
        _platform("Toptal·Engineering", "Global", "https://www.toptal.com/freelance-jobs", "Curated talent network", "Manual paste of work you are authorized to view", ["senior embedded engineering", "IoT architecture"], "Discovery", "Not an automated source; membership and engagement suitability are platform-controlled.", workspace=Workspace.embedded, access=embedded_access),
    ]


def platform_catalog(workspace: Workspace | None = None) -> list[PlatformProfile]:
    catalogs = {
        Workspace.general: general_platform_catalog(),
        Workspace.embedded: embedded_platform_catalog(),
    }
    if workspace:
        return catalogs[workspace]
    return [*catalogs[Workspace.general], *catalogs[Workspace.embedded]]
