import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Bot, Check, Clock3, Maximize2, Minimize2, Pencil, Plus, Send, Trash2, User, X } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { askAI } from "../../services/api";
import { useLanguage } from "../../language";
import catMascot from "../../assets/easylearn-cat.gif";
import botAvatar from "../../assets/chatbot-avatar.png";
import "./TutorWidget.css";
import "./TutorHover.css";

type ChatAction = { label: string; path: string };
type Message = { role: "user" | "assistant"; content: string; actions?: ChatAction[] };
type ChatSession = { id: string; title: string; updatedAt: number; messages: Message[] };

const STORAGE_KEY = "easylearn-bm-chat-sessions-v2";

function wantsNavigation(value: string) {
  const text = value.toLowerCase();
  return ["practice", "practise", "latihan", "open", "start", "buka", "mula", "cuba", "i want", "saya nak"].some((term) => text.includes(term));
}

function getActions(value: string): ChatAction[] {
  if (!wantsNavigation(value)) return [];
  const text = value.toLowerCase();
  const actions: ChatAction[] = [];
  const add = (label: string, path: string) => { if (!actions.some((item) => item.path === path)) actions.push({ label, path }); };
  if (text.includes("dashboard") || text.includes("prestasi")) add("Open Dashboard", "/dashboard");
  if (text.includes("karangan panjang") || text.includes("long essay")) add("Open Karangan Panjang", "/karangan-panjang-latihan");
  if (text.includes("karangan pendek") || text.includes("short essay")) add("Open Karangan Pendek", "/karangan-pendek-latihan");
  if (text.includes("bertutur") || text.includes("speaking")) add("Open Ujian Bertutur", "/ujian-bertutur-latihan");
  if (text.includes("mendengar") || text.includes("listening")) add("Open Ujian Mendengar", "/ujian-mendengar-latihan");
  if (text.includes("bina ayat")) add("Open Bina Ayat", "/bina-ayat-latihan");
  if (text.includes("golongan kata") || text.includes("tatabahasa") || text.includes("grammar")) add("Open Golongan Kata", "/golongan-kata-latihan");
  if (text.includes("jenis ayat")) add("Open Jenis Ayat", "/jenis-ayat-latihan");
  if (text.includes("kesalahan bahasa")) add("Open Kesalahan Bahasa", "/kesalahan-bahasa-latihan");
  if (text.includes("pemahaman") || text.includes("comprehension")) add("Open Pemahaman", "/pemahaman-latihan");
  if (text.includes("rumusan") || text.includes("summary")) add("Open Rumusan", "/rumusan-latihan");
  if (!actions.length) add("Open Practice", "/practice");
  return actions.slice(0, 3);
}

function readSessions(): ChatSession[] {
  try { const value = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]"); return Array.isArray(value) ? value : []; }
  catch { return []; }
}

export default function AIChatBar() {
  const navigate = useNavigate();
  const { language } = useLanguage();
  const welcomeMessage: Message = { role: "assistant", content: language === "bm" ? "Hai! Saya tutor AI Bahasa Melayu EasyLearn. Tanya saya tentang Tatabahasa, Karangan, Pemahaman, Bertutur atau Mendengar." : "Hi! I’m your EasyLearn Bahasa Melayu tutor. Ask me about Tatabahasa, Karangan, Pemahaman, speaking or listening." };
  const [open, setOpen] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const [view, setView] = useState<"chat" | "history">("chat");
  const [sessions, setSessions] = useState<ChatSession[]>(readSessions);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([welcomeMessage]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const sortedSessions = useMemo(() => [...sessions].sort((a, b) => b.updatedAt - a.updatedAt), [sessions]);

  useEffect(() => localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions)), [sessions]);
  useEffect(() => bottomRef.current?.scrollIntoView({ behavior: "smooth" }), [messages, loading, open, view]);
  useEffect(() => { if (open && view === "chat") setTimeout(() => inputRef.current?.focus(), 80); }, [open, view]);

  const startNewChat = () => { setActiveId(null); setMessages([welcomeMessage]); setInput(""); setView("chat"); setEditingId(null); };
  const saveSessionMessages = (sessionId: string, nextMessages: Message[], title?: string) => setSessions((current) => {
    const existing = current.find((session) => session.id === sessionId);
    const next: ChatSession = { id: sessionId, title: title || existing?.title || "New BM chat", updatedAt: Date.now(), messages: nextMessages };
    return [next, ...current.filter((session) => session.id !== sessionId)];
  });
  const loadSession = (session: ChatSession) => { setActiveId(session.id); setMessages(session.messages.length ? session.messages : [welcomeMessage]); setView("chat"); };
  const deleteSession = (id: string) => { setSessions((current) => current.filter((session) => session.id !== id)); if (id === activeId) startNewChat(); };
  const beginRename = (session: ChatSession) => { setEditingId(session.id); setEditingTitle(session.title); };
  const finishRename = (id: string) => { const title = editingTitle.trim(); if (title) setSessions((current) => current.map((session) => session.id === id ? { ...session, title } : session)); setEditingId(null); setEditingTitle(""); };

  async function sendMessage(event?: React.FormEvent) {
    event?.preventDefault();
    const value = input.trim();
    if (!value || loading) return;
    const sessionId = activeId || `${Date.now()}-${Math.random().toString(36).slice(2)}`;
    const firstUserMessage = messages.every((message) => message.role !== "user");
    const title = firstUserMessage ? value.slice(0, 42) : undefined;
    const userMessages: Message[] = [...(firstUserMessage ? [] : messages), { role: "user", content: value }];
    setActiveId(sessionId); setMessages(userMessages); saveSessionMessages(sessionId, userMessages, title); setInput(""); setLoading(true);
    try {
      const reply = await askAI(value);
      const nextMessages: Message[] = [...userMessages, { role: "assistant", content: reply, actions: getActions(value) }];
      setMessages(nextMessages); saveSessionMessages(sessionId, nextMessages, title);
    } catch {
      const nextMessages: Message[] = [...userMessages, { role: "assistant", content: language === "bm" ? "Maaf, tutor BM tidak dapat dihubungi buat sementara waktu." : "The BM tutor is temporarily unavailable." }];
      setMessages(nextMessages); saveSessionMessages(sessionId, nextMessages, title);
    } finally { setLoading(false); }
  }

  const quickPrompts = language === "bm" ? ["Terangkan satu konsep Tatabahasa", "Beri saya petua menulis Karangan", "Bantu saya berlatih Pemahaman"] : ["Explain a Tatabahasa concept", "Give me Karangan writing tips", "Help me practise Pemahaman"];

  return <div className={`el-tutor ${expanded ? "is-expanded" : ""}`}>
    {!open && <button type="button" className="el-tutor-nudge" onClick={() => setOpen(true)}><strong>{language === "bm" ? "Tanya saya apa-apa!" : "Come ask me anything!"}</strong><span>{language === "bm" ? "Saya boleh bantu Bahasa Melayu SPM." : "I can help with SPM Bahasa Melayu."}</span></button>}
    {open && <section className={`el-tutor-panel ${expanded ? "expanded" : ""}`} aria-label="Bahasa Melayu AI tutor"><header className="el-tutor-header"><div className="el-tutor-identity"><img src={botAvatar} alt=""/><div><strong>Bahasa Melayu AI Tutor</strong><span>● Online · SPM Bahasa Melayu only</span></div></div><div className="el-tutor-tools"><button type="button" onClick={() => setView(view === "history" ? "chat" : "history")} title="Chat history"><Clock3/></button><button type="button" onClick={startNewChat} title="New chat"><Plus/></button><button type="button" onClick={() => setExpanded((value) => !value)} title={expanded ? "Restore window" : "Open full view"}>{expanded ? <Minimize2/> : <Maximize2/>}</button><button type="button" onClick={() => { setOpen(false); setExpanded(false); }} title="Close"><X/></button></div></header>
      {view === "history" ? <div className="el-tutor-history"><div className="el-tutor-history-title"><div><strong>Chat history</strong><span>Your Bahasa Melayu tutor conversations</span></div><button type="button" onClick={startNewChat}><Plus/> New chat</button></div>{sortedSessions.length === 0 ? <div className="el-tutor-empty"><Clock3/><strong>No conversations yet</strong><span>Your chats will be saved here.</span></div> : sortedSessions.map((session) => <article className={`el-tutor-session ${session.id === activeId ? "active" : ""}`} key={session.id} onClick={() => editingId !== session.id && loadSession(session)}><div>{editingId === session.id ? <input autoFocus value={editingTitle} onChange={(event) => setEditingTitle(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter") finishRename(session.id); if (event.key === "Escape") setEditingId(null); }}/> : <><strong>{session.title}</strong><span>{session.messages[session.messages.length - 1]?.content || "Empty chat"}</span></>}</div><div>{editingId === session.id ? <button type="button" onClick={(event) => { event.stopPropagation(); finishRename(session.id); }}><Check/></button> : <button type="button" title="Rename" onClick={(event) => { event.stopPropagation(); beginRename(session); }}><Pencil/></button>}<button type="button" title="Delete" onClick={(event) => { event.stopPropagation(); deleteSession(session.id); }}><Trash2/></button></div></article>)}</div> : <><div className="el-tutor-messages">{messages.map((message, index) => <div key={index} className={`el-tutor-message ${message.role}`}><span>{message.role === "assistant" ? <Bot/> : <User/>}</span><div><ReactMarkdown>{message.content}</ReactMarkdown>{message.actions?.length ? <div className="el-tutor-actions">{message.actions.map((action) => <button key={action.path} type="button" onClick={() => { navigate(action.path); setOpen(false); }}>{action.label}</button>)}</div> : null}</div></div>)}{messages.length === 1 && <div className="el-tutor-prompts">{quickPrompts.map((prompt) => <button key={prompt} type="button" onClick={() => { setInput(prompt); setTimeout(() => inputRef.current?.focus(), 0); }}>{prompt}</button>)}</div>}{loading && <div className="el-tutor-message assistant"><span><Bot/></span><div className="el-tutor-thinking"><i/><i/><i/></div></div>}<div ref={bottomRef}/></div><form className="el-tutor-composer" onSubmit={sendMessage}><textarea ref={inputRef} rows={1} value={input} onChange={(event) => setInput(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); sendMessage(); } }} placeholder={language === "bm" ? "Tanya tentang Tatabahasa, Karangan…" : "Ask about Tatabahasa, Karangan…"}/><button disabled={!input.trim() || loading} aria-label="Send"><Send/></button></form><small className="el-tutor-note">EasyLearn AI can make mistakes. Check important answers.</small></>}
    </section>}
    <button type="button" className={`el-tutor-fab ${open ? "open" : ""}`} onClick={() => { setOpen((value) => !value); if (open) setExpanded(false); }} aria-label={open ? "Close Bahasa Melayu AI tutor" : "Open Bahasa Melayu AI tutor"}>{open ? <X/> : <img src={catMascot} alt="EasyLearn cat tutor"/>}</button>
  </div>;
}
