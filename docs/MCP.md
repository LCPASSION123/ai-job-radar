# AI Job Radar MCP

`backend.mcp_server` 是可运行的 stdio MCP server。它调用同机 FastAPI 服务，仅暴露本地数据的读取、分析、草稿和审计能力。

## 启动顺序

先启动 API：

```powershell
python -m uvicorn backend.main:app --port 8000
```

然后在 Codex/其他 MCP 客户端的 MCP 配置中注册：

```json
{
  "mcpServers": {
    "ai-job-radar": {
      "command": "python",
      "args": ["-m", "backend.mcp_server"],
      "cwd": "D:/AI/ai_job_radar_final",
      "env": { "AI_JOB_RADAR_API_URL": "http://127.0.0.1:8000" }
    }
  }
}
```

如果客户端没有使用该虚拟环境，请将 `command` 改为 `.venv` 中的 Python 绝对路径。

## 工具

| Tool | 用途 |
|---|---|
| `list_platforms` | 读取内置接单平台目录与合规导入路线 |
| `search_jobs` | 搜索和评分已导入的任务 |
| `recommend_ai_deliverable_jobs` | 按时长/预算筛出高 AI 自主、低风险候选 |
| `get_job` | 获取任务评分、草稿与交付计划 |
| `generate_proposal` | 生成仅供人工审核的草稿 |
| `recent_audit_events` | 读取本地审计日志 |

没有登录、Cookie、验证码、投标、私信、合同、支付或交付工具。MCP 的输出只能作为人工判断和手动操作的辅助，不得用于绕过平台规则。
