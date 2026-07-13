import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { publicDemo } from "./publicDemo";
import "./styles.css";

const API = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
const PUBLIC_DEMO_MODE = import.meta.env.VITE_PUBLIC_DEMO === "true";
type Workspace = "general" | "embedded";
type Verdict = "recommend" | "caution" | "reject";
type Assessment = { target: string; scope: string; agentReadiness: number; blockers: string[]; recommendedArtifacts: string[]; sourceFilesProvided: boolean; toolchainKnown: boolean; testFixturesProvided: boolean };
type Job = { id: string; workspace: Workspace; platform: string; title: string; category: string; budget?: string; url?: string; description: string; deliverables: string[]; estimatedMinutes: number; score: number; verdict: Verdict; reason: string; proposalDraft: string; deliveryPlan: string[]; scoreBreakdown: Record<string, number | null>; embeddedAssessment?: Assessment | null };
type Connector = { platform: string; workspace: Workspace; mode: string; ok: boolean; message: string; supportsCsv: boolean; supportsPaste: boolean; supportsDomCapture: boolean };
type Platform = { workspace: Workspace; name: string; region: string; url: string; workModel: string; intakeMode: string; bestFor: string[]; suitability: string; note: string; agentAccess: string };
type TimeRange = "120" | "720" | "1440" | "10080" | "unlimited";
type PostedRange = "24" | "72" | "168" | "720" | "all";
const TIME_RANGES: { value: TimeRange; label: string; minutes: number }[] = [
  { value: "120", label: "2 小时", minutes: 120 }, { value: "720", label: "12 小时", minutes: 720 },
  { value: "1440", label: "24 小时", minutes: 1440 }, { value: "10080", label: "一周", minutes: 10080 },
  { value: "unlimited", label: "不限", minutes: 525600 },
];
const POSTED_RANGES: { value: PostedRange; label: string; hours?: number }[] = [
  { value: "24", label: "24 小时内", hours: 24 }, { value: "72", label: "3 天内", hours: 72 },
  { value: "168", label: "7 天内", hours: 168 }, { value: "720", label: "30 天内", hours: 720 },
  { value: "all", label: "不限" },
];
const PAGE_SIZE = 8;

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
  const [timeRange, setTimeRange] = useState<TimeRange>("720");
  const [postedRange, setPostedRange] = useState<PostedRange>("all");
  const [category, setCategory] = useState("");
  const [tagText, setTagText] = useState("");
  const [strictMode, setStrictMode] = useState(false);
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState("正在加载本地雷达数据…");
  const [paste, setPaste] = useState("");

  const load = async (nextWorkspace = workspace) => {
    if (PUBLIC_DEMO_MODE) {
      const source = publicDemo[nextWorkspace];
      const tags = tagText.split(",").map(tag => tag.trim().toLowerCase()).filter(Boolean);
      const result = (source.jobs as unknown as Job[]).filter(job => {
        const text = `${job.title} ${job.description} ${job.category} ${job.platform}`.toLowerCase();
        return (!query || text.includes(query.toLowerCase())) && (!platform || job.platform === platform) && (!category || job.category === category) && tags.every(tag => text.includes(tag));
      });
      setJobs(result); setSelected(result[0] || null); setPage(1); setPlatforms(source.platforms as unknown as Platform[]);
      setConnectors((source.platforms as unknown as Platform[]).map(item => ({ platform: item.name, workspace: nextWorkspace, mode: "public_demo_read_only", ok: true, message: "公开体验版：仅展示示例数据，不访问账号或平台。", supportsCsv: false, supportsPaste: false, supportsDomCapture: false })));
      setStatus(`公开体验版：已展示 ${result.length} 条示例任务。导入、账号连接和私有数据分析请使用本地版。`);
      return;
    }
    try {
      const params = new URLSearchParams({ workspace: nextWorkspace });
      const [result, sourceConnectors, sourcePlatforms] = await Promise.all([
        request<Job[]>("/jobs/search", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ workspace: nextWorkspace, query, platforms: platform ? [platform] : [], categories: category ? [category] : [], tags: tagText.split(",").map(tag => tag.trim()).filter(Boolean), postedWithinHours: POSTED_RANGES.find(item => item.value === postedRange)?.hours, max_results: 200 }) }),
        request<Connector[]>(`/connectors?${params}`), request<Platform[]>(`/platforms?${params}`),
      ]);
      setJobs(result); setSelected(result[0] || null); setPage(1); setConnectors(sourceConnectors); setPlatforms(sourcePlatforms);
      setStatus(`已评分 ${result.length} 条${nextWorkspace === "embedded" ? "嵌入式" : "通用"}任务。系统只分析本地导入数据，不代表你登录、报价或接单。`);
    } catch (error) { setStatus(error instanceof Error ? error.message : "无法连接后端"); }
  };

  useEffect(() => { void load(); }, [workspace]);

  const switchWorkspace = (next: Workspace) => {
    setWorkspace(next); setQuery(""); setPlatform(""); setCategory(""); setTagText(""); setTimeRange("720"); setPostedRange("all"); setStrictMode(false); setPage(1); setSelected(null);
  };

  const loadTarget = async () => {
    if (PUBLIC_DEMO_MODE) {
      const maxMinutes = TIME_RANGES.find(item => item.value === timeRange)!.minutes;
      const source = publicDemo[workspace];
      const result = (source.jobs as unknown as Job[]).filter(job => job.verdict !== "reject" && job.estimatedMinutes <= maxMinutes && (!category || job.category === category));
      setJobs(result); setSelected(result[0] || null); setPage(1);
      setStatus(`公开体验版：${result.length} 条示例候选。真实任务导入和私有分析仅在本地版提供。`);
      return;
    }
    try {
      const endpoint = workspace === "embedded" ? "/embedded/jobs/recommendations" : "/jobs/recommendations";
      const maxMinutes = TIME_RANGES.find(item => item.value === timeRange)!.minutes;
      const filters = { categories: category ? [category] : [], tags: tagText.split(",").map(tag => tag.trim()).filter(Boolean), postedWithinHours: POSTED_RANGES.find(item => item.value === postedRange)?.hours };
      const profile = workspace === "embedded"
        ? { workspace, maxMinutes, minimumBudgetCny: strictMode ? 50 : 30, minimumAiAutonomy: strictMode ? 0.85 : 0.65, maximumManualWorkLevel: strictMode ? 2 : 3, maximumRiskLevel: strictMode ? 2 : 3, minimumAgentReadiness: strictMode ? 80 : 60, allowSimulationOnly: true, ...filters }
        : { workspace, maxMinutes, minimumBudgetCny: strictMode ? 50 : 30, minimumAiAutonomy: strictMode ? 0.85 : 0.7, maximumManualWorkLevel: strictMode ? 2 : 3, maximumRiskLevel: strictMode ? 2 : 3, ...filters };
      const result = await request<Job[]>(endpoint, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(profile) });
      setJobs(result); setSelected(result[0] || null); setPage(1);
      const rangeLabel = TIME_RANGES.find(item => item.value === timeRange)!.label;
      setStatus(workspace === "embedded" ? `嵌入式桌面交付候选：${result.length} 条（${rangeLabel}、${strictMode ? "严格" : "宽松"}）。已排除真机、现场、量产和安全关键工作。` : `候选队列：${result.length} 条（${rangeLabel}、${strictMode ? "严格" : "宽松"}条件）。`);
    } catch (error) { setStatus(error instanceof Error ? error.message : "无法生成候选队列"); }
  };

  const importFile = async (file: File) => {
    if (PUBLIC_DEMO_MODE) return setStatus("公开体验版为只读展示；请在本地版导入自己的 CSV/JSON。"), undefined;
    const data = new FormData(); data.append("file", file);
    await request(`/jobs/import/${file.name.toLowerCase().endsWith(".csv") ? "csv" : "json"}`, { method: "POST", body: data });
    await load();
  };
  const importPaste = async () => {
    if (PUBLIC_DEMO_MODE) return setStatus("公开体验版为只读展示；请在本地版粘贴并分析任务。"), undefined;
    if (paste.trim().length < 10) return setStatus("请粘贴至少 10 个字符的任务详情。");
    await request("/jobs/paste", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ workspace, platform: platform || (workspace === "embedded" ? "嵌入式手动粘贴" : "手动粘贴"), text: paste }) });
    setPaste(""); await load();
  };
  const maxVisibleMinutes = TIME_RANGES.find(item => item.value === timeRange)!.minutes;
  const visible = useMemo(() => jobs.filter(job => job.estimatedMinutes <= maxVisibleMinutes), [jobs, maxVisibleMinutes]);
  const categoryOptions = useMemo(() => [...new Set(jobs.map(job => job.category))].sort(), [jobs]);
  const pageCount = Math.max(1, Math.ceil(visible.length / PAGE_SIZE));
  const currentPage = Math.min(page, pageCount);
  const pagedJobs = visible.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE);
  const counts = { recommend: jobs.filter(j => j.verdict === "recommend").length, caution: jobs.filter(j => j.verdict === "caution").length, reject: jobs.filter(j => j.verdict === "reject").length };
  const sourceUrl = (job: Job) => job.url || platforms.find(item => item.name === job.platform)?.url;

  return <main className={`radar ${workspace}`}>
    <header>
      <div><p className="eyebrow">LOCAL · EXPLAINABLE · HUMAN-IN-THE-LOOP</p><h1>{workspaceTitle(workspace)}</h1><p>{workspace === "embedded" ? "独立的嵌入式机会工作区：筛选可在桌面环境完成的固件补丁、协议解析、仿真、测试与文档；自动排除真机调试、现场服务、量产烧录和安全关键验证。" : "将你有权查看的任务导入本机后，筛出 AI 可短时间完成、人工参与低、风险低的候选；只生成草稿与交付计划。"}</p></div>
      <button onClick={() => void load()}>重新评分</button>
    </header>
    <nav className="workspace-tabs" aria-label="工作区"><button className={workspace === "general" ? "active" : ""} onClick={() => switchWorkspace("general")}>AI 接单雷达</button><button className={workspace === "embedded" ? "active" : ""} onClick={() => switchWorkspace("embedded")}>嵌入式接单雷达</button></nav>
    <p className="status">{status}</p>
    <section className="metrics"><Metric label="已扫描" value={jobs.length}/><Metric label="建议接" value={counts.recommend} tone="good"/><Metric label="谨慎" value={counts.caution} tone="warn"/><Metric label="不接" value={counts.reject} tone="bad"/></section>
    <section className="toolbar"><input aria-label="关键词" value={query} onChange={e => setQuery(e.target.value)} placeholder={workspace === "embedded" ? "关键词，如 ESP32、STM32、Zephyr、RTOS、协议、仿真" : "关键词，如 PPT、脚本、API docs"}/><select value={platform} onChange={e => setPlatform(e.target.value)}><option value="">全部平台</option>{platforms.map(item => <option key={item.name}>{item.name}</option>)}</select><label>单子类型 <select value={category} onChange={e => setCategory(e.target.value)}><option value="">全部</option>{categoryOptions.map(item => <option key={item}>{item}</option>)}</select></label><label>发布时间 <select value={postedRange} onChange={e => setPostedRange(e.target.value as PostedRange)}>{POSTED_RANGES.map(item => <option key={item.value} value={item.value}>{item.label}</option>)}</select></label><label>交付时间 <select value={timeRange} onChange={e => { setTimeRange(e.target.value as TimeRange); setPage(1); }}>{TIME_RANGES.map(item => <option key={item.value} value={item.value}>{item.label}</option>)}</select></label><input className="tag-filter" aria-label="自定义标签" value={tagText} onChange={e => setTagText(e.target.value)} placeholder="自定义标签，逗号分隔"/><label><input type="checkbox" checked={strictMode} onChange={e => setStrictMode(e.target.checked)}/> 严格条件（默认宽松）</label><button className="secondary" onClick={() => void load()}>搜索</button><button onClick={() => void loadTarget()}>{workspace === "embedded" ? "生成桌面交付候选" : "生成候选队列"}</button><label className="upload">导入 CSV/JSON<input type="file" accept=".csv,.json" onChange={e => e.target.files?.[0] && void importFile(e.target.files[0])}/></label><a className="secondary export" href={`${API}/exports/markdown`}>导出日报</a></section>
    {workspace === "embedded" && <section className="guardrail"><b>嵌入式交付边界：</b>只推荐已提供源码/工具链/测试条件，且能用 host test、仿真或 mock 验证的工作。真机测试、焊接、现场调试、量产烧录、生产部署、安全认证均不会被推荐。</section>}
    <section className="content"><div className="panel"><h2>推荐队列 <small>共 {visible.length} 条 · 第 {currentPage}/{pageCount} 页</small></h2>{pagedJobs.map(job => { const url = sourceUrl(job); return <article className={`job ${selected?.id === job.id ? "active" : ""}`} key={job.id} onClick={() => setSelected(job)}><span><b>{job.title}</b><small>{job.platform} · {job.category} · {job.budget || "预算未注明"} · {job.estimatedMinutes} 分钟</small><em>{job.reason}</em></span><div className="job-actions"><strong className={job.verdict}>{job.score}</strong>{url && <a href={url} target="_blank" rel="noreferrer" onClick={event => event.stopPropagation()}>{job.url ? "打开原任务 ↗" : "打开来源平台 ↗"}</a>}</div></article>})}{visible.length > 0 && <nav className="pagination" aria-label="推荐列表分页"><button className="secondary" disabled={currentPage === 1} onClick={() => setPage(currentPage - 1)}>上一页</button>{Array.from({ length: pageCount }, (_, index) => index + 1).slice(Math.max(0, currentPage - 3), currentPage + 2).map(item => <button key={item} className={item === currentPage ? "active" : "secondary"} onClick={() => setPage(item)}>{item}</button>)}<button className="secondary" disabled={currentPage === pageCount} onClick={() => setPage(currentPage + 1)}>下一页</button></nav>}{!visible.length && <p>还没有符合条件的任务。请调整筛选条件、导入 CSV/JSON、粘贴有权查看的任务详情，或通过只读扩展采集当前可见页面。</p>}</div>
      <aside className="panel details">{selected ? <><p className={`tag ${selected.verdict}`}>{selected.verdict === "recommend" ? "建议接" : selected.verdict === "caution" ? "谨慎" : "不接"} · {selected.score}/100</p><h2>{selected.title}</h2>{sourceUrl(selected) && <a className="open-source" href={sourceUrl(selected)} target="_blank" rel="noreferrer">{selected.url ? "在平台打开原任务 ↗" : "在平台打开来源页 ↗"}</a>}<p>{selected.description}</p>{selected.embeddedAssessment && <EmbeddedPanel assessment={selected.embeddedAssessment}/>}<h3>评分依据</h3><div className="breakdown">{Object.entries(selected.scoreBreakdown).filter(([, value]) => value !== null).map(([key,value]) => <span key={key}>{key}<b>{value}</b></span>)}</div><h3>交付物</h3><ul>{selected.deliverables.map(item => <li key={item}>{item}</li>)}</ul><h3>交付流程</h3><ol>{selected.deliveryPlan.map(item => <li key={item}>{item}</li>)}</ol><h3>投标草稿（必须人工审核并手动提交）</h3><pre>{selected.proposalDraft}</pre></> : <p>选择一个任务查看详情。</p>}</aside></section>
    <section className="panel"><h2>手动粘贴任务</h2><p className="muted">{workspace === "embedded" ? "推荐粘贴目标平台、芯片/SDK、源码与工具链、测试条件、是否需要真机/现场/烧录等信息。" : "粘贴标题、预算、要求和交付物；不要粘贴私人联系方式或敏感资料。"}</p><textarea className="paste" value={paste} onChange={e => setPaste(e.target.value)} placeholder="从你有权查看的任务页复制内容…"/><button onClick={() => void importPaste()}>导入并评分</button></section>
    <section className="panel"><h2>{workspace === "embedded" ? "嵌入式平台与线索目录" : "平台目录"}</h2><p>{workspace === "embedded" ? "“优先”表示适合作为嵌入式机会来源，不代表自动接入或保证成交；“线索”是工程社区/机会板，需要你自行核验对方与条款。" : "没有任何平台能保证稳定收入。优先选择范围小、资料齐全、修订次数有限且预算覆盖时间成本的任务。"}</p><div className="platforms">{platforms.map(item => <article key={item.name}><div><b>{item.name}</b><small>{item.region} · {item.suitability}</small></div><p>{item.workModel}</p><p className="muted">适合：{item.bestFor.join("、")}</p><p className="muted">{item.note}</p><a href={item.url} target="_blank" rel="noreferrer">打开平台（自行登录）</a></article>)}</div></section>
    <section className="panel"><h2>连接管理</h2><p className="muted">所有连接都只读取用户主动导入或采集的可见数据；不会保存账号、Cookie、Token，也不会替你操作平台。</p><div className="connectors">{connectors.map(connector => <article key={connector.platform}><b>{connector.platform}</b><small>{connector.mode}</small><p>{connector.message}</p><span>{connector.supportsCsv ? "CSV " : ""}{connector.supportsDomCapture ? "只读 DOM Capture " : ""}{connector.supportsPaste ? "手动粘贴" : ""}</span></article>)}</div></section>
  </main>;
}

function EmbeddedPanel({ assessment }: { assessment: Assessment }) { return <section className="embedded-assessment"><h3>嵌入式可交付性</h3><p><b>{assessment.agentReadiness}/100</b> Agent readiness · {assessment.target} · {assessment.scope}</p><div className="readiness"><span style={{ width: `${assessment.agentReadiness}%` }}/></div><small>源码 {assessment.sourceFilesProvided ? "已确认" : "未确认"} · 工具链 {assessment.toolchainKnown ? "已确认" : "未确认"} · 测试条件 {assessment.testFixturesProvided ? "已确认" : "未确认"}</small>{assessment.blockers.length > 0 ? <><h3>阻断项</h3><ul>{assessment.blockers.map(item => <li key={item}>{item}</li>)}</ul></> : <><h3>建议交付包</h3><ul>{assessment.recommendedArtifacts.map(item => <li key={item}>{item}</li>)}</ul></>}</section>; }
function Metric({ label, value, tone = "" }: { label: string; value: number; tone?: string }) { return <article className={`metric ${tone}`}><span>{label}</span><b>{value}</b></article>; }
createRoot(document.getElementById("root")!).render(<App />);
