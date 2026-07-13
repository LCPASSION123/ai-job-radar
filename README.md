# AI Job Radar

> 已配置好本地一键启动和 Codex MCP。请先看 [快速使用说明](docs/QUICKSTART.md)。

本机运行的 AI 接单机会雷达。它将你**有权查看**的任务（CSV/JSON、手动粘贴或浏览器扩展读取当前可见页）放进本地 SQLite，按可解释规则筛选“范围小、AI 自主度高、低风险、约两小时内可交付”的候选，并生成投标草稿和交付计划。

界面、投标草稿和 MCP/API 的投标草稿默认使用中文；如需英文，可在 API/MCP 的 `language` 参数中显式传入 `en`。

它不是自动接单机器人：不登录平台、不保存 Cookie/密码、不绕过验证码/反爬、不自动投标、发消息、签约、付款或交付。任何对外动作都必须由你在平台内复核并亲自确认。没有平台能保证“每天稳定 ¥50”；本工具只帮你缩短发现、评估和准备草稿的时间。

## 新增：嵌入式接单雷达（独立工作区）

前端顶部有两个完全分开的工作区：原有的“AI 接单雷达”和新增的“嵌入式接单雷达”。嵌入式工作区内置国内优先的机会目录（猪八戒·硬件开发、一品威客·硬件开发、程序员客栈·IoT、码市·物联网，以及电子发烧友、EEWorld、21IC 等工程线索来源）和海外目录（Upwork、Freelancer、Guru、Toptal）。工程社区被明确标记为“线索”，并不被表述为保证成交的平台。

嵌入式候选必须同时满足：

1. 已确认源码/仓库、目标与工具链，且能在桌面环境复现。
2. 有 host test、模拟器、mock 或其他可离线验证条件。
3. 没有真机调试、焊接、现场服务、物理交付、量产烧录、生产部署或安全关键验证。

点击“桌面交付候选（无硬件）”后，系统只推荐满足上述条件的任务，并给出 Agent readiness、阻断项、建议交付包和真机验证清单。样例数据展示了可接的 ESP32 协议解析/单元测试、Zephyr 文档任务，以及会被拒绝的现场电机调试和 BMS 量产烧录任务。

嵌入式任务的交付草稿会明确承诺边界：只能交付补丁、构建/测试记录和验证清单，不能声称已进行真机、生产或安全验证。

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

### 一次配置，以后直接打开网页

双击仓库根目录的 `Install-AI-Job-Radar-AutoStart.cmd` 一次。它会为当前 Windows 用户配置“登录后自动启动”（优先使用任务计划程序；若电脑策略禁止，则自动使用当前用户的 Startup 文件夹），并立即启动仪表盘。之后每次登录 Windows，工具会在后台自动启动；直接打开 `http://localhost:5173/` 就能看到内容，不需要再开终端或执行启动命令。

它只启动本机 `127.0.0.1` 上的前后端，不会登录任何接单平台、读取浏览器 Cookie 或向外发送账号信息。

## 使用流程

1. 在页面的“平台目录”打开目标平台并自行注册、登录和搜索。
2. 将单条任务详情粘贴进“手动粘贴任务”，或导入 CSV/JSON；也可安装 [`browser_extension/`](browser_extension/README.md) 并在已经打开的任务页点击一次采集。
3. 选择交付时间和条件后，点击“生成候选队列”。
4. 查看评分、风险、交付计划和投标草稿。草稿只能人工审核、复制并手动提交。
5. 导出 CSV/JSON/Markdown 日报，记录哪些类型的任务真正有回款后，再逐步调整门槛。

现在页面还提供 `2 小时 / 12 小时 / 24 小时 / 一周 / 不限` 五档交付时间。默认是**宽松条件**（预算 ≥¥30、较高 AI 自主度、人工/风险等级 ≤3），以减少漏掉的小单；勾选“严格条件”即可回到原先的 `¥50 / 2 小时 / AI 自主度 0.85 / 人工与风险 ≤2` 筛选。嵌入式工作区无论选择哪种条件，仍会排除真机、现场、量产和安全关键工作。

筛选栏还支持五档发布时间（24 小时、3 天、7 天、30 天、不限）、单子类型和自定义标签。多个标签用英文逗号分隔，任务须同时命中这些标签；匹配结果每页显示 8 条，可通过上一页/下一页翻阅全部符合项。通用与嵌入式工作区均支持这些筛选。

CSV 至少需要 `platform,title,description`。可选：`category,budget,budget_amount,currency,deliverables,constraints,estimated_minutes,ai_autonomy,manual_work_level,risk_level,client_reputation,deliverable_clarity,url`。列表可用 `|`、`;`、换行或 JSON 数组分隔。

```csv
platform,title,description,budget_amount,estimated_minutes,ai_autonomy,manual_work_level,risk_level,deliverables
Manual,Turn notes into a 10-slide deck,Use supplied notes and brand template,100,90,0.9,1,1,"PPTX|PDF"
```

## 平台与接入方式

通用工作区目录内置 Upwork、Freelancer、Fiverr、PeoplePerHour、Workana、猪八戒、一品威客、程序员客栈、码市。嵌入式目录见上节。优先考虑标准化的 PPT、脚本、技术写作、信息整理、基于用户资料的轻量自动化等任务；排除虚假评价、代写、冒充、深度伪造、支付生产环境、赌博和成人内容。

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

可用工具：`list_platforms`、`search_jobs`、`recommend_ai_deliverable_jobs`、`search_embedded_jobs`、`recommend_embedded_desk_only_jobs`、`get_job`、`generate_proposal`、`recent_audit_events`。都只读取/分析本地数据，绝不包含平台操作或硬件操作。详见 [docs/MCP.md](docs/MCP.md)。面向 GPT Actions 的静态 OpenAPI 文件在 [backend/openapi_action_schema.json](backend/openapi_action_schema.json)。

## 测试与构建

```powershell
python -m pytest -q
cd frontend
npm.cmd run build
```

测试覆盖评分、连接器契约、导入解析和严格候选筛选。`.env.example` 仅是空占位；默认 `LLM_PROVIDER=local`，无需任何真实 API Key。
