import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

const API = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
type Verdict = "recommend" | "caution" | "reject";
type Job = { id: string; platform: string; title: string; category: string; budget?: string; description: string; deliverables: string[]; estimatedMinutes: number; score: number; verdict: Verdict; reason: string; proposalDraft: string; deliveryPlan: string[]; scoreBreakdown: Record<string, number> };
type Connector = { platform: string; mode: string; ok: boolean; message: string; supportsCsv: boolean; supportsPaste: boolean; supportsDomCapture: boolean };
type Platform = { name: string; region: string; url: string; workModel: string; intakeMode: string; bestFor: string[]; suitability: string; note: string };

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API}${path}`, init);
  if (!response.ok) throw new Error((await response.json().catch(() => ({ detail: response.statusText }))).detail);
  return response.json() as Promise<T>;
}

function App() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [connectors, setConnectors] = useState<Connector[]>([]);
  const [platforms, setPlatforms] = useState<Platform[]>([]);
  const [selected, setSelected] = useState<Job | null>(null);
  const [query, setQuery] = useState("");
  const [platform, setPlatform] = useState("");
  const [onlyQuick, setOnlyQuick] = useState(true);
  const [status, setStatus] = useState("正在加载本地雷达数据…");
  const [paste, setPaste] = useState("");

  const load = async () => {
    try {
      const [result, sourceConnectors, sourcePlatforms] = await Promise.all([
        request<Job[]>("/jobs/search", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ query, platforms: platform ? [platform] : [], max_results: 200 }) }),
        request<Connector[]>("/connectors"), request<Platform[]>("/platforms")
      ]);
      setJobs(result); setSelected(result[0] || null); setConnectors(sourceConnectors); setPlatforms(sourcePlatforms);
      setStatus(`已评分 ${result.length} 条任务。结果仅供人工审核，系统不会代表你接单。`);
    } catch (error) { setStatus(error instanceof Error ? error.message : "无法连接后端"); }
  };

  const loadTarget = async () => {
    try {
      const result = await request<Job[]>("/jobs/recommendations", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ maxMinutes: 120, minimumBudgetCny: 50, minimumAiAutonomy: 0.85, maximumManualWorkLevel: 2, maximumRiskLevel: 2 }) });
      setJobs(result); setSelected(result[0] || null); setOnlyQuick(false);
      setStatus(`严格候选队列：${result.length} 条（≤2 小时、≥¥50、高 AI 自主、低风险）。`);
    } catch (error) { setStatus(error instanceof Error ? error.message : "无法生成候选队列"); }
  };

  useEffect(() => { void load(); }, []);
  const visible = useMemo(() => onlyQuick ? jobs.filter(job => job.estimatedMinutes <= 120) : jobs, [jobs, onlyQuick]);
  const counts = { recommend: jobs.filter(j => j.verdict === "recommend").length, caution: jobs.filter(j => j.verdict === "caution").length, reject: jobs.filter(j => j.verdict === "reject").length };
  const importFile = async (file: File) => { const data = new FormData(); data.append("file", file); await request(`/jobs/import/${file.name.toLowerCase().endsWith(".csv") ? "csv" : "json"}`, { method: "POST", body: data }); await load(); };
  const importPaste = async () => { if (paste.trim().length < 10) return setStatus("请粘贴至少 10 个字符的任务详情。"); await request("/jobs/paste", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ platform: platform || "手动粘贴", text: paste }) }); setPaste(""); await load(); };

  return <main className="radar">
    <header><div><p className="eyebrow">LOCAL · EXPLAINABLE · HUMAN-IN-THE-LOOP</p><h1>AI Job Radar</h1><p>本机任务雷达：将你已授权可见的任务导入后，筛出 AI 可在短时间完成、人工参与低、风险低的候选；只生成草稿与交付计划，绝不自动投标、私信、签约、付款或交付。</p></div><button onClick={() => void load()}>重新评分</button></header>
    <p className="status">{status}</p>
    <section className="metrics"><Metric label="已扫描" value={jobs.length}/><Metric label="建议接" value={counts.recommend} tone="good"/><Metric label="谨慎" value={counts.caution} tone="warn"/><Metric label="不接" value={counts.reject} tone="bad"/></section>
    <section className="toolbar"><input aria-label="关键词" value={query} onChange={e => setQuery(e.target.value)} placeholder="关键词，如 PPT、脚本、API docs"/><select value={platform} onChange={e => setPlatform(e.target.value)}><option value="">全部平台</option>{[...new Set([...jobs.map(j => j.platform), ...platforms.map(p => p.name)])].map(item => <option key={item}>{item}</option>)}</select><label><input type="checkbox" checked={onlyQuick} onChange={e => setOnlyQuick(e.target.checked)}/> 仅显示 2 小时内可交付</label><button className="secondary" onClick={() => void load()}>搜索</button><button onClick={() => void loadTarget()}>AI 快速候选（¥50/2h）</button><label className="upload">导入 CSV/JSON<input type="file" accept=".csv,.json" onChange={e => e.target.files?.[0] && void importFile(e.target.files[0])}/></label><a className="secondary export" href={`${API}/exports/markdown`}>导出日报</a></section>
    <section className="content"><div className="panel"><h2>推荐队列 <small>{visible.length} 条</small></h2>{visible.map(job => <button className={`job ${selected?.id === job.id ? "active" : ""}`} key={job.id} onClick={() => setSelected(job)}><span><b>{job.title}</b><small>{job.platform} · {job.category} · {job.budget || "预算未注明"} · {job.estimatedMinutes} 分钟</small><em>{job.reason}</em></span><strong className={job.verdict}>{job.score}</strong></button>)}{!visible.length && <p>尚无符合条件的任务。可导入 CSV/JSON、粘贴详情，或通过只读扩展采集当前任务页。</p>}</div><aside className="panel details">{selected ? <><p className={`tag ${selected.verdict}`}>{selected.verdict === "recommend" ? "建议接" : selected.verdict === "caution" ? "谨慎" : "不接"} · {selected.score}/100</p><h2>{selected.title}</h2><p>{selected.description}</p><h3>评分依据</h3><div className="breakdown">{Object.entries(selected.scoreBreakdown).map(([key,value]) => <span key={key}>{key}<b>{value}</b></span>)}</div><h3>交付物</h3><ul>{selected.deliverables.map(item => <li key={item}>{item}</li>)}</ul><h3>交付流程</h3><ol>{selected.deliveryPlan.map(item => <li key={item}>{item}</li>)}</ol><h3>投标草稿（必须人工审核与手动提交）</h3><pre>{selected.proposalDraft}</pre></> : <p>选择一个任务查看详情。</p>}</aside></section>
    <section className="panel"><h2>手动粘贴任务</h2><textarea className="paste" value={paste} onChange={e => setPaste(e.target.value)} placeholder="从你有权查看的任务页面复制标题、预算、要求和交付物；请勿粘贴私人联系方式或敏感资料。"/><button onClick={() => void importPaste()}>导入并评分</button></section>
    <section className="panel"><h2>平台目录</h2><p>没有任何平台能保证每天稳定收入。以下是明确的接单路径；优先选择范围小、资料齐全、允许一次轻量修改、预算覆盖时间成本的任务。</p><div className="platforms">{platforms.map(item => <article key={item.name}><div><b>{item.name}</b><small>{item.region} · {item.suitability}</small></div><p>{item.workModel}</p><p className="muted">适合：{item.bestFor.join("、")}</p><p className="muted">{item.note}</p><a href={item.url} target="_blank" rel="noreferrer">打开平台（自行登录）</a></article>)}</div></section>
    <section className="panel"><h2>平台连接管理</h2><div className="connectors">{connectors.map(connector => <article key={connector.platform}><b>{connector.platform}</b><small>{connector.mode}</small><p>{connector.message}</p><span>{connector.supportsCsv ? "CSV " : ""}{connector.supportsDomCapture ? "只读 DOM Capture " : ""}{connector.supportsPaste ? "手动粘贴" : ""}</span></article>)}</div></section>
  </main>;
}
function Metric({ label, value, tone = "" }: { label: string; value: number; tone?: string }) { return <article className={`metric ${tone}`}><span>{label}</span><b>{value}</b></article>; }
createRoot(document.getElementById("root")!).render(<App />);
