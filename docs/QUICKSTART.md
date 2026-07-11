# AI Job Radar：直接使用

## 每次使用

双击仓库根目录的 `Start-AI-Job-Radar.cmd`。它会自动启动 API 和网页、打开 `http://localhost:5173/`，且不受 PowerShell 执行策略影响。需要关闭时双击 `Stop-AI-Job-Radar.cmd`。

首次使用前只需安装一次依赖：

```powershell
cd D:\AI\ai_job_radar_final
Copy-Item .env.example .env
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
cd frontend
npm.cmd install
```

## 搜索真实任务（以 PeoplePerHour 为例）

1. 在网页的“平台目录”打开 PeoplePerHour；在浏览器中自行注册、登录和搜索。
2. 找到一个任务详情页后，复制标题、预算、要求和交付物，粘贴进 Radar 的“手动粘贴任务”。也可以用浏览器扩展采集当前可见页面，或导入 CSV/JSON。
3. 回到 Radar，点击“AI 快速候选（¥50/2h）”。
4. 打开候选任务，查看评分、风险、交付计划和投标草稿。
5. 只有你亲自复核内容、价格与平台规则后，才在平台内手动提交。

导入后，在 Codex 中可以直接这样说：

```text
通过 ai_job_radar MCP 查找 PeoplePerHour 的高分任务：两小时内可交付、预算约 ¥50 以上、AI 自主度高、低风险。对每项给出接单理由、风险点、投标草稿和交付清单。不要自动投标、发送消息、签约、付款或交付。
```

## Codex MCP 已配置

仓库中的 `.codex/config.toml` 已注册本地 `ai_job_radar` MCP。启动 Radar 后，新开一个 Codex task（或重启 Codex）即可发现这些工具：`list_platforms`、`search_jobs`、`recommend_ai_deliverable_jobs`、`get_job`、`generate_proposal`、`recent_audit_events`。

它们只访问本地 Radar 数据库；不保存平台 Cookie、密码或 Token，也不会代表你在任意平台执行外部操作。
