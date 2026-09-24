import React, { useEffect, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { keyframes } from "@mui/system";
import {
  Box,
  Paper,
  Typography,
  TextField,
  IconButton,
  InputAdornment,
  Button,
  Divider,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Tabs,
  Tab,
  useMediaQuery,
  useTheme,
  Chip,
} from "@mui/material";

import SendIcon from "@mui/icons-material/Send";
import AddIcon from "@mui/icons-material/Add";
import EditOutlinedIcon from "@mui/icons-material/EditOutlined";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import CheckIcon from "@mui/icons-material/Check";
import CloseOutlinedIcon from "@mui/icons-material/CloseOutlined";
import CameraAltOutlinedIcon from "@mui/icons-material/CameraAltOutlined";
import FunctionsIcon from "@mui/icons-material/Functions";
import AccessTimeOutlinedIcon from "@mui/icons-material/AccessTimeOutlined";
import KeyboardDoubleArrowLeftRoundedIcon from "@mui/icons-material/KeyboardDoubleArrowLeftRounded";
import KeyboardDoubleArrowRightRoundedIcon from "@mui/icons-material/KeyboardDoubleArrowRightRounded";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import ExpandLessIcon from "@mui/icons-material/ExpandLess";
import AutoAwesomeRoundedIcon from "@mui/icons-material/AutoAwesomeRounded";
import TipsAndUpdatesRoundedIcon from "@mui/icons-material/TipsAndUpdatesRounded";
import FavoriteRoundedIcon from "@mui/icons-material/FavoriteRounded";
import SchoolRoundedIcon from "@mui/icons-material/SchoolRounded";

import ReactMarkdown from "react-markdown";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import "katex/dist/katex.min.css";
import katex from "katex";

import { useLanguage } from "../../context/LanguageContext";
import { apiFetch } from "../../utils/apiFetch";
import { logUserActivity } from "../../utils/logger";
import chatbotAvatar from "../../assets/landingpage/chatbotIcon.png";
import { getEasyLearnmbols, getEasyLearnmbolsTooltip } from "../../utils/mathSymbols";

const dotsAnimation = keyframes`
  0%, 20% { opacity: 0.2; transform: translateY(0); }
  50% { opacity: 1; transform: translateY(-2px); }
  100% { opacity: 0.2; transform: translateY(0); }
`;

const ChatbotPage = () => {
  const { t, language } = useLanguage();
  const location = useLocation();
  const navigate = useNavigate();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("md"));

  const inputRef = useRef(null);
  const bottomRef = useRef(null);
  const activeRequestIdRef = useRef(0);
  const typingTimerRef = useRef(null);

  const [sessions, setSessions] = useState([]);
  const [activeChatSessionId, setActiveChatSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState("");

  const [isLoading, setIsLoading] = useState(false);
  const [isTypingReply, setIsTypingReply] = useState(false);

  const [editingSessionId, setEditingSessionId] = useState(null);
  const [editingTitleValue, setEditingTitleValue] = useState("");
  const [deleteTargetSession, setDeleteTargetSession] = useState(null);

  const [mobilePanel, setMobilePanel] = useState("chat");
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [showSymbolPad, setShowSymbolPad] = useState(false);
  const [quickSnapContext, setQuickSnapContext] = useState(null);
  const [isQuickSnapCardExpanded, setIsQuickSnapCardExpanded] = useState(false);

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

  const collapsedSessionIcons = [
    <SchoolRoundedIcon fontSize="small" />,
    <TipsAndUpdatesRoundedIcon fontSize="small" />,
    <AutoAwesomeRoundedIcon fontSize="small" />,
  ];

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

  const activeSessionTitle = activeChatSessionId
    ? sessions.find((s) => s.chat_session_id === activeChatSessionId)?.title ||
      t("chatbot_title")
    : t("chatbot_new_chat");

  useEffect(() => {
    const initialize = async () => {
      await fetchChatSessions();

      const routeSessionId = location.state?.chatSessionId;
      const routeQuickSnapContext = location.state?.quickSnapContext || null;

      if (routeQuickSnapContext) {
        setQuickSnapContext(routeQuickSnapContext);
        setIsQuickSnapCardExpanded(false);

      }

      if (routeSessionId) {
        await loadChatSession(routeSessionId, {
          preserveQuickSnapContext: Boolean(routeQuickSnapContext),
        });
        setMobilePanel("chat");
      } else if (routeQuickSnapContext) {
        setMessages([
          {
            sender: "bot",
            text: "",
            isQuickSnapIntro: true,
          },
        ]);
        setMobilePanel("chat");
      } else {
        setMessages(buildWelcomeMessages());
        setMobilePanel("chat");
      }
    };

    initialize();
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading, isTypingReply]);

  useEffect(() => {
    const onlyWelcome =
      messages.length === 1 && messages[0]?.isWelcome && !activeChatSessionId;

    if (onlyWelcome) {
      setMessages(buildWelcomeMessages());
    }
  }, [t]);

  useEffect(() => {
    return () => {
      stopTypingTimer();
    };
  }, []);

  const stopTypingTimer = () => {
    if (typingTimerRef.current) {
      clearInterval(typingTimerRef.current);
      typingTimerRef.current = null;
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
      const sessionList = Array.isArray(data.sessions) ? data.sessions : [];
      setSessions(sessionList);
    } catch (error) {
      console.error("Failed to load chat sessions:", error);
    }
  };

  const loadChatSession = async (
    chatSessionId,
    options = { preserveQuickSnapContext: false }
  ) => {
    activeRequestIdRef.current += 1;
    setIsLoading(false);
    stopTypingTimer();
    setIsTypingReply(false);
    setShowSymbolPad(false);

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
      
      setIsQuickSnapCardExpanded(false);
      setActiveChatSessionId(chatSessionId);
      setQuickSnapContext(restoredQuickSnapContext);

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

        if (!options.preserveQuickSnapContext) {
          setQuickSnapContext(null);
        }
      }

      if (isMobile) {
        setMobilePanel("chat");
      }
    } catch (error) {
      console.error("Failed to load chat session messages:", error);
    }
  };

  const handleNewChat = () => {
    activeRequestIdRef.current += 1;
    setQuickSnapContext(null);
    setIsQuickSnapCardExpanded(false);
    setActiveChatSessionId(null);
    setMessages(buildWelcomeMessages());
    setInputMessage("");
    setIsLoading(false);
    stopTypingTimer();
    setIsTypingReply(false);
    setShowSymbolPad(false);

    if (isMobile) {
      setMobilePanel("chat");
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
        setActiveChatSessionId(null);
        setMessages(buildWelcomeMessages());
      }

      closeDeleteConfirm();
      await fetchChatSessions();
    } catch (error) {
      console.error("Failed to delete chat:", error);
      closeDeleteConfirm();
    }
  };

  const handleGoToQuickSnapCheck = () => {
    navigate("/quick-snap", {
      state: {
        mode: "check_my_work",
      },
    });
  };

  const handleQuickPrompt = (promptText) => {
    if (isLoading || isTypingReply) return;
    setInputMessage(promptText);
    setMobilePanel("chat");
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
      const res = await apiFetch(
        `${process.env.REACT_APP_API_BASE_URL}/api/chat`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            message: userMessage,
            language,
            chat_session_id: activeChatSessionId,
            quick_snap_context: activeChatSessionId ? null : quickSnapContext || null,
          }),
        }
      );

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

      if (isMobile) {
        setMobilePanel("chat");
      }
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

  const messageContentSx = {
    fontSize: "15px",
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
    <Box sx={{ alignSelf: "flex-start", maxWidth: { xs: "88%", md: "72%" } }}>
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
        <Tooltip key={`${symbol.label}-${symbol.title}`} title={symbol.title}>
          <Button
            size="small"
            onClick={() => insertEasyLearnmbol(symbol.insert, symbol.cursorBack || 0)}
            sx={{
              minWidth: symbol.label.length > 2 ? 48 : 36,
              height: 32,
              px: 0.8,
              borderRadius: "10px",
              textTransform: "none",
              fontWeight: 800,
              fontSize: symbol.label.length > 2 ? "12px" : "14px",
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
            lineHeight: 1.6,
            display: isQuickSnapCardExpanded ? "block" : "-webkit-box",
            WebkitLineClamp: isQuickSnapCardExpanded ? "unset" : 4,
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
      : feedbackItems.slice(0, 3);

    return (
      <Box sx={{ display: "flex", flexDirection: "column", gap: 1.1, mt: 0.8 }}>
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
                p: 1.3,
                borderRadius: "12px",
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
                  mb: 0.8,
                }}
              >
                <Typography
                  variant="body2"
                  fontWeight={800}
                  sx={{
                    color: "#111827",
                    lineHeight: 1.4,
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
                    height: 23,
                    bgcolor: chipBg,
                    color: chipColor,
                    border: `1px solid ${borderColor}`,
                    fontWeight: 800,
                    fontSize: "11px",
                    flexShrink: 0,
                  }}
                />
              </Box>

              {item.student_wrote && (
                <Box
                  sx={{
                    bgcolor: "#F9FAFB",
                    border: "1px dashed #E5E7EB",
                    borderRadius: "8px",
                    px: 1,
                    py: 0.7,
                    mb: 0.8,
                  }}
                >
                  <Typography
                    variant="caption"
                    fontWeight={800}
                    sx={{
                      color: "#6B7280",
                      display: "block",
                      mb: 0.3,
                      textTransform: "uppercase",
                    }}
                  >
                    {language === "bm" ? "Pelajar tulis" : "Student wrote"}
                  </Typography>

                  <Typography
                    variant="body2"
                    sx={{
                      color: "#111827",
                      fontFamily: "monospace",
                      lineHeight: 1.5,
                      whiteSpace: "pre-wrap",
                      overflowWrap: "anywhere",
                      wordBreak: "break-word",
                      maxWidth: "100%",
                    }}
                  >
                    {renderTextWithAutoMath(item.student_wrote)}
                  </Typography>
                </Box>
              )}

              <Typography
                variant="body2"
                sx={{
                  color: "#4B5563",
                  lineHeight: 1.55,
                  overflowWrap: "anywhere",
                  wordBreak: "break-word",
                  maxWidth: "100%",
                }}
              >
                <Box component="span" fontWeight={800} sx={{ color: "#374151", mr: 0.5 }}>
                  {language === "bm" ? "Sebab:" : "Reason:"}
                </Box>
                {renderTextWithAutoMath(item.reason)}
              </Typography>
            </Box>
          );
        })}

        {!isQuickSnapCardExpanded && feedbackItems.length > 3 && (
          <Typography variant="caption" sx={{ color: "#6B7280", fontWeight: 700 }}>
            + {feedbackItems.length - 3} more marking steps
          </Typography>
        )}
      </Box>
    );
  };

  const renderQuickSnapFollowUpCard = () => {
    const isCheckWork = quickSnapContext?.mode === "check_my_work";
    const answerText = getQuickSnapAnswerText();
    const feedbackItems = getQuickSnapFeedbackItems();
    const hasExpandableContent =
      isCheckWork
        ? feedbackItems.length > 3 || Boolean(answerText)
        : Boolean(answerText);

    return (
      <Paper
        elevation={0}
        sx={{
          width: "100%",
          maxWidth: 760,
          mx: "auto",
          p: { xs: 2, md: 2.5 },
          borderRadius: "18px",
          background: "linear-gradient(135deg, #EEF2FF 0%, #ECFDF5 100%)",
          border: "1px solid #C7D2FE",
          boxShadow: "0 8px 24px rgba(56, 85, 192, 0.08)",
        }}
      >
        <Typography fontWeight={900} sx={{ color: "#111827", mb: 0.8 }}>
          {language === "bm"
            ? "Mod Follow-up Quick Snap"
            : "Quick Snap Follow-Up Mode"}
        </Typography>

        <Typography
          variant="body2"
          sx={{ color: "#374151", lineHeight: 1.6, mb: 1.5 }}
        >
          {language === "bm"
            ? "Anda sedang bertanya tentang keputusan Quick Snap tadi. Anda boleh tanya bahagian mana yang masih kurang jelas."
            : "You are asking about the Quick Snap result. You can ask which part is still unclear."}
        </Typography>

        <Box
          sx={{
            p: 1.5,
            borderRadius: "12px",
            bgcolor: "#ffffff",
            border: "1px solid #E5E7EB",
            mb: 1.5,
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
            sx={{ color: "#3855c0", display: "block", mt: 1 }}
          >
            {language === "bm" ? "Soalan" : "Question"}
          </Typography>

          <Typography
            variant="body2"
            fontWeight={700}
            sx={{
              color: "#111827",
              mt: 0.4,
              whiteSpace: "pre-wrap",
              display: isQuickSnapCardExpanded ? "block" : "-webkit-box",
              WebkitLineClamp: isQuickSnapCardExpanded ? "unset" : 3,
              WebkitBoxOrient: "vertical",
              overflow: "hidden",
              lineHeight: 1.55,
            }}
          >
            {renderTextWithAutoMath(
              quickSnapContext?.question_text || "Quick Snap result"
            )}
          </Typography>

          {(answerText || isCheckWork) && (
            <>
              <Typography
                variant="caption"
                fontWeight={800}
                sx={{ color: "#059669", display: "block", mt: 1.4 }}
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
                    mt: 0.4,
                    whiteSpace: "pre-wrap",
                    display: isQuickSnapCardExpanded ? "block" : "-webkit-box",
                    WebkitLineClamp: isQuickSnapCardExpanded ? "unset" : 3,
                    WebkitBoxOrient: "vertical",
                    overflow: "hidden",
                    lineHeight: 1.6,
                  }}
                >
                  {renderTextWithAutoMath(answerText)}
                </Typography>
              )}
            </>
          )}
        </Box>

        {hasExpandableContent && (
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
              mb: 1,
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
        )}

        <Typography variant="caption" sx={{ color: "#6B7280", display: "block" }}>
          {language === "bm"
            ? "Contoh: “Kenapa langkah ini salah?” atau “Boleh terangkan bahagian ini dengan lebih mudah?”"
            : "Example: “Why is this step wrong?” or “Can you explain this part more simply?”"}
        </Typography>
      </Paper>
    );
  };

  const renderWelcomeCard = () => (
    <Paper
      elevation={0}
      sx={{
        width: "100%",
        maxWidth: 720,
        mx: "auto",
        p: { xs: 2, md: 2.5 },
        borderRadius: "18px",
        background: "linear-gradient(135deg, #EEF2FF 0%, #FDF2F8 100%)",
        border: "1px solid #E0E7FF",
        boxShadow: "0 8px 24px rgba(56, 85, 192, 0.08)",
      }}
    >
      <Box sx={{ display: "flex", alignItems: "center", gap: 1.5, mb: 1 }}>
        <Box
          component="img"
          src={chatbotAvatar}
          alt="EasyLearn Tutor"
          sx={{
            width: 48,
            height: 48,
            objectFit: "contain",
            filter: "drop-shadow(0 6px 12px rgba(56, 85, 192, 0.18))",
            userSelect: "none",
            pointerEvents: "none",
          }}
        />

        <Box>
          <Typography fontWeight="bold" sx={{ color: "#111827", fontSize: 18 }}>
            {language === "bm" ? "Hai, saya EasyLearn Buddy!" : "Hi, I’m EasyLearn Buddy!"}
          </Typography>

          <Typography variant="body2" sx={{ color: "#6B7280" }}>
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
          lineHeight: 1.6,
          mb: 1.8,
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
              py: 0.8,
              bgcolor: "#ffffff",
              color: "#3855c0",
              fontWeight: 700,
              fontSize: "13px",
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

  const renderHistoryPanel = () => {
    const collapsed = sidebarCollapsed && !isMobile;

    return (
      <Paper
        elevation={0}
        sx={{
          width: {
            xs: "100%",
            md: collapsed ? 82 : 330,
          },
          height: "100%",
          flexShrink: 0,
          borderRadius: { xs: "18px", md: "22px" },
          border: "1px solid #E5E7EB",
          bgcolor: "#ffffff",
          boxShadow: "0 12px 30px rgba(17, 24, 39, 0.06)",
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
          transition: "width 0.25s ease",
        }}
      >
        <Box
          sx={{
            p: collapsed ? 1.2 : 2,
            borderBottom: "1px solid #E5E7EB",
            display: "flex",
            flexDirection: "column",
            alignItems: collapsed ? "center" : "stretch",
            gap: 1.2,
          }}
        >
          {collapsed ? (
            <>
              <Tooltip
                title={
                  language === "bm"
                    ? "Buka sidebar"
                    : "Expand sidebar"
                }
              >
                <IconButton
                  onClick={() => setSidebarCollapsed(false)}
                  sx={{
                    color: "#3855c0",
                    bgcolor: "#EEF2FF",
                    borderRadius: "12px",
                    "&:hover": {
                      bgcolor: "#E0E7FF",
                    },
                  }}
                >
                  <KeyboardDoubleArrowRightRoundedIcon fontSize="small" />
                </IconButton>
              </Tooltip>

              <Tooltip title={t("chatbot_new_chat")}>
                <Button
                  variant="contained"
                  onClick={handleNewChat}
                  sx={{
                    minWidth: 42,
                    width: 42,
                    height: 42,
                    borderRadius: "14px",
                    bgcolor: "#3855c0",
                    boxShadow: "0 8px 18px rgba(56, 85, 192, 0.18)",
                    "&:hover": {
                      bgcolor: "#2d4499",
                    },
                  }}
                >
                  <AddIcon />
                </Button>
              </Tooltip>
            </>
          ) : (
            <>
              <Box
                sx={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  gap: 1,
                }}
              >
                <Typography fontWeight={900} color="#111827">
                  {t("chatbot_history_title")}
                </Typography>

                <Tooltip
                  title={
                    language === "bm"
                      ? "Sembunyi sidebar"
                      : "Collapse sidebar"
                  }
                >
                  <IconButton
                    onClick={() => setSidebarCollapsed(true)}
                    sx={{
                      display: { xs: "none", md: "inline-flex" },
                      color: "#3855c0",
                      bgcolor: "#EEF2FF",
                      borderRadius: "12px",
                      flexShrink: 0,
                      "&:hover": {
                        bgcolor: "#E0E7FF",
                      },
                    }}
                  >
                    <KeyboardDoubleArrowLeftRoundedIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
              </Box>

              <Button
                fullWidth
                variant="contained"
                startIcon={<AddIcon />}
                onClick={handleNewChat}
                sx={{
                  height: 42,
                  borderRadius: "14px",
                  textTransform: "none",
                  fontWeight: 800,
                  bgcolor: "#3855c0",
                  boxShadow: "0 8px 18px rgba(56, 85, 192, 0.18)",
                  "&:hover": {
                    bgcolor: "#2d4499",
                  },
                }}
              >
                {t("chatbot_new_chat")}
              </Button>
            </>
          )}
        </Box>

        {!collapsed && <Divider />}

        <Box
          sx={{
            flex: 1,
            minHeight: 0,
            overflowY: "auto",
            overflowX: "hidden",
            p: collapsed ? 1.2 : 2,
            display: "flex",
            flexDirection: "column",
            gap: 1.2,
          }}
        >
          {sessions.length === 0 ? (
            collapsed ? (
              <Tooltip title={t("chatbot_history_empty")}>
                <Box
                  sx={{
                    width: 42,
                    height: 42,
                    borderRadius: "14px",
                    bgcolor: "#F3F4F6",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    color: "#9CA3AF",
                  }}
                >
                  <AccessTimeOutlinedIcon fontSize="small" />
                </Box>
              </Tooltip>
            ) : (
              <Paper
                elevation={0}
                sx={{
                  p: 2,
                  borderRadius: "14px",
                  border: "1px solid #E5E7EB",
                  bgcolor: "#F9FAFB",
                }}
              >
                <Typography variant="body2" fontWeight={700} color="#111827">
                  {t("chatbot_history_empty")}
                </Typography>

                <Typography variant="caption" color="textSecondary">
                  {t("chatbot_history_hint")}
                </Typography>
              </Paper>
            )
          ) : (
            sessions.map((session, index) => {
              const isActive = session.chat_session_id === activeChatSessionId;
              const isEditing = editingSessionId === session.chat_session_id;
              const collapsedIcon =
                collapsedSessionIcons[index % collapsedSessionIcons.length];

              if (collapsed) {
                return (
                  <Tooltip
                    key={session.chat_session_id}
                    title={
                      session.is_quick_snap_session
                        ? `${session.title || t("chatbot_new_chat")} · ${
                            language === "bm" ? "Follow-up Quick Snap" : "Quick Snap Follow-up"
                          }`
                        : session.title || t("chatbot_new_chat")
                    }
                    placement="right"
                  >
                    <IconButton
                      onClick={() => loadChatSession(session.chat_session_id)}
                      sx={{
                        width: 44,
                        height: 44,
                        borderRadius: "14px",
                        color: isActive ? "#3855c0" : "#6B7280",
                        bgcolor: isActive ? "#EEF2FF" : "#F9FAFB",
                        border: isActive ? "1px solid #C7D2FE" : "1px solid #E5E7EB",
                        "&:hover": {
                          bgcolor: "#EEF2FF",
                          color: "#3855c0",
                        },
                      }}
                    >
                      {collapsedIcon}
                    </IconButton>
                  </Tooltip>
                );
              }

              return (
                <Paper
                  key={session.chat_session_id}
                  elevation={0}
                  onClick={() =>
                    !isEditing && loadChatSession(session.chat_session_id)
                  }
                  sx={{
                    p: 1.5,
                    borderRadius: "14px",
                    border: isActive ? "1px solid #3855c0" : "1px solid #E5E7EB",
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
                        <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
                          <TextField
                            size="small"
                            value={editingTitleValue}
                            autoFocus
                            onChange={(e) => setEditingTitleValue(e.target.value)}
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
                            fontWeight={800}
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
                                height: 23,
                                mb: 0.7,
                                borderRadius: "8px",
                                bgcolor: "#ECFDF5",
                                color: "#047857",
                                border: "1px solid #A7F3D0",
                                fontWeight: 800,
                                fontSize: "11px",
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
                      <Box sx={{ display: "flex", alignItems: "center", gap: 0.25 }}>
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
            })
          )}
        </Box>
      </Paper>
    );
  };

  const renderChatPanel = () => (
    <Paper
      elevation={0}
      sx={{
        flex: 1,
        height: "100%",
        minWidth: 0,
        borderRadius: { xs: "18px", md: "22px" },
        border: "1px solid #E5E7EB",
        bgcolor: "#ffffff",
        boxShadow: "0 12px 30px rgba(17, 24, 39, 0.06)",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
      }}
    >
      <Box
        sx={{
          px: { xs: 2, md: 2.5 },
          py: 1.6,
          background:
            "linear-gradient(135deg, #495ead 0%, #809af1 55%, #5672ce 100%)",
          color: "white",
          flexShrink: 0,
          display: "flex",
          alignItems: "center",
          justifyContent: "flex-start",
          gap: 1.5,
        }}
      >
        <Box sx={{ display: "flex", alignItems: "center", gap: 1.5, minWidth: 0 }}>
          <Box
            component="img"
            src={chatbotAvatar}
            alt="EasyLearn Tutor"
            sx={{
              width: 46,
              height: 46,
              objectFit: "contain",
              filter: "drop-shadow(0 6px 12px rgba(0,0,0,0.18))",
              userSelect: "none",
              pointerEvents: "none",
              flexShrink: 0,
            }}
          />

          <Box sx={{ minWidth: 0 }}>
            <Typography fontWeight={900} lineHeight={1.2} noWrap>
              {t("chatbot_title")}
            </Typography>

            <Typography
              variant="caption"
              sx={{
                color: "#BBF7D0",
                fontWeight: 800,
                display: "block",
              }}
              noWrap
            >
              ● {t("chatbot_online")} · {activeSessionTitle}
            </Typography>
          </Box>
        </Box>
      </Box>

      <Box
        sx={{
          flex: 1,
          minHeight: 0,
          overflowY: "auto",
          overflowX: "hidden",
          bgcolor: "linear-gradient(180deg, #F8FAFF 0%, #F9FAFB 100%)",
          px: { xs: 2, md: 4 },
          py: 3,
          display: "flex",
          flexDirection: "column",
          gap: 2.2,
          scrollbarGutter: "stable",
        }}
      >
        {messages.map((msg, index) => {
          if (msg.isQuickSnapIntro) {
            return (
              <Box key={msg.id || index} sx={{ width: "100%" }}>
                {renderQuickSnapFollowUpCard()}
              </Box>
            );
          }

          if (msg.isWelcome) {
            return (
              <Box key={msg.id || index} sx={{ width: "100%" }}>
                {renderWelcomeCard()}
              </Box>
            );
          }

          return (
            <Box
              key={msg.id || index}
              sx={{
                width: "100%",
                display: "flex",
                flexDirection: "column",
                alignItems: msg.sender === "user" ? "flex-end" : "flex-start",
              }}
            >
              <Paper
                elevation={0}
                sx={{
                  p: { xs: 1.5, md: 1.8 },
                  maxWidth: { xs: "88%", md: "72%" },
                  minWidth: 0,
                  overflow: "hidden",
                  borderRadius:
                    msg.sender === "user"
                      ? "16px 16px 6px 16px"
                      : "16px 16px 16px 6px",
                  bgcolor: msg.sender === "user" ? "#3855c0" : "#ffffff",
                  color: msg.sender === "user" ? "white" : "#111827",
                  border: msg.sender === "user" ? "none" : "1px solid #E5E7EB",
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

      <Box
        sx={{
          px: { xs: 2, md: 3 },
          py: 1.5,
          borderTop: "1px solid #E5E7EB",
          bgcolor: "#ffffff",
          flexShrink: 0,
        }}
      >
        {showSymbolPad && renderSymbolPad()}

        <TextField
          fullWidth
          multiline
          minRows={1}
          maxRows={4}
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
              minHeight: 52,
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
                      width: 34,
                      height: 34,
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
                    width: 36,
                    height: 36,
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
            fontSize: "11px",
            mt: 0.8,
            lineHeight: 1.35,
          }}
        >
          {aiDisclaimer}
        </Typography>
      </Box>
    </Paper>
  );

  return (
    <Box
      sx={{
        height: { xs: "auto", md: "calc(100vh - 160px)" },
        minHeight: { xs: "auto", md: 0 },
        width: "100%",
        overflow: { xs: "visible", md: "hidden" },
      }}
    >
      {isMobile && (
        <Box sx={{ mb: 1.5 }}>
          <Typography
            variant="h4"
            fontWeight={900}
            sx={{ color: "#111827", mb: 0.5 }}
          >
            {t("chatbot_title")}
          </Typography>

          <Typography sx={{ color: "#6B7280", lineHeight: 1.5 }}>
            {t("chatbot_fullpage_subtitle")}
          </Typography>
        </Box>
      )}

      {isMobile && (
        <Box sx={{ display: "flex", justifyContent: "center", mb: 1.5 }}>
          <Tabs
            value={mobilePanel}
            onChange={(_, value) => setMobilePanel(value)}
            TabIndicatorProps={{
              style: {
                height: "100%",
                borderRadius: "12px",
                backgroundColor: "#EEF2FF",
                border: "1px solid #3855c0",
                zIndex: 0,
              },
            }}
            sx={{
              minHeight: "42px",
              backgroundColor: "#F3F4F6",
              borderRadius: "14px",
              padding: "4px",
              "& .MuiTabs-indicator": { zIndex: 0 },
            }}
          >
            <Tab
              value="history"
              label={t("chatbot_mobile_history_tab")}
              disableRipple
              sx={{
                textTransform: "none",
                fontWeight: 800,
                minHeight: "36px",
                borderRadius: "10px",
                zIndex: 1,
                px: 3,
                color: mobilePanel === "history" ? "#3855c0" : "#6B7280",
                "&.Mui-selected": { color: "#3855c0" },
              }}
            />

            <Tab
              value="chat"
              label={t("chatbot_mobile_chat_tab")}
              disableRipple
              sx={{
                textTransform: "none",
                fontWeight: 800,
                minHeight: "36px",
                borderRadius: "10px",
                zIndex: 1,
                px: 3,
                color: mobilePanel === "chat" ? "#3855c0" : "#6B7280",
                "&.Mui-selected": { color: "#3855c0" },
              }}
            />
          </Tabs>
        </Box>
      )}

      <Box
        sx={{
          height: {
            xs: "auto",
            md: "100%",
          },
          minHeight: 0,
          display: "flex",
          gap: { xs: 0, md: 2 },
          flexDirection: { xs: "column", md: "row" },
          overflow: { xs: "visible", md: "hidden" },
        }}
      >
        {(!isMobile || mobilePanel === "history") && renderHistoryPanel()}
        {(!isMobile || mobilePanel === "chat") && renderChatPanel()}
      </Box>

      <Dialog
        open={Boolean(deleteTargetSession)}
        onClose={closeDeleteConfirm}
        maxWidth="xs"
        fullWidth
      >
        <DialogTitle>{t("chatbot_delete_confirm_title")}</DialogTitle>

        <DialogContent>
          <DialogContentText>
            {t("chatbot_delete_confirm_body")}
          </DialogContentText>
        </DialogContent>

        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={closeDeleteConfirm}>{t("chatbot_cancel")}</Button>

          <Button onClick={confirmDeleteChat} color="error" variant="contained">
            {t("chatbot_confirm")}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ChatbotPage;