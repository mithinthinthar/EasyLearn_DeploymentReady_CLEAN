import { initializeApp } from "https://www.gstatic.com/firebasejs/12.19.0/firebase-app.js";
import { getAuth, GoogleAuthProvider, onAuthStateChanged, signInWithPopup } from "https://www.gstatic.com/firebasejs/12.19.0/firebase-auth.js";
import { firebaseConfig } from "./firebase-config.js";

const IS_LOCAL = ["localhost", "127.0.0.1"].includes(window.location.hostname);
const AUTH_SERVICE = IS_LOCAL ? "http://localhost:4500" : "/platform-api";
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const provider = new GoogleAuthProvider();
provider.setCustomParameters({ prompt: "select_account" });
const loginButton = document.querySelector("#google-login");
const message = document.querySelector("#auth-message");
let selectedRole = "student";
let loginInProgress = false;

function setMessage(text, error = false) {
  message.textContent = text;
  message.classList.toggle("error", error);
}

async function platformFetch(path, options = {}) {
  const response = await fetch(`${AUTH_SERVICE}${path}`, { credentials: "include", ...options, headers: { "Content-Type": "application/json", ...(options.headers || {}) } });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || data.message || `Request failed (${response.status})`);
  return data;
}

document.querySelectorAll(".role-option").forEach((button) => button.addEventListener("click", () => {
  selectedRole = button.dataset.role;
  document.querySelectorAll(".role-option").forEach((item) => item.classList.toggle("selected", item === button));
}));

loginButton.addEventListener("click", async () => {
  loginInProgress = true;
  loginButton.disabled = true;
  setMessage("Opening Google sign-in…");
  try {
    const result = await signInWithPopup(auth, provider);
    const token = await result.user.getIdToken(true);
    await platformFetch("/auth/session", { method: "POST", body: JSON.stringify({ id_token: token, requested_role: selectedRole }) });
    setMessage("Signed in. Opening your dashboard…");
    window.location.replace("./index.html");
  } catch (error) {
    console.error(error);
    setMessage(error.message || "Sign-in failed.", true);
    loginButton.disabled = false;
    loginInProgress = false;
  }
});

onAuthStateChanged(auth, async () => {
  if (loginInProgress) return;
  try { await platformFetch("/auth/me"); window.location.replace("./index.html"); }
  catch { loginButton.disabled = false; }
});
