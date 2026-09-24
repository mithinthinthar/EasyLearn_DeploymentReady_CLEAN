const rawApiUrl =
  process.env.REACT_APP_HISTORY_API_URL || "http://127.0.0.1:5000";

export const HISTORY_API_URL = rawApiUrl.replace(/\/$/, "");
export const LOCAL_MODE = process.env.REACT_APP_LOCAL_MODE === "true";
