import React, { useState, useRef, useEffect } from "react";
import {
  Box,
  Fab,
  Paper,
  Typography,
  IconButton,
  TextField,
  InputAdornment,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Button,
  Chip,
} from "@mui/material";
import { keyframes } from "@mui/system";
import { logUserActivity } from "../utils/logger";
import { useLanguage } from "../context/LanguageContext";
import { apiFetch } from "../utils/apiFetch";
import { useNavigate } from "react-router-dom";
import "katex/dist/katex.min.css";
import katex from "katex";

// Icons
import CloseIcon from "@mui/icons-material/Close";
import SendIcon from "@mui/icons-material/Send";
import MenuIcon from "@mui/icons-material/AccessTimeOutlined";
import AddIcon from "@mui/icons-material/Add";
import EditOutlinedIcon from "@mui/icons-material/EditOutlined";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import CheckIcon from "@mui/icons-material/Check";
import CloseOutlinedIcon from "@mui/icons-material/CloseOutlined";
import LaunchOutlinedIcon from "@mui/icons-material/LaunchOutlined";
import CameraAltOutlinedIcon from "@mui/icons-material/CameraAltOutlined";
import FunctionsIcon from "@mui/icons-material/Functions";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import ExpandLessIcon from "@mui/icons-material/ExpandLess";
import AutoAwesomeRoundedIcon from "@mui/icons-material/AutoAwesomeRounded";
import TipsAndUpdatesRoundedIcon from "@mui/icons-material/TipsAndUpdatesRounded";
import FavoriteRoundedIcon from "@mui/icons-material/FavoriteRounded";
import SchoolRoundedIcon from "@mui/icons-material/SchoolRounded";

import chatbotAvatar from "../assets/landingpage/chatbotIcon.png";
import mathsyCatGif from "../assets/landingpage/mathsyCat.GIF";

// Markdown / math
import ReactMarkdown from "react-markdown";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import "katex/dist/katex.min.css";

//math symbols
import { getEasyLearnmbols, getEasyLearnmbolsTooltip } from "../utils/mathSymbols";

const floatAnimation = keyframes`
  0% { transform: translateY(0px); }
  50% { transform: translateY(-8px); }
  100% { transform: translateY(0px); }
`;

const pulseAnimation = keyframes`
  0% { box-shadow: 0 0 0 0 rgba(88, 80, 252, 0.35); }
  70% { box-shadow: 0 0 0 15px rgba(88, 80, 252, 0); }
  100% { box-shadow: 0 0 0 0 rgba(88, 80, 252, 0); }
`;

const dotsAnimation = keyframes`
  0%, 20% { opacity: 0.2; transform: translateY(0); }
  50% { opacity: 1; transform: translateY(-2px); }
  100% { opacity: 0.2; transform: translateY(0); }
`;

const FloatingChatbot = () => {
  const { t, language } = useLanguage();
  const navigate = useNavigate();
  const chatbotContainerRef = useRef(null);
  const inputRef = useRef(null);

  const [isOpen, setIsOpen] = useState(false);
  const [view, setView] = useState("chat");
  const [inputMessage, setInputMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isTypingReply, setIsTypingReply] = useState(false);
  const [showNudge, setShowNudge] = useState(false);
  const [showSymbolPad, setShowSymbolPad] = useState(false);

  const [sessions, setSessions] = useState([]);
  const [activeChatSessionId, setActiveChatSessionId] = useState(null);
  const [messages, setMessages] = useState([]);

  const [editingSessionId, setEditingSessionId] = useState(null);
  const [editingTitleValue, setEditingTitleValue] = useState("");
  const [deleteTargetSession, setDeleteTargetSession] = useState(null);
  const [quickSnapContext, setQuickSnapContext] = useState(null);
  const [isQuickSnapCardExpanded, setIsQuickSnapCardExpanded] = useState(false);

  const bottomRef = useRef(null);
  const activeRequestIdRef = useRef(0);
  const typingTimerRef = useRef(null);

  const quickPrompts =
    language === "bm"
      ? [
          {
            label: "Terangkan konsep",
            text: "Boleh terangkan satu konsep Matematik SPM dengan mudah?",
            icon: <SchoolRoundedIcon fontSize="small" />,
          },
          {
            label: "Beri hint",
            text: "Boleh beri saya hint sahaja?",
            icon: <TipsAndUpdatesRoundedIcon fontSize="small" />,
          },
          {
            label: "Motivasi",
            text: "Saya perlu motivasi belajar Matematik.",
            icon: <FavoriteRoundedIcon fontSize="small" />,
          },
        ]
      : [
          {
            label: "Explain concept",
            text: "Can you explain an SPM Mathematics concept simply?",
            icon: <SchoolRoundedIcon fontSize="small" />,
          },
          {
            label: "Give me hints",
            text: "Can you give me hints only?",
            icon: <TipsAndUpdatesRoundedIcon fontSize="small" />,
          },
          {
            label: "Motivate me",
            text: "I need motivation studying Mathematics.",
            icon: <FavoriteRoundedIcon fontSize="small" />,
          },
        ];

  const mathSymbols = getEasyLearnmbols(language);
  
  const aiDisclaimer =
    language === "bm"
      ? "EasyLearn ialah AI dan mungkin membuat kesilapan."
      : "EasyLearn is AI and can make mistakes.";

  const buildWelcomeMessages = () => [
    {
      sender: "bot",
      text: t("chatbot_welcome"),
      isWelcome: true,
    },
  ];

  useEffect(() => {
    if (messages.length === 0) return;
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, view, isTypingReply, isLoading]);

  useEffect(() => {
    const onlyWelcome =
      messages.length === 1 && messages[0]?.isWelcome && !activeChatSessionId;

    if (onlyWelcome) {
      setMessages(buildWelcomeMessages());
    }
  }, [t]);

  useEffect(() => {
    return () => {
      if (typingTimerRef.current) {
        clearInterval(typingTimerRef.current);
      }
    };
  }, []);

  useEffect(() => {
    if (isOpen) {
      setShowNudge(false);
      return;
    }

    const showTimer = setTimeout(() => {
      setShowNudge(true);
    }, 1200);

    const hideTimer = setTimeout(() => {
      setShowNudge(false);
    }, 7500);

    return () => {
      clearTimeout(showTimer);
      clearTimeout(hideTimer);
    };
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen) return;

    // During Quick Snap follow-up, student needs to click/scroll the Quick Snap page
    // without accidentally closing the floating chatbot.
    if (quickSnapContext) return;

    const handleClickOutside = (event) => {
      if (
        chatbotContainerRef.current &&
        !chatbotContainerRef.current.contains(event.target)
      ) {
        handleCloseChat();
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    document.addEventListener("touchstart", handleClickOutside);

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("touchstart", handleClickOutside);
    };
  }, [isOpen, quickSnapContext]);

  useEffect(() => {
    const handleQuickSnapFollowUp = (event) => {
      const context = event.detail;
      if (!context) return;

      activeRequestIdRef.current += 1;
      stopTypingTimer();

      setQuickSnapContext(context);
      setIsOpen(true);
      setShowNudge(false);
      setView("chat");
      setInputMessage("");
      setActiveChatSessionId(null);
      setIsLoading(false);
      setIsTypingReply(false);
      setShowSymbolPad(false);
      setIsQuickSnapCardExpanded(false);

      setMessages([
        {
          sender: "bot",
          text:
            language === "bm"
              ? "Saya dah buka mod follow-up untuk keputusan Quick Snap ini. Anda boleh tanya bahagian mana yang masih kurang jelas sambil rujuk semula jawapan atau semakan di halaman Quick Snap."
              : "I’ve opened follow-up mode for this Quick Snap result. You can ask which part is still unclear while referring back to the solution or marking feedback on this page.",
          isQuickSnapIntro: true,
        },
      ]);

      setTimeout(() => {
        inputRef.current?.focus();
      }, 100);
    };

    window.addEventListener("openQuickSnapFollowUpChat", handleQuickSnapFollowUp);

    return () => {
      window.removeEventListener(
        "openQuickSnapFollowUpChat",
        handleQuickSnapFollowUp
      );
    };
  }, [language]);

  const stopTypingTimer = () => {
    if (typingTimerRef.current) {
      clearInterval(typingTimerRef.current);
      typingTimerRef.current = null;
    }
  };

  const resetToFreshChat = () => {
    activeRequestIdRef.current += 1;
    stopTypingTimer();
    setView("chat");
    setInputMessage("");
    setActiveChatSessionId(null);
    setMessages(buildWelcomeMessages());
    setIsLoading(false);
    setIsTypingReply(false);
    setShowSymbolPad(false);
  };

  const handleOpenChat = () => {
    setIsOpen(true);
    resetToFreshChat();
  };

  const handleCloseChat = () => {
    setIsOpen(false);
    activeRequestIdRef.current += 1;
    stopTypingTimer();
    setView("chat");
    setInputMessage("");
    setActiveChatSessionId(null);
    setMessages([]);
    setIsLoading(false);
    setIsTypingReply(false);
    setEditingSessionId(null);
    setEditingTitleValue("");
    setDeleteTargetSession(null);
    setShowSymbolPad(false);
    setQuickSnapContext(null);
  };

  const handleQuickPrompt = (promptText) => {
    if (isLoading || isTypingReply) return;
    setInputMessage(promptText);
  };

  const handleOpenFullChatbotPage = () => {
    if (isLoading || isTypingReply) return;

    const chatSessionIdToOpen = activeChatSessionId || null;
    const quickSnapContextToOpen = quickSnapContext || null;

    handleCloseChat();

    navigate("/chatbot", {
      state: {
        chatSessionId: chatSessionIdToOpen,
        quickSnapContext: quickSnapContextToOpen,
      },
    });
  };

  const handleGoToQuickSnapCheck = () => {
    handleCloseChat();

    navigate("/quick-snap", {
      state: {
        mode: "check_my_work",
      },
    });
  };

  const insertEasyLearnmbol = (symbol, cursorBack = 0) => {
    const textarea = inputRef.current;
    const start = textarea?.selectionStart ?? inputMessage.length;
    const end = textarea?.selectionEnd ?? inputMessage.length;

    const nextValue =
      inputMessage.slice(0, start) + symbol + inputMessage.slice(end);

    const nextCursorPosition = start + symbol.length - cursorBack;

    setInputMessage(nextValue);

    setTimeout(() => {
      if (inputRef.current) {
        inputRef.current.focus();
        inputRef.current.setSelectionRange(nextCursorPosition, nextCursorPosition);
      }
    }, 0);
  };

  const mapBackendMessagesToUi = (backendMessages = []) => {
    return backendMessages.map((msg) => ({
      id: msg.message_id,
      sender: msg.sender === "assistant" ? "bot" : "user",
      text: msg.message_text,
      tutoringMode: msg.tutoring_mode,
      showQuickSnapCta: Boolean(msg.show_quick_snap_cta),
      createdAt: msg.created_at,
    }));
  };

  const fetchChatSessions = async () => {
    try {
      const res = await apiFetch(
        `${process.env.REACT_APP_API_BASE_URL}/api/chat/sessions`,
        { method: "GET" }
      );

      const data = await res.json();
      setSessions(Array.isArray(data.sessions) ? data.sessions : []);
    } catch (error) {
      console.error("Failed to load chat sessions:", error);
    }
  };

  const loadChatSession = async (chatSessionId, switchToChat = true) => {
    activeRequestIdRef.current += 1;
    stopTypingTimer();
    setIsLoading(false);
    setIsTypingReply(false);

    try {
      const res = await apiFetch(
        `${process.env.REACT_APP_API_BASE_URL}/api/chat/sessions/${chatSessionId}/messages`,
        { method: "GET" }
      );

      const data = await res.json();

      if (!res.ok || data.success === false) {
        throw new Error(data.message || "Failed to load messages");
      }

      const mappedMessages = mapBackendMessagesToUi(data.messages || []);
      const restoredQuickSnapContext = data.quick_snap_context || null;

      setActiveChatSessionId(chatSessionId);
      setQuickSnapContext(restoredQuickSnapContext);
      setIsQuickSnapCardExpanded(false);

      if (restoredQuickSnapContext) {
        setMessages([
          {
            sender: "bot",
            text: "",
            isQuickSnapIntro: true,
          },
          ...mappedMessages,
        ]);
      } else {
        setMessages(mappedMessages.length ? mappedMessages : buildWelcomeMessages());
      }

      if (switchToChat) {
        setView("chat");
      }
    } catch (error) {
      console.error("Failed to load chat session messages:", error);
    }
  };

  const handleNewChat = () => {
    setQuickSnapContext(null);
    resetToFreshChat();
  };

  const toggleHistory = async () => {
    const nextView = view === "history" ? "chat" : "history";
    setView(nextView);

    if (nextView === "history") {
      await fetchChatSessions();
    }
  };

  const startEditTitle = (session) => {
    setEditingSessionId(session.chat_session_id);
    setEditingTitleValue(session.title || "");
  };

  const cancelEditTitle = () => {
    setEditingSessionId(null);
    setEditingTitleValue("");
  };

  const saveEditedTitle = async (sessionId) => {
    const trimmedTitle = editingTitleValue.trim();
    if (!trimmedTitle) return;

    try {
      const res = await apiFetch(
        `${process.env.REACT_APP_API_BASE_URL}/api/chat/sessions/${sessionId}/title`,
        {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ title: trimmedTitle }),
        }
      );

      const data = await res.json();

      if (!res.ok || data.success === false) {
        throw new Error(data.message || "Failed to update title");
      }

      setEditingSessionId(null);
      setEditingTitleValue("");
      await fetchChatSessions();
    } catch (error) {
      console.error("Failed to update chat title:", error);
    }
  };

  const openDeleteConfirm = (session) => {
    setDeleteTargetSession(session);
  };

  const closeDeleteConfirm = () => {
    setDeleteTargetSession(null);
  };

  const confirmDeleteChat = async () => {
    if (!deleteTargetSession) return;

    try {
      const res = await apiFetch(
        `${process.env.REACT_APP_API_BASE_URL}/api/chat/sessions/${deleteTargetSession.chat_session_id}`,
        { method: "DELETE" }
      );

      const data = await res.json();

      if (!res.ok || data.success === false) {
        throw new Error(data.message || "Failed to delete chat");
      }

      if (deleteTargetSession.chat_session_id === activeChatSessionId) {
        resetToFreshChat();
      }

      closeDeleteConfirm();
      await fetchChatSessions();
    } catch (error) {
      console.error("Failed to delete chat:", error);
      closeDeleteConfirm();
    }
  };

  const typeAssistantReply = (
    fullText,
    requestId,
    tutoringMode = null,
    showQuickSnapCta = false
  ) => {
    stopTypingTimer();
    setIsTypingReply(true);

    let index = 0;
    const chunkSize = 3;

    setMessages((prev) => [
      ...prev,
      {
        sender: "bot",
        text: "",
        tutoringMode,
        showQuickSnapCta,
      },
    ]);

    typingTimerRef.current = setInterval(() => {
      if (activeRequestIdRef.current !== requestId) {
        stopTypingTimer();
        setIsTypingReply(false);
        return;
      }

      index += chunkSize;
      const partialText = fullText.slice(0, index);

      setMessages((prev) => {
        const updated = [...prev];

        if (updated.length > 0) {
          updated[updated.length - 1] = {
            ...updated[updated.length - 1],
            text: partialText,
          };
        }

        return updated;
      });

      if (index >= fullText.length) {
        stopTypingTimer();
        setIsTypingReply(false);
      }
    }, 18);
  };

  const handleSendMessage = async () => {
    logUserActivity("used_chatbot");

    if (!inputMessage.trim() || isLoading || isTypingReply) return;

    const userMessage = inputMessage.trim();
    const requestId = Date.now();
    activeRequestIdRef.current = requestId;

    setInputMessage("");
    setShowSymbolPad(false);
    setIsLoading(true);

    setMessages((prev) => {
      const base = prev.length === 1 && prev[0]?.isWelcome ? [] : prev;
      return [...base, { sender: "user", text: userMessage }];
    });

    try {
      const res = await apiFetch(`${process.env.REACT_APP_API_BASE_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: userMessage,
          language,
          chat_session_id: activeChatSessionId,
          quick_snap_context: activeChatSessionId ? null : quickSnapContext || null,
        }),
      });

      const data = await res.json();

      if (activeRequestIdRef.current !== requestId) return;

      if (!res.ok || data.success === false) {
        throw new Error(data.message || "Failed to send message");
      }

      if (data.chat_session_id) {
        setActiveChatSessionId(data.chat_session_id);
      }

      setIsLoading(false);

      typeAssistantReply(
        data.reply || t("chatbot_error"),
        requestId,
        data.tutoring_mode || null,
        Boolean(data.show_quick_snap_cta)
      );

      await fetchChatSessions();
    } catch (error) {
      if (activeRequestIdRef.current !== requestId) return;

      console.error("Chatbot API Error:", error);

      setMessages((prev) => [
        ...prev,
        {
          sender: "bot",
          text: t("chatbot_error"),
        },
      ]);

      setIsLoading(false);
    }
  };

  const formatMath = (text) => {
    if (!text) return "";

    return text
      .split("\\(")
      .join("$")
      .split("\\)")
      .join("$")
      .split("\\[")
      .join("$$")
      .split("\\]")
      .join("$$");
  };

  const messageContentSx = {
    fontSize: "14px",
    wordBreak: "break-word",
    overflowWrap: "anywhere",

    "& p": {
      margin: "0 0 10px 0",
      lineHeight: 1.75,
    },

    "& p:last-child": {
      marginBottom: 0,
    },

    "& ul, & ol": {
      margin: "8px 0 10px 20px",
      paddingLeft: "16px",
    },

    "& li": {
      marginBottom: "6px",
      lineHeight: 1.7,
    },

    "& strong": {
      fontWeight: 800,
    },

    "& pre": {
      whiteSpace: "pre-wrap",
      wordBreak: "break-word",
      overflowX: "auto",
      margin: "10px 0",
    },

    "& code": {
      whiteSpace: "pre-wrap",
      wordBreak: "break-word",
    },

    "& .katex-display": {
      margin: "0.75em 0",
      overflowX: "auto",
      overflowY: "hidden",
    },

    "& table": {
      display: "block",
      overflowX: "auto",
      maxWidth: "100%",
    },
  };

  const renderThinkingIndicator = (label) => (
    <Box sx={{ alignSelf: "flex-start", maxWidth: "80%" }}>
      <Paper
        elevation={0}
        sx={{
          p: 1.2,
          borderRadius: "16px 16px 16px 6px",
          bgcolor: "#ffffff",
          color: "#111827",
          border: "1px solid #E5E7EB",
          boxShadow: "0 8px 22px rgba(17, 24, 39, 0.06)",
        }}
      >
        <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
          <Typography
            variant="caption"
            sx={{ color: "textSecondary", fontStyle: "italic" }}
          >
            {label}
          </Typography>

          <Box sx={{ display: "flex", gap: 0.4 }}>
            {[0, 1, 2].map((dot) => (
              <Box
                key={dot}
                sx={{
                  width: 6,
                  height: 6,
                  borderRadius: "50%",
                  bgcolor: "#3855c0",
                  animation: `${dotsAnimation} 1s infinite`,
                  animationDelay: `${dot * 0.15}s`,
                }}
              />
            ))}
          </Box>
        </Box>
      </Paper>
    </Box>
  );

  const renderQuickSnapCta = () => (
    <Button
      size="small"
      startIcon={<CameraAltOutlinedIcon />}
      onClick={handleGoToQuickSnapCheck}
      sx={{
        mt: 1,
        ml: 0.5,
        borderRadius: "14px",
        textTransform: "none",
        fontWeight: 800,
        fontSize: "12px",
        px: 1.6,
        py: 0.75,
        bgcolor: "#EEF2FF",
        color: "#3855c0",
        border: "1px solid #C7D2FE",
        boxShadow: "0 6px 16px rgba(56, 85, 192, 0.10)",
        "&:hover": {
          bgcolor: "#E0E7FF",
        },
      }}
    >
      {language === "bm" ? "Pergi ke Quick Snap" : "Go to Quick Snap"}
    </Button>
  );

  const renderSymbolPad = () => (
    <Paper
      elevation={0}
      sx={{
        mb: 1,
        p: 1,
        borderRadius: "14px",
        bgcolor: "#F8FAFF",
        border: "1px solid #E0E7FF",
        display: "flex",
        flexWrap: "wrap",
        gap: 0.7,
      }}
    >
      {mathSymbols.map((symbol) => (
        <Tooltip key={symbol.label} title={symbol.title}>
          <Button
            size="small"
            onClick={() =>
              insertEasyLearnmbol(symbol.insert, symbol.cursorBack || 0)
            }
            sx={{
              minWidth: 34,
              height: 30,
              px: 0.8,
              borderRadius: "10px",
              textTransform: "none",
              fontWeight: 800,
              fontSize: "14px",
              bgcolor: "#ffffff",
              color: "#3855c0",
              border: "1px solid #DDE3FF",
              "&:hover": {
                bgcolor: "#EEF2FF",
                borderColor: "#C7D2FE",
              },
            }}
          >
            {symbol.label}
          </Button>
        </Tooltip>
      ))}
    </Paper>
  );

  const getQuickSnapFeedbackItems = () => {
    if (!quickSnapContext) return [];

    if (quickSnapContext.mode !== "check_my_work") return [];

    const summary = quickSnapContext.correctness_summary;

    if (!summary || !Array.isArray(summary.stepwise_evaluation)) {
      return [];
    }

    return summary.stepwise_evaluation.map((step, index) => ({
      id: index,
      step: step.step || `Step ${index + 1}`,
      student_wrote: step.student_wrote || "",
      reason: step.reason || "",
      marks_awarded: step.marks_awarded ?? 0,
      max_marks: step.max_marks ?? 1,
    }));
  };

  const getQuickSnapAnswerText = () => {
    if (!quickSnapContext) return "";

    if (quickSnapContext.mode === "solve_question") {
      if (quickSnapContext.final_answer) {
        const finalAnswer = quickSnapContext.final_answer;

        if (typeof finalAnswer === "object" && finalAnswer !== null) {
          return Object.entries(finalAnswer)
            .map(([key, value]) => {
              const label = key.startsWith("(") ? key : `(${key})`;
              return `${label} ${value}`;
            })
            .join("\n");
        }

        return String(finalAnswer);
      }

      if (quickSnapContext.result_summary) {
        return String(quickSnapContext.result_summary);
      }

      if (Array.isArray(quickSnapContext.steps) && quickSnapContext.steps.length > 0) {
        const lastStep = quickSnapContext.steps[quickSnapContext.steps.length - 1];
        return String(lastStep?.math || lastStep?.text || "");
      }

      return "";
    }

    if (quickSnapContext.mode === "check_my_work") {
      const scoreText =
        quickSnapContext.score !== null && quickSnapContext.score !== undefined
          ? `Score: ${quickSnapContext.score}${
              quickSnapContext.max_score ? ` / ${quickSnapContext.max_score}` : ""
            }`
          : "";

      const summary = quickSnapContext.correctness_summary;

      if (summary?.overall_feedback) {
        return `${scoreText}\n${summary.overall_feedback}`.trim();
      }

      return scoreText;
    }

    return "";
  };

  const renderTextWithAutoMath = (text) => {
    if (!text) return null;

    const renderMathInline = (mathContent, index) => {
      const normalizedMath = mathContent
        .replace(/×/g, "\\times")
        .replace(/\^(\d+)/g, "^{$1}");

      try {
        return (
          <Box
            component="span"
            key={index}
            sx={{
              color: "#2563EB",
              mx: 0.25,
              maxWidth: "100%",
              overflowWrap: "anywhere",
              wordBreak: "break-word",
              verticalAlign: "baseline",
              "& .katex": {
                whiteSpace: "normal",
                maxWidth: "100%",
              },
              "& .katex-html": {
                whiteSpace: "normal",
                maxWidth: "100%",
              },
            }}
            dangerouslySetInnerHTML={{
              __html: katex.renderToString(normalizedMath, {
                throwOnError: false,
                displayMode: false,
              }),
            }}
          />
        );
      } catch {
        return <span key={index}>{mathContent}</span>;
      }
    };

    const explicitParts = String(text).split(
      /(\\\([\s\S]*?\\\)|\$[^$]+\$)/g
    );

    return explicitParts.flatMap((part, partIndex) => {
      if (!part) return null;

      if (part.startsWith("\\(") && part.endsWith("\\)")) {
        return renderMathInline(part.slice(2, -2), `explicit-${partIndex}`);
      }

      if (part.startsWith("$") && part.endsWith("$")) {
        return renderMathInline(part.slice(1, -1), `dollar-${partIndex}`);
      }

      const autoMathRegex =
        /((?:\(?[-+]?\d*[a-zA-Z](?:\^\d+)?\)?|\(?[-+]?\d+(?:\.\d+)?\)?)(?:\s*(?:[+\-*/×=]|\)\()\s*(?:\(?[-+]?\d*[a-zA-Z](?:\^\d+)?\)?|\(?[-+]?\d+(?:\.\d+)?\)?))+)/g;

      return part.split(autoMathRegex).map((subPart, subIndex) => {
        if (!subPart) return null;

        const looksLikeMath = autoMathRegex.test(subPart);
        autoMathRegex.lastIndex = 0;

        // Avoid converting normal English sentences into KaTeX.
        const hasLongWords = /[A-Za-z]{3,}/.test(subPart);

        if (looksLikeMath && !hasLongWords && subPart.length <= 80) {
          return renderMathInline(subPart, `auto-${partIndex}-${subIndex}`);
        }

        return (
          <span
            key={`text-${partIndex}-${subIndex}`}
            style={{
              overflowWrap: "anywhere",
              wordBreak: "break-word",
            }}
          >
            {subPart}
          </span>
        );
      });
    });
  };

  const renderQuickSnapFeedbackPreview = () => {
    const feedbackItems = getQuickSnapFeedbackItems();

    if (!feedbackItems.length) {
      const answerText = getQuickSnapAnswerText();

      if (!answerText) return null;

      return (
        <Typography
          variant="body2"
          sx={{
            color: "#374151",
            mt: 0.5,
            whiteSpace: "pre-wrap",
            lineHeight: 1.5,
            display: isQuickSnapCardExpanded ? "block" : "-webkit-box",
            WebkitLineClamp: isQuickSnapCardExpanded ? "unset" : 3,
            WebkitBoxOrient: "vertical",
            overflow: "hidden",
          }}
        >
          {renderTextWithAutoMath(answerText)}
        </Typography>
      );
    }

    const visibleItems = isQuickSnapCardExpanded
      ? feedbackItems
      : feedbackItems.slice(0, 2);

    return (
      <Box sx={{ display: "flex", flexDirection: "column", gap: 1, mt: 0.8 }}>
        {quickSnapContext?.score !== null && quickSnapContext?.score !== undefined && (
          <Chip
            size="small"
            label={`Score: ${quickSnapContext.score} / ${quickSnapContext.max_score ?? "-"}`}
            sx={{
              alignSelf: "flex-start",
              bgcolor: "#ECFDF5",
              color: "#047857",
              border: "1px solid #A7F3D0",
              fontWeight: 800,
            }}
          />
        )}

        {visibleItems.map((item) => {
          const marksAwarded = Number(item.marks_awarded ?? 0);
          const maxMarks = Number(item.max_marks ?? 1);

          const isFull = marksAwarded === maxMarks;
          const isZero = marksAwarded === 0;

          const chipColor = isFull ? "#047857" : isZero ? "#DC2626" : "#D97706";
          const chipBg = isFull ? "#ECFDF5" : isZero ? "#FEF2F2" : "#FFFBEB";
          const borderColor = isFull ? "#A7F3D0" : isZero ? "#FECACA" : "#FDE68A";

          return (
            <Box
              key={item.id}
              sx={{
                p: 1.1,
                borderRadius: "10px",
                bgcolor: "#FFFFFF",
                border: `1px solid ${borderColor}`,
                minWidth: 0,
                maxWidth: "100%",
                overflow: "hidden",
              }}
            >
              <Box
                sx={{
                  display: "flex",
                  justifyContent: "space-between",
                  gap: 1,
                  alignItems: "flex-start",
                  mb: 0.6,
                }}
              >
                <Typography
                  variant="body2"
                  fontWeight={800}
                  sx={{
                    color: "#111827",
                    fontSize: "12.5px",
                    lineHeight: 1.35,
                    flex: 1,
                    minWidth: 0,
                    overflowWrap: "anywhere",
                    wordBreak: "break-word",
                  }}
                >
                  {item.step}
                </Typography>

                <Chip
                  size="small"
                  label={`${marksAwarded}/${maxMarks}`}
                  sx={{
                    height: 21,
                    bgcolor: chipBg,
                    color: chipColor,
                    border: `1px solid ${borderColor}`,
                    fontWeight: 800,
                    fontSize: "10px",
                    flexShrink: 0,
                  }}
                />
              </Box>

              {item.student_wrote && (
                <Typography
                  variant="caption"
                  sx={{
                    display: "block",
                    color: "#6B7280",
                    mb: 0.4,
                    fontFamily: "monospace",
                    bgcolor: "#F9FAFB",
                    px: 0.8,
                    py: 0.5,
                    borderRadius: "6px",
                    whiteSpace: "pre-wrap",
                    overflowWrap: "anywhere",
                    wordBreak: "break-word",
                    maxWidth: "100%",
                  }}
                >
                  {renderTextWithAutoMath(item.student_wrote)}
                </Typography>
              )}

              <Typography
                variant="caption"
                sx={{
                  color: "#4B5563",
                  lineHeight: 1.45,
                  display: "block",
                  overflowWrap: "anywhere",
                  wordBreak: "break-word",
                  maxWidth: "100%",
                }}
              >
                {renderTextWithAutoMath(item.reason)}
              </Typography>
            </Box>
          );
        })}

        {!isQuickSnapCardExpanded && feedbackItems.length > 2 && (
          <Typography variant="caption" sx={{ color: "#6B7280", fontWeight: 700 }}>
            + {feedbackItems.length - 2} more marking steps
          </Typography>
        )}
      </Box>
    );
  };

  const renderQuickSnapFollowUpCard = () => {
    const isCheckWork = quickSnapContext?.mode === "check_my_work";
    const questionText = quickSnapContext?.question_text || "Quick Snap result";
    const answerText = getQuickSnapAnswerText();

    return (
      <Paper
        elevation={0}
        sx={{
          p: 1.6,
          borderRadius: "16px",
          background: "linear-gradient(135deg, #EEF2FF 0%, #ECFDF5 100%)",
          border: "1px solid #C7D2FE",
          boxShadow: "0 8px 24px rgba(56, 85, 192, 0.08)",
        }}
      >
        <Typography fontWeight={900} sx={{ color: "#111827", mb: 0.7, fontSize: 14 }}>
          {language === "bm"
            ? "Mod Follow-up Quick Snap"
            : "Quick Snap Follow-Up Mode"}
        </Typography>

        <Typography
          variant="body2"
          sx={{ color: "#374151", lineHeight: 1.55, mb: 1.2, fontSize: 12.5 }}
        >
          {language === "bm"
            ? "Anda sedang bertanya tentang keputusan Quick Snap tadi."
            : "You are asking about the Quick Snap result."}
        </Typography>

        <Box
          sx={{
            p: 1.2,
            borderRadius: "12px",
            bgcolor: "#ffffff",
            border: "1px solid #E5E7EB",
            mb: 1,
          }}
        >
          <Typography
            variant="caption"
            fontWeight={800}
            sx={{ color: "#6B7280", textTransform: "uppercase", display: "block" }}
          >
            {isCheckWork
              ? language === "bm"
                ? "Semakan Kerja"
                : "Check My Work"
              : language === "bm"
                ? "Penyelesaian Soalan"
                : "Solve Question"}
          </Typography>

          <Typography
            variant="caption"
            fontWeight={800}
            sx={{ color: "#3855c0", display: "block", mt: 0.8 }}
          >
            {language === "bm" ? "Soalan" : "Question"}
          </Typography>

          <Typography
            variant="body2"
            fontWeight={700}
            sx={{
              color: "#111827",
              mt: 0.3,
              whiteSpace: "pre-wrap",
              display: isQuickSnapCardExpanded ? "block" : "-webkit-box",
              WebkitLineClamp: isQuickSnapCardExpanded ? "unset" : 2,
              WebkitBoxOrient: "vertical",
              overflow: "hidden",
            }}
          >
            {questionText}
          </Typography>

          {answerText && (
            <>
              <Typography
                variant="caption"
                fontWeight={800}
                sx={{ color: "#059669", display: "block", mt: 1.2 }}
              >
                {isCheckWork
                  ? language === "bm"
                    ? "Maklum Balas"
                    : "Feedback"
                  : language === "bm"
                    ? "Jawapan"
                    : "Answer"}
              </Typography>

              {isCheckWork ? (
                renderQuickSnapFeedbackPreview()
              ) : (
                <Typography
                  variant="body2"
                  sx={{
                    color: "#374151",
                    mt: 0.3,
                    whiteSpace: "pre-wrap",
                    display: isQuickSnapCardExpanded ? "block" : "-webkit-box",
                    WebkitLineClamp: isQuickSnapCardExpanded ? "unset" : 2,
                    WebkitBoxOrient: "vertical",
                    overflow: "hidden",
                    lineHeight: 1.5,
                    overflowWrap: "anywhere",
                    wordBreak: "break-word",
                  }}
                >
                  {renderTextWithAutoMath(answerText)}
                </Typography>
              )}
            </>
          )}
        </Box>

        <Button
          size="small"
          endIcon={isQuickSnapCardExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
          onClick={() => setIsQuickSnapCardExpanded((prev) => !prev)}
          sx={{
            textTransform: "none",
            fontWeight: 800,
            fontSize: "12px",
            color: "#3855c0",
            px: 0,
            minWidth: "auto",
          }}
        >
          {isQuickSnapCardExpanded
            ? language === "bm"
              ? "Tunjuk kurang"
              : "Show less"
            : language === "bm"
              ? "Tunjuk lagi"
              : "Show more"}
        </Button>
      </Paper>
    );
  };

  const renderWelcomeCard = () => (
    <Paper
      elevation={0}
      sx={{
        p: 2,
        borderRadius: "18px",
        background: "linear-gradient(135deg, #EEF2FF 0%, #FDF2F8 100%)",
        border: "1px solid #E0E7FF",
        boxShadow: "0 8px 24px rgba(56, 85, 192, 0.08)",
      }}
    >
      <Box sx={{ display: "flex", alignItems: "center", gap: 1.5, mb: 1 }}>
        <Box
          sx={{
            width: 38,
            height: 38,
            borderRadius: "12px",
            bgcolor: "#ffffff",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            boxShadow: "0 6px 16px rgba(56, 85, 192, 0.12)",
          }}
        >
          <AutoAwesomeRoundedIcon sx={{ color: "#3855c0", fontSize: 22 }} />
        </Box>

        <Box>
          <Typography fontWeight="bold" sx={{ color: "#111827", fontSize: 14 }}>
            {language === "bm" ? "Hai, saya EasyLearn Buddy!" : "Hi, I’m EasyLearn Buddy!"}
          </Typography>

          <Typography variant="caption" sx={{ color: "#6B7280" }}>
            {language === "bm"
              ? "Saya boleh bantu anda belajar Matematik SPM."
              : "I can help you learn SPM Mathematics."}
          </Typography>
        </Box>
      </Box>

      <Typography
        variant="body2"
        sx={{
          color: "#374151",
          lineHeight: 1.55,
          mb: 1.5,
        }}
      >
        {t("chatbot_welcome")}
      </Typography>

      <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1 }}>
        {quickPrompts.map((prompt) => (
          <Button
            key={prompt.label}
            size="small"
            startIcon={prompt.icon}
            onClick={() => handleQuickPrompt(prompt.text)}
            disabled={isLoading || isTypingReply}
            sx={{
              textTransform: "none",
              borderRadius: "14px",
              px: 1.4,
              py: 0.7,
              bgcolor: "#ffffff",
              color: "#3855c0",
              fontWeight: 700,
              fontSize: "12px",
              border: "1px solid #DDE3FF",
              boxShadow: "0 4px 12px rgba(56, 85, 192, 0.08)",
              "&:hover": {
                bgcolor: "#F8FAFF",
                borderColor: "#3855c0",
              },
            }}
          >
            {prompt.label}
          </Button>
        ))}
      </Box>
    </Paper>
  );

  return (
    <>
      <Box ref={chatbotContainerRef}>
        {!isOpen && showNudge && (
          <Paper
            onClick={handleOpenChat}
            elevation={0}
            sx={{
              position: "fixed",
              bottom: 100,
              right: 94,
              zIndex: 1000,
              px: 1.6,
              py: 1,
              borderRadius: "16px 16px 4px 16px",
              bgcolor: "#ffffff",
              border: "1px solid #E0E7FF",
              boxShadow: "0 10px 28px rgba(56, 85, 192, 0.16)",
              cursor: "pointer",
              maxWidth: 190,
              animation: `${floatAnimation} 3s ease-in-out infinite`,
              "&:hover": {
                bgcolor: "#F8FAFF",
                borderColor: "#C7D2FE",
              },
            }}
          >
            <Typography
              sx={{
                fontSize: "13px",
                fontWeight: 800,
                color: "#3855c0",
                lineHeight: 1.35,
              }}
            >
              {language === "bm"
                ? "Tanya saya apa-apa!"
                : "Come ask me anything!"}
            </Typography>

            <Typography
              sx={{
                fontSize: "11px",
                color: "#6B7280",
                mt: 0.2,
              }}
            >
              {language === "bm"
                ? "Saya boleh bantu Matematik SPM."
                : "I can help with SPM Math."}
            </Typography>
          </Paper>
        )}

        <Tooltip
          title={!isOpen && !showNudge ? t("chatbot_fab_tooltip") : ""}
          placement="left"
          arrow
        >
          <Fab
            key={isOpen ? "chatbot-open" : "chatbot-closed"}
            aria-label="chat"
            disableRipple
            disableFocusRipple
            disableTouchRipple
            onClick={isOpen ? handleCloseChat : handleOpenChat}
            sx={{
              position: "fixed",
              bottom: 24,
              right: 24,
              zIndex: 1000,
              width: isOpen ? 58 : 88,
              height: isOpen ? 58 : 88,
              minHeight: isOpen ? 58 : 88,
              backgroundColor: isOpen ? "#3855c0" : "transparent !important",
              border: "none",
              boxShadow: isOpen
                ? "0 14px 30px rgba(56, 85, 192, 0.25)"
                : "none",
              overflow: "visible",
              transition: "none",

              "&:hover": {
                backgroundColor: isOpen ? "#2d4499" : "transparent !important",
                boxShadow: isOpen
                  ? "0 14px 30px rgba(56, 85, 192, 0.25)"
                  : "none",
              },

              "&:active": {
                backgroundColor: isOpen ? "#2d4499" : "transparent !important",
                boxShadow: "none",
              },

              "&:focus": {
                backgroundColor: isOpen ? "#3855c0" : "transparent !important",
                boxShadow: isOpen
                  ? "0 14px 30px rgba(56, 85, 192, 0.25)"
                  : "none",
              },

              "&.Mui-focusVisible": {
                backgroundColor: isOpen ? "#3855c0" : "transparent !important",
                boxShadow: isOpen
                  ? "0 14px 30px rgba(56, 85, 192, 0.25)"
                  : "none",
              },

              animation: !isOpen
                ? `${floatAnimation} 3s ease-in-out infinite`
                : "none",
            }}
          >
            {isOpen ? (
              <CloseIcon sx={{ color: "white", fontSize: 24 }} />
            ) : (
              <Box
                component="img"
                src={mathsyCatGif}
                alt="EasyLearn Buddy"
                sx={{
                  width: 88,
                  height: 88,
                  objectFit: "contain",
                  transform: "scale(1.85)",
                  transformOrigin: "center",
                  filter: "drop-shadow(0 12px 18px rgba(56, 85, 192, 0.22))",
                  pointerEvents: "none",
                  userSelect: "none",
                }}
              />
            )}
          </Fab>
        </Tooltip>

        {isOpen && (
          <Paper
            elevation={10}
            sx={{
              position: "fixed",
              bottom: 92,
              right: 24,
              width: { xs: "90vw", sm: "360px" },
              height: "500px",
              maxHeight: "80vh",
              zIndex: 1000,
              borderRadius: "20px",
              display: "flex",
              flexDirection: "column",
              overflow: "hidden",
              background: "#ffffff",
              border: "1px solid rgba(229, 231, 235, 0.9)",
              boxShadow: "0 24px 70px rgba(17, 24, 39, 0.22)",
            }}
          >
            <Box
              sx={{
                background:
                  "linear-gradient(135deg, #495ead 0%, #809af1 55%, #5672ce 100%)",
                color: "white",
                p: 1.6,
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                flexShrink: 0,
              }}
            >
              <Box sx={{ display: "flex", alignItems: "center", gap: 1.5 }}>
                <Box
                  component="img"
                  src={chatbotAvatar}
                  alt="EasyLearn Tutor"
                  sx={{
                    width: 44,
                    height: 44,
                    objectFit: "contain",
                    filter: "drop-shadow(0 6px 12px rgba(0,0,0,0.18))",
                    userSelect: "none",
                    pointerEvents: "none",
                  }}
                />

                <Box>
                  <Typography variant="subtitle2" fontWeight="bold" lineHeight={1.2}>
                    {t("chatbot_title")}
                  </Typography>

                  <Typography
                    variant="caption"
                    sx={{ color: "#BBF7D0", fontWeight: "bold" }}
                  >
                    ● {t("chatbot_online")}
                  </Typography>
                </Box>
              </Box>

              <Box sx={{ display: "flex", gap: 0 }}>
                <Tooltip title={t("chatbot_history")}>
                  <IconButton
                    size="small"
                    onClick={toggleHistory}
                    sx={{
                      color: "white",
                      opacity: view === "history" ? 1 : 0.75,
                      "&:hover": {
                        opacity: 1,
                        bgcolor: "rgba(255,255,255,0.12)",
                      },
                    }}
                  >
                    <MenuIcon fontSize="small" />
                  </IconButton>
                </Tooltip>

                <Tooltip title={t("chatbot_new_chat")}>
                  <IconButton
                    size="small"
                    onClick={handleNewChat}
                    sx={{
                      color: "white",
                      opacity: 0.75,
                      "&:hover": {
                        opacity: 1,
                        bgcolor: "rgba(255,255,255,0.12)",
                      },
                    }}
                  >
                    <AddIcon fontSize="small" />
                  </IconButton>
                </Tooltip>

                <Tooltip
                  title={
                    isLoading || isTypingReply
                      ? t("chatbot_expand_busy")
                      : t("chatbot_open_full_page")
                  }
                >
                  <span>
                    <IconButton
                      size="small"
                      onClick={handleOpenFullChatbotPage}
                      disabled={isLoading || isTypingReply}
                      sx={{
                        color: "white",
                        opacity: isLoading || isTypingReply ? 0.45 : 0.75,
                        "&:hover": {
                          opacity: 1,
                          bgcolor: "rgba(255,255,255,0.12)",
                        },
                      }}
                    >
                      <LaunchOutlinedIcon fontSize="small" />
                    </IconButton>
                  </span>
                </Tooltip>

                <IconButton
                  size="small"
                  onClick={handleCloseChat}
                  sx={{
                    color: "white",
                    ml: 0.5,
                    "&:hover": {
                      bgcolor: "rgba(255,255,255,0.12)",
                    },
                  }}
                >
                  <CloseIcon fontSize="small" />
                </IconButton>
              </Box>
            </Box>

            <Box
              sx={{
                flex: 1,
                minHeight: 0,
                background:
                  view === "history"
                    ? "#F9FAFB"
                    : "linear-gradient(180deg, #F8FAFF 0%, #F9FAFB 100%)",
                display: "flex",
                flexDirection: "column",
                overflow: "hidden",
              }}
            >
              {view === "history" ? (
                <Box sx={{ p: 2, overflowY: "auto", flex: 1 }}>
                  <Typography fontWeight="bold" mb={2} color="#111827">
                    {t("chatbot_history_title")}
                  </Typography>

                  {sessions.length === 0 ? (
                    <Paper
                      sx={{
                        p: 2,
                        borderRadius: "16px",
                        border: "1px solid #E5E7EB",
                        boxShadow: "none",
                        bgcolor: "#ffffff",
                      }}
                    >
                      <Typography variant="body2" fontWeight="600" color="#111827">
                        {t("chatbot_history_empty")}
                      </Typography>

                      <Typography variant="caption" color="textSecondary">
                        {t("chatbot_history_hint")}
                      </Typography>
                    </Paper>
                  ) : (
                    <Box sx={{ display: "flex", flexDirection: "column", gap: 1.25 }}>
                      {sessions.map((session) => {
                        const isActive =
                          session.chat_session_id === activeChatSessionId;
                        const isEditing =
                          editingSessionId === session.chat_session_id;

                        return (
                          <Paper
                            key={session.chat_session_id}
                            onClick={() =>
                              !isEditing && loadChatSession(session.chat_session_id, true)
                            }
                            sx={{
                              p: 1.5,
                              borderRadius: "14px",
                              border: isActive
                                ? "1px solid #3855c0"
                                : "1px solid #E5E7EB",
                              boxShadow: isActive
                                ? "0 8px 22px rgba(56, 85, 192, 0.10)"
                                : "none",
                              bgcolor: isActive ? "#EEF2FF" : "#ffffff",
                              cursor: isEditing ? "default" : "pointer",
                              transition: "all 0.2s ease",
                              "&:hover": {
                                bgcolor: isEditing
                                  ? isActive
                                    ? "#EEF2FF"
                                    : "#ffffff"
                                  : isActive
                                    ? "#E7EDFF"
                                    : "#F9FAFB",
                              },
                            }}
                          >
                            <Box
                              sx={{
                                display: "flex",
                                alignItems: "flex-start",
                                justifyContent: "space-between",
                                gap: 1,
                              }}
                            >
                              <Box sx={{ flex: 1, minWidth: 0 }}>
                                {isEditing ? (
                                  <Box
                                    sx={{
                                      display: "flex",
                                      alignItems: "center",
                                      gap: 0.5,
                                    }}
                                  >
                                    <TextField
                                      size="small"
                                      value={editingTitleValue}
                                      autoFocus
                                      onChange={(e) =>
                                        setEditingTitleValue(e.target.value)
                                      }
                                      onKeyDown={(e) => {
                                        if (e.key === "Enter") {
                                          saveEditedTitle(session.chat_session_id);
                                        }

                                        if (e.key === "Escape") {
                                          cancelEditTitle();
                                        }
                                      }}
                                      sx={{
                                        flex: 1,
                                        "& .MuiOutlinedInput-root": {
                                          bgcolor: "#ffffff",
                                          borderRadius: "10px",
                                        },
                                      }}
                                    />

                                    <IconButton
                                      size="small"
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        saveEditedTitle(session.chat_session_id);
                                      }}
                                      sx={{ color: "#3855c0" }}
                                    >
                                      <CheckIcon fontSize="small" />
                                    </IconButton>

                                    <IconButton
                                      size="small"
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        cancelEditTitle();
                                      }}
                                      sx={{ color: "#6B7280" }}
                                    >
                                      <CloseOutlinedIcon fontSize="small" />
                                    </IconButton>
                                  </Box>
                                ) : (
                                  <>
                                    <Typography
                                      variant="body2"
                                      fontWeight="bold"
                                      color="#111827"
                                      sx={{
                                        mb: 0.5,
                                        overflow: "hidden",
                                        textOverflow: "ellipsis",
                                        whiteSpace: "nowrap",
                                      }}
                                    >
                                      {session.title || t("chatbot_new_chat")}
                                    </Typography>

                                    {session.is_quick_snap_session && (
                                      <Chip
                                        size="small"
                                        label={language === "bm" ? "Follow-up Quick Snap" : "Quick Snap Follow-up"}
                                        icon={<CameraAltOutlinedIcon sx={{ fontSize: "14px !important" }} />}
                                        sx={{
                                          height: 22,
                                          mb: 0.6,
                                          borderRadius: "8px",
                                          bgcolor: "#ECFDF5",
                                          color: "#047857",
                                          border: "1px solid #A7F3D0",
                                          fontWeight: 800,
                                          fontSize: "10.5px",
                                          "& .MuiChip-icon": {
                                            color: "#047857",
                                            ml: "6px",
                                          },
                                        }}
                                      />
                                    )}

                                    <Typography
                                      variant="caption"
                                      sx={{
                                        color: "#6B7280",
                                        display: "block",
                                        overflow: "hidden",
                                        textOverflow: "ellipsis",
                                        whiteSpace: "nowrap",
                                      }}
                                    >
                                      {session.last_message_preview ||
                                        t("chatbot_history_loading")}
                                    </Typography>
                                  </>
                                )}
                              </Box>

                              {!isEditing && (
                                <Box
                                  sx={{
                                    display: "flex",
                                    alignItems: "center",
                                    gap: 0.25,
                                  }}
                                >
                                  <Tooltip title={t("chatbot_edit_title")}>
                                    <IconButton
                                      size="small"
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        startEditTitle(session);
                                      }}
                                      sx={{ color: "#6B7280" }}
                                    >
                                      <EditOutlinedIcon fontSize="small" />
                                    </IconButton>
                                  </Tooltip>

                                  <Tooltip title={t("chatbot_delete_chat")}>
                                    <IconButton
                                      size="small"
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        openDeleteConfirm(session);
                                      }}
                                      sx={{ color: "#6B7280" }}
                                    >
                                      <DeleteOutlineIcon fontSize="small" />
                                    </IconButton>
                                  </Tooltip>
                                </Box>
                              )}
                            </Box>
                          </Paper>
                        );
                      })}
                    </Box>
                  )}
                </Box>
              ) : (
                <Box
                  sx={{
                    p: 2,
                    display: "flex",
                    flexDirection: "column",
                    gap: 2,
                    overflowY: "auto",
                    overflowX: "hidden",
                    flex: 1,
                    minHeight: 0,
                  }}
                >
                  {messages.map((msg, index) => {
                    if (msg.isQuickSnapIntro) {
                      return (
                        <Box key={msg.id || index} sx={{ alignSelf: "stretch" }}>
                          {renderQuickSnapFollowUpCard()}
                        </Box>
                      );
                    }
                    if (msg.isWelcome) {
                      return (
                        <Box key={msg.id || index} sx={{ alignSelf: "stretch" }}>
                          {renderWelcomeCard()}
                        </Box>
                      );
                    }

                    return (
                      <Box
                        key={msg.id || index}
                        sx={{
                          alignSelf:
                            msg.sender === "user" ? "flex-end" : "flex-start",
                          width: "100%",
                          display: "flex",
                          flexDirection: "column",
                          alignItems:
                            msg.sender === "user" ? "flex-end" : "flex-start",
                        }}
                      >
                        <Paper
                          elevation={0}
                          sx={{
                            p: 1.5,
                            maxWidth: "85%",
                            minWidth: 0,
                            overflow: "hidden",
                            borderRadius:
                              msg.sender === "user"
                                ? "16px 16px 6px 16px"
                                : "16px 16px 16px 6px",
                            bgcolor: msg.sender === "user" ? "#3855c0" : "#ffffff",
                            color: msg.sender === "user" ? "white" : "#111827",
                            border:
                              msg.sender === "user"
                                ? "none"
                                : "1px solid #E5E7EB",
                            boxShadow:
                              msg.sender === "user"
                                ? "0 10px 24px rgba(56, 85, 192, 0.22)"
                                : "0 8px 22px rgba(17, 24, 39, 0.06)",
                          }}
                        >
                          <Box sx={messageContentSx}>
                            <ReactMarkdown
                              remarkPlugins={[remarkMath]}
                              rehypePlugins={[rehypeKatex]}
                            >
                              {formatMath(msg.text)}
                            </ReactMarkdown>
                          </Box>
                        </Paper>

                        {msg.sender === "bot" &&
                          msg.showQuickSnapCta &&
                          renderQuickSnapCta()}
                      </Box>
                    );
                  })}

                  {isLoading && renderThinkingIndicator(t("chatbot_thinking_label"))}
                  {isTypingReply && renderThinkingIndicator(t("chatbot_typing_label"))}

                  <div ref={bottomRef} />
                </Box>
              )}
            </Box>

            {view === "chat" && (
              <Box
                sx={{
                  p: 1.5,
                  bgcolor: "white",
                  borderTop: "1px solid #E5E7EB",
                  flexShrink: 0,
                }}
              >
                {showSymbolPad && renderSymbolPad()}

                <TextField
                  fullWidth
                  multiline
                  minRows={1}
                  maxRows={3}
                  variant="outlined"
                  placeholder={t("chatbot_placeholder")}
                  size="small"
                  value={inputMessage}
                  disabled={isLoading || isTypingReply}
                  inputRef={inputRef}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      handleSendMessage();
                    }
                  }}
                  sx={{
                    "& .MuiOutlinedInput-root": {
                      minHeight: 50,
                      borderRadius: "18px",
                      bgcolor: "#F8FAFC",
                      border: "1px solid #DDE3FF",
                      transition: "all 0.2s ease",
                      alignItems: "center",
                      px: 0.8,
                      py: 0.6,

                      "& fieldset": {
                        border: "none",
                      },

                      "&:hover": {
                        bgcolor: "#ffffff",
                        borderColor: "#C7D2FE",
                      },

                      "&.Mui-focused": {
                        bgcolor: "#ffffff",
                        boxShadow: "0 0 0 4px rgba(99, 102, 241, 0.12)",
                      },
                    },

                    "& .MuiInputBase-inputMultiline": {
                      py: "0 !important",
                      lineHeight: "22px",
                    },

                    "& textarea": {
                      lineHeight: "22px",
                    },

                    "& textarea::placeholder": {
                      lineHeight: "22px",
                    },
                  }}
                  InputProps={{
                    endAdornment: (
                      <InputAdornment position="end" sx={{ alignSelf: "center", m: 0 }}>
                        <Tooltip title={getEasyLearnmbolsTooltip(language)}>
                          <IconButton
                            onClick={() => setShowSymbolPad((prev) => !prev)}
                            disabled={isLoading || isTypingReply}
                            sx={{
                              width: 32,
                              height: 32,
                              mr: 0.4,
                              borderRadius: "10px",
                              color: showSymbolPad ? "#ffffff" : "#3855c0",
                              bgcolor: showSymbolPad ? "#3855c0" : "#EEF2FF",
                              "&:hover": {
                                bgcolor: showSymbolPad ? "#2d4499" : "#E0E7FF",
                              },
                              "&.Mui-disabled": {
                                bgcolor: "#F3F4F6",
                                color: "#9CA3AF",
                              },
                            }}
                          >
                            <FunctionsIcon sx={{ fontSize: 18 }} />
                          </IconButton>
                        </Tooltip>

                        <IconButton
                          onClick={handleSendMessage}
                          disabled={!inputMessage.trim() || isLoading || isTypingReply}
                          sx={{
                            bgcolor: inputMessage.trim() ? "#3855c0" : "transparent",
                            width: 34,
                            height: 34,
                            ml: 0.3,
                            flexShrink: 0,
                            borderRadius: "12px",

                            "&:hover": {
                              bgcolor: inputMessage.trim() ? "#2d4499" : "transparent",
                            },

                            "&.Mui-disabled": {
                              bgcolor: "transparent",
                            },
                          }}
                        >
                          <SendIcon
                            fontSize="small"
                            sx={{
                              color: inputMessage.trim() ? "#ffffff" : "#9CA3AF",
                            }}
                          />
                        </IconButton>
                      </InputAdornment>
                    ),
                  }}
                />

                <Typography
                  variant="caption"
                  sx={{
                    display: "block",
                    textAlign: "center",
                    color: "#9CA3AF",
                    fontSize: "10.5px",
                    mt: 0.8,
                    lineHeight: 1.35,
                  }}
                >
                  {aiDisclaimer}
                </Typography>
              </Box>
            )}
          </Paper>
        )}
      </Box>

      <Dialog
        open={Boolean(deleteTargetSession)}
        onClose={closeDeleteConfirm}
        maxWidth="xs"
        fullWidth
      >
        <DialogTitle>{t("chatbot_delete_confirm_title")}</DialogTitle>

        <DialogContent>
          <DialogContentText>{t("chatbot_delete_confirm_body")}</DialogContentText>
        </DialogContent>

        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={closeDeleteConfirm}>{t("chatbot_cancel")}</Button>

          <Button onClick={confirmDeleteChat} color="error" variant="contained">
            {t("chatbot_confirm")}
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default FloatingChatbot;