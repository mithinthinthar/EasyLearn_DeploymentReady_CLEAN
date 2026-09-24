const PLATFORM_URL = process.env.REACT_APP_SHARED_AUTH_URL || (["localhost", "127.0.0.1"].includes(window.location.hostname) ? "http://localhost:4500" : "/platform-api");

function findNumber(value, names) {
  if (!value || typeof value !== "object") return null;
  for (const name of names) if (typeof value[name] === "number") return value[name];
  for (const child of Object.values(value)) {
    const found = findNumber(child, names);
    if (found !== null) return found;
  }
  return null;
}

function classify(pathname) {
  if (pathname === "/api/practice/save-attempt") return { type: "practice", title: "Mathematics practice", questions: 1 };
  if (pathname === "/api/quick-snap/log") return { type: "quick_snap", title: "Quick Snap", questions: 1 };
  if (pathname === "/api/chat") return { type: "ai_tutor", title: "Mathematics AI Tutor", questions: 0 };
  return null;
}

export function installMathematicsActivityTracker() {
  const original = window.fetch.bind(window);
  window.fetch = async (input, init) => {
    const response = await original(input, init);
    const url = typeof input === "string" ? input : input.toString();
    const method = (init?.method || "GET").toUpperCase();
    let pathname = "";
    try { pathname = new URL(url, window.location.origin).pathname; } catch { /* ignore malformed URLs */ }
    const activity = classify(pathname);
    if (response.ok && method === "POST" && !url.startsWith(PLATFORM_URL) && activity) {
      response.clone().json().catch(() => ({})).then((data) => original(`${PLATFORM_URL}/events`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          subject: "mathematics",
          activity_type: activity.type,
          title: activity.title,
          percentage: findNumber(data, ["percentage", "accuracy", "score_percentage"]),
          score: findNumber(data, ["score", "marks_awarded"]),
          max_score: findNumber(data, ["max_score", "total_marks"]),
          questions_answered: activity.questions,
          metadata: { endpoint: pathname },
        }),
      })).catch(() => {});
    }
    return response;
  };
}
