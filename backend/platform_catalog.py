"""Curated marketplace directory; informational and account-free by design."""

from backend.models import PlatformProfile


def platform_catalog() -> list[PlatformProfile]:
    return [
        PlatformProfile(name="Upwork", region="全球", url="https://www.upwork.com/nx/search/jobs/", workModel="项目竞标 / 固定价或时薪", intakeMode="官方 API 授权后只读检索；否则浏览器只读采集或导入", bestFor=["技术文档", "脚本", "自动化小工具", "PPT"], suitability="优先", note="客户与预算信息相对完整；官方 API 需要账号和 OAuth 授权。"),
        PlatformProfile(name="Freelancer", region="全球", url="https://www.freelancer.com/jobs/", workModel="项目竞标", intakeMode="官方 API 授权后只读检索；否则浏览器只读采集或导入", bestFor=["文案", "数据整理", "简单开发", "设计素材"], suitability="优先", note="适合固定范围的小项目；只保留草稿，不自动出价。"),
        PlatformProfile(name="Fiverr", region="全球", url="https://www.fiverr.com/", workModel="上架标准化服务 / 项目邀约", intakeMode="CSV、粘贴或浏览器只读采集", bestFor=["标准化 PPT", "短视频脚本", "文案", "图片素材"], suitability="优先", note="更适合把可复用交付物包装成标准服务，而不是广泛抓取项目。"),
        PlatformProfile(name="Contra", region="全球", url="https://contra.com/jobs", workModel="项目列表 / 作品集获客", intakeMode="CSV、粘贴或浏览器只读采集", bestFor=["创意交付", "内容", "设计", "独立顾问服务"], suitability="观察", note="适合有清晰作品集的独立服务；先验证所在地区的收款可用性。"),
        PlatformProfile(name="PeoplePerHour", region="英国及全球", url="https://www.peopleperhour.com/", workModel="项目竞标 / 固定报价服务", intakeMode="CSV、粘贴或浏览器只读采集", bestFor=["文案", "设计", "网页小改", "营销素材"], suitability="观察", note="优先选择要求明确、资料齐全且修订次数有限的项目。"),
        PlatformProfile(name="Workana", region="拉美及全球", url="https://www.workana.com/jobs", workModel="项目检索与报价", intakeMode="CSV、粘贴或浏览器只读采集", bestFor=["西语/葡语内容", "设计", "开发", "运营素材"], suitability="观察", note="有明确项目检索和报价流程；需自行确认语言与收款条件。"),
        PlatformProfile(name="猪八戒", region="中国", url="https://www.zbj.com/", workModel="服务店铺 / 需求交易", intakeMode="CSV、粘贴或浏览器只读采集", bestFor=["文案", "设计", "PPT", "网站与小程序素材"], suitability="优先", note="国内服务交易平台；不得绕开站内沟通和交易规则。"),
        PlatformProfile(name="一品威客", region="中国", url="https://www.epwk.com/service/", workModel="服务商店铺 / 众包接单", intakeMode="CSV、粘贴或浏览器只读采集", bestFor=["品牌素材", "文案", "设计", "营销内容"], suitability="优先", note="可建立标准化服务；适合清晰、可复用的交付包。"),
    ]
