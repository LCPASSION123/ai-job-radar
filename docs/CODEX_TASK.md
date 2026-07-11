# Codex 一次性开发指令

你是资深全栈工程师。请基于当前仓库把 AI Job Radar 从展示版升级为 MVP。不要询问用户，直接实现。

## 产品目标
构建一个合规的接单分析工具，帮助 GPT/Codex 检索接单平台任务，筛选“AI可短时间完成、人工参与低、风险低”的单子，并生成投标草稿和交付流程。

## 硬性边界
1. 不绕过登录、验证码、反爬、付费墙和平台风控。
2. 不自动投标、不自动付款、不自动发送客户消息，除非用户在界面二次确认。
3. 不接违法、虚假评论、论文代写、刷量、冒充真人、非自愿换脸、生产支付修复等高风险单。
4. API Key、Cookie、Token全部走本地加密密钥库或.env，不写入仓库。

## 技术栈
- Frontend: React + TypeScript + Vite
- Backend: FastAPI + Pydantic + SQLite
- Scheduler: APScheduler
- LLM Provider: OpenAI-compatible adapter，支持 GPT 和 Gemini API Key
- Connector Strategy: official API > user export CSV > browser extension DOM capture > manual paste

## 必须实现
1. 平台连接管理：Upwork、Freelancer、Fiverr、PeoplePerHour、猪八戒、一品威客、百度众测、京东众智。
2. 连接器抽象：`search_jobs(query, filters)`、`normalize_job(raw)`、`health_check()`。
3. Upwork和Freelancer按官方API预留真实实现；没有官方稳定API的平台只做CSV/手动导入/浏览器扩展入口。
4. Job评分器：AI自主度、预计时长、人工参与、风险、预算、客户信誉、交付物清晰度。
5. 推荐队列：建议接/谨慎/不接，并解释原因。
6. 投标草稿生成：按平台语言、预算、交付物生成，不承诺虚假能力。
7. 交付流程生成：文案、PPT、短视频脚本、AI图像、技术写作分别模板化。
8. 审计日志：记录每次检索、评分、导出、确认操作。
9. 导出：CSV/JSON/Markdown日报。
10. 测试：评分器单元测试、连接器契约测试、导入解析测试。

## 最终交付
- 可运行MVP
- README中文说明
- `.env.example`
- OpenAPI schema，用于接入GPT Actions
- MCP server说明，用于Codex/ChatGPT插件化接入
- 不要提交真实凭据。
