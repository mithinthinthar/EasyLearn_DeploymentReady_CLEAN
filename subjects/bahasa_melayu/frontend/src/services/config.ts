const RAW_API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || (["localhost", "127.0.0.1"].includes(window.location.hostname) ? "http://localhost:8000" : "/bm-api");

export const API_BASE_URL = RAW_API_BASE_URL.replace(/\/$/, "");
export const API_URL = `${API_BASE_URL}/api`;
