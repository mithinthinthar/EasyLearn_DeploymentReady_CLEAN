import React, { useEffect, useMemo, useState } from "react";
import { getAuth } from "firebase/auth";
import MathUiIcon from "../components/MathUiIcon";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { DashboardData } from "../types";
import { HISTORY_API_URL } from "../config";
import { useAuth } from "../context/AuthContext";
import { TOPICS } from "../data/topics";
import "./Dashboard.css";
import "./DashboardPolish.css";
import "./DashboardVisualParity.css";

const PORTAL_URL = process.env.REACT_APP_PORTAL_URL || (["localhost", "127.0.0.1"].includes(window.location.hostname) ? "http://localhost:4000" : "/");
interface MasteryLevel { chapter: number; mastery: number; }
interface DashboardProps { onPractice?: () => void; }

const gradeFor = (score: number) => score >= 90 ? "A+" : score >= 80 ? "A" : score >= 75 ? "A-" : score >= 70 ? "B+" : score >= 65 ? "B" : score >= 60 ? "C+" : score >= 50 ? "C" : score >= 40 ? "D" : score >= 30 ? "E" : "G";
const topicName = (chapter?: number) => TOPICS.find((topic) => topic.chapterNumber === chapter)?.subtitle || (chapter ? `Chapter ${chapter}` : "a History chapter");
const formatMinutes = (minutes: number) => { const value = Math.max(0, Math.round(minutes || 0)); return `${Math.floor(value / 60)}h ${value % 60}m`; };
const dateKey = (date: Date) => `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;

export default function Dashboard({ onPractice }: DashboardProps) {
  const { portalUser } = useAuth();
  const [data, setData] = useState<DashboardData | null>(null);
  const [mastery, setMastery] = useState<MasteryLevel[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const currentYear = new Date().getFullYear();
  const [selectedHeatmapYear, setSelectedHeatmapYear] = useState(currentYear);
  const [heatmapTip, setHeatmapTip] = useState<{ label: string; x: number; y: number } | null>(null);

  useEffect(() => {
    if (portalUser?.role !== "student") { setLoading(false); return; }
    (async () => {
      try {
        const user = getAuth().currentUser;
        if (!user) throw new Error("Student session unavailable");
        const token = await user.getIdToken();
        const headers = { Authorization: `Bearer ${token}`, "Content-Type": "application/json" };
        const [dashboardResponse, masteryResponse] = await Promise.all([
          fetch(`${HISTORY_API_URL}/dashboard`, { headers }),
          fetch(`${HISTORY_API_URL}/quiz/mastery`, { method: "POST", headers }),
        ]);
        if (!dashboardResponse.ok) throw new Error("Could not load History dashboard");
        setData(await dashboardResponse.json());
        if (masteryResponse.ok) {
          const payload = await masteryResponse.json();
          const raw = payload.mastery_levels || {};
          const values: MasteryLevel[] = Array.isArray(raw)
            ? raw.map((item: any) => ({ chapter: Number(item.chapter), mastery: Number(item.mastery) }))
            : Object.entries(raw).map(([chapter, value]) => ({ chapter: Number(chapter), mastery: Number(value) }));
          setMastery(values.filter((item) => Number.isFinite(item.chapter) && Number.isFinite(item.mastery)).map((item) => ({ ...item, mastery: item.mastery > 1 ? item.mastery / 100 : item.mastery })).sort((a, b) => a.chapter - b.chapter));
        }
      } catch (caught: any) { setError(caught.message || "Dashboard unavailable"); }
      finally { setLoading(false); }
    })();
  }, [portalUser?.role]);

  const score = data?.average_score || 0;
  const totalQuestions = data?.total_questions || 0;
  const totalMinutes = data?.total_minutes || 0;
  const confidence = Math.min(95, Math.round(35 + Math.sqrt(totalQuestions) * 6));
  const masteryByChapter = useMemo(() => new Map(mastery.map((item) => [item.chapter, item.mastery])), [mastery]);
  const topics = useMemo(() => TOPICS.map((topic) => ({ chapter: topic.chapterNumber, title: topic.subtitle, mastery: masteryByChapter.get(topic.chapterNumber) ?? 0, attempted: masteryByChapter.has(topic.chapterNumber) })), [masteryByChapter]);
  const attemptedTopics = topics.filter((topic) => topic.attempted);
  const strongest = [...attemptedTopics].sort((a, b) => b.mastery - a.mastery)[0];
  const focus = [...attemptedTopics].sort((a, b) => a.mastery - b.mastery)[0];
  const secondFocus = [...attemptedTopics].sort((a, b) => a.mastery - b.mastery)[1];
  const masteredCount = attemptedTopics.filter((topic) => topic.mastery >= .8).length;
  const averageCount = attemptedTopics.filter((topic) => topic.mastery >= .5 && topic.mastery < .8).length;
  const reviewCount = attemptedTopics.filter((topic) => topic.mastery < .5).length;
  const recentPoints = data?.history || [];
  const trendDirection = recentPoints.length < 2 ? "Building your baseline" : recentPoints[recentPoints.length - 1].accuracy > recentPoints[0].accuracy ? "Improving recently" : recentPoints[recentPoints.length - 1].accuracy < recentPoints[0].accuracy ? "Needs renewed focus" : "Stable recently";
  const selectedYearPoints = recentPoints.filter((point) => Number(point.date.slice(0, 4)) === selectedHeatmapYear);
  const activeDays = new Set(selectedYearPoints.map((point) => point.date)).size;
  const weeklyPoints = recentPoints.filter((point) => Date.now() - new Date(`${point.date}T00:00:00`).getTime() <= 7 * 86400000);
  const weeklyMinutes = weeklyPoints.reduce((sum, point) => sum + (point.minutes || 0), 0);
  const weeklyTarget = 3;
  const completedSessions = Math.min(weeklyTarget, recentPoints.filter((point) => Date.now() - new Date(`${point.date}T00:00:00`).getTime() <= 7 * 86400000).length);
  const heatmap = useMemo(() => {
    const activity = new Map((data?.history || []).map((point) => [point.date, point]));
    const firstDay = new Date(selectedHeatmapYear, 0, 1);
    const leadingCells = (firstDay.getDay() + 6) % 7;
    const daysInYear = Math.round((new Date(selectedHeatmapYear + 1, 0, 1).getTime() - firstDay.getTime()) / 86400000);
    const leading = Array.from({ length: leadingCells }, (_, index) => ({ key: `leading-${index}`, date: "", count: 0, minutes: 0, level: 0, placeholder: true }));
    const days = Array.from({ length: daysInYear }, (_, index) => {
      const date = new Date(selectedHeatmapYear, 0, index + 1);
      const key = dateKey(date); const point = activity.get(key); const count = point?.questions_answered || 0; const minutes = point?.minutes || 0;
      return { key, date: key, count, minutes, level: minutes === 0 ? 0 : minutes < 10 ? 1 : minutes < 20 ? 2 : minutes < 40 ? 3 : 4, placeholder: false };
    });
    const trailingCells = (7 - ((leading.length + days.length) % 7)) % 7;
    const trailing = Array.from({ length: trailingCells }, (_, index) => ({ key: `trailing-${index}`, date: "", count: 0, minutes: 0, level: 0, placeholder: true }));
    return [...leading, ...days, ...trailing];
  }, [data?.history, selectedHeatmapYear]);
  const bestDayMinutes = Math.max(0, ...selectedYearPoints.map((point) => point.minutes || 0));

  if (portalUser?.role !== "student") return <main className="history-dashboard"><section className="history-role-panel"><p>{portalUser?.role?.toUpperCase()} VIEW</p><h1>History performance is read-only</h1><span>Use the main EasyLearn dashboard to choose a student and compare all three subjects.</span><a href={PORTAL_URL}>Open EasyLearn Dashboard</a></section></main>;
  if (loading) return <main className="history-dashboard"><div className="history-loading">Loading your History performance overview…</div></main>;

  return <main className="history-dashboard">
    <header className="dashboard-intro"><h1>Hello, {portalUser?.name || "learner"}</h1><p>Let’s continue improving your SPM History performance today! Here is your performance overview.</p></header>
    {error && <div className="history-error">{error}</div>}

    <section className="history-kpi-grid">
      <article className="grade-card"><span>SPM Predicted Grade</span><strong>{gradeFor(score)}</strong><small>↗ {confidence}% Confidence</small></article>
      <article><div className="kpi-head"><span>Questions Attempted</span><i className="blue"><MathUiIcon name="book"/></i></div><strong>{totalQuestions}</strong><small>Across History practice</small></article>
      <article><div className="kpi-head"><span>Correct Attempt Rate</span><i className="green"><MathUiIcon name="target"/></i></div><strong>{score}%</strong><small className="positive">◎ Live Accuracy</small></article>
      <article><div className="kpi-head"><span>Total Study Time</span><i className="orange"><MathUiIcon name="clock"/></i></div><strong>{formatMinutes(totalMinutes)}</strong><small className="positive">+{formatMinutes(weeklyMinutes)} this week</small></article>
    </section>

    <section className="dashboard-two-column">
      <article className="history-panel ai-performance">
        <h2><MathUiIcon name="autoGraph"/> AI Performance Overview</h2>
        <div className="trend-card"><div className="trend-heading"><div><span>Recent Performance Trend</span><strong>{trendDirection}</strong></div><small><MathUiIcon name="autoGraph"/> Live Trend</small></div><div className="history-chart"><ResponsiveContainer><LineChart data={recentPoints}><CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e8ecf3"/><XAxis dataKey="date" hide/><YAxis domain={[0,100]} hide/><Tooltip formatter={(value: any) => [`${value}%`, "Accuracy"]}/><Line type="monotone" dataKey="accuracy" stroke="#78a0ff" strokeWidth={3} dot={{ r: 3, fill: "#78a0ff" }} fill="#eaf0ff"/></LineChart></ResponsiveContainer></div></div>
        <div className="summary-row"><MathUiIcon name="check" className="success"/><div><strong>Strength</strong><p>{strongest ? `${strongest.title} is currently your strongest topic at ${Math.round(strongest.mastery * 100)}% mastery.` : "Continue practising so the system can identify your strengths."}</p></div></div>
        <div className="summary-row"><MathUiIcon name="warning" className="warning"/><div><strong>Concern</strong><p>{focus ? `Your main revision focus should be ${focus.title}.` : "Complete more History practice to identify your main revision focus."}</p></div></div>
        <div className="summary-row feedback"><MathUiIcon name="article"/><div><strong>Feedback Summary</strong><p>Your predicted grade is {gradeFor(score)} with an estimated score of {Math.round(score)}/100 and {confidence}% confidence. {totalQuestions < 30 ? "More practice will improve prediction reliability." : "Keep following your recommended topics to strengthen your result."}</p></div></div>
      </article>

      <div className="right-dashboard-column">
        <article className="history-panel topic-mastery"><h2><MathUiIcon name="barChart"/> Topic Mastery</h2><div className="mastery-legend"><span className="mastered">● {masteredCount} Mastered</span><span className="average">● {averageCount} Average</span><span className="review">● {reviewCount} Review</span><span>● {topics.length - attemptedTopics.length} Unattempted</span></div><div className="mastery-overall"><i style={{ width: `${topics.length ? attemptedTopics.length / topics.length * 100 : 0}%` }}/></div><div className="topic-list">{topics.map((topic) => <div className="topic-row" key={topic.chapter}><div><small>Form 4 · Chapter {topic.chapter}</small><strong>{topic.title}</strong><span>Questions attempted: {topic.attempted ? "Yes" : "No"}</span></div><b>{Math.round(topic.mastery * 100)}%</b></div>)}</div></article>
        <article className="history-panel recommendations"><h2><MathUiIcon name="lightbulb"/> Topic Recommendations</h2>{focus ? <div className="recommendation priority"><div><strong>{focus.title}</strong><span>High Priority</span></div><p>This topic is recommended because its current mastery is {Math.round(focus.mastery * 100)}%.</p><button onClick={onPractice}>Practice Now</button></div> : <p className="empty-copy">Complete a quiz to unlock a personalised recommendation.</p>}{secondFocus && <div className="recommendation"><div><strong>{secondFocus.title}</strong><span>Secondary Review</span></div><p>Include this topic in your next revision session.</p></div>}</article>
      </div>
    </section>

    <section className="history-panel study-insights"><h2><MathUiIcon name="calendar"/> Study Insights &amp; Personalized Schedule</h2><div className="insight-layout"><div className="learner-card"><span>Study Pattern Insight</span><strong>{activeDays >= 4 ? "Consistent Learner" : activeDays >= 2 ? "Flexible Learner" : "Building a Routine"}</strong><p>You had {activeDays} active day(s) in your recorded History activity.</p><div><b>Suggestion</b><p>Set a simple weekly target to make your revision more consistent.</p></div></div><div className="consistency-card"><div><div><span>Consistency Across the Year</span><strong>How consistently you spent time learning in the system</strong></div><div className="heatmap-controls"><b>{activeDays} active days</b><select value={selectedHeatmapYear} onChange={(event) => setSelectedHeatmapYear(Number(event.target.value))} aria-label="Consistency tracker year"><option value={currentYear}>{currentYear}</option><option value={currentYear - 1}>{currentYear - 1}</option></select></div></div><div className="heatmap-scroll"><div className="heatmap" aria-label={`${activeDays} active History study days`}>{heatmap.map((cell) => <button type="button" key={cell.key} className={`heatmap-cell level-${cell.level}${cell.placeholder ? " placeholder" : ""}`} aria-label={cell.placeholder ? undefined : `${cell.date}: ${cell.minutes} minutes`} onMouseEnter={(event) => !cell.placeholder && setHeatmapTip({ label: `${cell.date} • ${cell.minutes} min`, x: event.clientX, y: event.clientY })} onMouseMove={(event) => !cell.placeholder && setHeatmapTip({ label: `${cell.date} • ${cell.minutes} min`, x: event.clientX, y: event.clientY })} onMouseLeave={() => setHeatmapTip(null)} onFocus={(event) => { if (!cell.placeholder) { const box = event.currentTarget.getBoundingClientRect(); setHeatmapTip({ label: `${cell.date} • ${cell.minutes} min`, x: box.left + box.width / 2, y: box.top }); } }} onBlur={() => setHeatmapTip(null)}/>)}</div></div><div className="heatmap-footer"><small>Best day: {bestDayMinutes} min</small><div className="heatmap-scale" aria-label="Activity intensity"><i className="level-0"/><i className="level-1"/><i className="level-2"/><i className="level-3"/><i className="level-4"/></div></div></div></div>
      <div className="schedule-card"><div className="schedule-title"><strong>Personalized Study Schedule</strong><span>{completedSessions}/{weeklyTarget} sessions done</span></div><div className="schedule-metrics"><div><span>◷ Study timing insight</span><strong>Not enough timing data yet</strong></div><div><span>● Recommended Session Length</span><strong>20 minutes</strong></div><div><span>ϟ Weekly Target</span><strong>{weeklyTarget} sessions</strong></div></div><div className="target-progress"><span>Weekly Target Progress</span><b>{completedSessions}/{weeklyTarget} sessions done</b><i><em style={{ width: `${completedSessions / weeklyTarget * 100}%` }}/></i></div><div className="next-session"><div><span>Next Suggested Session</span><strong>Next session → {topicName(focus?.chapter)}</strong></div><button onClick={onPractice}>Practice This Session <MathUiIcon name="play" size={14}/></button></div></div>
    </section>
    {heatmapTip && <div className="history-heatmap-tooltip" style={{ left: heatmapTip.x, top: heatmapTip.y }}>{heatmapTip.label}</div>}
  </main>;
}
