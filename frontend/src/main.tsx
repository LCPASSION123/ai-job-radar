import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

const API = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
type Workspace = "general" | "embedded";
type Verdict = "recommend" | "caution" | "reject";
type Assessment = { target: string; scope: string; agentReadiness: number; blockers: string[]; recommendedArtifacts: string[]; sourceFilesProvided: boolean; toolchainKnown: boolean; testFixturesProvided: boolean };
type Job = { id: string; workspace: Workspace; platform: string; title: string; category: string; budget?: string; description: string; deliverables: string[]; estimatedMinutes: number; score: number; verdict: Verdict; reason: string; proposalDraft: string; deliveryPlan: string[]; scoreBreakdown: Record<string, number | null>; embeddedAssessment?: Assessment | null };
type Connector = { platform: string; workspace: Workspace; mode: string; ok: boolean; message: string; supportsCsv: boolean; supportsPaste: boolean; supportsDomCapture: boolean };
type Platform = { workspace: Workspace; name: string; region: string; url: string; workModel: string; intakeMode: string; bestFor: string[]; suitability: string; note: string; agentAccess: string };

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API}${path}`, init);
  if (!response.ok) throw new Error((await response.json().catch(() => ({ detail: response.statusText }))).detail);
  return response.json() as Promise<T>;
}

function workspaceTitle(workspace: Workspace) { return workspace === "embedded" ? "嵌入式接单雷达" : "AI 接单雷达"; }

function App() {
  const [workspace, setWorkspace] = useState<Workspace>("general");
  const [jobs, setJobs] = useState<Job[]>([]);
  const [connectors, setConnectors] = useState<Connector[]>([]);
  const [platforms, setPlatforms] = useState<Platform[]>([]);
  const [selected, setSelected] = useState<Job | null>(null);
  const [query, setQuery] = useState("");
  const [platform, setPlatform] = useState("");
  const [onlyQuick, setOnlyQuick] = useState(true);
  const [status, setStatus] = useState("正在加载本地雷达数据…");
  const [paste, setPaste] = useState("");

  const load = async (nextWorkspace = workspace) => {
    try {
      const params = new URLSearchParams({ workspace: nextWorkspace });
      const [result, sourceConnectors, sourcePlatforms] = await Promise.all([
        request<Job[]>("/jobs/search", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ workspace: nextWorkspace, query, platforms: platform ? [platform] : [], max_results: 200 }) }),
        request<Connector[]>(`/connectors?${params}`), request<Platform[]>(`/platforms?${params}`),
      ]);
      setJobs(result); setSelected(result[0] || null); setConnectors(sourceConnectors); setPlatforms(sourcePlatforms);
      setStatus(`已评分 ${result.length} 条${nextWorkspace === "embedded" ? "嵌入式" : "通用"}任务。系统只分析本地导入数据，不代表你登录、报价或接单。`);
    } catch (error) { setStatus(error instanceof Error ? error.message : "无法连接后端"); }
  };

  useEffect(() => { void load(); }, [workspace]);

  const switchWorkspace = (next: Workspace) => {
    setWorkspace(next); setQuery(""); setPlatform(""); setOnlyQuick(true); setSelected(null);
  };

  const loadTarget = async () => {
    try {
      const endpoint = workspace === "embedded" ? "/embedded/jobs/recommendations" : "/jobs/recommendations";
      const profile = workspace === "embedded"
        ? { workspace, maxMinutes: 120, minimumBudgetCny: 50, minimumAiAutonomy: 0.85, maximumManualWorkLevel: 2, maximumRiskLevel: 2, minimumAgentReadiness: 80, allowSimulationOnly: true }
        : { workspace, maxMinutes: 120, minimumBudgetCny: 50, minimumAiAutonomy: 0.85, maximumManualWorkLevel: 2, maximumRiskLevel: 2 };
      const result = await request<Job[]>(endpoint, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(profile) });
      setJobs(result); setSelected(result[0] || null); setOnlyQuick(false);
      setStatus(workspace === "embedded" ? `嵌入式桌面交付候选：${result.length} 条。已排除真机、现场、量产和安全关键工作。` : `严格候选队列：${result.length} 条（≤2 小时、≥¥50、高 AI 自主、低风险）。`);
    } catch (error) { setStatus(error instanceof Error ? error.message : "无法生成候选队列"); }
  };

  const importFile = async (file: File) => {
    const data = new FormData(); data.append("file", file);
    await request(`/jobs/import/${file.name.toLowerCase().endsWith(".csv") ? "csv" : "json"}`, { method: "POST", body: data });
    await load();
  };
  const importPaste = async () => {
    if (paste.trim().length < 10) return setStatus("请粘贴至少 10 个字符的任务详情。");
    await request("/jobs/paste", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ workspace, platform: platform || (workspace === "embedded" ? "嵌入式手动粘贴" : "手动粘贴"), text: paste }) });
    setPaste(""); await load();
  };
  const visible = useMemo(() => onlyQuick ? jobs.filter(job => job.estimatedMinutes <= 120) : jobs, [jobs, onlyQuick]);
  const counts = { recommend: jobs.filter(j => j.verdict === "recommend").length, caution: jobs.filter(j => j.verdict === "caution").length, reject: jobs.filter(j => j.verdict === "reject").length };

  return <main className={`radar ${workspace}`}>
    <header>
      <div><p className="eyebrow">LOCAL · EXPLAINABLE · HUMAN-IN-THE-LOOP</p><h1>{workspaceTitle(workspace)}</h1><p>{workspace === "embedded" ? "独立的嵌入式机会工作区：筛选可在桌面环境完成的固件补丁、协议解析、仿真、测试与文档；自动排除真机调试、现场服务、量产烧录和安全关键验证。" : "将你有权查看的任务导入本机后，筛出 AI 可短时间完成、人工参与低、风险低的候选；只生成草稿与交付计划。"}</p></div>
      <button onClick={() => void load()}>重新评分</button>
    </header>
    <nav className="workspace-tabs" aria-label="工作区"><button className={workspace === "general" ? "active" : ""} onClick={() => switchWorkspace("general")}>AI 接单雷达</button><button className={workspace === "embedded" ? "active" : ""} onClick={() => switchWorkspace("embedded")}>嵌入式接单雷达</button></nav>
    <p className="status">{status}</p>
    <section className="metrics"><Metric label="已扫描" value={jobs.length}/><Metric label="建议接" value={counts.recommend} tone="good"/><Metric label="谨慎" value={counts.caution} tone="warn"/><Metric label="不接" value={counts.reject} tone="bad"/></section>
    <section className="toolbar"><input aria-label="关键词" value={query} onChange={e => setQuery(e.target.value)} placeholder={workspace === "embedded" ? "关键词，如 ESP32、STM32、Zephyr、RTOS、协议、仿真" : "关键词，如 PPT、脚本、API docs"}/><select value={platform} onChange={e => setPlatform(e.target.value)}><option value="">全部平台</option>{platforms.map(item => <option key={item.name}>{item.name}</option>)}</select><label><input type="checkbox" checked={onlyQuick} onChange={e => setOnlyQuick(e.target.checked)}/> 仅显示 2 小时内可交付</label><button className="secondary" onClick={() => void load()}>搜索</button><button onClick={() => void loadTarget()}>{workspace === "embedded" ? "桌面交付候选（无硬件）" : "AI 快速候选（¥50/2h）"}</button><label className="upload">导入 CSV/JSON<input type="file" accept=".csv,.json" onChange={e => e.target.files?.[0] && void importFile(e.target.files[0])}/></label><a className="secondary export" href={`${API}/exports/markdown`}>导出日报</a></section>
    {workspace === "embedded" && <section className="guardrail"><b>嵌入式交付边界：</b>只推荐已提供源码/工具链/测试条件，且能用 host test、仿真或 mock 验证的工作。真机测试、焊接、现场调试、量产烧录、生产部署、安全认证均不会被推荐。</section>}
    <section className="content"><div className="panel"><h2>推荐队列 <small>{visible.length} 条</small></h2>{visible.map(job => <button className={`job ${selected?.id === job.id ? "active" : ""}`} key={job.id} onClick={() => setSelected(job)}><span><b>{job.title}</b><small>{job.platform} · {job.category} · {job.budget || "预算未注明"} · {job.estimatedMinutes} 分钟</small><em>{job.reason}</em></span><strong className={job.verdict}>{job.score}</strong></button>)}{!visible.length && <p>还没有符合条件的任务。请导入 CSV/JSON、粘贴有权查看的任务详情，或通过只读扩展采集当前可见页面。</p>}</div>
      <aside className="panel details">{selected ? <><p className={`tag ${selected.verdict}`}>{selected.verdict === "recommend" ? "建议接" : selected.verdict === "caution" ? "谨慎" : "不接"} · {selected.score}/100</p><h2>{selected.title}</h2><p>{selected.description}</p>{selected.embeddedAssessment && <EmbeddedPanel assessment={selected.embeddedAssessment}/>}<h3>评分依据</h3><div className="breakdown">{Object.entries(selected.scoreBreakdown).filter(([, value]) => value !== null).map(([key,value]) => <span key={key}>{key}<b>{value}</b></span>)}</div><h3>交付物</h3><ul>{selected.deliverables.map(item => <li key={item}>{item}</li>)}</ul><h3>交付流程</h3><ol>{selected.deliveryPlan.map(item => <li key={item}>{item}</li>)}</ol><h3>投标草稿（必须人工审核并手动提交）</h3><pre>{selected.proposalDraft}</pre></> : <p>选择一个任务查看详情。</p>}</aside></section>
    <section className="panel"><h2>手动粘贴任务</h2><p className="muted">{workspace === "embedded" ? "推荐粘贴目标平台、芯片/SDK、源码与工具链、测试条件、是否需要真机/现场/烧录等信息。" : "粘贴标题、预算、要求和交付物；不要粘贴私人联系方式或敏感资料。"}</p><textarea className="paste" value={paste} onChange={e => setPaste(e.target.value)} placeholder="从你有权查看的任务页复制内容…"/><button onClick={() => void importPaste()}>导入并评分</button></section>
    <section className="panel"><h2>{workspace === "embedded" ? "嵌入式平台与线索目录" : "平台目录"}</h2><p>{workspace === "embedded" ? "“优先”表示适合作为嵌入式机会来源，不代表自动接入或保证成交；“线索”是工程社区/机会板，需要你自行核验对方与条款。" : "没有任何平台能保证稳定收入。优先选择范围小、资料齐全、修订次数有限且预算覆盖时间成本的任务。"}</p><div className="platforms">{platforms.map(item => <article key={item.name}><div><b>{item.name}</b><small>{item.region} · {item.suitability}</small></div><p>{item.workModel}</p><p className="muted">适合：{item.bestFor.join("、")}</p><p className="muted">{item.note}</p><a href={item.url} target="_blank" rel="noreferrer">打开平台（自行登录）</a></article>)}</div></section>
    <section className="panel"><h2>连接管理</h2><p className="muted">所有连接都只读取用户主动导入或采集的可见数据；不会保存账号、Cookie、Token，也不会替你操作平台。</p><div className="connectors">{connectors.map(connector => <article key={connector.platform}><b>{connector.platform}</b><small>{connector.mode}</small><p>{connector.message}</p><span>{connector.supportsCsv ? "CSV " : ""}{connector.supportsDomCapture ? "只读 DOM Capture " : ""}{connector.supportsPaste ? "手动粘贴" : ""}</span></article>)}</div></section>
  </main>;
}

function EmbeddedPanel({ assessment }: { assessment: Assessment }) { return <section className="embedded-assessment"><h3>嵌入式可交付性</h3><p><b>{assessment.agentReadiness}/100</b> Agent readiness · {assessment.target} · {assessment.scope}</p><div className="readiness"><span style={{ width: `${assessment.agentReadiness}%` }}/></div><small>源码 {assessment.sourceFilesProvided ? "已确认" : "未确认"} · 工具链 {assessment.toolchainKnown ? "已确认" : "未确认"} · 测试条件 {assessment.testFixturesProvided ? "已确认" : "未确认"}</small>{assessment.blockers.length > 0 ? <><h3>阻断项</h3><ul>{assessment.blockers.map(item => <li key={item}>{item}</li>)}</ul></> : <><h3>建议交付包</h3><ul>{assessment.recommendedArtifacts.map(item => <li key={item}>{item}</li>)}</ul></>}</section>; }
function Metric({ label, value, tone = "" }: { label: string; value: number; tone?: string }) { return <article className={`metric ${tone}`}><span>{label}</span><b>{value}</b></article>; }
createRoot(document.getElementById("root")!).render(<App />);
