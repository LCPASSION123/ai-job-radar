# AI Job Radar

> 已配置好本地一键启动和 Codex MCP。请先看 [快速使用说明](docs/QUICKSTART.md)。

本机运行的 AI 接单机会雷达。它将你**有权查看**的任务（CSV/JSON、手动粘贴或浏览器扩展读取当前可见页）放进本地 SQLite，按可解释规则筛选“范围小、AI 自主度高、低风险、约两小时内可交付”的候选，并生成投标草稿和交付计划。

它不是自动接单机器人：不登录平台、不保存 Cookie/密码、不绕过验证码/反爬、不自动投标、发消息、签约、付款或交付。任何对外动作都必须由你在平台内复核并亲自确认。没有平台能保证“每天稳定 ¥50”；本工具只帮你缩短发现、评估和准备草稿的时间。

## 最快启动

需要 Python 3.11+、Node.js 20+。

```powershell
Copy-Item .env.example .env
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn backend.main:app --reload --port 8000
```

另开一个终端：

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

打开 `http://localhost:5173`。后端 API 文档在 `http://127.0.0.1:8000/docs`，健康检查为 `http://127.0.0.1:8000/health`。

## 使用流程

1. 在页面的“平台目录”打开目标平台并自行注册、登录和搜索。
2. 将单条任务详情粘贴进“手动粘贴任务”，或导入 CSV/JSON；也可安装 [`browser_extension/`](browser_extension/README.md) 并在已经打开的任务页点击一次采集。
3. 点击“AI 快速候选（¥50/2h）”，它会使用 `≤120 分钟、预算 ≥¥50、AI 自主度 ≥0.85、人工/风险等级 ≤2` 的严格条件筛选。
4. 查看评分、风险、交付计划和投标草稿。草稿只能人工审核、复制并手动提交。
5. 导出 CSV/JSON/Markdown 日报，记录哪些类型的任务真正有回款后，再逐步调整门槛。

CSV 至少需要 `platform,title,description`。可选：`category,budget,budget_amount,currency,deliverables,constraints,estimated_minutes,ai_autonomy,manual_work_level,risk_level,client_reputation,deliverable_clarity,url`。列表可用 `|`、`;`、换行或 JSON 数组分隔。

```csv
platform,title,description,budget_amount,estimated_minutes,ai_autonomy,manual_work_level,risk_level,deliverables
Manual,Turn notes into a 10-slide deck,Use supplied notes and brand template,100,90,0.9,1,1,"PPTX|PDF"
```

## 平台与接入方式

目录内置 Upwork、Freelancer、Fiverr、Contra、PeoplePerHour、Workana、猪八戒、一品威客。优先考虑标准化的 PPT、脚本、技术写作、信息整理、基于用户资料的轻量自动化等任务；排除虚假评价、代写、冒充、深度伪造、支付生产环境、赌博和成人内容。

- Upwork / Freelancer：仅为官方 API 授权预留适配点；没有你的独立授权时使用导入或只读采集。
- 其他平台：CSV、手动粘贴、或用户点击触发的只读 DOM Capture。
- 浏览器扩展不使用全站权限，只在点击后读取当前标签页可见文本，且只允许发送到 `localhost`。

各平台收款条件、费率、地域限制、服务规则会变化，请在注册和报价前自行核验；不要把账号、密码、Cookie 或 Token 提供给本项目或 MCP。

严格候选的金额门槛只用于初筛：已识别的美元、欧元、英镑会按保守的固定下限换算为人民币，未识别币种或未注明预算的任务不会进入该队列。报价前应以平台页面的实际币种和到手金额为准。

## 给 Codex / GPT 的 MCP 接入

项目已包含运行中的 stdio MCP bridge，而非仅文档预留。先启动后端，再在支持 MCP 的客户端中添加：

```json
{
  "mcpServers": {
    "ai-job-radar": {
      "command": "D:\\AI\\ai_job_radar_final\\.venv\\Scripts\\python.exe",
      "args": ["-m", "backend.mcp_server"],
      "cwd": "D:\\AI\\ai_job_radar_final",
      "env": { "AI_JOB_RADAR_API_URL": "http://127.0.0.1:8000" }
    }
  }
}
```

可用工具：`list_platforms`、`search_jobs`、`recommend_ai_deliverable_jobs`、`get_job`、`generate_proposal`、`recent_audit_events`。都只读取/分析本地数据，绝不包含平台操作。详见 [docs/MCP.md](docs/MCP.md)。面向 GPT Actions 的静态 OpenAPI 文件在 [backend/openapi_action_schema.json](backend/openapi_action_schema.json)。

## 测试与构建

```powershell
python -m pytest -q
cd frontend
npm.cmd run build
```

测试覆盖评分、连接器契约、导入解析和严格候选筛选。`.env.example` 仅是空占位；默认 `LLM_PROVIDER=local`，无需任何真实 API Key。
