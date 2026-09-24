const PLATFORM_URL = import.meta.env.VITE_SHARED_AUTH_URL || (["localhost", "127.0.0.1"].includes(window.location.hostname) ? "http://localhost:4500" : "/platform-api");
function findNumber(value: any, names: string[]): number | null { if (!value || typeof value !== "object") return null; for (const name of names) if (typeof value[name] === "number") return value[name]; for (const child of Object.values(value)) { const found = findNumber(child, names); if (found !== null) return found; } return null; }
export function installBmActivityTracker() {
  const original = window.fetch.bind(window);
  window.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
    const response = await original(input, init);
    const url = typeof input === "string" ? input : input.toString();
    const method = (init?.method || "GET").toUpperCase();
    if (response.ok && method === "POST" && !url.startsWith(PLATFORM_URL) && /(submit|chat)/i.test(url)) {
      response.clone().json().catch(() => ({})).then((data) => original(`${PLATFORM_URL}/events`, { method: "POST", credentials: "include", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ subject: "bahasa_melayu", activity_type: /\/ai\//i.test(url) ? "ai_tutor" : "practice", title: /\/ai\//i.test(url) ? "Bahasa Melayu AI Tutor" : "Bahasa Melayu practice", percentage: findNumber(data, ["percentage", "average_percentage", "score_percentage"]), score: findNumber(data, ["score", "marks_awarded", "total_score"]), max_score: findNumber(data, ["max_score", "total_marks"]), questions_answered: /\/ai\//i.test(url) ? 0 : 1 }) })).catch(() => {});
    }
    return response;
  };
}
