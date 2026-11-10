// Behance 프로젝트 페이지를 사용자 크롬에서 읽고 영상 링크만 골라 돌려줌.
// 1) 사용자 쿠키로 바로 가져오기 → 2) 안 되면 백그라운드 탭으로 실제로 열어서 읽기.

const PROJECT = /^https:\/\/(www\.)?behance\.net\/gallery\/\d+/i;
const VID = /^(https?:)?\/\/([\w-]+\.)*(vimeo\.com|youtube\.com|youtube-nocookie\.com|youtu\.be|adobe\.io|dailymotion\.com|wistia\.(com|net)|loom\.com|streamable\.com|tiktok\.com|instagram\.com|facebook\.com|twitch\.tv)\//i;

function pick(stateJson) {
  const p = JSON.parse(stateJson).project.project;
  const seen = new Set(), list = [];
  const add = (u) => {
    u = String(u).replace(/&amp;/g, "&");
    if (u.startsWith("//")) u = "https:" + u;
    if (/^https?:\/\//.test(u) && VID.test(u) && !seen.has(u)) { seen.add(u); list.push(u); }
  };
  const fromHtml = (h) => { const re = /<iframe[^>]*?\ssrc=["']([^"']+)/gi; let m; while ((m = re.exec(h || ""))) add(m[1]); };
  for (const m of p.modules || []) {
    if (m.__typename === "EmbedModule") fromHtml(m.originalEmbed || m.fluidEmbed);
    else if (m.__typename === "VideoModule") fromHtml(m.embed);
  }
  const t = p.name || "Behance project";
  const covers = p.covers || {};
  const all = Array.isArray(covers.allAvailable) ? covers.allAvailable : [];
  const img = (all.find((c) => c && c.type === "JPG") || all[0] || {}).url || "";
  return { t, img, site: "Behance", v: list.map((u, i) => [u, list.length > 1 ? `${t} ${i + 1}` : t]) };
}

const STATE_RE = /<script[^>]*id="beconfig-store_state"[^>]*>([\s\S]*?)<\/script>/;

async function viaFetch(url) {
  const r = await fetch(url, { credentials: "include" });
  const m = (await r.text()).match(STATE_RE);
  return m ? m[1] : null;
}

async function viaTab(url) {
  const tab = await chrome.tabs.create({ url, active: false });
  try {
    for (let i = 0; i < 40; i++) {   // 최대 약 20초
      await new Promise((r) => setTimeout(r, 500));
      try {
        const [res] = await chrome.scripting.executeScript({
          target: { tabId: tab.id },
          func: () => document.getElementById("beconfig-store_state")?.textContent || null,
        });
        if (res && res.result) return res.result;
      } catch (e) { /* 아직 로딩 중 */ }
    }
    return null;
  } finally {
    chrome.tabs.remove(tab.id).catch(() => {});
  }
}

chrome.runtime.onMessage.addListener((msg, sender, reply) => {
  if (!msg || msg.type !== "expand") return;
  const url = String(msg.url || "").split("#")[0];
  if (!PROJECT.test(url)) { reply({ error: "Not a Behance project link." }); return; }
  (async () => {
    try {
      const state = (await viaFetch(url).catch(() => null)) || (await viaTab(url));
      if (!state) return reply({ error: "Couldn't read this Behance project." });
      const data = pick(state);
      reply(data.v.length ? data : { error: "No videos in this Behance project." });
    } catch (e) {
      reply({ error: "Couldn't read this Behance project." });
    }
  })();
  return true;   // 비동기 응답
});
