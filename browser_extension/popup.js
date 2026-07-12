const apiInput = document.getElementById("api");
const workspaceInput = document.getElementById("workspace");
const status = document.getElementById("status");
const capture = document.getElementById("capture");

chrome.storage.local.get({ apiUrl: "http://127.0.0.1:8000", workspace: "general" }, ({ apiUrl, workspace }) => {
  apiInput.value = apiUrl;
  workspaceInput.value = workspace;
});

function detectPlatform(hostname) {
  const rules = [["upwork", "Upwork"], ["freelancer", "Freelancer"], ["fiverr", "Fiverr"], ["contra", "Contra"], ["peopleperhour", "PeoplePerHour"], ["workana", "Workana"], ["proginn", "程序员客栈·IoT"], ["codemart", "码市·物联网"], ["elecfans", "电子发烧友·工程机会"], ["eeworld", "EEWorld·工程机会"], ["21ic", "21IC·工程机会"], ["zbj", "猪八戒"], ["epwk", "一品威客"]];
  return (rules.find(([fragment]) => hostname.includes(fragment)) || ["Browser capture", "Browser capture"])[1];
}

function extractVisibleJob() {
  const heading = [...document.querySelectorAll("h1,h2,[role='heading']")].map(node => node.innerText.trim()).find(Boolean) || document.title;
  const text = (document.querySelector("main") || document.body).innerText.replace(/\n{3,}/g, "\n\n").trim().slice(0, 45000);
  return { title: heading.slice(0, 200), description: text, url: location.href, platform: location.hostname };
}

capture.addEventListener("click", async () => {
  const apiUrl = apiInput.value.trim().replace(/\/$/, "");
  const workspace = workspaceInput.value;
  if (!/^http:\/\/(127\.0\.0\.1|localhost)(:\d+)?$/.test(apiUrl)) {
    status.textContent = "只允许发送到本机 HTTP API。";
    return;
  }
  capture.disabled = true;
  status.textContent = "正在读取当前可见页面…";
  try {
    await chrome.storage.local.set({ apiUrl, workspace });
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab?.id || !tab.url) throw new Error("未找到当前标签页。");
    const [{ result }] = await chrome.scripting.executeScript({ target: { tabId: tab.id }, func: extractVisibleJob });
    const response = await fetch(`${apiUrl}/jobs/dom-capture`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ workspace, platform: detectPlatform(new URL(tab.url).hostname), jobs: [result] })
    });
    if (!response.ok) throw new Error((await response.json().catch(() => ({ detail: response.statusText }))).detail);
    status.textContent = "已导入本地雷达。回到网页点击“重新评分”查看。";
  } catch (error) {
    status.textContent = `采集失败：${error instanceof Error ? error.message : "未知错误"}`;
  } finally { capture.disabled = false; }
});
