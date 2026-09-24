import React, { useEffect, useRef, useState } from "react";
import { useLocation } from "react-router-dom";
import {
  Box,
  Typography,
  Paper,
  Button,
  CircularProgress,
  Divider,
  Tabs,
  Tab,
  Chip,
  Collapse,
  TextField
} from "@mui/material";
import 'katex/dist/katex.min.css';
import katex from 'katex';
import CloudUploadOutlinedIcon from "@mui/icons-material/CloudUploadOutlined";
import PhotoCameraOutlinedIcon from "@mui/icons-material/PhotoCameraOutlined";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import AutoFixHighIcon from "@mui/icons-material/AutoFixHigh";
import FunctionsIcon from "@mui/icons-material/Functions";
import FactCheckOutlinedIcon from "@mui/icons-material/FactCheckOutlined";
import ChatOutlinedIcon from "@mui/icons-material/ChatOutlined";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import ExpandLessIcon from "@mui/icons-material/ExpandLess";
import { useLanguage } from "../../context/LanguageContext";
import { apiFetch } from "../../utils/apiFetch";
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import HighlightOffIcon from '@mui/icons-material/HighlightOff';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';
import DisclaimerText from "../../components/DisclaimerText";

const QuickSnapPage = () => {
  const { language, t } = useLanguage();
  const isEnglish = language !== "bm";

const text = {
  uploadQuestion: isEnglish ? "Upload Question Image" : "Muat Naik Imej Soalan",
  uploadWork: isEnglish ? "Upload Your Work" : "Muat Naik Jalan Kerja Anda",
  questionSubtitle: isEnglish
    ? "Drag and drop your question image here"
    : "Tarik dan lepaskan imej soalan anda di sini",
  workSubtitle: isEnglish
    ? "Snap a clear photo of your working steps"
    : "Ambil gambar jalan kerja anda dengan jelas",
  browse: isEnglish ? "Browse" : "Pilih Fail",
  solveNow: isEnglish ? "Solve Now" : "Selesaikan Sekarang",
  checkNow: isEnglish ? "Check My Work" : "Semak Jalan Kerja",
  processing: isEnglish ? "Processing..." : "Sedang Diproses...",
  remove: isEnglish ? "Remove" : "Padam",
  uploadBoth: isEnglish
    ? "Please upload both the question image and your answer image."
    : "Sila muat naik imej soalan dan imej jawapan anda.",
  confirmCoordinates: isEnglish ? "Confirm Coordinates" : "Sahkan Koordinat",
  coordinateHelp: isEnglish
    ? "Please enter the exact coordinates from the graph before solving."
    : "Sila masukkan koordinat tepat daripada graf sebelum menyelesaikan soalan.",
  confirmSolve: isEnglish ? "Confirm & Solve" : "Sahkan & Selesaikan",
  hideQuestion: isEnglish ? "Hide Question Image" : "Sembunyikan Imej Soalan",
  viewQuestion: isEnglish ? "View Question Image" : "Lihat Imej Soalan",
  scanNew: isEnglish ? "Scan New Question" : "Imbas Soalan Baharu",
  stepBreakdown: isEnglish ? "Step-by-Step Breakdown" : "Pecahan Langkah demi Langkah",
  studentWrote: isEnglish ? "Student Wrote:" : "Pelajar Menulis:",
  reason: isEnglish ? "Reason:" : "Sebab:",
  noSummary: isEnglish
    ? "No step-by-step summary available."
    : "Tiada ringkasan langkah demi langkah tersedia.",
};
  const location = useLocation();

  const [mode, setMode] = useState("solve_question");
  useEffect(() => {
    if (location.state?.mode === "check_my_work") {
      setMode("check_my_work");
      setResult(null);
    }
  }, [location.state?.mode]);
  const [selectedImage, setSelectedImage] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [selectedAnswerImage, setSelectedAnswerImage] = useState(null);
  const [selectedAnswerFile, setSelectedAnswerFile] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [result, setResult] = useState(null);
  const [isQuestionOpen, setIsQuestionOpen] = useState(false);
  const fileInputRef = useRef(null);
  const answerFileInputRef = useRef(null);
  const [coordinateValues, setCoordinateValues] = useState({});

  const handleModeChange = (_event, newValue) => {
    if (!newValue) return;
    setMode(newValue);
    setResult(null);
    clearImage("all");
  };
  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e, type = "question") => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const file = e.dataTransfer.files?.[0];

    if (!file) return;

    if (!file.type.startsWith("image/")) {
      alert(isEnglish ? "Please upload an image file." : "Sila muat naik fail imej.");
      return;
    }

    handleImageSelect(file, type);
  };
  
  const handleFileChange = (e, type = "question") => {
    if (e.target.files && e.target.files[0]) {
      handleImageSelect(e.target.files[0], type);
    }
  };

  const handleImageSelect = (file, type = "question") => {
    const imageUrl = URL.createObjectURL(file);
    if (type === "question") {
      setSelectedImage(imageUrl);
      setSelectedFile(file);
    } else {
      setSelectedAnswerImage(imageUrl);
      setSelectedAnswerFile(file);
    }
    setResult(null);
  };

  const clearImage = (type = "all") => {
    if (type === "question" || type === "all") {
      setSelectedImage(null);
      setSelectedFile(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
    if (type === "answer" || type === "all") {
      setSelectedAnswerImage(null);
      setSelectedAnswerFile(null);
      if (answerFileInputRef.current) answerFileInputRef.current.value = "";
    }
    if (type === "all") {
      setResult(null);
      setIsQuestionOpen(true); 
    }
  };

  const cleanLatexText = (text) => {
    return String(text || "")
      // Fix double backslashes before fractions (AI sometimes double-escapes)
      .replace(/\\\\(dfrac|frac)/g, "\\$1")
      // Fix stray backslash before a period at the end (e.g., `1000\.`)
      .replace(/\\\.\s*$/g, "")
      // Fix random stray backslash at the very end
      .replace(/\\\s*$/g, "")
      // Convert proper LaTeX commands into safe display symbols
      .replace(/\\neq?(?![a-zA-Z])/g, "≠")
      .replace(/\\leq?(?![a-zA-Z])/g, "≤")
      .replace(/\\geq?(?![a-zA-Z])/g, "≥")
      .replace(/[ \t]{2,}/g, " ")
      .trim();
  };

const wrapFinalAnswerMath = (text) => {
  let clean = cleanLatexText(text);

  // Already wrapped for your renderInlineMath
  if (clean.includes("$") || clean.includes("\\(")) {
    return clean;
  }
  // Pure maths answer
  const textWithoutLatex = clean.replace(/\\[a-zA-Z]+/g, "");
  const hasEnglishWords = /[a-zA-Z]{3,}/.test(textWithoutLatex);

  if (!hasEnglishWords) {
    return `$${clean}$`;
  }

  return clean;
};

const formatFinalAnswer = (value) => {
  if (!value) return null;

  const entries =
    typeof value === "object" && value !== null
      ? Object.entries(value)
      : String(value)
          .split("\n")
          .filter((line) => line.trim())
          .map((line, index) => [null, line]);

  return entries.map(([key, answer], idx) => {
    const displayKey = key
      ? key.startsWith("(")
        ? key
        : `(${key})`
      : "";

    const cleanAnswer = wrapFinalAnswerMath(answer);

    return (
      <Typography
        key={idx}
        component="div"
        sx={{
          display: "block",
          mb: 1.5,
          color: "#065F46",
          fontWeight: "700",
          lineHeight: 1.8,
          wordBreak: "break-word",
          fontSize: {
            xs: "1rem",
            sm: "1.1rem",
            md: "1.2rem",
          },
          "& .katex": {
            fontSize: "1.1em",
          },
        }}
      >
        {displayKey && (
          <Box component="span" sx={{ mr: 1 }}>
            {displayKey}
          </Box>
        )}
        {renderInlineMath(cleanAnswer)}
      </Typography>
    );
  });
};

  const normalizeSolveResult = (apiData) => {
    return {
      mode: "solve_question",
      result_type: "solution",
      status: apiData.status || "success",
      question_text:
        apiData.question_text ||
        apiData.detected_question ||
        apiData.display_parsed_equation ||
        apiData.parsed_equation ||
        apiData.equation ||
        apiData.input_text ||
        "",
      steps: Array.isArray(apiData.steps) ? apiData.steps : [],
      final_answer: apiData.final_answer ?? apiData.answer ?? "",
      message: apiData.message || "",
    };
  };

  const normalizeCheckResult = (apiData) => {
    return {
      mode: "check_my_work",
      result_type: "work_check",
      status: apiData.status || "success",
      question_text: apiData.question_text || apiData.detected_question || "",
      score: apiData.score ?? null,
      max_score: apiData.max_score ?? null,
      correctness_summary: apiData.correctness_summary || apiData.summary || "",
      message: apiData.message || "",
    };
  };

  const logQuickSnapEvent = async ({
    modeUsed,
    resultType,
    followUpChatOpened = false,
  }) => {
    try {
      await apiFetch(`${process.env.REACT_APP_API_BASE_URL}/api/quick-snap/log`, {
        method: "POST",
        body: JSON.stringify({
          mode: modeUsed,
          result_type: resultType,
          follow_up_chat_opened: followUpChatOpened,
          timestamp: new Date().toISOString(),
        }),
      });
    } catch (error) {
      console.error("Failed to log quick snap event:", error);
    }
  };
  const renderInlineMath = (text) => {
    if (!text) return null;

    const safeText = cleanLatexText(text);

    const parts = safeText.split(/(\$[\s\S]*?\$|\\\([\s\S]*?\\\)|\\begin\{[^}]+\}[\s\S]*?\\end\{[^}]+\})/g);
    
    return parts.map((part, index) => {
      // 1. Handle standard inline math wrapped in $
      if (part.startsWith('$') && part.endsWith('$')) {
        let mathContent = part.slice(1, -1);
        // ✨ ADD SPACE PRESERVER
        mathContent = mathContent.replace(/(?<=[a-zA-Z0-9.,])\s+(?=[a-zA-Z0-9])/g, "\\ ");
        return <Box component="span" key={index} sx={{ color: "#2563EB", mx: 0.5 }} dangerouslySetInnerHTML={{ __html: katex.renderToString(mathContent, { throwOnError: false, displayMode: false }) }} />;
      } 
      // 2. NEW: Handle inline math wrapped in \( and \)
      else if (part.startsWith('\\(') && part.endsWith('\\)')) {
        let mathContent = part.slice(2, -2);
        // ✨ ADD SPACE PRESERVER
        mathContent = mathContent.replace(/(?<=[a-zA-Z0-9.,])\s+(?=[a-zA-Z0-9])/g, "\\ ");
        return <Box component="span" key={index} sx={{ color: "#2563EB", mx: 0.5 }} dangerouslySetInnerHTML={{ __html: katex.renderToString(mathContent, { throwOnError: false, displayMode: false }) }} />;
      }
      // 3. Handle matrices and block math
      else if (part.startsWith('\\begin{')) {
        // ✨ ADD SPACE PRESERVER
        let mathContent = part.replace(/(?<=[a-zA-Z0-9.,])\s+(?=[a-zA-Z0-9])/g, "\\ ");
        return <Box key={index} sx={{ bgcolor: "#F9FAFB", border: "1px solid #E5E7EB", borderRadius: "10px", p: 2, my: 1.5, overflowX: "auto", color: "#2563EB", display: "block", "& .katex": { fontSize: "1.1rem" } }} dangerouslySetInnerHTML={{ __html: katex.renderToString(mathContent, { throwOnError: false, displayMode: true }) }} />;
      }
      
      // 4. Return normal text
      return <span key={index}>{part}</span>;
    });
  };
  const getAllCoordinatePoints = (coordinateInput) => {
    if (Array.isArray(coordinateInput?.shapes) && coordinateInput.shapes.length > 0) {
      return coordinateInput.shapes.flatMap((shape) => shape.point_labels || []);
    }
    return [
      ...(coordinateInput?.object_points || []),
      ...(coordinateInput?.image_points || []),
      ...(coordinateInput?.other_required_points || []),
    ];
  };
const sanitizeMathBlockForKatex = (value) => {
  let clean = cleanLatexText(value);

  if (!clean) return "";

  clean = clean
    .replace(/^\s*\$\$\s*/, "")
    .replace(/\s*\$\$\s*$/, "")
    .replace(/^\s*\$\s*/, "")
    .replace(/\s*\$\s*$/, "")
    .trim();

  const alignedMatch = clean.match(
    /^\\begin\{aligned\}([\s\S]*)\\end\{aligned\}$/i
  );

  if (alignedMatch) {
    let inner = alignedMatch[1].trim();

    inner = inner
      .replace(/&\s*=/g, "=")
      .replace(/=\s*&/g, "=")
      .trim();

    clean = inner;
  }

  return clean;
};

const renderMathBlock = (value) => {
  const clean = sanitizeMathBlockForKatex(value);

  if (!clean) return null;

  try {
    return (
      <Box
        sx={{
          bgcolor: "#F9FAFB",
          border: "1px solid #E5E7EB",
          borderRadius: "10px",
          p: 2,
          overflowX: "auto",
          maxWidth: "100%",
          boxSizing: "border-box",
          color: "#2563EB",
          "& .katex": { fontSize: "1.1rem" },
          "& .katex-display": { margin: 0 },
        }}
        dangerouslySetInnerHTML={{
          __html: katex.renderToString(clean, {
            throwOnError: true,
            displayMode: true,
          }),
        }}
      />
    );
  } catch (error) {
    console.error("QuickSnap KaTeX block render error:", error, clean);

    return (
      <Typography
        variant="body2"
        color="error"
        sx={{ whiteSpace: "pre-wrap", fontFamily: "monospace" }}
      >
        {clean}
      </Typography>
    );
  }
};
const parseSuggestedCoordinate = (value) => {
  const text = String(value || "").trim();
  const match = text.match(/\(?\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\)?/);

  if (!match) {
    return { x: "", y: "" };
  }

  return {
    x: match[1],
    y: match[2],
  };
};

const initializeCoordinateValues = (coordinateInput) => {
  const allPoints = getAllCoordinatePoints(coordinateInput);
  const initial = {};

  allPoints.forEach((point) => {
    const suggested = coordinateInput?.suggested_coordinates?.[point] || "";
    initial[point] = parseSuggestedCoordinate(suggested);
  });

  setCoordinateValues(initial);
};

const handleCoordinateChange = (point, axis, value) => {
  setCoordinateValues((prev) => ({
    ...prev,
    [point]: {
      ...prev[point],
      [axis]: value,
    },
  }));
};

const parseCoordinateInput = (value) => {
  const text = String(value || "").trim();

  if (!text) return null;

  if (text.includes("/")) {
    const [num, den] = text.split("/").map(Number);

    if (!Number.isFinite(num) || !Number.isFinite(den) || den === 0) {
      return null;
    }

    return num / den;
  }

  const number = Number(text);
  return Number.isFinite(number) ? number : null;
};
const buildConfirmedCoordinates = () => {
  const coordinateInput = result?.coordinate_input;
  const allPoints = getAllCoordinatePoints(coordinateInput);
  const confirmed = {};

  for (const point of allPoints) {
    const x = coordinateValues?.[point]?.x;
    const y = coordinateValues?.[point]?.y;

    if (x === "" || y === "" || x === undefined || y === undefined) {
      alert(`Please enter both x and y for point ${point}`);
      return null;
    }

    const parsedX = parseCoordinateInput(x);
    const parsedY = parseCoordinateInput(y);

    if (parsedX === null || parsedY === null) {
      alert(`Please enter valid coordinates for point ${point}`);
      return null;
    }

    confirmed[point] = {
      x: parsedX,
      y: parsedY,
    };
  }

  return confirmed;
};
  const handleSubmit = async (options = {}) => {
    const confirmedCoordinates = options.confirmedCoordinates || null;
    const pendingInterpreted = options.interpreted || null;
    const pendingCoordinateInput = options.coordinateInput || null;

    if (mode === "solve_question" && !selectedFile) return;

    if (mode === "check_my_work" && (!selectedFile || !selectedAnswerFile)) {
      alert(text.uploadBoth);
      return;
    }

    if (isProcessing) return;

    setIsProcessing(true);
    setIsQuestionOpen(false);
    setResult(null);

    try {
      const getBase64 = (file) =>
        new Promise((resolve, reject) => {
          const reader = new FileReader();
          reader.readAsDataURL(file);
          reader.onload = () => resolve(reader.result);
          reader.onerror = (error) => reject(error);
        });

      const base64Data = await getBase64(selectedFile);

      let base64AnswerData = null;
      if (mode === "check_my_work") {
        base64AnswerData = await getBase64(selectedAnswerFile);
      }

      let endpoint = "";
      let payload = {};

      if (mode === "solve_question") {
        endpoint = `${process.env.REACT_APP_API_BASE_URL}/api/ai/solve`;

        payload = {
          image: base64Data,
          language: language,
        };

        if (confirmedCoordinates) {
          payload.confirmed_coordinates = confirmedCoordinates;
        }

        if (pendingInterpreted) {
          payload.interpreted = pendingInterpreted;
        }

        if (pendingCoordinateInput) {
          payload.coordinate_input = pendingCoordinateInput;
        }
      } else if (mode === "check_my_work") {
        endpoint = `${process.env.REACT_APP_API_BASE_URL}/api/ai/grade-new`;

        payload = {
          question_image: base64Data,
          student_image: base64AnswerData,
          language: language,
        };

        if (confirmedCoordinates) {
          payload.confirmed_coordinates = confirmedCoordinates;
        }

        if (pendingInterpreted) {
          payload.interpreted = pendingInterpreted;
        }

        if (pendingCoordinateInput) {
          payload.coordinate_input = pendingCoordinateInput;
        }
      }

      const response = await apiFetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      const apiData = await response.json();

      if (!response.ok || !apiData.success) {
        throw new Error(apiData.message || "AI processing failed");
      }

      let normalized = {};
      if (apiData.result?.needs_user_coordinates) {
          const coordinateInput = apiData.result.coordinate_input || {};

          initializeCoordinateValues(coordinateInput);

          normalized = {
            mode: "solve_question",
            result_type: "coordinate_confirmation",
            status: "needs_user_coordinates",
            needs_user_coordinates: true,
            question_text:
              apiData.result.question_text ||
              "Transformation question needs coordinate confirmation",
            reason:
              apiData.result.reason ||
              "Exact coordinates are required from the Cartesian plane.",
            coordinate_input: coordinateInput,
            pending_interpreted: apiData.result.pending_interpreted || null,
            steps: [],
            final_answer: "",
          };

          setResult(normalized);

          await logQuickSnapEvent({
            modeUsed: mode,
            resultType: normalized.result_type,
            followUpChatOpened: false,
          });

          return;
        }
      if (mode === "solve_question") {
        const rawFinalAnswer =
          apiData.result.final_answers || apiData.result.final_answer;

        let extractedFinalAnswer = "";

        if (typeof rawFinalAnswer === "object" && rawFinalAnswer !== null) {
          extractedFinalAnswer = rawFinalAnswer;
        } else {
          extractedFinalAnswer = String(rawFinalAnswer || "");
        }

        normalized = {
          mode: "solve_question",
          result_type: "solution",
          status: "success",
          question_text: apiData.result.question_text || "AI Solution Generated",
          steps: apiData.result.steps || [],
          final_answer: extractedFinalAnswer,
        };
      } else if (mode === "check_my_work") {
        const gradingResult = apiData.result || {};

        const detectedQuestionText =
          gradingResult.question_text ||
          gradingResult.detected_question ||
          gradingResult.extracted_question ||
          gradingResult.question_summary ||
          gradingResult.question ||
          gradingResult.problem_text ||
          gradingResult.correctness_summary?.question_text ||
          "AI Grading Report";

        normalized = {
          mode: "check_my_work",
          result_type: "work_check",
          status: "success",
          question_text: detectedQuestionText,
          score: gradingResult.score,
          max_score: gradingResult.max_score,
          correctness_summary: gradingResult,
        };
      }

      setResult(normalized);

      await logQuickSnapEvent({
        modeUsed: mode,
        resultType: normalized.result_type,
        followUpChatOpened: false,
      });
    } catch (error) {
      console.error(error);

      setResult({
        mode,
        status: "error",
        message: error.message,
      });
    } finally {
      setIsProcessing(false);
    }
  };
  
  const handleContinueInChat = async () => {
    if (!result || result.status === "error") return;

    const quickSnapContext = {
      source: "quick_snap",
      mode: result.mode,
      result_type: result.result_type,
      question_text: result.question_text || "",
      steps: result.steps || [],
      final_answer: result.final_answer || "",
      score: result.score ?? null,
      max_score: result.max_score ?? null,
      correctness_summary: result.correctness_summary || null,
      created_at: new Date().toISOString(),
    };

    window.dispatchEvent(
      new CustomEvent("openQuickSnapFollowUpChat", {
        detail: quickSnapContext,
      })
    );

    if (result?.result_type) {
      await logQuickSnapEvent({
        modeUsed: mode,
        resultType: result.result_type,
        followUpChatOpened: true,
      });
    }
  };

  const renderSolveStep = (step, index) => {
    // Safely extract text and math, ensuring they exist
    const baseTitle = step.step || `Step ${index + 1}`;
    
    // 2. Next, use that baseTitle to construct the final stepTitle
    const stepTitle = step.subpart 
      ? `Part (${step.subpart}) - ${baseTitle}` 
      : baseTitle;
    let stepText = cleanLatexText(step.text || "");
    
    // Handle cases where math might be an object, string, or empty
    let stepMath = "";
    if (typeof step.math === "string") {
      stepMath = step.math;
    } else if (step.math && typeof step.math === "object") {
      // Fallback just in case the LLM hallucinates a nested object
      stepMath = step.math.display_math || JSON.stringify(step.math);
    }
    stepMath = cleanLatexText(stepMath);
    stepMath = stepMath.replace(/\\\(/g, "").replace(/\\\)/g, "");
    const mathLooksLikeSentence =
      /\b(If|then|Premise|Conclusion|because|opposite|therefore|namely)\b/i.test(stepMath);

    if (mathLooksLikeSentence) {
      stepText = [stepText, stepMath].filter(Boolean).join("\n");
      stepMath = "";
    }
    return (
      <Box
        key={index}
        sx={{
          display: "flex",
          alignItems: "flex-start",
          gap: { xs: 1.5, sm: 2 },
          mb: 3,
          width: "100%",
          minWidth: 0,
        }}
      >
        {/* The Number Bubble */}
        <Box
          sx={{
            width: 32,
            height: 32,
            borderRadius: "50%",
            bgcolor: "#EEF2FF",
            color: "#3855c0",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontWeight: "bold",
            fontSize: "14px",
            flexShrink: 0,
            mt: 0.5, // Slight top margin to align with text
          }}
        >
          {index + 1}
        </Box>

        {/* The Content Area */}
        <Box
          sx={{
            flex: 1,
            minWidth: 0,
            maxWidth: "100%",
            overflow: "hidden",
          }}
        >
          <Typography
            component="div"
            variant="subtitle1"
            fontWeight="bold"
            sx={{
              mb: 0.5,
              color: "#111827",
              maxWidth: "100%",
              overflowWrap: "anywhere",
              wordBreak: "break-word",
              lineHeight: 1.35,
            }}
          >
            {renderInlineMath(stepTitle)}
          </Typography>

          {/* Render the Explanation Text (if any exists) */}
          {stepText && (
            <Typography
              component="div" // ✨ ADD THIS LINE to prevent HTML nesting warnings
              variant="body1"
              sx={{
                color: "#4B5563",
                whiteSpace: "pre-wrap", 
                mb: stepMath ? 1.5 : 0, 
                lineHeight: 1.6
              }}
            >
              {renderInlineMath(stepText)}
            </Typography>
          )}

          {/* Render the Math Equation Box (if any exists) */}
          {/* Render the Math Equation Box using KaTeX */}
          {stepMath && (
            renderMathBlock(stepMath)
          )}
        </Box>
      </Box>
    );
  };

  const renderDropzone = (type) => {
    const isQuestion = type === "question";
    const currentImage = isQuestion ? selectedImage : selectedAnswerImage;
    const inputRef = isQuestion ? fileInputRef : answerFileInputRef;
    const title = isQuestion ? text.uploadQuestion : text.uploadWork;
    const subtitle = isQuestion ? text.questionSubtitle : text.workSubtitle;

    const isSolveMode = mode === "solve_question";

    return (
      <Paper
        elevation={0}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={(e) => handleDrop(e, type)}
        sx={{
          p: isSolveMode && currentImage ? 1 : 3,
          borderRadius: "20px",
          border: "2px dashed",
          borderColor: isDragging ? "#3855c0" : "#E5E7EB",
          backgroundColor: isDragging ? "#F0F4FF" : "#ffffff",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          textAlign: "center",
          height: "100%",
          flex: 1,
          transition: "all 0.2s ease",
        }}
      >
        {!currentImage ? (
          <>
            <Box sx={{ p: 2, bgcolor: "#F3F4F6", borderRadius: "50%", mb: 2 }}>
              <CloudUploadOutlinedIcon sx={{ fontSize: 32, color: "#6B7280" }} />
            </Box>
            <Typography variant="h6" fontWeight="bold" mb={1}>{title}</Typography>
            <Typography variant="body2" color="textSecondary" mb={3}>{subtitle}</Typography>

            <Box sx={{ display: "flex", gap: 1, justifyContent: "center" }}>
              <Button
                variant="contained"
                onClick={() => inputRef.current.click()}
                sx={{ bgcolor: "#3855c0", borderRadius: "10px", textTransform: "none", fontWeight: "bold" }}
              >
                {text.browse}
              </Button>
            </Box>
            <input
              type="file"
              hidden
              ref={inputRef}
              accept="image/*"
              onChange={(e) => handleFileChange(e, type)}
            />
          </>
        ) : (
          <>
            <Box
              sx={{
                width: "100%",
                height: isSolveMode ? "auto" : 250,
                // ✨ DECREASED max height from 600 to 400
                maxHeight: isSolveMode ? 400 : "none", 
                borderRadius: "12px",
                mb: 2,
                bgcolor: "#F9FAFB",
                border: "1px solid #E5E7EB",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                overflow: "hidden",
                p: isSolveMode ? 0 : 1, 
              }}
            >
              <Box
                component="img"
                src={currentImage}
                alt={title}
                sx={{
                  maxWidth: "100%",
                  // ✨ DECREASED max height from 600px to 400px
                  maxHeight: isSolveMode ? "400px" : "100%",
                  width: isSolveMode ? "100%" : "auto", 
                  objectFit: "contain",
                  borderRadius: "8px",
                  display: "block"
                }}
              />
            </Box>
            <Button
              variant="outlined"
              color="error"
              fullWidth
              startIcon={<DeleteOutlineIcon />}
              onClick={() => clearImage(type)}
              disabled={isProcessing}
              sx={{ borderRadius: "10px", textTransform: "none", fontWeight: "bold" }}
            >
              {text.remove}
            </Button>
          </>
        )}
      </Paper>
    );
  };

  // 2. Update renderUploadCard to handle the layouts based on the mode
  const renderUploadCard = () => (
    <Box sx={{ width: "100%", display: "flex", flexDirection: "column", gap: 3 }}>
      
      {/* Dynamic Layout: 1 box for solving, 2 boxes for checking */}
      <Box sx={{ 
        display: "flex", 
        flexDirection: { xs: "column", md: mode === "check_my_work" ? "row" : "column" }, 
        gap: 3,
        justifyContent: "center"
      }}>
        {renderDropzone("question")}
        {mode === "check_my_work" && renderDropzone("answer")}
      </Box>

      {/* Main Submit Button for the entire form */}
      {((mode === "solve_question" && selectedImage) || 
        (mode === "check_my_work" && selectedImage && selectedAnswerImage)) && (
        <Button
          variant="contained"
          fullWidth
          size="large"
          startIcon={
            isProcessing ? <CircularProgress size={20} color="inherit" /> : 
            (mode === "solve_question" ? <AutoFixHighIcon /> : <FactCheckOutlinedIcon />)
          }
          onClick={() => handleSubmit()}
          disabled={isProcessing}
          sx={{
            bgcolor: "#1ac089",
            "&:hover": { bgcolor: "#159c6f" },
            borderRadius: "10px",
            textTransform: "none",
            fontWeight: "bold",
            py: 1.5,
            fontSize: "1.1rem"
          }}
        >
          {isProcessing
            ? text.processing
            : mode === "solve_question"
            ? text.solveNow
            : text.checkNow}
        </Button>
      )}
    </Box>
  );
const renderCoordinateConfirmationPanel = () => {
  const coordinateInput = result?.coordinate_input || {};
  const shapes = coordinateInput.shapes || [];

  const objectPoints = coordinateInput.object_points || [];
  const imagePoints = coordinateInput.image_points || [];
  const otherPoints = coordinateInput.other_required_points || [];

  const renderCoordinateRows = (points) => {
    return points.map((point) => (
      <Box
        key={point}
        sx={{
          display: "grid",
          gridTemplateColumns: { xs: "1fr", sm: "90px 1fr 1fr" },
          gap: 1.5,
          alignItems: "center",
          mb: 1.5,
        }}
      >
        <Typography fontWeight="bold" sx={{ color: "#111827" }}>
          {point}
        </Typography>

        <TextField
          size="small"
          label="x"
          type="text"
          placeholder="e.g. 7.5 or 15/2"
          value={coordinateValues?.[point]?.x || ""}
          onChange={(e) => handleCoordinateChange(point, "x", e.target.value)}
        />

        <TextField
          size="small"
          label="y"
          type="text"
          placeholder="e.g. -1 or -3/2"
          value={coordinateValues?.[point]?.y || ""}
          onChange={(e) => handleCoordinateChange(point, "y", e.target.value)}
        />
      </Box>
    ));
  };

  const handleConfirmAndSolve = () => {
    const confirmedCoordinates = buildConfirmedCoordinates();

    if (!confirmedCoordinates) return;

    handleSubmit({
      confirmedCoordinates,
      interpreted: result?.pending_interpreted || null,
      coordinateInput: result?.coordinate_input || null,
    });
  };

  return (
    <Box>
      <Typography variant="h6" fontWeight="bold" sx={{ mb: 1, color: "#111827" }}>
        {text.confirmCoordinates}
      </Typography>

      <Typography variant="body2" sx={{ color: "#6B7280", mb: 3 }}>
        {result?.reason ||
          text.coordinateHelp}
      </Typography>

      <Paper
        elevation={0}
        sx={{
          p: 3,
          borderRadius: "16px",
          border: "1px solid #E5E7EB",
          bgcolor: "#F9FAFB",
        }}
      >
        {shapes.length > 0 ? (
          <>
            {shapes.map((shape, index) => (
              <Box key={shape.shape_label || index}>
                <Typography fontWeight="bold" sx={{ mb: 0.5, color: "#3855c0" }}>
                  {shape.shape_label || `Shape ${index + 1}`}
                </Typography>

                <Typography variant="caption" sx={{ display: "block", color: "#6B7280", mb: 1.5 }}>
                  Role: {shape.role_guess || "unknown"}
                </Typography>

                {renderCoordinateRows(shape.point_labels || [])}

                {index < shapes.length - 1 && <Divider sx={{ my: 2 }} />}
              </Box>
            ))}
          </>
        ) : (
          <>
            {objectPoints.length > 0 && (
              <>
                <Typography fontWeight="bold" sx={{ mb: 1.5, color: "#3855c0" }}>
                  Object Coordinates
                </Typography>
                {renderCoordinateRows(objectPoints)}
                <Divider sx={{ my: 2 }} />
              </>
            )}

            {imagePoints.length > 0 && (
              <>
                <Typography fontWeight="bold" sx={{ mb: 1.5, color: "#3855c0" }}>
                  Image Coordinates
                </Typography>
                {renderCoordinateRows(imagePoints)}
                <Divider sx={{ my: 2 }} />
              </>
            )}

            {otherPoints.length > 0 && (
              <>
                <Typography fontWeight="bold" sx={{ mb: 1.5, color: "#3855c0" }}>
                  Other Required Coordinates
                </Typography>
                {renderCoordinateRows(otherPoints)}
              </>
            )}
          </>
        )}

        <Button
          fullWidth
          variant="contained"
          onClick={handleConfirmAndSolve}
          disabled={isProcessing}
          sx={{ mt: 2 }}
        >
          {text.confirmSolve}
        </Button>
      </Paper>
    </Box>
  );
};
  const renderResultPanel = () => (
    <Paper
      sx={{
        p: 4,
        borderRadius: "20px",
        height: "100%",
        boxShadow: "0 10px 30px rgba(0,0,0,0.05)",
        display: "flex",
        flexDirection: "column",
      }}
    >
      {result.status === "error" ? (
        <Box
          sx={{
            mb: 3,
            p: 2,
            borderRadius: "12px",
            backgroundColor: "#FEF2F2",
            border: "1px solid #FECACA",
          }}
        >
          <Typography fontWeight="bold" sx={{ color: "#B91C1C", mb: 0.5 }}>
            {t("quicksnap_error_title")}
          </Typography>
          <Typography variant="body2" sx={{ color: "#7F1D1D" }}>
            {result.message}
          </Typography>
        </Box>
      ) : (
        <>
          <Box
            sx={{
              mb: 2.5,
              display: "flex",
              alignItems: "center",
              gap: 1.5,
              p: 1.5,
              bgcolor: "#f0eeee",
              border: "1px solid #E5E7EB",
              borderRadius: "12px",
            }}
          >
            <FunctionsIcon sx={{ color: "#3855c0", fontSize: 22, flexShrink: 0 }} />

            <Box sx={{ minWidth: 0 }}>
              <Typography
                variant="caption"
                fontWeight="bold"
                sx={{
                  color: "#6B7280",
                  display: "block",
                  lineHeight: 1.2,
                  mb: 0.4,
                  textTransform: "uppercase",
                  letterSpacing: "0.4px",
                }}
              >
                {t("quicksnap_detected_question")}
              </Typography>

              <Typography
                variant="body1"
                fontWeight="600"
                sx={{
                  color: "#111827",
                  lineHeight: 1.35,
                  wordBreak: "break-word",
                }}
              >
                {result.question_text || t("quicksnap_no_result")}
              </Typography>
            </Box>
          </Box>

          <Divider sx={{ mb: 3 }} />

          {result.mode === "solve_question" ? (
          <>
            {result.needs_user_coordinates ? (
              renderCoordinateConfirmationPanel()
            ) : (
              <>
                <Typography variant="h6" fontWeight="bold" mb={2} color="#111827">
                  {t("quicksnap_solution_title")}
                </Typography>

                {result.steps?.map((step, index) => renderSolveStep(step, index))}

                {result.final_answer && (
                  <Box
                    sx={{
                      mt: 4,
                      p: 2.5,
                      borderRadius: "16px",
                      backgroundColor: "#EAFBF3",
                      border: "1px solid #A7E7C9",
                      textAlign: "center",
                      ml: { xs: 0, sm: "48px" },
                      width: { xs: "100%", sm: "calc(100% - 48px)" },
                      boxSizing: "border-box",
                    }}
                  >
                    <Typography
                      variant="subtitle1"
                      fontWeight="bold"
                      sx={{
                        color: "#0F766E",
                        mb: 1,
                        letterSpacing: "0.6px",
                        fontSize: {
                          xs: "0.95rem",
                          sm: "1.05rem",
                          md: "1.15rem",
                        },
                      }}
                    >
                      {t("quicksnap_final_answer")}
                    </Typography>

                    <Box
                      sx={{
                        color: "#065F46",
                        whiteSpace: "pre-wrap",
                      }}
                    >
                      {formatFinalAnswer(result.final_answer)}
                    </Box>
                  </Box>
                )}
              </>
            )}
          </>
          ) : (
            <>
              <Typography variant="h6" fontWeight="bold" mb={2} color="#111827">
                {t("quicksnap_checking_title")}
              </Typography>

              <Box
                sx={{
                  mb: 3,
                  display: "flex",
                  alignItems: "center",
                  gap: 1.5,
                  flexWrap: "wrap",
                }}
              >
                <Typography
                  fontWeight="bold"
                  sx={{ color: "#111827" }}
                >
                  {t("quicksnap_score")}:
                </Typography>

                <Box
                  sx={{
                    display: "inline-flex",
                    alignItems: "center",
                    px: 2,
                    py: 0.9,
                    borderRadius: "12px",
                    bgcolor: "#ECFDF5",
                    border: "1px solid #A7F3D0",
                  }}
                >
                  <Typography
                    variant="h6"
                    fontWeight="bold"
                    sx={{ color: "#065F46", lineHeight: 1 }}
                  >
                    {result.score ?? "-"}
                    {result.max_score ? ` / ${result.max_score}` : ""}
                  </Typography>
                </Box>
              </Box>

              <Box sx={{ mt: 3, mb: 1 }}>
  <Typography variant="h6" fontWeight="bold" sx={{ mb: 2, color: "#111827" }}>
    {text.stepBreakdown}
  </Typography>

  {/* Check if correctness_summary contains our structured JSON array */}
  {Array.isArray(result?.correctness_summary?.stepwise_evaluation) ? (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      {result.correctness_summary.stepwise_evaluation.map((stepData, index) => {
        // Determine color scheme dynamically based on marks
        const isFullMarks = stepData.marks_awarded === stepData.max_marks;
        const isZeroMarks = stepData.marks_awarded === 0;
        
        // Default to yellow for partial marks
        let bgColor = "#FFFBEB"; 
        let borderColor = "#FDE68A";
        let iconColor = "#D97706";
        let StatusIcon = ErrorOutlineIcon;

        // The Tick (Checkmark) for correct answers
        if (isFullMarks) {
          bgColor = "#ECFDF5"; 
          borderColor = "#A7F3D0";
          iconColor = "#059669";
          StatusIcon = CheckCircleOutlineIcon; 
        } 
        // The Cross for incorrect answers
        else if (isZeroMarks) {
          bgColor = "#FEF2F2"; 
          borderColor = "#FECACA";
          iconColor = "#DC2626";
          StatusIcon = HighlightOffIcon; 
        }

        return (
          <Paper
            key={index}
            elevation={0}
            sx={{
              p: 2,
              borderRadius: "12px",
              border: "1px solid",
              borderColor: borderColor,
              bgcolor: bgColor,
            }}
          >
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1.5 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <StatusIcon sx={{ color: iconColor, fontSize: 22 }} />
                <Typography fontWeight="bold" sx={{ color: "#111827", fontSize: "1.05rem" }}>
                  {stepData.step}
                </Typography>
              </Box>
              
              <Chip
                label={`${stepData.marks_awarded} / ${stepData.max_marks} marks`}
                size="small"
                sx={{
                  bgcolor: "rgba(255, 255, 255, 0.7)",
                  fontWeight: "bold",
                  color: iconColor,
                  border: "1px solid",
                  borderColor: borderColor
                }}
              />
            </Box>
            
            {/* ✨ The "What the Student Wrote" Box */}
            <Box 
              sx={{ 
                ml: 3.8, // Indent past the icon
                mb: 1.5, 
                p: 1.5, 
                bgcolor: 'rgba(255, 255, 255, 0.6)', 
                borderRadius: '8px', 
                border: '1px dashed', 
                borderColor: borderColor 
              }}
            >
              <Typography 
                variant="caption" 
                fontWeight="bold" 
                sx={{ 
                  color: iconColor, 
                  display: 'block', 
                  mb: 0.5, 
                  textTransform: 'uppercase', 
                  letterSpacing: '0.5px' 
                }}
              >
                {text.studentWrote}
              </Typography>
              <Typography 
                variant="body2" 
                sx={{ 
                  fontFamily: 'monospace', 
                  color: '#111827', 
                  fontSize: '0.95rem' 
                }}
              >
                <Typography component="div" variant="body2" sx={{ fontFamily: 'monospace', color: '#111827', fontSize: '0.95rem' }}>
                  {renderInlineMath(stepData.student_wrote || stepData.reason)}
                </Typography>
              </Typography>
            </Box>

            {/* ✨ The Reason Section */}
            <Typography 
              variant="body2" 
              sx={{ 
                color: "#4B5563", 
                pl: 3.8, 
                lineHeight: 1.6 
              }}
            >
              <Box component="span" fontWeight="bold" sx={{ color: "#374151", mr: 0.5 }}>{text.reason}</Box>
              {renderInlineMath(stepData.reason)}
            </Typography>
          </Paper>
        );
      })}
    </Box>
  ) : (
    // ✨ FALLBACK UI: If the AI failed to generate the JSON array, show this instead of crashing
    <Paper
      elevation={0}
      sx={{
        p: 2,
        borderRadius: "12px",
        bgcolor: "#F9FAFB",
        border: "1px solid #E5E7EB",
      }}
    >
      <Typography sx={{ color: "#4B5563", whiteSpace: "pre-wrap" }}>
        {typeof result?.correctness_summary === 'string' 
          ? result.correctness_summary 
          : result?.message || text.noSummary}
      </Typography>
    </Paper>
  )}
</Box>
            </>
          )}

          <Button
            variant="outlined"
            startIcon={<ChatOutlinedIcon />}
            onClick={handleContinueInChat}
            sx={{
              mt: 4,
              borderRadius: "10px",
              textTransform: "none",
              fontWeight: "bold",
              alignSelf: "flex-start",
            }}
          >
            {t("quicksnap_continue_chat")}
          </Button>
          <Box sx={{ display: "flex", justifyContent: "center", mt: 2.5 }}>
            <DisclaimerText sx={{ mt: 0 }} />
          </Box>
        </>
      )}
    </Paper>
  );

  return (
    <Box>
      <Box mb={4} textAlign="center">
        <Typography variant="h4" fontWeight="bold" sx={{ color: "#111827", mb: 1 }}>
          {t("quicksnap_title")}
        </Typography>
        <Typography color="textSecondary" variant="subtitle1">
          {t("quicksnap_subtitle")}
        </Typography>
      </Box>

      <Box sx={{ display: "flex", justifyContent: "center", mb: 3 }}>
        <Tabs
          value={mode}
          onChange={handleModeChange}
          TabIndicatorProps={{
            style: {
              height: "100%",
              borderRadius: "10px",
              backgroundColor: "#EEF2FF",
              border: "1px solid #3855c0",
              zIndex: 0,
            },
          }}
          sx={{
            minHeight: "40px",
            backgroundColor: "#F3F4F6",
            borderRadius: "12px",
            padding: "4px",
            "& .MuiTabs-indicator": { zIndex: 0 },
          }}
        >
          <Tab
            disableRipple
            value="solve_question"
            label={t("quicksnap_tab_solve")}
            sx={{
              textTransform: "none",
              fontWeight: "bold",
              minHeight: "34px",
              borderRadius: "8px",
              zIndex: 1,
              px: 3,
              color: mode === "solve_question" ? "#3855c0" : "#6B7280",
              "&.Mui-selected": { color: "#3855c0" },
            }}
          />
          <Tab
            disableRipple
            value="check_my_work"
            label={t("quicksnap_tab_check")}
            sx={{
              textTransform: "none",
              fontWeight: "bold",
              minHeight: "34px",
              borderRadius: "8px",
              zIndex: 1,
              px: 3,
              color: mode === "check_my_work" ? "#3855c0" : "#6B7280",
              "&.Mui-selected": { color: "#3855c0" },
            }}
          />
        </Tabs>
      </Box>

      <Box sx={{ width: "100%", maxWidth: "1400px", mx: "auto", px: 2 }}>
        {!result ? (
          <Box sx={{ display: "flex", justifyContent: "center" }}>
            <Box sx={{ width: "100%", maxWidth: 720 }}>
              {renderUploadCard()}
            </Box>
          </Box>
        ) : (
          <Box
            sx={{
              display: "flex",
              flexDirection: "column",
              gap: 3,
              alignItems: "center",
            }}
          >
            {/* ✨ CONTROLS ROW (Stretches Full Width) ✨ */}
            <Box 
              sx={{ 
                width: "100%", 
                // REMOVED maxWidth here!
                display: "flex", 
                justifyContent: "space-between", 
                alignItems: "center",
                px: 1 
              }}
            >
              <Button
                onClick={() => setIsQuestionOpen(!isQuestionOpen)}
                startIcon={isQuestionOpen ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                sx={{ 
                  color: "#6B7280", 
                  fontWeight: "bold", 
                  textTransform: "none",
                  "&:hover": { bgcolor: "#F3F4F6" }
                }}
              >
                {isQuestionOpen ? text.hideQuestion : text.viewQuestion}
              </Button>

              <Button
                variant="outlined"
                color="error"
                onClick={() => clearImage("all")}
                sx={{ 
                  borderRadius: "8px", 
                  textTransform: "none", 
                  fontWeight: "bold" 
                }}
              >
                {text.scanNew}
              </Button>
            </Box>

            {/* ✨ COLLAPSIBLE QUESTION BOX ✨ */}
            <Box sx={{ width: "100%", display: "flex", justifyContent: "center" }}>
              <Collapse in={isQuestionOpen} sx={{ width: "100%" }}>
                <Box sx={{ pb: 1, display: "flex", justifyContent: "center" }}>
                  {/* Keep the image card reasonably sized so the photo isn't stretched */}
                  <Box sx={{ width: "100%", maxWidth: "800px" }}>
                    {renderUploadCard()}
                  </Box>
                </Box>
              </Collapse>
            </Box>

            {/* ✨ MAXIMUM WIDTH ANSWER BOX ✨ */}
            <Box sx={{ width: "100%" }}> 
              {/* REMOVED maxWidth here so it expands completely! */}
              {renderResultPanel()}
            </Box>
          </Box>
        )}
      </Box>
    </Box>
  );
};

export default QuickSnapPage;