import React, { useState, useEffect, useRef } from "react";
import {
  Box,
  Typography,
  Paper,
  Button,
  Chip,
  Container,
  IconButton,
  Fade,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  CircularProgress,
  Portal,
} from "@mui/material";
import { useNavigate, useLocation } from "react-router-dom";
import katex from "katex";
import "katex/dist/katex.min.css";
import Confetti from "react-confetti";
import { useWindowSize } from "react-use";
import { logUserActivity } from "../../utils/logger";
import { useLanguage } from "../../context/LanguageContext";
import { apiFetch } from "../../utils/apiFetch";
import AiDisclaimerText from "../../components/DisclaimerText";

// Icons
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import CheckCircleOutlineIcon from "@mui/icons-material/CheckCircleOutline";
import HighlightOffIcon from "@mui/icons-material/HighlightOff";
import LocalFireDepartmentIcon from "@mui/icons-material/LocalFireDepartment";
import LightbulbOutlinedIcon from "@mui/icons-material/LightbulbOutlined";
import AutoGraphIcon from "@mui/icons-material/AutoGraph";
import DisclaimerText from "../../components/DisclaimerText";

const PracticePageKertas1 = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { width, height } = useWindowSize();
  const { language } = useLanguage();

  const { form, chapter_id, chapter, chapter_string, topic } = location.state || {
    form: "Form 4",
    chapter_id: 1,
    chapter: "General Practice",
    chapter_string: "General Practice",
    topic: "General Practice",
  };

  const selectedChapter = chapter_string || chapter || topic;

  const user = JSON.parse(localStorage.getItem("user")) || {};
  const isEnglish = language !== "bm";

  const text = {
    paper: isEnglish ? "Paper 1 (Objective)" : "Kertas 1 (Objektif)",
    checkBtn: isEnglish ? "Check Answer" : "Semak Jawapan",
    nextBtn: isEnglish ? "Next Question" : "Soalan Seterusnya",
    correct: isEnglish ? "Correct!" : "Tepat!",
    wrong: isEnglish ? "Incorrect" : "Tidak Tepat",
    explanation: isEnglish ? "Explanation" : "Penerangan",
    streak: isEnglish ? "Streak" : "Deretan",

    exitTitle: isEnglish ? "Exit Practice?" : "Keluar dari Latihan?",
    exitDesc: isEnglish
      ? "Your current progress and streak will be saved. Are you sure you want to leave?"
      : "Kemajuan dan deretan semasa anda akan disimpan. Adakah anda pasti ingin keluar?",
    cancelBtn: isEnglish ? "Cancel" : "Batal",
    confirmExitBtn: isEnglish ? "Save & Exit" : "Simpan & Keluar",

    sessionComplete: isEnglish ? "Session Complete! " : "Sesi Tamat! ",
    summaryDesc: isEnglish
      ? "Great job! Your progress has been securely saved."
      : "Syabas! Kemajuan anda telah disimpan. Berikut adalah pencapaian anda:",
    questionsAttempted: isEnglish ? "Questions Attempted" : "Soalan Dijawab",
    accuracyLabel: isEnglish ? "Accuracy" : "Ketepatan",
    needsReview: isEnglish ? "Needs Review" : "Perlu Ulangkaji",
    highestStreakLabel: isEnglish ? "Highest Streak" : "Deretan Tertinggi",
    backToDash: isEnglish
      ? "Back to Menu"
      : "Kembali ke Menu",

    noQuestions: isEnglish
      ? "Congratulations! You have completed all the questions. Stay Tuned for More !!"
      : "Tahniah! Anda telah menyelesaikan semua soalan. Tunggu yang lebih baik !!",
    goBack: isEnglish ? "Go Back" : "Kembali",
  };

  const difficultyLabel = (difficulty) => {
    if (isEnglish) return difficulty;
    if (difficulty === "Easy") return "Mudah";
    if (difficulty === "Moderate") return "Sederhana";
    if (difficulty === "Hard") return "Sukar";
    return difficulty;
  };

  const [selectedOption, setSelectedOption] = useState(null);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [currentVariant, setCurrentVariant] = useState(null);

  const [retryMode, setRetryMode] = useState(false);
  const [streak, setStreak] = useState(0);
  const [highestStreak, setHighestStreak] = useState(0);
  const [totalAttempted, setTotalAttempted] = useState(0);
  const [correctAnswers, setCorrectAnswers] = useState(0);
  const [isGeneratingExplanation, setIsGeneratingExplanation] = useState(false);
  const [showExplanation, setShowExplanation] = useState(false);
  const [openExitDialog, setOpenExitDialog] = useState(false);
  const [showSummaryModal, setShowSummaryModal] = useState(false);
  const [isSavingAttempt, setIsSavingAttempt] = useState(false);
  const [questions, setQuestions] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isLoading, setIsLoading] = useState(true);

  const [startTime, setStartTime] = useState(Date.now());
  const [attemptsLog, setAttemptsLog] = useState([]);

  const [practiceId, setPracticeId] = useState(null);
  const [adaptiveInfo, setAdaptiveInfo] = useState(null);
  const [openEasierDialog, setOpenEasierDialog] = useState(false);
  const [adaptiveMessage, setAdaptiveMessage] = useState("");

  const optionLetterToIndex = (letter) => {
  const mapping = { A: 0, B: 1, C: 2, D: 3 };
  return mapping[String(letter || "").trim().toUpperCase()] ?? -1;
};
  const renderInlineMath = (text) => {
    if (!text) return null;
    const parts = text.split(/(\$\$[\s\S]*?\$\$|\$[^$]+\$|\\\([\s\S]*?\\\)|\\begin\{[^}]+\}[\s\S]*?\\end\{[^}]+\})/g); 
    return parts.map((part, index) => {
      if (part.startsWith('$$') && part.endsWith('$$')) {
        const mathContent = part.slice(2, -2);
        return <Box component="span" key={index} sx={{ color: "inherit", mx: 0.5 }} dangerouslySetInnerHTML={{ __html: katex.renderToString(mathContent, { throwOnError: false, displayMode: false }) }} />;
      } else if (part.startsWith('$') && part.endsWith('$')) {
        const mathContent = part.slice(1, -1);
        return <Box component="span" key={index} sx={{ color: "inherit", mx: 0.5 }} dangerouslySetInnerHTML={{ __html: katex.renderToString(mathContent, { throwOnError: false, displayMode: false }) }} />;
      } else if (part.startsWith('\\(') && part.endsWith('\\)')) {
        const mathContent = part.slice(2, -2);
        return <Box component="span" key={index} sx={{ color: "inherit", mx: 0.5 }} dangerouslySetInnerHTML={{ __html: katex.renderToString(mathContent, { throwOnError: false, displayMode: false }) }} />;
      } else if (part.startsWith('\\begin{')) {
        return <Box key={index} sx={{ bgcolor: "#F9FAFB", border: "1px solid #E5E7EB", borderRadius: "10px", p: 2, my: 1.5, overflowX: "auto", color: "inherit", display: "block", "& .katex": { fontSize: "1.1rem" } }} dangerouslySetInnerHTML={{ __html: katex.renderToString(part, { throwOnError: false, displayMode: true }) }} />;
      }
      return <span key={index}>{part}</span>;
    });
  };

  const isActuallyMath = (value) => {
    const text = String(value || "").trim();
    if (!text) return false;
    return /[=+\-*/^√∠°%<>≠≤≥∪∩]|\\(?:frac|sqrt|times|div|begin|cup|cap|ne|neq|le|ge|text|left|right|rightarrow|to|Rightarrow|implies|therefore|because|quad|qquad)\b|[0-9]/.test(text);
  };

  const normalizeLatexText = (value) => {
    return String(value || "")
      .replace(/(\b[A-Z]\s*\\(?:cup|cap)\s*[A-Z]\s*)(?:(?:\\\\|\\Rightarrow|\\implies|\\rightarrow|=>|\n)\s*)*(?:eq|e)\s*([A-Z]\b)/g, "$1\\ne $2")
      .replace(/\/frac/g, "\\frac")
      .replace(/(^|[^\\])frac\s*\{/g, "$1\\frac{")
      .replace(/\\neq/g, "\\ne")
      .replace(/\n\s*eq\s*/g, "\\ne ")
      .replace(/\n\s*e\s*/g, "\\ne ")
      .replace(/(^|[^\\])neq/g, "$1\\ne")
      .replace(/(\b[A-Z]\s*\\(?:cup|cap)\s*[A-Z]\s*)e\s*([A-Z]\b)/g, "$1\\ne $2")
      .replace(/(\b[A-Z]\s*)cup(\s*[A-Z]\b)/g, "$1\\cup$2")
      .replace(/(\b[A-Z]\s*)cap(\s*[A-Z]\b)/g, "$1\\cap$2")
      .replace(/\\text\{\s*(\\begin\{(?:aligned|align|array|matrix|pmatrix|bmatrix|cases)\}[\s\S]*?\\end\{(?:aligned|align|array|matrix|pmatrix|bmatrix|cases)\})\s*\}/g, "$1")
      .replace(/(\\begin\{(?:aligned|align|array|matrix|pmatrix|bmatrix|cases)\})\s*\$/g, "$1 ")
      .replace(/\$\s*(\\end\{(?:aligned|align|array|matrix|pmatrix|bmatrix|cases)\})/g, " $1")
      .replace(/^\$\s*(\\begin\{[^}]+\})/, "$1")
      .replace(/(\\end\{[^}]+\})\s*\$$/, "$1")
      .trim();
  };

  const hasRawLatexCommand = (value) => {
    return /\\(?:frac|sqrt|times|div|cup|cap|ne|neq|le|ge|text|left|right|rightarrow|to|Rightarrow|implies|therefore|because|quad|qquad)\b/.test(String(value || ""));
  };

  const hasLatexWrapper = (value) => {
    const text = String(value || "");
    return /\$[^$]+\$/.test(text) || /\\\([\s\S]*?\\\)/.test(text) || /\\begin\{[^}]+\}/.test(text);
  };

  const renderMixedLatexSentence = (value) => {
    const clean = normalizeLatexText(value);
    if (!clean) return null;
    const mathRegex = /([A-Z]\s*\\(?:cup|cap)\s*[A-Z]\s*(?:=|\\ne|\\neq|≠)\s*[A-Z])/g;
    const parts = [];
    let lastIndex = 0;
    let match;
    while ((match = mathRegex.exec(clean)) !== null) {
      if (match.index > lastIndex) {
        parts.push(<span key={`text-${lastIndex}`}>{clean.slice(lastIndex, match.index)}</span>);
      }
      const mathContent = match[1].replace(/\\neq/g, "\\ne");
      parts.push(
        <Box component="span" key={`math-${match.index}`} sx={{ color: "inherit", mx: 0.25 }} dangerouslySetInnerHTML={{ __html: katex.renderToString(mathContent, { throwOnError: false, displayMode: false }) }} />
      );
      lastIndex = match.index + match[1].length;
    }
    if (parts.length === 0) return null;
    if (lastIndex < clean.length) {
      parts.push(<span key={`text-${lastIndex}`}>{clean.slice(lastIndex)}</span>);
    }
    return parts;
  };

  const isSentenceLikeAnswer = (value) => {
    const text = String(value || "").trim();
    if (!text) return false;
    const textWithoutLatexCommands = text.replace(/\\[a-zA-Z]+/g, "");
    const words = textWithoutLatexCommands.match(/\b[A-Za-z]{3,}\b/g) || [];
    const mathFunctionWords = ["sin", "cos", "tan", "log", "ln"];
    const realWords = words.filter((word) => !mathFunctionWords.includes(word.toLowerCase()));
    return realWords.length >= 1 && (/\s/.test(text) || /[.,]/.test(text));
  };

  const renderMathOrText = (value) => {
    const clean = normalizeLatexText(value);
    if (!clean) return null;
    if (clean.startsWith('$') && clean.endsWith('$') && clean.match(/\$/g)?.length === 2) {
      const innerText = clean.slice(1, -1);
      
      // If it has actual words and spaces, it's a sentence masquerading as math
      if (isSentenceLikeAnswer(innerText)) {
        // Strip the outer $ and re-wrap only the words with subscripts (_), superscripts (^), or backslashes (\)
        clean = innerText.replace(/(\S*[_^\\]\S*)/g, '$$$1$$');
      }
    }
    if (hasLatexWrapper(clean)) return renderInlineMath(clean);
    if (hasRawLatexCommand(clean)) return renderInlineMath(`$${clean}$`);
    const mixedLatexSentence = renderMixedLatexSentence(clean);
    if (mixedLatexSentence) {
      return <Box component="span" sx={{ color: "inherit", fontWeight: "inherit", fontFamily: "inherit" }}>{mixedLatexSentence}</Box>;
    }
    if (isSentenceLikeAnswer(clean)) {
      return <Box component="span" sx={{ color: "inherit", fontWeight: "inherit", fontFamily: "inherit" }}>{clean}</Box>;
    }
    if (isActuallyMath(clean)) return renderInlineMath(`$${clean}$`);
    return renderInlineMath(clean);
  };
const getLocalizedTableCell = (cell) => {
  if (cell === null || cell === undefined) return "";

  if (typeof cell === "number" || typeof cell === "boolean") {
    return String(cell);
  }

  if (typeof cell === "string") {
    return cell;
  }

  if (typeof cell === "object") {
    if (isEnglish) {
      return String(
        cell.text_en ??
        cell.header_en ??
        cell.label_en ??
        cell.en ??
        cell.value_en ??
        cell.text_ms ??
        cell.header_ms ??
        cell.value ??
        ""
      );
    }

    return String(
      cell.text_ms ??
      cell.header_ms ??
      cell.label_ms ??
      cell.ms ??
      cell.value_ms ??
      cell.text_en ??
      cell.header_en ??
      cell.value ??
      ""
    );
  }

  return String(cell);
};
const normalizeObjectTable = (tableData) => {
  const header = Array.isArray(tableData.header) ? tableData.header : [];
  const rows = Array.isArray(tableData.rows) ? tableData.rows : [];

  if (header.length > 0 && rows.length > 0 && Array.isArray(rows[0])) {
    return [
      header.map(getLocalizedTableCell),
      ...rows.map((row) =>
        Array.isArray(row)
          ? row.map(getLocalizedTableCell)
          : Object.values(row || {}).map(getLocalizedTableCell)
      ),
    ];
  }

  const headerObj = Array.isArray(tableData.header)
    ? tableData.header[0]
    : tableData.header;

  const rowObjects = rows;

  if (!headerObj || typeof headerObj !== "object" || rowObjects.length === 0) {
    return null;
  }

  const keys = Object.keys(headerObj);

  const headerRow = keys.map((key) => getLocalizedTableCell(headerObj[key]));

  const bodyRows = rowObjects.map((rowObj) =>
    keys.map((key) => getLocalizedTableCell(rowObj?.[key]))
  );

  return [headerRow, ...bodyRows];
};
const normalizeReviewOptions = (rawOptions) => {
  let optionList = [];

  if (Array.isArray(rawOptions)) {
    optionList = rawOptions;
  } else if (rawOptions && typeof rawOptions === "object") {
    optionList = Object.entries(rawOptions).map(([label, value]) => {
      if (value && typeof value === "object") {
        return { label, ...value };
      }

      return {
        label,
        text_en: String(value ?? ""),
        text_ms: String(value ?? ""),
      };
    });
  }

  return ["A", "B", "C", "D"].map((label) => {
    const found =
      optionList.find((option) => {
        if (!option || typeof option !== "object") return false;

        return (
          String(option.label || "")
            .trim()
            .toUpperCase()
            .replace(".", "") === label
        );
      }) || {};

    const textEn =
      found.text_en ??
      found.text ??
      found.value ??
      found.answer ??
      "";

    const textMs =
      found.text_ms ??
      found.text_bm ??
      found.text_malay ??
      textEn ??
      "";

    return {
      label,
      text_en: String(textEn || ""),
      text_ms: String(textMs || textEn || ""),
      image_path: String(found.image_path || found.image || ""),
    };
  });
};

  const isUsefulExplanation = (value) => {
    const text = String(value || "").trim();
    const lower = text.toLowerCase();

    if (!lower) return false;

    if (/^correct answer:\s*[abcd]$/i.test(text)) return false;
    if (/^jawapan betul:\s*[abcd]$/i.test(text)) return false;

    // Too short usually means it is just answer justification, not teaching.
    if (text.length < 120) return false;

    // Reject common shallow generated explanations.
    const weakPatterns = [
      /^the correct option is [abcd]/i,
      /^option [abcd] is correct/i,
      /^pilihan yang betul ialah [abcd]/i,
      /which corresponds to option [abcd]\.?$/i,
    ];

    if (weakPatterns.some((pattern) => pattern.test(text))) {
      return false;
    }

    // Explanation should show reasoning, not only state the answer.
    const hasReasoningWords =
      /(because|since|therefore|hence|substitute|calculate|compare|formula|first|next|kerana|maka|oleh itu|banding|gantikan|kira)/i.test(
        text
      );

    return hasReasoningWords;
  };

  const getQuestionStableKey = (question) => {
    if (!question) return "";

    if (question.is_review_variant) {
      return `variant:${question.review_variant_id || ""}`;
    }

    return `question:${question.id || ""}`;
  };

  const updateQuestionExplanationByKey = (
    targetQuestionKey,
    explanationEn,
    explanationBm
  ) => {
    setQuestions((prevQuestions) =>
      prevQuestions.map((question) => {
        const questionKey = getQuestionStableKey(question);

        if (questionKey !== targetQuestionKey) return question;

        return {
          ...question,
          explanation_en: explanationEn || question.explanation_en,
          explanation_bm: explanationBm || question.explanation_bm,
        };
      })
    );
  };
  
  const generateK1Explanation = async (question, selectedIndex, isCorrectAnswer) => {
    const targetQuestionKey = getQuestionStableKey(question);

    const existingExplanation = isEnglish
      ? question.explanation_en
      : question.explanation_bm;

    // Generated review variants may already have proper explanation.
    if (question.is_review_variant && isUsefulExplanation(existingExplanation)) {
      return;
    }

    const shouldRegenerateExplanation =
      !isUsefulExplanation(existingExplanation);

    setIsGeneratingExplanation(true);

    try {
      const selectedOptionLetter = String.fromCharCode(65 + selectedIndex);

      const response = await apiFetch(
        `${process.env.REACT_APP_API_BASE_URL}/api/questions/kertas1/explain`,
        {
          method: "POST",
          body: JSON.stringify({
          question_id: question.id || null,
          review_variant_id: question.review_variant_id || null,

          question_text: isEnglish ? question.question_en : question.question_bm,
          question_text_en: question.question_en || "",
          question_text_bm: question.question_bm || "",

          question_image: question.question_image || "",
          table_data: question.table_data || {},

          chapter: question.chapter || selectedChapter,
          difficulty: question.difficulty || "",
          difficulty_level: question.difficulty_level || "",

          correct_option: question.correctOption,
          selected_option: selectedOptionLetter,
          is_correct: isCorrectAnswer,
          language: language,

          options: ["A", "B", "C", "D"].map((label, index) => ({
            label,
            text_en: question.options_en?.[index] || "",
            text_bm: question.options_bm?.[index] || "",
            image_path: question.options_image?.[index] || "",
          })),
        })
        }
      );

      const data = await response.json().catch(() => ({}));

      if (response.ok && data.success) {
        updateQuestionExplanationByKey(
          targetQuestionKey,
          data.explanation_en,
          data.explanation_bm
        );
      }
    } catch (error) {
      console.error("Failed to generate K1 explanation:", error);
    } finally {
      setIsGeneratingExplanation(false);
    }
  };
  
  const formatK1ReviewVariant = (variant) => {
    const q = variant.question || {};
    const marking = variant.marking_scheme || {};
    const options = normalizeReviewOptions(q.options || []);
    const snapshot = variant.frontend_snapshot || {};

    return {
      id: null,
      is_review_variant: true,
      review_variant_id: variant.variant_id,
      review_depth: snapshot.review_depth || variant.review_depth || 1,

      form: snapshot.form || form,
      chapter: snapshot.chapter || selectedChapter,
      chapter_id: snapshot.chapter_id || chapter_id,

      difficulty: snapshot.difficulty || "Moderate",
      difficulty_level: snapshot.difficulty_level || 3,

      question_no: "Review",
      question_en: Array.isArray(q.instructions_en)
        ? q.instructions_en.join("\n\n")
        : "",
      question_bm: Array.isArray(q.instructions_ms)
        ? q.instructions_ms.join("\n\n")
        : "",

      question_image: q.image_path || "",
      table_data: q.table_data || {},

      options_en: ["A", "B", "C", "D"].map(
        (label) => options.find((o) => o.label === label)?.text_en || ""
      ),
      options_bm: ["A", "B", "C", "D"].map(
        (label) => options.find((o) => o.label === label)?.text_ms || ""
      ),
      options_image: ["A", "B", "C", "D"].map(
        (label) => options.find((o) => o.label === label)?.image_path || ""
      ),

      correctOption: marking.final_answer,
      correctAnswerIndex: optionLetterToIndex(marking.final_answer),

      explanation_en: marking.explanation_en || `Correct answer: ${marking.final_answer}`,
      explanation_bm: marking.explanation_bm || `Jawapan betul: ${marking.final_answer}`,
      explanation_image: "",
    };
  };
  
  const formatK1Questions = (rawQuestions) => {
    return rawQuestions.map((q) => ({
      id: q.id,

      form: q.form || form,
      chapter: q.chapter,
      chapter_id: chapter_id,

      difficulty: q.difficulty,
      difficulty_level: q.difficulty_level,

      question_no: q.question_no,
      question_en: q.question_en,
      question_bm: q.question_bm,
      question_image: q.question_image,
      table_data: q.table_data || {},

      options_en: [q.optA_en, q.optB_en, q.optC_en, q.optD_en],
      options_bm: [q.optA_bm, q.optB_bm, q.optC_bm, q.optD_bm],
      options_image: [
        q.optA_image,
        q.optB_image,
        q.optC_image,
        q.optD_image,
      ],

      correctAnswerIndex: q.correct_answer_index,
      correctOption: q.correct_option,

      explanation_en: q.explanation_en,
      explanation_bm: q.explanation_bm,
      explanation_image: q.explanation_image,
    }));
  };

  const startPracticeSession = async () => {
    const response = await apiFetch(
      `${process.env.REACT_APP_API_BASE_URL}/api/practice/start-session`,
      {
        method: "POST",
        body: JSON.stringify({
          chapter_id: chapter_id,
          paper_type: "kertas1",
          session_language: language,
        }),
      }
    );

    const data = await response.json();

    if (!data.success) {
      throw new Error(data.message || "Failed to start practice session.");
    }

    setPracticeId(data.practice_id);
    return data.practice_id;
  };

  const fetchNextK1Item = async (practiceIdOverride = practiceId, forceRetry = retryMode) => {
    const activePracticeId = practiceIdOverride || practiceId;

    if (!activePracticeId) {
      console.error("Missing practiceId. Cannot fetch next K1 item.");
      return;
    }

    setIsLoading(true);

    try {
      const response = await apiFetch(
        `${process.env.REACT_APP_API_BASE_URL}/api/practice/next-item?practice_id=${encodeURIComponent(
          activePracticeId
        )}&form=${encodeURIComponent(
          form
        )}&chapter=${encodeURIComponent(
          selectedChapter
        )}&paper_type=kertas1&language=${encodeURIComponent(
          language
        )}&retry_mode=${forceRetry ? 1 : 0}`
      );

      const data = await response.json();

      console.log("K1 NEXT ITEM RESPONSE:", data);

      if (!response.ok || !data.success) {
        console.error("Failed to fetch next K1 item:", data.message || data);
        return;
      }

      if (data.item_type === "normal_question") {
        setShowExplanation(false);
        setQuestions([]);
        setCurrentVariant(null);
        setQuestions(formatK1Questions(data.questions || []));
        setCurrentIndex(0);
        setSelectedOption(null);
        setIsSubmitted(false);
        setIsGeneratingExplanation(false);
        setStartTime(Date.now());
        return;
      }

      if (data.item_type === "review_variant") {
        setShowExplanation(false);
        setQuestions([]);
        setCurrentVariant(data.variant);
        setQuestions([formatK1ReviewVariant(data.variant)]);
        setCurrentIndex(0);
        setSelectedOption(null);
        setIsSubmitted(false);
        setIsGeneratingExplanation(false);
        setStartTime(Date.now());
        return;
      }

      if (data.item_type === "session_complete") {
        if (totalAttempted > 0) {
          await endPracticeSession();
          setShowSummaryModal(true);
        } else {
          setQuestions([]);
        }
        return;
      }

      setQuestions([]);
    } catch (error) {
      console.error("K1 next item fetch error:", error);
    } finally {
      setIsLoading(false);
    }
  };
  const handleRetryPractice = async () => {
    setShowSummaryModal(false);
    setRetryMode(true);
    setShowExplanation(false);
    setIsGeneratingExplanation(false);
    setStreak(0);
    setHighestStreak(0);
    setTotalAttempted(0);
    setCorrectAnswers(0);
    setAttemptsLog([]);
    setSelectedOption(null);
    setIsSubmitted(false);
    setCurrentVariant(null);

    const newPracticeId = await startPracticeSession();
    await fetchNextK1Item(newPracticeId, true);
  };
  const handleSelect = (index) => {
    if (!isSubmitted) setSelectedOption(index);
  };

  const handleSubmit = async () => {
  if (isSubmitted || selectedOption === null || isLoading || isSavingAttempt) {
    return;
  }

  setIsSavingAttempt(true);

  logUserActivity("practiced_kertas1");

  const isCorrectAnswer = selectedOption === currentQuestion.correctAnswerIndex;
  const timeTaken = Math.floor((Date.now() - startTime) / 1000);

  const attemptRecord = {
    question_id: currentQuestion.is_review_variant ? null : currentQuestion.id,
    review_variant_id: currentQuestion.review_variant_id || null,
    exercise_stage_id: null,

    paper_type: "kertas1",
    form_snapshot: form,
    chapter_snapshot_id: chapter_id,
    chapter_snapshot: currentQuestion.chapter || selectedChapter,

    difficulty_snapshot: currentQuestion.difficulty,
    difficulty_level_snapshot: currentQuestion.difficulty_level || 1,

    is_correct: isCorrectAnswer ? 1 : 0,
    score: isCorrectAnswer ? 1 : 0,
    max_score: 1,
    answer_revealed: 0,

    time_taken_seconds: timeTaken,
    attempted_at: new Date().toISOString(),
  };

  setIsSubmitted(true);
  setTotalAttempted((prev) => prev + 1);
  setAttemptsLog((prev) => [...prev, attemptRecord]);

  if (isCorrectAnswer) {
    const newStreak = streak + 1;
    setStreak(newStreak);
    setCorrectAnswers((prev) => prev + 1);

    if (newStreak > highestStreak) {
      setHighestStreak(newStreak);
    }
  } else {
    setStreak(0);
  }

  try {
    await saveSingleAttempt(attemptRecord);
  } catch (error) {
    console.error("Failed to save K1 attempt:", error);
  } finally {
    setIsSavingAttempt(false);
  }
};
  const handleShowExplanation = async () => {
    if (!currentQuestion || selectedOption === null || isGeneratingExplanation) {
      return;
    }

    setShowExplanation(true);

    const isCorrectAnswer =
      selectedOption === currentQuestion.correctAnswerIndex;

    await generateK1Explanation(
      currentQuestion,
      selectedOption,
      isCorrectAnswer
    );
  };
  const saveSingleAttempt = async (attemptRecord) => {
  if (!practiceId) {
    throw new Error("Missing practiceId. Cannot save attempt.");
  }

  const response = await apiFetch(
    `${process.env.REACT_APP_API_BASE_URL}/api/practice/save-attempt`,
    {
      method: "POST",
      body: JSON.stringify({
        practice_id: practiceId,
        form: form,
        chapter: selectedChapter,
        paper_type: "kertas1",
        language: language,
        attempt: attemptRecord,
      }),
    }
  );

  const data = await response.json().catch(() => ({}));

  if (!response.ok || !data.success) {
    throw new Error(data.message || "Failed to save attempt.");
  }

  console.log("K1 SAVE ATTEMPT RESPONSE:", data);
  return data;
};

  const endPracticeSession = async () => {
    if (!practiceId) return;

    try {
      await apiFetch(`${process.env.REACT_APP_API_BASE_URL}/api/practice/end-session`, {
        method: "POST",
        body: JSON.stringify({
          practice_id: practiceId,
          highest_streak: highestStreak,
        }),
      });
    } catch (error) {
      console.error("Failed to end practice session:", error);
    }
  };
  useEffect(() => {
    if (isSubmitted) {
      window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" });
    }
  }, [isSubmitted]);

  useEffect(() => {
    const initialisePractice = async () => {
      setIsLoading(true);

      try {
        const newPracticeId = await startPracticeSession();
        await fetchNextK1Item(newPracticeId);
      } catch (error) {
        console.error("Failed to initialise K1 practice:", error);
        setIsLoading(false);
      }
    };

    initialisePractice();
  }, [chapter_id, form, selectedChapter]);

  const currentQuestion = questions[currentIndex];

  if (isLoading) {
    return (
      <Box
        sx={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          height: "100vh",
        }}
      >
        <CircularProgress />
      </Box>
    );
  }

  if (!currentQuestion) {
    return (
      <Box
        sx={{
          textAlign: "center",
          mt: 10,
          px: 2,
        }}
      >
        <Typography variant="h5" fontWeight="bold" sx={{ mb: 3 }}>
          {text.noQuestions}
        </Typography>

        <Box
          sx={{
            display: "flex",
            justifyContent: "center",
            gap: 2,
            flexWrap: "wrap",
          }}
        >
          <Button
            variant="outlined"
            onClick={handleRetryPractice}
            sx={{
              borderRadius: "10px",
              px: 4,
              py: 1.2,
              fontWeight: "bold",
              textTransform: "none",
            }}
          >
            {isEnglish ? "Retry Practice" : "Cuba Semula Latihan"}
          </Button>

          <Button
            variant="contained"
            onClick={() => navigate("/practice")}
            sx={{
              bgcolor: "#3855c0",
              borderRadius: "10px",
              px: 4,
              py: 1.2,
              fontWeight: "bold",
              textTransform: "none",
              "&:hover": { bgcolor: "#2d4499" },
            }}
          >
            {text.goBack}
          </Button>
        </Box>
      </Box>
    );
  }
  

  const handleNextQuestion = async () => {
    if (isSavingAttempt || isGeneratingExplanation || isLoading) {
      return;
    }

    setSelectedOption(null);
    setIsSubmitted(false);
    setIsGeneratingExplanation(false);
    setShowExplanation(false);
    setStartTime(Date.now());

    await fetchNextK1Item();
  };

  const handleConfirmExit = async () => {
    await endPracticeSession();
    setOpenExitDialog(false);
    setShowSummaryModal(true);
  };

  const handleReturnToMenu = async () => {
    await endPracticeSession();
    setShowSummaryModal(false);
    navigate("/practice");
  };

  const wrongAnswers = totalAttempted - correctAnswers;
  const accuracy =
    totalAttempted > 0
      ? Math.round((correctAnswers / totalAttempted) * 100)
      : 0;

  const getDifficultyColor = (diff) => {
    if (diff === "Easy") return { bg: "#D1FAE5", text: "#065F46" };
    if (diff === "Moderate") return { bg: "#FEF3C7", text: "#92400E" };
    if (diff === "Hard") return { bg: "#FEE2E2", text: "#991B1B" };
    return { bg: "#F3F4F6", text: "#374151" };
  };
  const renderTableData = (tableData) => {
  if (!tableData || Object.keys(tableData).length === 0) return null;

  const renderRows = (rows) => {
    if (!Array.isArray(rows) || rows.length === 0) return null;

    return (
      <Box
        component="table"
        sx={{
          width: "100%",
          borderCollapse: "collapse",
          mt: 2,
          bgcolor: "white",
          "& td, & th": {
            border: "1px solid #D1D5DB",
            p: 1,
            textAlign: "center",
            fontSize: "14px",
          },
          "& th": {
            bgcolor: "#F3F4F6",
            fontWeight: "bold",
          },
        }}
      >
        <tbody>
          {rows.map((row, rowIndex) => {
            const rowCells = Array.isArray(row) ? row : Object.values(row || {});

            return (
              <tr key={rowIndex}>
                {rowCells.map((cell, cellIndex) => {
                  const Tag = rowIndex === 0 ? "th" : "td";

                  return (
                    <Tag key={cellIndex}>
                      {renderMathOrText(getLocalizedTableCell(cell))}
                    </Tag>
                  );
                })}
              </tr>
            );
          })}
        </tbody>
      </Box>
    );
  };

  // Case 1: table_data = { header: [{ MalayKey: EnglishHeader }], rows: [{ MalayKey: value }] }
  if (tableData.header && Array.isArray(tableData.rows)) {
    const normalizedRows = normalizeObjectTable(tableData);

    if (normalizedRows) {
      return renderRows(normalizedRows);
    }
  }

  // Case 2: table_data = { columns: [...], rows: [...] }
  if (Array.isArray(tableData.columns) || Array.isArray(tableData.rows)) {
    const headerRow = Array.isArray(tableData.columns)
      ? tableData.columns.map(getLocalizedTableCell)
      : [];

    const rows = [
      ...(headerRow.length > 0 ? [headerRow] : []),
      ...(Array.isArray(tableData.rows) ? tableData.rows : []),
    ];

    return renderRows(rows);
  }

  // Case 3: table_data = { headers: [[...], [...]], rows: [...] }
  if (Array.isArray(tableData.headers)) {
    const rows = [
      ...tableData.headers,
      ...(Array.isArray(tableData.rows) ? tableData.rows : []),
    ];

    return renderRows(rows);
  }

  // Case 4: table_data = { "Table 1": [[...], [...]] }
  return (
    <Box sx={{ mt: 2 }}>
      {Object.entries(tableData).map(([title, rows]) => (
        <Box key={title} sx={{ mb: 2 }}>
          <Typography variant="subtitle2" fontWeight="bold" sx={{ mb: 1 }}>
            {title}
          </Typography>
          {renderRows(rows)}
        </Box>
      ))}
    </Box>
  );
};
  const diffColors = getDifficultyColor(currentQuestion.difficulty);

  return (
    <Box sx={{ minHeight: "100vh", bgcolor: "#f9fbfd", pb: 6 }}>
      {/* TOP APP BAR */}
      <Box
        sx={{
          bgcolor: "white",
          px: { xs: 2, md: 4.5 },
          py: { xs: 1.8, md: 2.2 },
          minHeight: { xs: 64, md: 74 },
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 1.5,
          boxShadow: "0px 1px 6px rgba(0,0,0,0.06)",
          position: "sticky",
          top: 0,
          zIndex: 10,
        }}
      >
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            gap: 1,
            minWidth: 0,
            flex: 1,
          }}
        >
          <IconButton
            onClick={() => setOpenExitDialog(true)}
            sx={{ color: "#111827", p: 1.2 }}
          >
            <ArrowBackIcon sx={{ fontSize: 28 }} />
          </IconButton>

          <Typography
            variant="h6"
            color="#111827"
            fontWeight="900"
            sx={{
              textTransform: "uppercase",
              fontSize: { xs: "13px", sm: "15px", md: "17px" },
              lineHeight: 1.35,
              letterSpacing: "0.3px",
              whiteSpace: "normal",
              wordBreak: "break-word",
              minWidth: 0,
            }}
          >
            {text.paper} › {topic}
          </Typography>
        </Box>

        <Box
          sx={{
            display: "flex",
            gap: 1,
            alignItems: "center",
            flexShrink: 0,
          }}
        >
          <Chip
            icon={<AutoGraphIcon style={{ color: diffColors.text, fontSize: "15px" }} />}
            label={difficultyLabel(currentQuestion.difficulty)}
            sx={{
              bgcolor: diffColors.bg,
              color: diffColors.text,
              fontWeight: "bold",
              borderRadius: "8px",
              height: 36,
              "& .MuiChip-label": {
                px: 1,
                fontSize: "12px",
              },
            }}
          />

          <Chip
            icon={<LocalFireDepartmentIcon style={{ color: "#EA580C", fontSize: "15px" }} />}
            label={window.innerWidth < 600 ? `${streak}` : `${streak} ${text.streak}`}
            sx={{
              bgcolor: "#FFEDD5",
              color: "#C2410C",
              fontWeight: "bold",
              borderRadius: "8px",
              height: 36,
              "& .MuiChip-label": {
                px: 1,
                fontSize: "12px",
              },
            }}
          />
        </Box>
      </Box>

      {/* MAIN QUESTION CONTAINER */}
      <Container maxWidth="md" sx={{ mt: 5 }}>
        <Paper
          elevation={0}
          sx={{
            p: { xs: 3, md: 5 },
            borderRadius: "20px",
            border: "1px solid #E5E7EB",
            mb: 4,
            maxWidth: "100%",
            overflow: "hidden",
          }}
        >
          <Typography
            variant="h5"
            fontWeight="600"
            color="#111827"
            sx={{ 
              lineHeight: 1.5,
              wordBreak: "break-word", // <-- Forces long strings to break
              overflowWrap: "anywhere",
              minWidth: 0,
              maxWidth: "100%",
              overflowX: "auto",
              overflowY: "hidden",
              "& .katex": {
                fontSize: { xs: "0.9em", sm: "1em" },
                maxWidth: "100%",
              },
              "& .katex-display": {
                maxWidth: "100%",
                overflowX: "auto",
                overflowY: "hidden",
                margin: "0.5em 0",
                paddingBottom: "4px",
              },
            }}
          >
            {renderMathOrText((isEnglish ? currentQuestion.question_en : currentQuestion.question_bm) || "")}
          </Typography>

          {currentQuestion.question_image && (
            <Box sx={{ mt: 3, display: "flex", justifyContent: "center" }}>
              <img
                src={currentQuestion.question_image}
                alt="Question diagram"
                style={{
                  maxWidth: "100%",
                  maxHeight: "300px",
                  borderRadius: "8px",
                  objectFit: "contain",
                }}
              />
            </Box>
          )}
          {renderTableData(currentQuestion.table_data)}
        </Paper>

        <Box
          sx={{
            display: "flex",
            flexDirection: "column",
            gap: 2,
            mb: 4,
          }}
        >
          {(isEnglish
            ? currentQuestion.options_en
            : currentQuestion.options_bm
          ).map((opt, index) => {
            const isSelected = selectedOption === index;
            const isCorrectAnswer = currentQuestion.correctAnswerIndex === index;

            let borderColor = "#E5E7EB";
            let bgColor = "#ffffff";
            let textColor = "#4B5563";

            if (isSubmitted) {
              if (isCorrectAnswer) {
                borderColor = "#10B981";
                bgColor = "#ECFDF5";
                textColor = "#065F46";
              } else if (isSelected && !isCorrectAnswer) {
                borderColor = "#EF4444";
                bgColor = "#FEF2F2";
                textColor = "#991B1B";
              }
            } else if (isSelected) {
              borderColor = "#3855c0";
              bgColor = "#EEF2FF";
              textColor = "#3855c0";
            }

            return (
              <Paper
                key={index}
                elevation={0}
                onClick={() => handleSelect(index)}
                sx={{
                  p: 2,
                  display: "flex",
                  alignItems: "center",
                  gap: 3,
                  cursor: isSubmitted ? "default" : "pointer",
                  border: `2px solid ${borderColor}`,
                  borderRadius: "16px",
                  bgcolor: bgColor,
                  minWidth: 0,
                  maxWidth: "100%",
                  overflow: "hidden",
                  transition: "all 0.2s ease",
                  "&:hover": {
                    borderColor: isSubmitted ? borderColor : "#3855c0",
                    bgcolor: isSubmitted ? bgColor : "#F9FAFB",
                  },
                }}
              >
                <Box
                  sx={{
                    width: 36,
                    height: 36,
                    borderRadius: "50%",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontWeight: "bold",
                    fontSize: "16px",
                    flexShrink: 0,
                    bgcolor:
                      isSubmitted && (isCorrectAnswer || isSelected)
                        ? borderColor
                        : isSelected
                        ? "#3855c0"
                        : "#F3F4F6",
                    color:
                      isSubmitted && (isCorrectAnswer || isSelected)
                        ? "#ffffff"
                        : isSelected
                        ? "#ffffff"
                        : "#6B7280",
                  }}
                >
                  {String.fromCharCode(65 + index)}
                </Box>

                <Typography
                  variant="body1"
                  fontWeight={isSelected ? "bold" : "medium"}
                  color={textColor}
                  sx={{
                    flexGrow: 1,
                    minWidth: 0,
                    maxWidth: "100%",
                    fontSize: { xs: "14px", sm: "16px" },
                    lineHeight: 1.55,
                    overflowWrap: "anywhere",
                    wordBreak: "break-word",
                    overflowX: "auto",
                    overflowY: "hidden",
                    "& .katex": {
                      fontSize: { xs: "0.9em", sm: "1em" },
                      maxWidth: "100%",
                    },
                    "& .katex-display": {
                      maxWidth: "100%",
                      overflowX: "auto",
                      overflowY: "hidden",
                      margin: "0.35em 0",
                      paddingBottom: "4px",
                    },
                  }}
                >
                  {renderMathOrText(opt)}

                  {currentQuestion.options_image &&
                    currentQuestion.options_image[index] && (
                      <Box sx={{ mt: 1.5 }}>
                        <img
                          src={currentQuestion.options_image[index]}
                          alt={`Option ${index}`}
                          style={{
                            maxWidth: "200px",
                            maxHeight: "150px",
                            borderRadius: "8px",
                            objectFit: "contain",
                          }}
                        />
                      </Box>
                    )}
                </Typography>

                {isSubmitted && isCorrectAnswer && (
                  <CheckCircleOutlineIcon sx={{ color: "#10B981" }} />
                )}
                {isSubmitted && isSelected && !isCorrectAnswer && (
                  <HighlightOffIcon sx={{ color: "#EF4444" }} />
                )}
              </Paper>
            );
          })}
        </Box>

        <Box sx={{ display: "flex", justifyContent: "flex-end", mb: 4 }}>
          {!isSubmitted ? (
            <Button
              variant="contained"
              size="large"
              disabled={selectedOption === null || isSubmitted || isLoading}
              onClick={handleSubmit}
              sx={{
                px: 5,
                py: 1.5,
                borderRadius: "12px",
                fontSize: "16px",
                fontWeight: "bold",
                bgcolor: "#3855c0",
                "&:hover": { bgcolor: "#2d4499" },
                textTransform: "none",
              }}
            >
              {text.checkBtn}
            </Button>
          ) : null}
        </Box>

        {isSubmitted && (
          <Fade in={isSubmitted}>
            <Box>
              <Paper
                elevation={0}
                sx={{
                  p: 3,
                  mb: 3,
                  borderRadius: "16px",
                  display: "flex",
                  alignItems: "flex-start",
                  gap: 2,
                  bgcolor:
                    selectedOption === currentQuestion.correctAnswerIndex
                      ? "#ECFDF5"
                      : "#FEF2F2",
                  border: `1px solid ${
                    selectedOption === currentQuestion.correctAnswerIndex
                      ? "#A7F3D0"
                      : "#FECACA"
                  }`,
                }}
              >
                {selectedOption === currentQuestion.correctAnswerIndex ? (
                  <CheckCircleOutlineIcon
                    sx={{ color: "#10B981", fontSize: 32, mt: 0.5 }}
                  />
                ) : (
                  <HighlightOffIcon
                    sx={{ color: "#EF4444", fontSize: 32, mt: 0.5 }}
                  />
                )}

                <Box flex={1}>
                  <Box
                    sx={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      gap: 2,
                      flexWrap: "wrap",
                      mb: 2,
                    }}
                  >
                    <Typography
                      variant="h6"
                      fontWeight="bold"
                      color={
                        selectedOption === currentQuestion.correctAnswerIndex
                          ? "#065F46"
                          : "#991B1B"
                      }
                    >
                      {selectedOption === currentQuestion.correctAnswerIndex
                        ? text.correct
                        : text.wrong}
                    </Typography>

                    <DisclaimerText sx={{ mt: 0, flexShrink: 0 }} />
                  </Box>

                 {showExplanation && (
                  <Box
                    sx={{
                      mt: 2,
                      p: 2,
                      bgcolor: "rgba(255,255,255,0.6)",
                      borderRadius: "12px",
                      border: "1px dashed rgba(0,0,0,0.1)",
                    }}
                  >
                    <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1 }}>
                      <LightbulbOutlinedIcon
                        fontSize="small"
                        sx={{ color: "#D97706" }}
                      />
                      <Typography
                        variant="subtitle2"
                        fontWeight="bold"
                        color="#D97706"
                        textTransform="uppercase"
                      >
                        {text.explanation}
                      </Typography>
                    </Box>

                    {isGeneratingExplanation ? (
                      <Typography variant="body1" color="#6B7280">
                        {isEnglish
                          ? "Preparing explanation..."
                          : "Menyediakan penerangan..."}
                      </Typography>
                    ) : (
                      <Typography
                        variant="body1"
                        color="#4B5563"
                        sx={{ whiteSpace: "pre-line" }}
                      >
                        {renderMathOrText((isEnglish ? currentQuestion.explanation_en : currentQuestion.explanation_bm) || "")}
                      </Typography>
                    )}

                    {currentQuestion.explanation_image && (
                      <Box sx={{ mt: 2, display: "flex", justifyContent: "center" }}>
                        <img
                          src={currentQuestion.explanation_image}
                          alt="Explanation diagram"
                          style={{
                            maxWidth: "100%",
                            maxHeight: "250px",
                            borderRadius: "8px",
                            objectFit: "contain",
                            border: "1px solid #E5E7EB",
                          }}
                        />
                      </Box>
                    )}
                  </Box>
                )}
                </Box>
              </Paper>
              <Box
              sx={{
                display: "flex",
                gap: 2,
                flexDirection: { xs: "column", sm: "row" },
              }}
            >
              {!showExplanation && (
                <Button
                  variant="outlined"
                  fullWidth
                  size="large"
                  disabled={isSavingAttempt || isGeneratingExplanation || isLoading}
                  onClick={handleShowExplanation}
                  startIcon={
                    isGeneratingExplanation ? (
                      <CircularProgress size={18} color="inherit" />
                    ) : (
                      <LightbulbOutlinedIcon />
                    )
                  }
                  sx={{
                    py: 1.5,
                    borderRadius: "12px",
                    fontSize: "16px",
                    fontWeight: "bold",
                    textTransform: "none",
                  }}
                >
                  {isGeneratingExplanation
                    ? isEnglish
                      ? "Preparing explanation..."
                      : "Menyediakan penerangan..."
                    : isEnglish
                    ? "Show Explanation"
                    : "Tunjuk Penerangan"}
                </Button>
              )}

              <Button
                variant="contained"
                fullWidth
                size="large"
                disabled={isSavingAttempt || isLoading || isGeneratingExplanation}
                onClick={handleNextQuestion}
                sx={{
                  py: 1.5,
                  borderRadius: "12px",
                  fontSize: "16px",
                  fontWeight: "bold",
                  bgcolor: "#111827",
                  "&:hover": { bgcolor: "#374151" },
                  textTransform: "none",
                  boxShadow: "0 8px 20px rgba(0,0,0,0.1)",
                }}
              >
                {isSavingAttempt
                  ? isEnglish
                    ? "Saving..."
                    : "Menyimpan..."
                  : text.nextBtn}
              </Button>
            </Box>
            </Box>
          </Fade>
        )}
      </Container>
      <Dialog
        open={openEasierDialog}
        onClose={() => setOpenEasierDialog(false)}
        PaperProps={{ sx: { borderRadius: "20px", padding: 1, maxWidth: "430px" } }}
      >
        <DialogTitle sx={{ fontWeight: "bold", color: "#111827" }}>
          {isEnglish ? "Hard Questions Completed" : "Soalan Sukar Selesai"}
        </DialogTitle>

        <DialogContent>
          <DialogContentText sx={{ color: "#4B5563" }}>
            {adaptiveMessage ||
              (isEnglish
                ? "You have completed all hard questions. Do you want to continue with the remaining easier questions?"
                : "Anda telah menyelesaikan semua soalan sukar. Adakah anda mahu teruskan dengan soalan yang lebih mudah?")}
          </DialogContentText>
        </DialogContent>

        <DialogActions sx={{ px: 3, pb: 2, justifyContent: "space-between" }}>
          <Button
            onClick={async () => {
              setOpenEasierDialog(false);
              await endPracticeSession();
              setShowSummaryModal(true);
            }}
            sx={{ color: "#6B7280", fontWeight: "bold", textTransform: "none" }}
          >
            {isEnglish ? "No, finish" : "Tidak, tamatkan"}
          </Button>

          <Button
            onClick={() => {
              setOpenEasierDialog(false);
              fetchNextK1Item();
            }}
            variant="contained"
            sx={{
              bgcolor: "#3855c0",
              borderRadius: "10px",
              fontWeight: "bold",
              textTransform: "none",
            }}
          >
            {isEnglish ? "Yes, continue" : "Ya, teruskan"}
          </Button>
        </DialogActions>
      </Dialog>
      <Dialog
        open={openExitDialog}
        onClose={() => setOpenExitDialog(false)}
        PaperProps={{
          sx: { borderRadius: "20px", padding: 1, maxWidth: "400px" },
        }}
      >
        <DialogTitle sx={{ fontWeight: "bold", color: "#111827", pb: 1 }}>
          {text.exitTitle}
        </DialogTitle>
        <DialogContent>
          <DialogContentText sx={{ color: "#4B5563" }}>
            {text.exitDesc}
          </DialogContentText>
        </DialogContent>
        <DialogActions
          sx={{
            justifyContent: "center",
            gap: 2,
            pt: 2,
            pb: 1,
            flexWrap: "wrap",
          }}
        >
          <Button
            onClick={() => setOpenExitDialog(false)}
            sx={{ color: "#6B7280", fontWeight: "bold", textTransform: "none" }}
          >
            {text.cancelBtn}
          </Button>
          <Button
            onClick={handleConfirmExit}
            variant="contained"
            disableElevation
            sx={{
              bgcolor: "#3855c0",
              "&:hover": { bgcolor: "#2d4499" },
              borderRadius: "10px",
              fontWeight: "bold",
              textTransform: "none",
            }}
          >
            {text.confirmExitBtn}
          </Button>
        </DialogActions>
      </Dialog>

      {showSummaryModal && (
        <Portal>
          <Confetti
            width={width}
            height={height}
            recycle={false}
            numberOfPieces={width < 600 ? 180 : 500}
            gravity={0.15}
            style={{
              zIndex: 99999,
              position: "fixed",
              top: 0,
              left: 0,
              pointerEvents: "none",
            }}
          />
        </Portal>
      )}

      <Dialog
        open={showSummaryModal}
        maxWidth="xs"
        fullWidth
        PaperProps={{
          sx: {
            borderRadius: { xs: "22px", sm: "28px" },
            width: { xs: "calc(100% - 24px)", sm: 440 },
            maxWidth: { xs: "calc(100% - 24px)", sm: 440 },
            maxHeight: { xs: "calc(100dvh - 32px)", sm: "90vh" },
            m: { xs: 1.5, sm: 2 },
            overflow: "hidden",
            textAlign: "center",
          },
        }}
      >
        <DialogContent
          sx={{
            p: { xs: 2.2, sm: 4 },
            overflowY: "auto",
            maxHeight: { xs: "calc(100dvh - 32px)", sm: "90vh" },
            textAlign: "center",
          }}
        >
          <Typography
            sx={{
              fontSize: { xs: "2rem", sm: "2.7rem" },
              fontWeight: 900,
              color: "#3855c0",
              lineHeight: 1.12,
              mb: 1,
            }}
          >
            {text.sessionComplete}
          </Typography>

          <Typography
            sx={{
              fontSize: { xs: "0.95rem", sm: "1.05rem" },
              color: "#6B7280",
              lineHeight: 1.7,
              mb: { xs: 2.2, sm: 3 },
            }}
          >
            {text.summaryDesc}
          </Typography>

          <Box
            sx={{
              display: "grid",
              gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
              gap: { xs: 1.2, sm: 2 },
            }}
          >
            <Box
              sx={{
                bgcolor: "#F3F4F6",
                p: { xs: 1.4, sm: 2 },
                borderRadius: "16px",
                minHeight: { xs: 105, sm: 125 },
                display: "flex",
                flexDirection: "column",
                justifyContent: "center",
                alignItems: "center",
              }}
            >
              <Typography
                sx={{
                  fontSize: { xs: "1.8rem", sm: "2.4rem" },
                  fontWeight: 900,
                  color: "#1F2937",
                  lineHeight: 1,
                }}
              >
                {totalAttempted}
              </Typography>

              <Typography
                sx={{
                  mt: 1,
                  fontSize: { xs: "0.78rem", sm: "0.95rem" },
                  color: "#6B7280",
                  fontWeight: 800,
                  lineHeight: 1.25,
                }}
              >
                {text.questionsAttempted}
              </Typography>
            </Box>

            <Box
              sx={{
                bgcolor: "#ECFDF5",
                p: { xs: 1.4, sm: 2 },
                borderRadius: "16px",
                minHeight: { xs: 105, sm: 125 },
                display: "flex",
                flexDirection: "column",
                justifyContent: "center",
                alignItems: "center",
              }}
            >
              <Typography
                sx={{
                  fontSize: { xs: "1.8rem", sm: "2.4rem" },
                  fontWeight: 900,
                  color: "#047857",
                  lineHeight: 1,
                }}
              >
                {accuracy}%
              </Typography>

              <Typography
                sx={{
                  mt: 1,
                  fontSize: { xs: "0.78rem", sm: "0.95rem" },
                  color: "#059669",
                  fontWeight: 800,
                  lineHeight: 1.25,
                }}
              >
                {text.accuracyLabel}
              </Typography>
            </Box>

            <Box
              sx={{
                bgcolor: "#FEF2F2",
                p: { xs: 1.4, sm: 2 },
                borderRadius: "16px",
                minHeight: { xs: 105, sm: 125 },
                display: "flex",
                flexDirection: "column",
                justifyContent: "center",
                alignItems: "center",
              }}
            >
              <Typography
                sx={{
                  fontSize: { xs: "1.8rem", sm: "2.4rem" },
                  fontWeight: 900,
                  color: "#DC2626",
                  lineHeight: 1,
                }}
              >
                {wrongAnswers}
              </Typography>

              <Typography
                sx={{
                  mt: 1,
                  fontSize: { xs: "0.78rem", sm: "0.95rem" },
                  color: "#EF4444",
                  fontWeight: 800,
                  lineHeight: 1.25,
                }}
              >
                {text.needsReview}
              </Typography>
            </Box>

            <Box
              sx={{
                bgcolor: "#FFF7ED",
                p: { xs: 1.4, sm: 2 },
                borderRadius: "16px",
                minHeight: { xs: 105, sm: 125 },
                display: "flex",
                flexDirection: "column",
                justifyContent: "center",
                alignItems: "center",
              }}
            >
              <Typography
                sx={{
                  fontSize: { xs: "1.8rem", sm: "2.4rem" },
                  fontWeight: 900,
                  color: "#EA580C",
                  lineHeight: 1,
                }}
              >
                🔥 {highestStreak}
              </Typography>

              <Typography
                sx={{
                  mt: 1,
                  fontSize: { xs: "0.78rem", sm: "0.95rem" },
                  color: "#D97706",
                  fontWeight: 800,
                  lineHeight: 1.25,
                }}
              >
                {text.highestStreakLabel}
              </Typography>
            </Box>
          </Box>

          <Box
            sx={{
              display: "flex",
              flexDirection: { xs: "column", sm: "row" },
              gap: { xs: 1.2, sm: 1.5 },
              mt: { xs: 2.4, sm: 3 },
            }}
          >
            <Button
              fullWidth
              variant="outlined"
              onClick={handleRetryPractice}
              sx={{
                borderRadius: "18px",
                py: { xs: 1.15, sm: 1.4 },
                fontWeight: 800,
                textTransform: "none",
                fontSize: { xs: "0.95rem", sm: "1rem" },
              }}
            >
              {isEnglish ? "Retry Practice" : "Cuba Semula Latihan"}
            </Button>

            <Button
              fullWidth
              variant="contained"
              onClick={handleReturnToMenu}
              sx={{
                borderRadius: "18px",
                py: { xs: 1.15, sm: 1.4 },
                fontWeight: 800,
                textTransform: "none",
                fontSize: { xs: "0.95rem", sm: "1rem" },
                bgcolor: "#3855c0",
                boxShadow: "0 8px 20px rgba(56,85,192,0.25)",
                "&:hover": { bgcolor: "#2d4499" },
              }}
            >
              {text.backToDash}
            </Button>
          </Box>
        </DialogContent>
      </Dialog>
    </Box>
  );
};

export default PracticePageKertas1;
