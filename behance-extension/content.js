// 다운로더 페이지(127.0.0.1 / localhost)에서만 실행됨.
// 페이지가 "이 Behance 링크 풀어줘" 요청 → 확장 백그라운드에 전달 → 결과를 페이지로 돌려줌.
document.documentElement.dataset.vdExt = "1";

window.addEventListener("message", (e) => {
  if (e.source !== window || e.origin !== location.origin) return;
  const m = e.data;
  if (!m || m.vd !== "expand" || typeof m.url !== "string") return;
  chrome.runtime.sendMessage({ type: "expand", url: m.url }, (res) => {
    const err = chrome.runtime.lastError;
    window.postMessage({ vd: "expanded", id: m.id, ...(err ? { error: err.message } : res) }, location.origin);
  });
});
