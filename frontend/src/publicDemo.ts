export type DemoWorkspace = "general" | "embedded";

export const publicDemo = {
  general: {
    jobs: [
      { id: "public-copy-1", workspace: "general", platform: "Upwork", title: "根据已有资料润色英文品牌介绍", category: "copywriting", budget: "40 USD fixed", url: "https://www.upwork.com/nx/search/jobs/", description: "公开体验数据：客户已提供初稿，仅需在不改变事实的前提下润色英文文案。", deliverables: ["润色后的文案", "修改说明", "一次轻量修改"], estimatedMinutes: 60, score: 91, verdict: "recommend", reason: "资料齐全、交付边界清晰，适合 AI 辅助完成后人工复核。", proposalDraft: "您好，我可以基于您提供的初稿进行英文润色，并保留原有事实与品牌语气。交付前会进行人工校对。", deliveryPlan: ["确认语气与禁用表述。", "完成润色并标注主要修改。", "人工复核事实与语言质量。"], scoreBreakdown: { aiAutonomy: 94, timeFit: 94, manualEffort: 100, risk: 100, budgetFit: 90, clientReputation: 80, deliverableClarity: 100 } },
      { id: "public-ppt-2", workspace: "general", platform: "Fiverr", title: "把会议笔记整理成 10 页汇报 PPT", category: "ppt", budget: "60 USD fixed", url: "https://www.fiverr.com/", description: "公开体验数据：提供完整会议笔记与版式参考，要求生成简洁的内部汇报。", deliverables: ["PPTX", "PDF 预览", "讲稿要点"], estimatedMinutes: 100, score: 84, verdict: "recommend", reason: "内容来源明确，适合模板化排版和人工视觉复核。", proposalDraft: "您好，我可以根据会议笔记整理清晰的 10 页汇报，并提供 PPTX 与 PDF 预览。", deliveryPlan: ["整理页面结构。", "套用统一版式。", "人工检查排版和信息准确性。"], scoreBreakdown: { aiAutonomy: 86, timeFit: 80, manualEffort: 80, risk: 100, budgetFit: 78, clientReputation: 70, deliverableClarity: 90 } },
    ],
    platforms: [
      { workspace: "general", name: "Upwork", region: "全球", url: "https://www.upwork.com/nx/search/jobs/", workModel: "项目竞标", intakeMode: "本地导入或只读采集", bestFor: ["技术写作", "自动化", "PPT"], suitability: "优先", note: "公开版仅展示目录；请自行登录并核验任务。", agentAccess: "只读" },
      { workspace: "general", name: "Fiverr", region: "全球", url: "https://www.fiverr.com/", workModel: "标准化服务", intakeMode: "本地导入或只读采集", bestFor: ["文案", "脚本", "设计素材"], suitability: "优先", note: "适合可重复的标准化交付。", agentAccess: "只读" },
    ],
  },
  embedded: {
    jobs: [
      { id: "public-esp32-1", workspace: "embedded", platform: "程序员客栈·IoT", title: "ESP32 UART 协议解析：修复帧边界并补充 CRC 测试", category: "embedded_firmware", budget: "300 CNY fixed", url: "https://www.proginn.com/", description: "公开体验数据：已提供源码、ESP-IDF 工具链与 host test 测试向量；不需要真机、烧录或现场服务。", deliverables: ["C/C++ 补丁", "host-side 单元测试", "构建与测试记录"], estimatedMinutes: 90, score: 92, verdict: "recommend", reason: "源码、工具链和离线测试条件齐全，适合桌面环境交付。", proposalDraft: "您好，我可以完成可在桌面环境复现的协议解析补丁，并提供测试记录与真机验证清单。", deliveryPlan: ["复现 host test。", "实现最小化补丁。", "运行测试并输出验证清单。"], scoreBreakdown: { aiAutonomy: 90, timeFit: 85, manualEffort: 100, risk: 100, budgetFit: 95, clientReputation: 80, deliverableClarity: 100, embeddedReadiness: 95 }, embeddedAssessment: { target: "ESP32 / ESP-IDF", scope: "UART 协议解析与 CRC 测试", agentReadiness: 95, blockers: [], recommendedArtifacts: ["补丁与变更说明", "host test 结果", "人工真机验证清单"], sourceFilesProvided: true, toolchainKnown: true, testFixturesProvided: true } },
      { id: "public-zephyr-2", workspace: "embedded", platform: "Upwork·Embedded Systems", title: "根据现有代码编写 Zephyr 传感器驱动接入文档", category: "embedded_documentation", budget: "70 USD fixed", url: "https://www.upwork.com/nx/search/jobs/", description: "公开体验数据：基于已提供仓库撰写 Markdown 接入指南，不虚构硬件测试结果。", deliverables: ["Markdown 接入指南", "配置表", "已知限制说明"], estimatedMinutes: 80, score: 89, verdict: "recommend", reason: "基于已有代码和工具链完成文档，交付范围清晰。", proposalDraft: "您好，我可以根据现有仓库整理 Zephyr 驱动接入文档，并清楚标明未经真机验证的部分。", deliveryPlan: ["梳理代码与配置。", "起草接入文档。", "人工核对术语与示例。"], scoreBreakdown: { aiAutonomy: 93, timeFit: 88, manualEffort: 100, risk: 100, budgetFit: 85, clientReputation: 90, deliverableClarity: 100, embeddedReadiness: 90 }, embeddedAssessment: { target: "Zephyr RTOS", scope: "传感器驱动接入文档", agentReadiness: 90, blockers: [], recommendedArtifacts: ["Markdown 文档", "配置表", "限制说明"], sourceFilesProvided: true, toolchainKnown: true, testFixturesProvided: true } },
    ],
    platforms: [
      { workspace: "embedded", name: "程序员客栈·IoT", region: "中国", url: "https://www.proginn.com/", workModel: "开发项目撮合", intakeMode: "本地导入或只读采集", bestFor: ["ESP32", "嵌入式 Linux", "IoT"], suitability: "观察", note: "优先选择源码、工具链和测试条件明确的任务。", agentAccess: "只读" },
      { workspace: "embedded", name: "Upwork·Embedded Systems", region: "全球", url: "https://www.upwork.com/nx/search/jobs/", workModel: "项目竞标", intakeMode: "本地导入或只读采集", bestFor: ["C/C++", "Zephyr", "ESP-IDF"], suitability: "优先", note: "仅搜索与分析；报价须人工审核和提交。", agentAccess: "只读" },
    ],
  },
} as const;
