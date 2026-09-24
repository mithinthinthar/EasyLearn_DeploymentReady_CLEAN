const PLATFORM_URL = process.env.REACT_APP_SHARED_AUTH_URL || (["localhost", "127.0.0.1"].includes(window.location.hostname) ? "http://localhost:4500" : "/platform-api");

function findNumber(value: any, names: string[]): number | null {
  if (!value || typeof value !== "object") return null;
  for (const name of names) if (typeof value[name] === "number") return value[name];
  for (const child of Object.values(value)) { const found = findNumber(child, names); if (found !== null) return found; }
  return null;
}

export function installHistoryActivityTracker() {
  const original = window.fetch.bind(window);
  window.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
    const response = await original(input, init);
    const url = typeof input === "string" ? input : input.toString();
    const method = (init?.method || "GET").toUpperCase();
    const pathname = (() => { try { return new URL(url, window.location.origin).pathname; } catch { return ""; } })();
    const isEssaySubmission = pathname === "/api/grade";
    const isTutorMessage = pathname === "/api/chat";
    if (response.ok && method === "POST" && !url.startsWith(PLATFORM_URL) && (isEssaySubmission || isTutorMessage)) {
      response.clone().json().catch(() => ({})).then((data) => {
        const percentage = findNumber(data, ["percentage", "accuracy", "average_score"]);
        const score = findNumber(data, ["score", "marks_awarded"]);
        const maxScore = findNumber(data, ["max_score", "total_marks"]);
        return original(`${PLATFORM_URL}/events`, { method: "POST", credentials: "include", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ subject: "history", activity_type: isTutorMessage ? "ai_tutor" : "essay", title: isTutorMessage ? "History AI Tutor" : "History essay practice", percentage, score, max_score: maxScore, questions_answered: isTutorMessage ? 0 : 1 }) });
      }).catch(() => {});
    }
    return response;
  };
}
