import React, { useEffect, useMemo, useRef, useState } from "react";
import {
  Bot,
  Check,
  Clock3,
  Maximize2,
  Minimize2,
  Pencil,
  Plus,
  Send,
  Trash2,
  User,
  X,
} from "lucide-react";
import { auth } from "../lib/firebase";
import { HISTORY_API_URL } from "../config";
import catMascot from "../assets/easylearn-cat.gif";
import botAvatar from "../assets/chatbot-avatar.png";
import "./TutorWidget.css";
import "./TutorHover.css";

type Message = { role: "user" | "assistant"; content: string };
type ChatSession = {
  id: string;
  title: string;
  updatedAt: number;
  messages: Message[];
};

const STORAGE_KEY = "easylearn-history-chat-sessions-v2";
const welcomeMessage: Message = {
  role: "assistant",
  content:
    "Hi! I’m your EasyLearn History tutor. Ask me about SPM History topics, causes, effects, timelines or exam technique.",
};

function readSessions(): ChatSession[] {
  try {
    const value = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
    return Array.isArray(value) ? value : [];
  } catch {
    return [];
  }
}

export default function HistoryChatbot() {
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
  const sortedSessions = useMemo(
    () => [...sessions].sort((a, b) => b.updatedAt - a.updatedAt),
    [sessions],
  );

  useEffect(
    () => localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions)),
    [sessions],
  );
  useEffect(
    () => bottomRef.current?.scrollIntoView({ behavior: "smooth" }),
    [messages, loading, open, view],
  );
  useEffect(() => {
    if (open && view === "chat")
      setTimeout(() => inputRef.current?.focus(), 80);
  }, [open, view]);

  const startNewChat = () => {
    setActiveId(null);
    setMessages([welcomeMessage]);
    setInput("");
    setView("chat");
    setEditingId(null);
  };
  const saveSessionMessages = (
    sessionId: string,
    nextMessages: Message[],
    title?: string,
  ) =>
    setSessions((current) => {
      const existing = current.find((session) => session.id === sessionId);
      const next: ChatSession = {
        id: sessionId,
        title: title || existing?.title || "New History chat",
        updatedAt: Date.now(),
        messages: nextMessages,
      };
      return [next, ...current.filter((session) => session.id !== sessionId)];
    });
  const loadSession = (session: ChatSession) => {
    setActiveId(session.id);
    setMessages(session.messages.length ? session.messages : [welcomeMessage]);
    setView("chat");
  };
  const deleteSession = (id: string) => {
    setSessions((current) => current.filter((session) => session.id !== id));
    if (id === activeId) startNewChat();
  };
  const beginRename = (session: ChatSession) => {
    setEditingId(session.id);
    setEditingTitle(session.title);
  };
  const finishRename = (id: string) => {
    const title = editingTitle.trim();
    if (title)
      setSessions((current) =>
        current.map((session) =>
          session.id === id ? { ...session, title } : session,
        ),
      );
    setEditingId(null);
    setEditingTitle("");
  };

  async function sendMessage(event?: React.FormEvent) {
    event?.preventDefault();
    const value = input.trim();
    if (!value || loading) return;
    const sessionId =
      activeId || `${Date.now()}-${Math.random().toString(36).slice(2)}`;
    const firstUserMessage = messages.every(
      (message) => message.role !== "user",
    );
    const title = firstUserMessage ? value.slice(0, 42) : undefined;
    const userMessages: Message[] = [
      ...(firstUserMessage ? [] : messages),
      { role: "user", content: value },
    ];
    setActiveId(sessionId);
    setMessages(userMessages);
    saveSessionMessages(sessionId, userMessages, title);
    setInput("");
    setLoading(true);
    try {
      const token = await auth.currentUser?.getIdToken();
      const response = await fetch(`${HISTORY_API_URL}/api/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token || ""}`,
        },
        body: JSON.stringify({
          message: value,
          history: userMessages.slice(-8),
        }),
      });
      const data = await response.json();
      if (!response.ok)
        throw new Error(data.error || "History tutor unavailable");
      const nextMessages: Message[] = [
        ...userMessages,
        { role: "assistant", content: data.reply },
      ];
      setMessages(nextMessages);
      saveSessionMessages(sessionId, nextMessages, title);
    } catch (error: any) {
      const nextMessages: Message[] = [
        ...userMessages,
        {
          role: "assistant",
          content:
            error.message || "The History tutor is temporarily unavailable.",
        },
      ];
      setMessages(nextMessages);
      saveSessionMessages(sessionId, nextMessages, title);
    } finally {
      setLoading(false);
    }
  }

  const quickPrompts = [
    "Explain an SPM History concept simply",
    "Give me a hint for a KBAT question",
    "Help me revise an important timeline",
  ];

  return (
    <div className={`el-tutor ${expanded ? "is-expanded" : ""}`}>
      {!open && (
        <button
          type="button"
          className="el-tutor-nudge"
          onClick={() => setOpen(true)}
        >
          <strong>Come ask me anything!</strong>
          <span>I can help with SPM History.</span>
        </button>
      )}
      {open && (
        <section
          className={`el-tutor-panel ${expanded ? "expanded" : ""}`}
          aria-label="History AI tutor"
        >
          <header className="el-tutor-header">
            <div className="el-tutor-identity">
              <img src={botAvatar} alt="" />
              <div>
                <strong>History AI Tutor</strong>
                <span>● Online · SPM History only</span>
              </div>
            </div>
            <div className="el-tutor-tools">
              <button
                type="button"
                onClick={() => setView(view === "history" ? "chat" : "history")}
                title="Chat history"
              >
                <Clock3 />
              </button>
              <button type="button" onClick={startNewChat} title="New chat">
                <Plus />
              </button>
              <button
                type="button"
                onClick={() => setExpanded((value) => !value)}
                title={expanded ? "Restore window" : "Open full view"}
              >
                {expanded ? <Minimize2 /> : <Maximize2 />}
              </button>
              <button
                type="button"
                onClick={() => {
                  setOpen(false);
                  setExpanded(false);
                }}
                title="Close"
              >
                <X />
              </button>
            </div>
          </header>
          {view === "history" ? (
            <div className="el-tutor-history">
              <div className="el-tutor-history-title">
                <div>
                  <strong>Chat history</strong>
                  <span>Your History tutor conversations</span>
                </div>
                <button type="button" onClick={startNewChat}>
                  <Plus /> New chat
                </button>
              </div>
              {sortedSessions.length === 0 ? (
                <div className="el-tutor-empty">
                  <Clock3 />
                  <strong>No conversations yet</strong>
                  <span>Your chats will be saved here.</span>
                </div>
              ) : (
                sortedSessions.map((session) => (
                  <article
                    className={`el-tutor-session ${session.id === activeId ? "active" : ""}`}
                    key={session.id}
                    onClick={() =>
                      editingId !== session.id && loadSession(session)
                    }
                  >
                    <div>
                      {editingId === session.id ? (
                        <input
                          autoFocus
                          value={editingTitle}
                          onChange={(event) =>
                            setEditingTitle(event.target.value)
                          }
                          onKeyDown={(event) => {
                            if (event.key === "Enter") finishRename(session.id);
                            if (event.key === "Escape") setEditingId(null);
                          }}
                        />
                      ) : (
                        <>
                          <strong>{session.title}</strong>
                          <span>
                            {session.messages[session.messages.length - 1]?.content || "Empty chat"}
                          </span>
                        </>
                      )}
                    </div>
                    <div>
                      {editingId === session.id ? (
                        <button
                          type="button"
                          onClick={(event) => {
                            event.stopPropagation();
                            finishRename(session.id);
                          }}
                        >
                          <Check />
                        </button>
                      ) : (
                        <button
                          type="button"
                          title="Rename"
                          onClick={(event) => {
                            event.stopPropagation();
                            beginRename(session);
                          }}
                        >
                          <Pencil />
                        </button>
                      )}
                      <button
                        type="button"
                        title="Delete"
                        onClick={(event) => {
                          event.stopPropagation();
                          deleteSession(session.id);
                        }}
                      >
                        <Trash2 />
                      </button>
                    </div>
                  </article>
                ))
              )}
            </div>
          ) : (
            <>
              <div className="el-tutor-messages">
                {messages.map((message, index) => (
                  <div
                    key={index}
                    className={`el-tutor-message ${message.role}`}
                  >
                    <span>
                      {message.role === "assistant" ? <Bot /> : <User />}
                    </span>
                    <div>{message.content}</div>
                  </div>
                ))}
                {messages.length === 1 && (
                  <div className="el-tutor-prompts">
                    {quickPrompts.map((prompt) => (
                      <button
                        key={prompt}
                        type="button"
                        onClick={() => {
                          setInput(prompt);
                          setTimeout(() => inputRef.current?.focus(), 0);
                        }}
                      >
                        {prompt}
                      </button>
                    ))}
                  </div>
                )}
                {loading && (
                  <div className="el-tutor-message assistant">
                    <span>
                      <Bot />
                    </span>
                    <div className="el-tutor-thinking">
                      <i />
                      <i />
                      <i />
                    </div>
                  </div>
                )}
                <div ref={bottomRef} />
              </div>
              <form className="el-tutor-composer" onSubmit={sendMessage}>
                <textarea
                  ref={inputRef}
                  rows={1}
                  value={input}
                  onChange={(event) => setInput(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" && !event.shiftKey) {
                      event.preventDefault();
                      sendMessage();
                    }
                  }}
                  placeholder="Ask an SPM History question…"
                />
                <button disabled={!input.trim() || loading} aria-label="Send">
                  <Send />
                </button>
              </form>
              <small className="el-tutor-note">
                EasyLearn AI can make mistakes. Check important facts.
              </small>
            </>
          )}
        </section>
      )}
      <button
        type="button"
        className={`el-tutor-fab ${open ? "open" : ""}`}
        onClick={() => {
          setOpen((value) => !value);
          if (open) setExpanded(false);
        }}
        aria-label={open ? "Close History AI tutor" : "Open History AI tutor"}
      >
        {open ? <X /> : <img src={catMascot} alt="EasyLearn cat tutor" />}
      </button>
    </div>
  );
}
