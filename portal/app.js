import { initializeApp } from "https://www.gstatic.com/firebasejs/12.19.0/firebase-app.js";
import { getAuth, onAuthStateChanged, signOut } from "https://www.gstatic.com/firebasejs/12.19.0/firebase-auth.js";
import { firebaseConfig } from "./firebase-config.js";

const IS_LOCAL = ["localhost", "127.0.0.1"].includes(window.location.hostname);
const AUTH_SERVICE = IS_LOCAL ? "http://localhost:4500" : "/platform-api";
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const $ = (selector) => document.querySelector(selector);
const signedIn = $("#signed-in-view");
const logoutButton = $("#logout-button");
const cards = [...document.querySelectorAll(".subject-card")];
let currentUser = null;

const SUBJECT_URLS = IS_LOCAL
  ? { history: "http://localhost:3000", mathematics: "http://localhost:3001", bahasa_melayu: "http://localhost:5173" }
  : { history: "/history/", mathematics: "/mathematics/", bahasa_melayu: "/bahasa-melayu/" };

cards.forEach((card) => {
  const subject = card.dataset.subject;
  const url = SUBJECT_URLS[subject];
  if (!url) return;
  card.dataset.url = url;
  const link = card.querySelector("a");
  if (link) link.href = url;
});

async function jsonResponse(response) {
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || data.message || `Request failed (${response.status})`);
  return data;
}

async function platformFetch(path, options = {}) {
  return jsonResponse(await fetch(`${AUTH_SERVICE}${path}`, { credentials: "include", ...options, headers: { "Content-Type": "application/json", ...(options.headers || {}) } }));
}

function showSignedOut() {
  currentUser = null;
  window.location.replace("./login.html");
}

function showSignedIn(user) {
  currentUser = user;
  signedIn.hidden = false;
  $("#portal-nav").hidden = false;
  $("#account-area").hidden = false;
  $("#user-name").textContent = user.name || "EasyLearn user";
  $("#user-email").textContent = user.email || "";
  $("#role-badge").textContent = user.role;
  $("#role-badge").className = `role-badge ${user.role}`;
  if (user.picture) { $("#user-picture").src = user.picture; $("#user-picture").hidden = false; }
  else $("#user-picture").hidden = true;
  $("#readonly-note").hidden = user.role === "student";
  $("#subjects-copy").textContent = user.role === "student" ? "Continue learning in any subject. Each subject opens on its dashboard." : "Open any subject to review student performance. Learning activities are read-only for this account.";
  showView("dashboard");
  loadDashboard();
  checkAll();

  // Warm the Math Flask function while the learner is still on the portal.
  // This does not block the dashboard. It reduces the chance that clicking
  // Mathematics has to pay the full Vercel cold-start cost.
  if (!IS_LOCAL) {
    fetch(`/math-api/?warm=${Date.now()}`, {
      method: "GET",
      cache: "no-store",
    }).catch(() => {});
  }
}

function showView(name) {
  $("#dashboard-view").hidden = name !== "dashboard";
  $("#subjects-view").hidden = name !== "subjects";
  document.querySelectorAll(".nav-button").forEach((button) => button.classList.toggle("active", button.dataset.view === name));
}

document.querySelectorAll(".nav-button").forEach((button) => button.addEventListener("click", () => showView(button.dataset.view)));

logoutButton.addEventListener("click", async () => {
  try { await platformFetch("/auth/logout", { method: "POST" }); } catch (error) { console.warn(error); }
  await signOut(auth).catch(() => {});
  showSignedOut();
});

onAuthStateChanged(auth, async (firebaseUser) => {
  try {
    if (firebaseUser) {
      const data = await platformFetch("/auth/me");
      showSignedIn(data.user);
    } else {
      const data = await platformFetch("/auth/me");
      showSignedIn(data.user);
    }
  } catch { showSignedOut(); }
});

function valueOrDash(value, suffix = "") { return value === null || value === undefined ? "—" : `${value}${suffix}`; }

function metricCard(icon, label, value, note) {
  return `<article class="metric-card"><span class="metric-icon">${icon}</span><div><p>${label}</p><strong>${value}</strong><small>${note}</small></div></article>`;
}

function subjectCards(subjects = []) {
  if (!subjects.length) return `<div class="empty-state">No subject activity has been recorded yet.</div>`;
  return subjects.map((subject) => `<article class="summary-card ${subject.subject}"><div class="summary-head"><strong>${subject.label}</strong><span>${valueOrDash(subject.average_score, "%")}</span></div><div class="progress-track"><i style="width:${subject.average_score || 0}%"></i></div><dl><div><dt>Activities</dt><dd>${subject.attempts}</dd></div><div><dt>Questions</dt><dd>${subject.questions_answered}</dd></div><div><dt>Time</dt><dd>${subject.minutes_spent} min</dd></div></dl></article>`).join("");
}

function activityRows(items = []) {
  if (!items.length) return `<div class="empty-state">No activity yet. Completed quizzes and practice sessions will appear here.</div>`;
  return items.map((item) => `<div class="activity-row"><span class="activity-dot ${item.subject}"></span><div><strong>${item.title || item.activityType}</strong><small>${(item.subject || "").replace("_", " ")} · ${item.activityType || "activity"}</small></div><b>${valueOrDash(item.percentage, "%")}</b></div>`).join("");
}

function studentRows(students = []) {
  if (!students.length) return `<div class="empty-state">No students are connected yet.</div>`;
  return students.map((summary) => `<button class="student-row" data-student="${summary.student.uid}"><span class="student-avatar">${(summary.student.name || "S").charAt(0).toUpperCase()}</span><div><strong>${summary.student.name}</strong><small>${summary.student.email}</small></div><span>${valueOrDash(summary.overall.average_score, "%")} average</span><b>View →</b></button>`).join("");
}

async function loadDashboard() {
  $("#dashboard-loading").hidden = false;
  $("#dashboard-error").hidden = true;
  $("#dashboard-content").hidden = true;
  try {
    const data = await platformFetch("/dashboard/overview");
    const role = data.role;
    $("#dashboard-title").textContent = role === "student" ? `Welcome back, ${(currentUser.name || "Student").split(" ")[0]}.` : role === "teacher" ? "Teaching overview" : "Family learning overview";
    $("#dashboard-subtitle").textContent = role === "student" ? "Track your progress and continue where you left off." : role === "teacher" ? "Monitor overall performance and open any student for a detailed view." : "See how your linked students are progressing across all three subjects.";
    $("#student-code-box").hidden = role !== "student" || !currentUser.student_code;
    $("#student-code").textContent = currentUser.student_code || "";
    $("#people-panel").hidden = role === "student";
    $("#link-student-form").hidden = role === "student";
    if (role === "student") {
      const overall = data.overall;
      $("#metric-grid").innerHTML = metricCard("◎", "Overall average", valueOrDash(overall.average_score, "%"), "Across scored activities") + metricCard("✓", "Activities", overall.activities, "Completed learning sessions") + metricCard("?", "Questions", overall.questions_answered, "Questions answered") + metricCard("◷", "Study time", `${overall.minutes_spent} min`, "Recorded across subjects");
      $("#subject-summary").innerHTML = subjectCards(data.subjects);
      $("#recent-activity").innerHTML = activityRows(data.recent_activity);
    } else {
      const cohort = data.cohort;
      $("#metric-grid").innerHTML = metricCard("◉", role === "teacher" ? "Students" : "Linked students", cohort.students, "Visible to this account") + metricCard("◎", "Average score", valueOrDash(cohort.average_score, "%"), "Across visible students") + metricCard("✓", "Activities", cohort.activities, "Recorded learning sessions") + metricCard("?", "Questions", cohort.questions_answered, "Questions answered");
      const allSubjects = ["history", "mathematics", "bahasa_melayu"].map((subject) => {
        const rows = data.students.map((s) => s.subjects.find((x) => x.subject === subject)).filter(Boolean);
        const scores = rows.map((x) => x.average_score).filter((x) => x !== null);
        return { subject, label: rows[0]?.label || subject, average_score: scores.length ? Math.round(scores.reduce((a,b)=>a+b,0)/scores.length*10)/10 : null, attempts: rows.reduce((a,b)=>a+b.attempts,0), questions_answered: rows.reduce((a,b)=>a+b.questions_answered,0), minutes_spent: rows.reduce((a,b)=>a+b.minutes_spent,0) };
      });
      $("#subject-summary").innerHTML = subjectCards(allSubjects);
      $("#people-heading").textContent = role === "teacher" ? "Student overview" : "Linked students";
      $("#people-subtitle").textContent = role === "teacher" ? "Select a learner to review individual subject progress." : "Connect more than one student using each learner’s EasyLearn code.";
      $("#student-list").innerHTML = studentRows(data.students);
      $("#recent-activity").innerHTML = activityRows(data.students.flatMap((s) => s.recent_activity || []).sort((a,b) => String(b.createdAt).localeCompare(String(a.createdAt))).slice(0,8));
      document.querySelectorAll(".student-row").forEach((button) => button.addEventListener("click", () => openStudent(button.dataset.student)));
    }
    $("#dashboard-loading").hidden = true;
    $("#dashboard-content").hidden = false;
  } catch (error) {
    $("#dashboard-loading").hidden = true;
    $("#dashboard-error").hidden = false;
    $("#dashboard-error").textContent = error.message;
  }
}

async function openStudent(uid) {
  try {
    const data = await platformFetch(`/dashboard/students/${uid}`);
    $("#student-dialog-content").innerHTML = `<p class="eyebrow">Individual learner</p><h2>${data.student.name}</h2><p class="muted">${data.student.email}</p><div class="metric-grid compact">${metricCard("◎", "Average", valueOrDash(data.overall.average_score, "%"), "All subjects")}${metricCard("✓", "Activities", data.overall.activities, "Completed")}</div><div class="subject-summary-grid">${subjectCards(data.subjects)}</div><h3>Recent activity</h3><div class="activity-list">${activityRows(data.recent_activity)}</div>`;
    $("#student-dialog").showModal();
  } catch (error) { alert(error.message); }
}

$("#close-dialog").addEventListener("click", () => $("#student-dialog").close());
$("#copy-code").addEventListener("click", async () => { await navigator.clipboard.writeText(currentUser.student_code); $("#copy-code").textContent = "Copied"; setTimeout(() => $("#copy-code").textContent = "Copy", 1200); });
$("#link-student-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const code = $("#student-code-input").value.trim();
  $("#link-message").textContent = "Connecting student…";
  try { await platformFetch("/relationships/students/link", { method: "POST", body: JSON.stringify({ student_code: code }) }); $("#student-code-input").value = ""; $("#link-message").textContent = "Student connected successfully."; await loadDashboard(); }
  catch (error) { $("#link-message").textContent = error.message; }
});

async function isReachable(url) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 3500);
  try { await fetch(`${url}/?status-check=${Date.now()}`, { mode: "no-cors", cache: "no-store", signal: controller.signal }); return true; }
  catch { return false; } finally { clearTimeout(timeout); }
}

async function checkAll() {
  $("#refresh-status").disabled = true;
  await Promise.all(cards.map(async (card) => {
    const badge = card.querySelector(".status-badge"); badge.className = "status-badge checking"; badge.innerHTML = "<i></i>Checking";
    const online = await isReachable(card.dataset.url); badge.className = `status-badge ${online ? "online" : "offline"}`; badge.innerHTML = `<i></i>${online ? "Ready" : "Starting"}`;
  }));
  $("#refresh-status").disabled = false;
}
$("#refresh-status").addEventListener("click", checkAll);
setInterval(() => { if (currentUser) checkAll(); }, 15000);
