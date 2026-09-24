import React, { useState, useRef, useEffect } from "react";
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
import Confetti from "react-confetti";
import { useWindowSize } from "react-use";
import { logUserActivity } from "../../utils/logger";
import { useLanguage } from "../../context/LanguageContext";
import { apiFetch } from "../../utils/apiFetch";
import 'katex/dist/katex.min.css';
import katex from 'katex';
import DisclaimerText from "../../components/DisclaimerText";

// Icons
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import CheckCircleOutlineIcon from "@mui/icons-material/CheckCircleOutline";
import HighlightOffIcon from "@mui/icons-material/HighlightOff";
import LocalFireDepartmentIcon from "@mui/icons-material/LocalFireDepartment";
import LightbulbOutlinedIcon from "@mui/icons-material/LightbulbOutlined";
import AutoGraphIcon from "@mui/icons-material/AutoGraph";
import CloudUploadOutlinedIcon from "@mui/icons-material/CloudUploadOutlined";
import PhotoCameraOutlinedIcon from "@mui/icons-material/PhotoCameraOutlined";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import DocumentScannerIcon from "@mui/icons-material/DocumentScanner";

const syllabusData = {
  "Form 4": [
    { id: 1, name: "Quadratic Functions and Equations in One Variable" },
    { id: 2, name: "Number Bases" },
    { id: 3, name: "Logical Reasoning" },
    { id: 4, name: "Operations on Sets" },
    { id: 5, name: "Network in Graph Theory" },
    { id: 6, name: "Linear Inequalities in Two Variables" },
    { id: 7, name: "Graphs of Motion" },
    { id: 8, name: "Measures of Dispersion for Ungrouped Data" },
    { id: 9, name: "Probability of Combined Events" },
    { id: 10, name: "Consumer Mathematics: Financial Management" }
  ],
  "Form 5": [
    { id: 1, name: "Variation" },
    { id: 2, name: "Matrices" },
    { id: 3, name: "Consumer Mathematics: Insurance" },
    { id: 4, name: "Consumer Mathematics: Taxation" },
    { id: 5, name: "Congruency, Enlargement and Combined Transformations" },
    { id: 6, name: "Ratios and Graphs of Trigonometric Functions" },
    { id: 7, name: "Measures of Dispersion for Grouped Data" },
    { id: 8, name: "Mathematical Modeling" }
  ]
};

const PracticePageKertas2 = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { width, height } = useWindowSize();
  const { language } = useLanguage();

  const { form, chapter_id, topic } = location.state || {
    form: "Form 4",
    chapter_id: 1,
    topic: "Subjective Practice",
  };

  const user = JSON.parse(localStorage.getItem("user")) || {};
  const isEnglish = language !== "bm";

  const text = {
    paper: isEnglish ? "Paper 2 (Subjective)" : "Kertas 2 (Subjektif)",
    submitBtn: isEnglish ? "Submit for Marking" : "Hantar untuk Disemak",
    nextBtn: isEnglish ? "Next Question" : "Soalan Seterusnya",
    correct: isEnglish ? "Excellent Work!" : "Kerja yang Cemerlang!",
    wrong: isEnglish ? "Needs Improvement" : "Perlu Diperbaiki",
    partial: isEnglish ? "Good Attempt!" : "Cubaan yang Baik!",
    zero: isEnglish ? "Needs More Practice" : "Perlu Lebih Latihan",
    explanation: isEnglish ? "AI Marking Feedback" : "Maklum Balas Semakan AI",
    streak: isEnglish ? "Streak" : "Deretan",
    uploadDesc: isEnglish
      ? "Write your solution on paper, snap a photo, and upload it here for AI marking."
      : "Tulis jawapan anda di atas kertas, ambil gambar, dan muat naik di sini untuk disemak oleh AI.",
    dragDrop: isEnglish
      ? "Drag & drop your answer sheet here"
      : "Tarik & letak kertas jawapan anda di sini",
    browse: isEnglish ? "Browse Files" : "Pilih Fail",
    camera: isEnglish ? "Take Photo" : "Ambil Gambar",
    remove: isEnglish ? "Remove" : "Padam",
    yourAnswerSheet: isEnglish ? "Your Answer Sheet:" : "Kertas Jawapan Anda:",
    aiMarking: isEnglish ? "AI is Marking..." : "AI Sedang Menyemak...",
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
    backToDash: isEnglish ? "Back to Menu" : "Kembali ke Menu",
    noQuestions: isEnglish
      ? "Congratulations! You have completed all the questions. Stay Tuned for More !!"
      : "Tahniah! Anda telah menyelesaikan semua soalan. Tunggu yang lebih baik !!",
    goBack: isEnglish ? "Go Back" : "Kembali",
    showDbAnswerBtn: isEnglish ? "Show Answer" : "Tunjuk Jawapan",
  };

  const stripRawPartPrefix = (value) => {
    return String(value || "")
      .replace(/^part\s*\([a-z]\)\s*[-:]\s*/i, "")
      .replace(/^\([a-z]\)\s*[-:]\s*/i, "")
      .trim();
  };

  const getDisplayLabelByStepIndex = (idx) => {
    const q = currentQuestions?.[idx];

    return (
      q?.display_subpart_label ||
      `(${String.fromCharCode(97 + idx)})`
    );
  };
  
  const getAlignedStepHeader = (step, idx) => {
    const title = stripRawPartPrefix(step?.step || `Step ${idx + 1}`);

    const label =
      step?.display_subpart_label ||
      getDisplayLabelByStepIndex(idx);

    return label ? `Part ${label} - ${title}` : title;
  };
  const getStepHeader = (step, idx) => {
    const title = step?.step || `Step ${idx + 1}`;
    const label = step?.display_subpart_label;

    return label ? `Part ${label} - ${title}` : title;
  };
  const renderInlineMath = (text) => {
    if (!text) return null;
    
    // This regex catches $...$, \(...\), \begin{...}...\end{...}, AND $$...$$
    const parts = text.split(/(\$\$[\s\S]*?\$\$|\$[^$]+\$|\\\([\s\S]*?\\\)|\\begin\{[^}]+\}[\s\S]*?\\end\{[^}]+\})/g); 
    
    return parts.map((part, index) => {
      // 1. Handle inline math wrapped in $$ ... $$
      if (part.startsWith('$$') && part.endsWith('$$')) {
        const mathContent = part.slice(2, -2);
        return <Box component="span" key={index} sx={{ color: "#2563EB", mx: 0.5 }} dangerouslySetInnerHTML={{ __html: katex.renderToString(mathContent, { throwOnError: false, displayMode: false }) }} />;
      }
      // 2. Handle standard inline math wrapped in $ ... $
      else if (part.startsWith('$') && part.endsWith('$')) {
        const mathContent = part.slice(1, -1);
        return <Box component="span" key={index} sx={{ color: "#2563EB", mx: 0.5 }} dangerouslySetInnerHTML={{ __html: katex.renderToString(mathContent, { throwOnError: false, displayMode: false }) }} />;
      } 
      // 3. Handle inline math wrapped in \( ... \)
      else if (part.startsWith('\\(') && part.endsWith('\\)')) {
        const mathContent = part.slice(2, -2);
        return <Box component="span" key={index} sx={{ color: "#2563EB", mx: 0.5 }} dangerouslySetInnerHTML={{ __html: katex.renderToString(mathContent, { throwOnError: false, displayMode: false }) }} />;
      }
      // 4. Handle matrices and block math
      else if (part.startsWith('\\begin{')) {
        return <Box key={index} sx={{ bgcolor: "#F9FAFB", border: "1px solid #E5E7EB", borderRadius: "10px", p: 2, my: 1.5, overflowX: "auto", color: "#2563EB", display: "block", "& .katex": { fontSize: "1.1rem" } }} dangerouslySetInnerHTML={{ __html: katex.renderToString(part, { throwOnError: false, displayMode: true }) }} />;
      }
      
      // 5. Return normal text
      return <span key={index}>{part}</span>;
    });
  };
  const difficultyLabel = (difficulty) => {
    if (isEnglish) return difficulty;
    if (difficulty === "Easy") return "Mudah";
    if (difficulty === "Medium" || difficulty === "Moderate") return "Sederhana";
    if (difficulty === "Hard") return "Sukar";
    return difficulty;
  };

  const [selectedFile, setSelectedFile] = useState(null); // Keep the raw file for Base64 conversion
  const [selectedImage, setSelectedImage] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [feedback, setFeedback] = useState(null);
  const [isFetchingAnswer, setIsFetchingAnswer] = useState(false);
  const [answerRevealed, setAnswerRevealed] = useState(false);
  const [streak, setStreak] = useState(0);
  const [highestStreak, setHighestStreak] = useState(0);
  const [totalAttempted, setTotalAttempted] = useState(0);
  const [correctAnswers, setCorrectAnswers] = useState(0);
  const [retryMode, setRetryMode] = useState(false);
  const [openExitDialog, setOpenExitDialog] = useState(false);
  const [showSummaryModal, setShowSummaryModal] = useState(false);
  const isSubmittingRef = useRef(false);
  const groupAttemptIdsRef = useRef({});
  const fileInputRef = useRef(null);
  const cameraInputRef = useRef(null);
  const isFetchingAnswerRef = useRef(false);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const isUploadLocked = isFetchingAnswer || isSubmitting || answerRevealed;
  const [startTime, setStartTime] = useState(Date.now());
  const [attemptsLog, setAttemptsLog] = useState([]);
  const [selectedForm] = useState(location.state?.form || "Form 4");
  const [selectedChapterId] = useState(location.state?.chapter_id || 1);
  const [chapterString] = useState(
    location.state?.chapter_string || "Chapter 1: Quadratic Functions and Equations in One Variable"
  );
  const [currentVariant, setCurrentVariant] = useState(null);
  const [isReviewMode, setIsReviewMode] = useState(false);

  const [questionStages, setQuestionStages] = useState([]);
  const [practiceId, setPracticeId] = useState(null);
  const [adaptiveInfo, setAdaptiveInfo] = useState(null);
  const [openEasierDialog, setOpenEasierDialog] = useState(false);
  const [adaptiveMessage, setAdaptiveMessage] = useState("");
  const [groupStageScores, setGroupStageScores] = useState({});
  const [displayQuestionMap, setDisplayQuestionMap] = useState({});
  const [nextDisplayQuestionNo, setNextDisplayQuestionNo] = useState(1);
  const getDisplayPartLabel = (q, index) => {
    return (
      q?.display_subpart_label ||
      getPartLabel(q) ||
      `(${String.fromCharCode(97 + index)})`
    );
  };
  const getCurrentQuestionIds = () => {
    return (currentQuestions || [])
      .map((q) => q.id || q.question_id)
      .filter(Boolean);
  };
  const getDisplayQuestionNoForStage = (stage) => {
    const key = stage?.group_id || stage?.exercise_stage_id;

    if (!key) return nextDisplayQuestionNo;

    if (displayQuestionMap[key]) {
      return displayQuestionMap[key];
    }

    const assignedNo = nextDisplayQuestionNo;

    setDisplayQuestionMap((prev) => ({
      ...prev,
      [key]: assignedNo,
    }));

    setNextDisplayQuestionNo((prev) => prev + 1);

    return assignedNo;
  };
  const normalizeForCompare = (value) =>
    String(value || "")
      .replace(/\s+/g, " ")
      .trim()
      .toLowerCase();
  const getStageImageUrls = (questions) => {
    const urls = [];

    questions.forEach((q) => {
      const imageUrls = safeJson(q.image_urls, []);

      if (Array.isArray(imageUrls)) {
        imageUrls.forEach((url) => {
          if (url && !urls.includes(url)) urls.push(url);
        });
      }

      [q.image_path, q.image_url, q._diagram_image_path].forEach((url) => {
        if (url && !urls.includes(url)) urls.push(url);
      });
    });

    return urls;
  };

  const ENABLE_TEST_SKIP = process.env.REACT_APP_ENABLE_TEST_SKIP === "true";

    const handleSkipForTesting = async () => {
      const timeTaken = Math.floor((Date.now() - startTime) / 1000);
      const maxScore = getCurrentMaxScore();

      const attemptRecord = {
        ...buildAttemptRecord({
          isCorrect: false,
          score: 0,
          maxScore,
          answerRevealed: 0,
          timeTaken,
        }),
        is_skipped: 1,
        testing_skip: 1,
      };

      try {
        await saveSingleAttempt(attemptRecord);
      } catch (error) {
        console.error("Failed to save skipped K2 attempt:", error);
      }

      resetQuestionUi();
      await handleNextQuestion();
    };
  const handleRetryPractice = async () => {
    setShowSummaryModal(false);
    setRetryMode(true);

    setStreak(0);
    setHighestStreak(0);
    setTotalAttempted(0);
    setCorrectAnswers(0);
    setAttemptsLog([]);
    setFeedback(null);
    setCurrentVariant(null);
    setIsReviewMode(false);
    setQuestionStages([]);
    setCurrentIndex(0);
    setSelectedFile(null);
    setSelectedImage(null);
    setAnswerRevealed(false);

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }

    try {
      const newPracticeId = await startPracticeSession();
      await fetchNextK2Item(newPracticeId, true);
    } catch (error) {
      console.error("Failed to retry K2 practice:", error);
      setIsLoading(false);
    }
  };
  
  const getInstructionsForLanguage = (q) => {
    const instructionsEn = safeJson(q.instructions_en, []);
    const instructionsMs = safeJson(q.instructions_ms, []);
    return isEnglish ? instructionsEn : instructionsMs;
  };

  const getSharedIntroCount = (questions) => {
    if (!questions || questions.length <= 1) return 0;

    const instructionLists = questions.map(getInstructionsForLanguage);

    let sharedCount = 0;

    while (true) {
      const baseText = normalizeForCompare(instructionLists[0]?.[sharedCount]);

      if (!baseText) break;

      const allSame = instructionLists.every(
        (list) => normalizeForCompare(list?.[sharedCount]) === baseText
      );

      if (!allSame) break;

      sharedCount += 1;
    }

    return sharedCount;
  };
  
  const getQuestionImageUrlByIndex = (q, imageIndex = 0) => {
    const imageUrls = safeJson(q.image_urls, []);

    if (Array.isArray(imageUrls) && imageUrls[imageIndex]) {
      return imageUrls[imageIndex];
    }

    if (imageIndex === 0) {
      return q.image_path || q.image_url || q._diagram_image_path || "";
    }

    return "";
  };

  const sequenceHasItem = (q, prefix, index) => {
    const sequence = safeJson(q.sequence, []);

    return Array.isArray(sequence)
      ? sequence.includes(`${prefix}_${index}`)
      : false;
  };

  const isImageSharedAcrossQuestions = (questions, imageIndex = 0) => {
    const imageUrls = questions
      .filter((q) => sequenceHasItem(q, "image", imageIndex))
      .map((q) => getQuestionImageUrlByIndex(q, imageIndex))
      .filter(Boolean);

    // If less than 2 questions use this image, it is not a shared image.
    if (imageUrls.length < 2) return false;

    return new Set(imageUrls).size === 1;
  };
  const getOriginalExerciseStageIdForReview = () => {
    return (
      currentStage?.original_exercise_stage_id ||
      currentQuestions?.[0]?.original_exercise_stage_id ||
      currentQuestions?.[0]?.exercise_stage_id ||
      ""
    );
  };

  const getOriginalQuestionIdsForReview = () => {
    return (currentQuestions || [])
      .map((q) => q.original_question_id || q.question_id || q.id)
      .filter(Boolean);
  };

  const isOriginalGroupRetryVariant = () => {
    return (
      currentVariant &&
      (
        currentVariant.source_mode === "group" ||
        currentVariant.source_group_id ||
        String(currentVariant.source_key || "").startsWith("group:")
      )
    );
  };
  const getSharedSequenceInfo = (q, sharedTextCount) => {
    const sequence = safeJson(q.sequence, []);
    const sharedTextIndexes = new Set();
    const sharedTableIndexes = new Set();
    const sharedImageIndexes = new Set();
    const sharedSequenceItems = [];

    for (let i = 0; i < sharedTextCount; i += 1) {
      sharedTextIndexes.add(i);
    }

    // If there is no sequence, only shared text can be rendered.
    if (!sequence || sequence.length === 0) {
      for (let i = 0; i < sharedTextCount; i += 1) {
        sharedSequenceItems.push(`text_${i}`);
      }

      return {
        sharedTextIndexes,
        sharedTableIndexes,
        sharedImageIndexes,
        sharedSequenceItems,
      };
    }

    // Keep shared prefix in original visual order:
    // text_0 -> table_0/image_0 -> stop when first unique command text appears.
    for (const item of sequence) {
      if (item.startsWith("text_")) {
        const textIndex = parseInt(item.split("_")[1], 10);

        if (textIndex < sharedTextCount) {
          sharedSequenceItems.push(item);
        } else {
          break;
        }
      } else if (item.startsWith("table_")) {
        const tableIndex = parseInt(item.split("_")[1], 10);

        // Safer: only share tables if you are sure they are common.
        // Otherwise, do not hide tables inside subparts.
        sharedTableIndexes.add(tableIndex);
        sharedSequenceItems.push(item);
      } else if (item.startsWith("image_")) {
        const imageIndex = parseInt(item.split("_")[1], 10);

        // Only treat image as shared if all relevant subparts use the exact same image URL.
        if (isImageSharedAcrossQuestions(currentQuestions, imageIndex)) {
          sharedImageIndexes.add(imageIndex);
          sharedSequenceItems.push(item);
        }
      }
    }

    return {
      sharedTextIndexes,
      sharedTableIndexes,
      sharedImageIndexes,
      sharedSequenceItems,
    };
  };
  const safeJson = (value, fallback) => {
    if (!value) return fallback;
    if (typeof value === "object") return value;

    try {
      return JSON.parse(value);
    } catch {
      return fallback;
    }
  };
  const getPartLabel = (q) => {
    let label = "";

    if (q.part) label += `(${q.part})`;
    if (q.subpart) label += `(${q.subpart})`;
    if (q.sub_subpart) label += `(${q.sub_subpart})`;

    return label;
  };
  const getMainPart = (q) => {
    return String(q?.part || "").trim().toLowerCase();
  };

const isSingleLetterPart = (value) => {
  return /^[a-z]$/i.test(String(value || "").trim());
};

const buildDisplayLabelsForStageQuestions = (questions) => {
  if (!questions || questions.length === 0) return [];

  const firstMainPart = getMainPart(questions[0]);

  // If the stage starts from (c), (d), etc., restart display from (a).
  // If it already starts from (a), keep the original label.
  const shouldRenumber =
    firstMainPart &&
    isSingleLetterPart(firstMainPart) &&
    firstMainPart !== "a";

  const mainPartMap = {};

  return questions.map((q, index) => {
    const originalLabel = getPartLabel(q);
    const originalPart = getMainPart(q);

    let displayLabel = "";

    if (shouldRenumber && isSingleLetterPart(originalPart)) {
      if (!mainPartMap[originalPart]) {
        mainPartMap[originalPart] = String.fromCharCode(
          97 + Object.keys(mainPartMap).length
        );
      }

      displayLabel = `(${mainPartMap[originalPart]})`;

      // Preserve nested subparts
      if (q.subpart) {
        displayLabel += `(${q.subpart})`;
      }

      if (q.sub_subpart) {
        displayLabel += `(${q.sub_subpart})`;
      }
    } else {
      displayLabel = originalLabel || `(${String.fromCharCode(97 + index)})`;
    }

    return {
      ...q,
      original_subpart_label: q.original_subpart_label || originalLabel,
      display_subpart_label: displayLabel,
    };
  });
};


const applyContinuousGroupPartLabels = (stages) => {
  if (!Array.isArray(stages) || stages.length <= 1) return stages;

  const clonedStages = stages.map((stage) => ({
    ...stage,
    questions: Array.isArray(stage.questions)
      ? stage.questions.map((q) => ({ ...q }))
      : [],
  }));

  const groupStagesMap = {};

  // 1. Group all stages by their group_id
  clonedStages.forEach((stage) => {
    const groupKey = stage.group_id;
    if (!groupKey) return;

    if (!groupStagesMap[groupKey]) {
      groupStagesMap[groupKey] = [];
    }
    groupStagesMap[groupKey].push(stage);
  });

  // 2. Process each group to make the part labels continuous
  Object.values(groupStagesMap).forEach((groupStages) => {
    // Sort by stage_index to ensure chronological order (Stage 1, Stage 2, etc.)
    const sortedStages = groupStages.sort(
      (a, b) => Number(a.stage_index || 0) - Number(b.stage_index || 0)
    );

    let nextAvailableCharCode = 97; // 97 is the char code for 'a'

    sortedStages.forEach((stage) => {
      // Track the mapping for this specific stage.
      // This ensures if a stage has (a)(i) and (a)(ii), both map to the SAME new letter.
      const stagePartMap = {};

      stage.questions = (stage.questions || []).map((q) => {
        const originalPart = String(q.part || "").trim().toLowerCase();

        // If there is no part label defined, leave it alone
        if (!originalPart) return q;

        // If we haven't seen this part IN THIS STAGE yet, assign it the next continuous letter
        if (!stagePartMap[originalPart]) {
          stagePartMap[originalPart] = String.fromCharCode(nextAvailableCharCode);
          nextAvailableCharCode += 1;
        }

        const newPartLabel = stagePartMap[originalPart];

        // Reconstruct the full display label (e.g., (c)(i) or (d))
        let newDisplayLabel = `(${newPartLabel})`;
        if (q.subpart) newDisplayLabel += `(${String(q.subpart).trim()})`;
        if (q.sub_subpart) newDisplayLabel += `(${String(q.sub_subpart).trim()})`;

        return {
          ...q,
          original_subpart_label:
            q.original_subpart_label ||
            q.display_subpart_label ||
            getPartLabel(q), // preserves the backend's original label
          display_subpart_label: newDisplayLabel,
        };
      });
    });
  });

  return clonedStages;
};

  const difficultyFromLevel = (level) => {
    const numericLevel = Number(level || 3);

    if (numericLevel <= 2) return "Easy";
    if (numericLevel === 3) return "Moderate";
    return "Hard";
  };
  const groupQuestionsByStage = (questions) => {
    const stageMap = {};

    questions.forEach((q) => {
      const stageId =
        q.exercise_stage_id ||
        `${q.group_id || `Q${q.question_no}`}_S${q.stage_index || 1}`;

      const rowDifficultyLevel = Number(
        q.group_difficulty_level ||
        q.adaptive_difficulty_level ||
        q.difficulty_level ||
        3
      );

      const rowDifficulty = difficultyFromLevel(rowDifficultyLevel);
      if (!stageMap[stageId]) {
        stageMap[stageId] = {
          exercise_stage_id: stageId,
          stage_index: Number(q.stage_index || 1),
          group_id: q.group_id,
          question_no: q.question_no,
          difficulty: rowDifficulty,
          difficulty_level: rowDifficultyLevel,
          questions: [],
        };
      }

      stageMap[stageId].questions.push(q);
      stageMap[stageId].difficulty_level = Math.max(
        Number(stageMap[stageId].difficulty_level || 1),
        rowDifficultyLevel
      );

      stageMap[stageId].difficulty = difficultyFromLevel(
        stageMap[stageId].difficulty_level
      );
    });

  const builtStages = Object.values(stageMap)
    .map((stage) => {
      const sortedQuestions = stage.questions.sort((a, b) => {
        const aKey = `${a.part || ""}${a.subpart || ""}${a.sub_subpart || ""}`;
        const bKey = `${b.part || ""}${b.subpart || ""}${b.sub_subpart || ""}`;
        return aKey.localeCompare(bKey);
      });

      return {
        ...stage,
        questions: buildDisplayLabelsForStageQuestions(sortedQuestions),
      };
    })
    .sort((a, b) => a.stage_index - b.stage_index);

  return applyContinuousGroupPartLabels(builtStages);
};
  
  const startPracticeSession = async () => {
    const response = await apiFetch(
      `${process.env.REACT_APP_API_BASE_URL}/api/practice/start-session`,
      {
        method: "POST",
        body: JSON.stringify({
          chapter_id: selectedChapterId,
          paper_type: "kertas2",
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

  const fetchNextK2Item = async (practiceIdOverride = practiceId, forceRetry = retryMode) => {
    const activePracticeId = practiceIdOverride || practiceId;

    if (!activePracticeId) {
      console.error("Missing practiceId. Cannot fetch next K2 item.");
      return;
    }

    setIsLoading(true);

    try {
      const response = await apiFetch(
        `${process.env.REACT_APP_API_BASE_URL}/api/practice/next-item?practice_id=${encodeURIComponent(
          activePracticeId
        )}&form=${encodeURIComponent(
          selectedForm
        )}&chapter=${encodeURIComponent(
          chapterString
        )}&paper_type=kertas2&language=${encodeURIComponent(
          language
        )}&retry_mode=${forceRetry ? 1 : 0}`

      );

      const data = await response.json();

      console.log("K2 NEXT ITEM RESPONSE:", data);

      if (!response.ok || !data.success) {
        console.error("Failed to fetch next K2 item:", data.message || data);
        return;
      }

      if (data.item_type === "normal_question") {
        const groupedStages = groupQuestionsByStage(data.questions || []);

        setCurrentVariant(null);
        setIsReviewMode(false);
        setQuestionStages(groupedStages);
        setCurrentIndex(0);
        resetQuestionUi();
        return;
      }

      if (data.item_type === "review_variant") {
        const reviewStages = buildStagesFromReviewVariant(data.variant);

        setCurrentVariant(data.variant);
        setIsReviewMode(true);
        setQuestionStages(reviewStages);
        setCurrentIndex(0);
        resetQuestionUi();
        return;
      }
    
      if (data.item_type === "session_complete") {
        if (totalAttempted > 0) {
          await endPracticeSession();
          setShowSummaryModal(true);
        } else {
          setQuestionStages([]);
        }
        return;
      }

      setQuestionStages([]);
    } catch (error) {
      console.error("K2 next item fetch error:", error);
    } finally {
      setIsLoading(false);
    }
  };
  const saveSingleAttempt = async (attemptRecord) => {
    if (!practiceId) {
      console.error("Missing practiceId. Cannot save attempt.");
      return null;
    }

    const response = await apiFetch(`${process.env.REACT_APP_API_BASE_URL}/api/practice/save-attempt`, {
      method: "POST",
        body: JSON.stringify({
          practice_id: practiceId,
          form: selectedForm,
          chapter: chapterString,
          paper_type: "kertas2",
          language: language,
          attempt: attemptRecord,
        }),
    });

    return await response.json();
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
    const initialisePractice = async () => {
      setIsLoading(true);

      try {
        const newPracticeId = await startPracticeSession();
        await fetchNextK2Item(newPracticeId);
      } catch (error) {
        console.error("Failed to initialise K2 practice:", error);
        setIsLoading(false);
      }
    };

    if (selectedForm && chapterString) {
      initialisePractice();
    }
  }, [selectedForm, chapterString]);

  useEffect(() => {
    if (feedback) {
      window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" });
    }
  }, [feedback]);

  const currentStage = questionStages[currentIndex];
  const currentQuestions = currentStage?.questions || [];
  const currentQuestion = currentQuestions[0];
  const displayQuestionNo =
    currentStage?.group_id
      ? displayQuestionMap[currentStage.group_id]
      : displayQuestionMap[currentStage?.exercise_stage_id];
  useEffect(() => {
    if (!currentStage) return;

    const key = currentStage.group_id || currentStage.exercise_stage_id;
    if (!key) return;

    if (!displayQuestionMap[key]) {
      setDisplayQuestionMap((prev) => ({
        ...prev,
        [key]: nextDisplayQuestionNo,
      }));

      setNextDisplayQuestionNo((prev) => prev + 1);
    }
  }, [currentStage, displayQuestionMap, nextDisplayQuestionNo]);

  if (isLoading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", alignItems: "center", height: "100vh" }}>
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

  const handleDragOver = (e) => {
    e.preventDefault();

    if (isUploadLocked || isFetchingAnswerRef.current) return;

    setIsDragging(true);
  };

  const handleDragLeave = () => {
    if (isUploadLocked || isFetchingAnswerRef.current) return;

    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();

    if (isUploadLocked || isFetchingAnswerRef.current) {
      setIsDragging(false);
      return;
    }

    setIsDragging(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleImageSelect(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e) => {
    if (isUploadLocked || isFetchingAnswerRef.current) {
      e.target.value = "";
      return;
    }

    if (e.target.files && e.target.files[0]) {
      handleImageSelect(e.target.files[0]);
    }
  };

  const handleImageSelect = (file) => {
    if (isUploadLocked || isFetchingAnswerRef.current) return;

    setSelectedFile(file);
    setSelectedImage(URL.createObjectURL(file));
    setFeedback(null);
  };
  const clearImage = () => {
    setSelectedFile(null);
    setSelectedImage(null);
    setFeedback(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };
  const normalizeAnswerKey = (value) => {
    return String(value || "")
      .toLowerCase()
      .replace(/^part\s*/i, "")
      .replace(/\s+/g, "")
      .replace(/[()_\-.]/g, "")
      .trim();
  };

  const buildStepDisplayLabel = (step, idx) => {
    if (step?.display_subpart_label) {
      return step.display_subpart_label;
    }

    if (step?.part && step?.subpart) {
      return `(${step.part})(${step.subpart})`;
    }

    if (step?.part) {
      return `(${step.part})`;
    }

    if (step?.label) {
      return step.label;
    }

    const q = currentQuestions?.[idx];
    return q?.display_subpart_label || `(${String.fromCharCode(97 + idx)})`;
  };

  const getStepSubpartKey = (step, idx) => {
    return normalizeAnswerKey(buildStepDisplayLabel(step, idx));
  };

  const isLastStepForSameSubpart = (steps, idx) => {
    const currentKey = getStepSubpartKey(steps[idx], idx);

    for (let i = idx + 1; i < steps.length; i += 1) {
      if (getStepSubpartKey(steps[i], i) === currentKey) {
        return false;
      }
    }

    return true;
  };
  const hasFinalAnswerValue = (value) => {
    if (value === null || value === undefined) return false;

    if (typeof value === "string") {
      return value.trim().length > 0;
    }

    if (typeof value === "object") {
      return Object.keys(value).length > 0;
    }

    return Boolean(value);
  };

  const pickFinalAnswerSource = (...values) => {
    return values.find(hasFinalAnswerValue) || {};
  };
  const getFinalAnswerForStep = (step, idx, explanation) => {
  const finalAnswers = pickFinalAnswerSource(
    explanation?.final_answers,
    explanation?.final_answer_by_part,
    explanation?.final_answer
  );

  const stepFinal =
    step?.final_answer ||
    step?.answer ||
    "";

  if (stepFinal) return String(stepFinal);

  // If final_answer is one string, show it only at the LAST step.
  if (typeof finalAnswers === "string") {
    const totalSteps = explanation?.steps?.length || 1;
    return idx === totalSteps - 1 ? finalAnswers : "";
  }

  if (!finalAnswers || typeof finalAnswers !== "object") {
    return "";
  }

  const normalizedFinalAnswers = {};

  Object.entries(finalAnswers).forEach(([key, value]) => {
    normalizedFinalAnswers[normalizeAnswerKey(key)] = value;
  });

  const displayLabel = buildStepDisplayLabel(step, idx);

  const possibleKeys = [
    displayLabel,
    step?.display_subpart_label,
    step?.subpart,
    step?.part,
    step?.label,
    step?.part && step?.subpart ? `(${step.part})(${step.subpart})` : "",
    step?.part && step?.subpart ? `${step.part}(${step.subpart})` : "",
  ].filter(Boolean);

  for (const key of possibleKeys) {
    if (finalAnswers[key]) {
      return String(finalAnswers[key]);
    }

    const normalizedKey = normalizeAnswerKey(key);

    if (normalizedFinalAnswers[normalizedKey]) {
      return String(normalizedFinalAnswers[normalizedKey]);
    }
  }

  return "";
};
  const getCurrentGroupAttemptId = () => {
    const groupId = currentStage?.group_id || currentQuestion?.group_id;

    if (!groupId || currentQuestion?.group_chapter === "Mixed") {
      return null;
    }

    const key = `${practiceId}_${groupId}`;
    // If this is Stage 1, start a new group attempt run.
    // This is important when the failed group is repeated later.
    if (Number(currentStage?.stage_index || 1) === 1 || !groupAttemptIdsRef.current[key]) {
      groupAttemptIdsRef.current[key] = `${key}_${Date.now()}`;
    }

    return groupAttemptIdsRef.current[key];
  };
  const buildAttemptRecord = ({
    isCorrect,
    score = null,
    maxScore = null,
    answerRevealed = 0,
    timeTaken,
  }) => {
    const groupId = currentStage?.group_id || currentQuestion?.group_id || null;
    const isMixedGroup = currentQuestion?.group_chapter === "Mixed";

    return {
      question_id: currentVariant
        ? currentVariant?.source_question_id || null
        : currentQuestion?.id || currentQuestion?.question_id || null,
      exercise_stage_id: currentStage?.exercise_stage_id || null,

      group_attempt_id: !isMixedGroup && groupId ? getCurrentGroupAttemptId() : null,
      group_id_snapshot: !isMixedGroup && groupId ? groupId : null,

      paper_type: "kertas2",

      form_snapshot: selectedForm,
      chapter_snapshot_id: selectedChapterId,
      chapter_snapshot: chapterString,

      difficulty_snapshot: displayedDifficulty,
      difficulty_level_snapshot:
        currentStage?.difficulty_level ||
        currentQuestion?.adaptive_difficulty_level ||
        currentQuestion?.group_difficulty_level ||
        currentQuestion?.difficulty_level ||
        3,

      is_correct: isCorrect ? 1 : 0,

      score: score,
      max_score: maxScore,

      answer_revealed: answerRevealed,

      time_taken_seconds: timeTaken,
      review_variant_id: currentVariant?.variant_id || null,
      variant_stage_index: currentVariant
        ? Number(currentQuestion?.variant_stage_index || currentStage?.stage_index || currentIndex + 1)
        : null,

      variant_stage_count: currentVariant ? questionStages.length : null,

      is_variant_final_stage: currentVariant
        ? currentIndex >= questionStages.length - 1
          ? 1
          : 0
        : 1,
      attempted_at: new Date().toISOString(),
    };
  };
  const getCurrentGroupKey = () => {
  // Mixed chapter groups should behave like individual questions
  if (currentQuestion?.group_chapter === "Mixed") {
    return `single_${currentQuestion?.id}`;
  }

  return (
    currentStage?.group_id ||
    currentQuestion?.group_id ||
    currentStage?.exercise_stage_id ||
    `single_${currentQuestion?.id}`
  );
};

const updateGroupStageScore = ({
  score,
  maxScore,
  isFullMark,
  answerRevealed = 0,
}) => {
  const groupKey = getCurrentGroupKey();
  const stageId = currentStage?.exercise_stage_id || `QID_${currentQuestion?.id}`;

  setGroupStageScores((prev) => {
    const existingGroup = prev[groupKey] || {
      group_id: currentStage?.group_id || currentQuestion?.group_id || "",
      question_no: currentStage?.question_no || currentQuestion?.question_no || "",
      stages: {},
    };

    return {
      ...prev,
      [groupKey]: {
        ...existingGroup,
        stages: {
          ...existingGroup.stages,
          [stageId]: {
            exercise_stage_id: stageId,
            stage_index: Number(currentStage?.stage_index || currentQuestion?.stage_index || 1),
            score: Number(score || 0),
            max_score: Number(maxScore || 0),
            is_correct: isFullMark ? 1 : 0,
            answer_revealed: answerRevealed ? 1 : 0,
            attempted_at: new Date().toISOString(),
          },
        },
      },
    };
  });
};

const getFeedbackTitle = (status) => {
  if (status === "correct") return text.correct;
  if (status === "partial") return text.partial;
  if (status === "zero") return text.zero;
  return text.wrong;
};

const getFeedbackTheme = (status) => {
  if (status === "correct") {
    return {
      bg: "#ECFDF5",
      border: "#A7F3D0",
      title: "#065F46",
      icon: "#10B981",
    };
  }

  if (status === "partial") {
    return {
      bg: "#FFFBEB",
      border: "#FCD34D",
      title: "#92400E",
      icon: "#F59E0B",
    };
  }

  if (status === "zero" || status === "wrong") {
    return {
      bg: "#FEF2F2",
      border: "#FECACA",
      title: "#991B1B",
      icon: "#EF4444",
    };
  }

  if (status === "solution") {
    return {
      bg: "#EFF6FF",
      border: "#BFDBFE",
      title: "#1E40AF",
      icon: "#3B82F6",
    };
  }

  return {
    bg: "#F9FAFB",
    border: "#E5E7EB",
    title: "#374151",
    icon: "#6B7280",
  };
};


const renderFeedbackIcon = (status) => {
  const theme = getFeedbackTheme(status);

  if (status === "correct") {
    return (
      <CheckCircleOutlineIcon
        sx={{ color: theme.icon, fontSize: 32, mt: 0.5 }}
      />
    );
  }

  if (status === "partial" || status === "solution") {
    return (
      <LightbulbOutlinedIcon
        sx={{ color: theme.icon, fontSize: 32, mt: 0.5 }}
      />
    );
  }

  return (
    <HighlightOffIcon
      sx={{ color: theme.icon, fontSize: 32, mt: 0.5 }}
    />
  );
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

    // Fix \neq accidentally parsed as newline + eq / e
    .replace(/\\neq/g, "\\ne")
    .replace(/\n\s*eq\s*/g, "\\ne ")
    .replace(/\n\s*e\s*/g, "\\ne ")
    .replace(/(^|[^\\])neq/g, "$1\\ne")

    // Fix already-broken "eA" / "e B" caused by \ne being swallowed
    // Example: A \cap B e A -> A \cap B \ne A
    .replace(/(\b[A-Z]\s*\\(?:cup|cap)\s*[A-Z]\s*)e\s*([A-Z]\b)/g, "$1\\ne $2")

    // Fix missing slash for set notation
    .replace(/(^|[^\\])cup/g, "$1\\cup")
    .replace(/(^|[^\\])cap/g, "$1\\cap")

    // Remove wrong \text{ ... } wrapper around display math environments
    .replace(
      /\\text\{\s*(\\begin\{(?:aligned|align|array|matrix|pmatrix|bmatrix|cases)\}[\s\S]*?\\end\{(?:aligned|align|array|matrix|pmatrix|bmatrix|cases)\})\s*\}/g,
      "$1"
    )

    // Remove $ inside display environments
    .replace(
      /(\\begin\{(?:aligned|align|array|matrix|pmatrix|bmatrix|cases)\})\s*\$/g,
      "$1 "
    )
    .replace(
      /\$\s*(\\end\{(?:aligned|align|array|matrix|pmatrix|bmatrix|cases)\})/g,
      " $1"
    )

    // Remove whole-field $ wrapper around environments
    .replace(/^\$\s*(\\begin\{[^}]+\})/, "$1")
    .replace(/(\\end\{[^}]+\})\s*\$$/, "$1")

    .trim();
};
const sanitizeMathBlockForKatex = (value) => {
  let clean = normalizeLatexText(value);

  if (!clean) return "";

  // Remove outer $...$ or $$...$$ if accidentally included
  clean = clean
    .replace(/^\s*\$\$\s*/, "")
    .replace(/\s*\$\$\s*$/, "")
    .replace(/^\s*\$\s*/, "")
    .replace(/\s*\$\s*$/, "")
    .trim();

  // Fix single-line aligned equations:
  // \begin{aligned} ... &= ... \end{aligned}
  // becomes: ... = ...
  const alignedMatch = clean.match(
    /^\\begin\{aligned\}([\s\S]*)\\end\{aligned\}$/i
  );

  if (alignedMatch) {
    let inner = alignedMatch[1].trim();

    // If it is only used for alignment around equals, remove alignment marker.
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
          width: "100%",
          overflowX: "auto",
          color: "#2563EB",
          "& .katex-display": {
            margin: 0,
          },
          "& .katex": {
            fontSize: "1.08rem",
          },
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
    console.error("KaTeX block render error:", error, clean);

    return (
      <Typography
        variant="body2"
        color="error"
        sx={{
          whiteSpace: "pre-wrap",
          fontFamily: "monospace",
        }}
      >
        {clean}
      </Typography>
    );
  }
};
const hasRawLatexCommand = (value) => {
  return /\\(?:frac|sqrt|times|div|cup|cap|ne|neq|le|ge|text|left|right|rightarrow|to|Rightarrow|implies|therefore|because|quad|qquad)\b/.test(
    String(value || "")
  );
};
const hasLatexWrapper = (value) => {
  const text = String(value || "");
  return (
    /\$[^$]+\$/.test(text) ||
    /\\\([\s\S]*?\\\)/.test(text) ||
    /\\begin\{[^}]+\}/.test(text)
  );
};

const renderMixedLatexSentence = (value) => {
  const clean = normalizeLatexText(value);

  if (!clean) return null;

  // Detect set expressions inside normal sentence:
  // A \cup B = B
  // A \cap B \ne A
  const mathRegex =
    /([A-Z]\s*\\(?:cup|cap)\s*[A-Z]\s*(?:=|\\ne|\\neq|≠)\s*[A-Z])/g;

  const parts = [];
  let lastIndex = 0;
  let match;

  while ((match = mathRegex.exec(clean)) !== null) {
    if (match.index > lastIndex) {
      parts.push(
        <span key={`text-${lastIndex}`}>
          {clean.slice(lastIndex, match.index)}
        </span>
      );
    }

    const mathContent = match[1].replace(/\\neq/g, "\\ne");

    parts.push(
      <Box
        component="span"
        key={`math-${match.index}`}
        sx={{ color: "inherit", mx: 0.25 }}
        dangerouslySetInnerHTML={{
          __html: katex.renderToString(mathContent, {
            throwOnError: false,
            displayMode: false,
          }),
        }}
      />
    );

    lastIndex = match.index + match[1].length;
  }

  if (parts.length === 0) return null;

  if (lastIndex < clean.length) {
    parts.push(
      <span key={`text-${lastIndex}`}>
        {clean.slice(lastIndex)}
      </span>
    );
  }

  return parts;
};

const isSentenceLikeAnswer = (value) => {
  const text = String(value || "").trim();

  if (!text) return false;

  // Remove LaTeX command names like \frac, \sqrt, \text
  const textWithoutLatexCommands = text.replace(/\\[a-zA-Z]+/g, "");

  // Detect real English/Malay words, not just variables like x, y, h
  const words = textWithoutLatexCommands.match(/\b[A-Za-z]{3,}\b/g) || [];

  const mathFunctionWords = ["sin", "cos", "tan", "log", "ln"];
  const realWords = words.filter(
    (word) => !mathFunctionWords.includes(word.toLowerCase())
  );

  return realWords.length >= 1 && (/\s/.test(text) || /[.,]/.test(text));
};

const renderMathOrText = (value) => {
  const clean = normalizeLatexText(value);

  if (!clean) return null;

  if (hasLatexWrapper(clean)) {
    return renderInlineMath(clean);
  }
  if (hasRawLatexCommand(clean)) {
    return renderInlineMath(`$${clean}$`);
  }
  // Important:
  // Sentence answers must NOT be wrapped in $...$,
  // otherwise KaTeX removes normal spacing between words.
  const mixedLatexSentence = renderMixedLatexSentence(clean);

  if (mixedLatexSentence) {
    return (
      <Box
        component="span"
        sx={{
          color: "inherit",
          fontWeight: "inherit",
          fontFamily: "inherit",
        }}
      >
        {mixedLatexSentence}
      </Box>
    );
  }

  if (isSentenceLikeAnswer(clean)) {
    return (
      <Box
        component="span"
        sx={{
          color: "inherit",
          fontWeight: "inherit",
          fontFamily: "inherit",
        }}
      >
        {clean}
      </Box>
    );
  }
  if (isActuallyMath(clean)) {
    return renderInlineMath(`$${clean}$`);
  }

  return renderInlineMath(clean);
};

const renderFinalAnswer = (value) => {
  const clean = normalizeLatexText(value);

  if (!clean) return null;

  if (/\\begin\{(?:aligned|align|array|matrix|pmatrix|bmatrix|cases)\}/.test(clean)) {
    return renderMathBlock(clean);
  }

  if (hasLatexWrapper(clean)) {
    return renderInlineMath(clean);
  }

  const mixedLatexSentence = renderMixedLatexSentence(clean);

  if (mixedLatexSentence) {
    return (
      <Box
        component="span"
        sx={{
          color: "inherit",
          fontWeight: "inherit",
          fontFamily: "inherit",
        }}
      >
        {mixedLatexSentence}
      </Box>
    );
  }

  // Handle mixed text + math, for example:
  // Minimum point = \left(\frac{1}{2}, -\frac{25}{4}\right)
  const mixedAnswerMatch = clean.match(/^(.+?=)\s*(.+)$/);

  if (mixedAnswerMatch) {
    const labelPart = mixedAnswerMatch[1];
    const mathPart = mixedAnswerMatch[2];

    const labelHasWords = /\b[A-Za-z]{3,}\b/.test(labelPart);

    if (labelHasWords && isActuallyMath(mathPart)) {
      return (
        <>
          <Box component="span" sx={{ color: "inherit", fontWeight: "inherit" }}>
            {labelPart}{" "}
          </Box>
          {renderInlineMath(`$${mathPart}$`)}
        </>
      );
    }
  }

  return renderMathOrText(clean);
};

const renderFeedbackPanel = () => {
  if (!feedback) return null;

  const theme = getFeedbackTheme(feedback.status);

  return (
    <Fade in={!!feedback}>
      <Box>
        <Paper
          elevation={0}
          sx={{
            p: { xs: 2, sm: 3 },
            mb: 3,
            borderRadius: "16px",
            display: "flex",
            alignItems: "flex-start",
            gap: 2,
            bgcolor: theme.bg,
            border: `1px solid ${theme.border}`,
            width: "100%",
            maxWidth: "100%",
            boxSizing: "border-box",
            overflow: "hidden",
          }}
        >
          {renderFeedbackIcon(feedback.status)}

          <Box
            sx={{
              flex: 1,
              minWidth: 0,
              maxWidth: "100%",
              overflow: "hidden",
            }}
          >
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
                color={theme.title}
              >
                {getFeedbackTitle(feedback.status)}
              </Typography>

              <DisclaimerText sx={{ mt: 0, flexShrink: 0 }} />
            </Box>

            <Box
              sx={{
                mt: 2,
                p: { xs: 1.5, sm: 2 },
                bgcolor: "rgba(255,255,255,0.6)",
                borderRadius: "12px",
                border: "1px dashed rgba(0,0,0,0.1)",
                width: "100%",
                maxWidth: "100%",
                boxSizing: "border-box",
                overflow: "hidden",
              }}
            >
              <Box
                sx={{
                  display: "flex",
                  alignItems: "center",
                  gap: 1,
                  mb: 1,
                }}
              >
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

              {typeof feedback.explanation === "string" ? (
                <Typography
                  variant="body1"
                  color="#4B5563"
                  sx={{ whiteSpace: "pre-line" }}
                >
                  {feedback.explanation}
                </Typography>
              ) : (
                <Box
                  sx={{
                    mt: 1,
                    width: "100%",
                    maxWidth: "100%",
                    minWidth: 0,
                    overflow: "hidden",
                    boxSizing: "border-box",
                  }}
                >
                  {/* 1. AI GRADING REPORT */}
                  {feedback.explanation?.stepwise_evaluation && (
                    <>
                      <Typography
                        variant="h6"
                        fontWeight="900"
                        color="#111827"
                        mb={2}
                        align="right"
                        sx={{ px: 1 }}
                      >
                        Total Score: {feedback.explanation?.score} /{" "}
                        {feedback.explanation?.max_score}
                      </Typography>

                      {feedback.explanation.stepwise_evaluation.map(
                        (step, idx) => (
                          <Paper
                            key={idx}
                            elevation={0}
                            sx={{
                              p: 2,
                              mb: 2,
                              border: "1px solid #E5E7EB",
                              borderRadius: "12px",
                              bgcolor: "rgba(255,255,255,0.8)",
                              width: "100%",
                              maxWidth: "100%",
                              minWidth: 0,
                              boxSizing: "border-box",
                              overflow: "hidden",
                            }}
                          >
                            <Box
                              sx={{
                                display: "flex",
                                justifyContent: "space-between",
                                alignItems: "flex-start",
                                mb: 1.5,
                                gap: 2,
                              }}
                            >
                              <Typography
                                variant="subtitle2"
                                fontWeight="bold"
                                color="#374151"
                              >
                                {getAlignedStepHeader(step, idx)}
                              </Typography>

                              <Chip
                                label={`${step.marks_awarded} / ${step.max_marks} Marks`}
                                size="small"
                                sx={{
                                  fontWeight: "bold",
                                  bgcolor:
                                    Number(step.marks_awarded || 0) >=
                                    Number(step.max_marks || 0)
                                      ? "#D1FAE5"
                                      : Number(step.marks_awarded || 0) > 0
                                      ? "#FEF3C7"
                                      : "#FEE2E2",
                                  color:
                                    Number(step.marks_awarded || 0) >=
                                    Number(step.max_marks || 0)
                                      ? "#065F46"
                                      : Number(step.marks_awarded || 0) > 0
                                      ? "#92400E"
                                      : "#991B1B",
                                }}
                              />
                            </Box>

                            <Typography variant="body2" color="#4B5563" mb={1}>
                              <strong>Student Wrote:</strong>{" "}
                              {renderInlineMath(step.student_wrote)}
                            </Typography>

                            <Typography
                              variant="body2"
                              color="#6B7280"
                              sx={{ fontStyle: "italic" }}
                            >
                              <strong>Reason:</strong>{" "}
                              {renderInlineMath(step.reason)}
                            </Typography>
                          </Paper>
                        )
                      )}
                    </>
                  )}

                  {/* 2. OFFICIAL SOLUTION / SHOW ANSWER */}
                  {feedback.explanation?.steps && (
                    <Box>
                      <Typography
                        variant="h6"
                        fontWeight="bold"
                        color="#111827"
                        mb={2}
                      >
                        {isEnglish
                          ? "Step-by-Step Solution"
                          : "Penyelesaian Langkah demi Langkah"}
                      </Typography>

                      {feedback.explanation.steps.map((step, idx) => {
                        let stepMath = normalizeLatexText(step.math || "");

                        const finalAnswer = normalizeLatexText(
                          getFinalAnswerForStep(step, idx, feedback.explanation)
                        );

                        const isDuplicateWorking =
                          stepMath &&
                          finalAnswer &&
                          normalizeForCompare(stepMath) === normalizeForCompare(finalAnswer);

                        const showWorking = stepMath && !isDuplicateWorking;

                        const showFinalAnswer =
                          finalAnswer &&
                          isLastStepForSameSubpart(feedback.explanation.steps, idx);


                        return (
                          <Paper
                            key={idx}
                            elevation={0}
                            sx={{
                              p: 2,
                              mb: 2,
                              border: "1px solid #E5E7EB",
                              borderRadius: "12px",
                              bgcolor: "rgba(255,255,255,0.8)",
                            }}
                          >
                            <Typography
                              variant="subtitle2"
                              fontWeight="bold"
                              color="#374151"
                              mb={1}
                            >
                              {getStepHeader(step, idx)}
                            </Typography>

                            {step.text && (
                              <Typography variant="body2" color="#4B5563" mb={1}>
                                {renderMathOrText(step.text)}
                              </Typography>
                            )}

                            {showWorking && (
                              <Box
                                sx={{
                                  mt: 1,
                                  mb: 1,
                                  p: 1.5,
                                  bgcolor: "#F9FAFB",
                                  border: "1px solid #E5E7EB",
                                  borderRadius: "10px",
                                  overflowX: "auto",
                                }}
                              >
                                <Typography
                                  variant="caption"
                                  fontWeight="bold"
                                  color="#6B7280"
                                  textTransform="uppercase"
                                >
                                  {isEnglish ? "Working" : "Jalan Kerja"}
                                </Typography>

                                <Box sx={{ mt: 0.5 }}>
                                  {renderMathBlock(stepMath)}
                                </Box>
                              </Box>
                            )}

                            {showFinalAnswer && (
                              <Box
                                sx={{
                                  mt: 1,
                                  mb: 1,
                                  p: 1.5,
                                  bgcolor: "#ECFDF5",
                                  border: "1px solid #A7F3D0",
                                  borderRadius: "10px",
                                  overflowX: "auto",
                                }}
                              >
                                <Typography
                                  variant="caption"
                                  fontWeight="bold"
                                  color="#047857"
                                  textTransform="uppercase"
                                >
                                  {isEnglish ? "Final Answer" : "Jawapan Akhir"}
                                </Typography>

                                <Box sx={{ mt: 0.5, color: "#065F46", fontWeight: "bold" }}>
                                  {renderFinalAnswer(finalAnswer)}
                                </Box>
                              </Box>
                            )}
                            {isLastStepForSameSubpart(feedback.explanation.steps, idx) &&
                              renderAnswerImagesForStep(feedback.explanation, step, idx)}
                          </Paper>
                        );
                      })}
                    </Box>
                  )}

                  {/* 3. OFFICIAL SOLUTION ATTACHED AFTER WRONG / PARTIAL GRADING */}
                  {feedback.explanation?.official_solution && (
                    <Box sx={{ mt: 3 }}>
                      <Typography
                        variant="h6"
                        fontWeight="bold"
                        color="#1E40AF"
                        mb={2}
                      >
                        {isEnglish
                          ? "Correct Answer Explanation"
                          : "Penerangan Jawapan Betul"}
                      </Typography>

                      {feedback.explanation.official_solution?.steps?.map(
                        (step, idx) => (
                          <Paper
                            key={idx}
                            elevation={0}
                            sx={{
                              p: 2,
                              mb: 2,
                              border: "1px solid #BFDBFE",
                              borderRadius: "12px",
                              bgcolor: "#EFF6FF",
                            }}
                          >
                            <Typography
                              variant="subtitle2"
                              fontWeight="bold"
                              color="#1E3A8A"
                              mb={1}
                            >
                              {getAlignedStepHeader(step, idx)}
                            </Typography>

                            {step.text && (
                              <Typography
                                variant="body2"
                                color="#374151"
                                mb={1}
                              >
                                {renderMathOrText(step.text)}
                              </Typography>
                            )}

                            {step.math && (
                              <Box
                                sx={{
                                  mt: 1,
                                  p: 1.5,
                                  bgcolor: "#FFFFFF",
                                  borderRadius: "10px",
                                  overflowX: "auto",
                                }}
                              >
                                {renderMathBlock(step.math)}
                              </Box>
                            )}
                            {isLastStepForSameSubpart(
                              feedback.explanation.official_solution.steps,
                              idx
                            ) &&
                              renderAnswerImagesForStep(
                                feedback.explanation.official_solution,
                                step,
                                idx
                              )}
                          </Paper>
                        )
                      )}
                    </Box>
                  )}
                </Box>
              )}
            </Box>
          </Box>
        </Paper>

        {renderGroupScoreSummary()}

        <Button
          variant="contained"
          fullWidth
          size="large"
          onClick={handleNextQuestion}
          sx={{
            bgcolor: "#3855c0",
            "&:hover": { bgcolor: "#2f46a3" },
            borderRadius: "14px",
            textTransform: "none",
            fontWeight: "bold",
            py: 1.4,
          }}
        >
          {text.nextBtn}
        </Button>
      </Box>
    </Fade>
  );
};
const getCurrentGroupScoreSummary = () => {
  const groupKey = getCurrentGroupKey();
  const group = groupStageScores[groupKey];

  if (!group) return null;

  const stages = Object.values(group.stages || {}).sort(
    (a, b) => Number(a.stage_index || 0) - Number(b.stage_index || 0)
  );

  if (!stages.length) return null;

  const totalScore = stages.reduce((sum, stage) => sum + Number(stage.score || 0), 0);
  const totalMax = stages.reduce((sum, stage) => sum + Number(stage.max_score || 0), 0);
  const isGroupFullMark = totalMax > 0 && totalScore >= totalMax;

  return {
    ...group,
    stages,
    totalScore,
    totalMax,
    isGroupFullMark,
  };
};
const getMarkingStatus = (score, maxScore) => {
  const numericScore = Number(score || 0);
  const numericMaxScore = Number(maxScore || 0);

  if (numericMaxScore > 0 && numericScore >= numericMaxScore) {
    return "correct";
  }

  if (numericScore <= 0) {
    return "zero";
  }

  return "partial";
};
const normalizePartKey = (value) => {
  return String(value || "")
    .toLowerCase()
    .replace(/\s+/g, "")
    .replace(/[()]/g, "")
    .trim();
};

const extractPartKey = (item) => {
  // Prefer explicit subpart field if your backend returns it
  const direct =
    item?.display_subpart_label ||
    (item?.part && item?.subpart ? `(${item.part})(${item.subpart})` : "") ||
    item?.subpart ||
    item?.part ||
    item?.question_part ||
    item?.label ||
    "";

  if (direct) return normalizePartKey(direct);

  // Fallback: try to extract from step text, e.g. "(a)(ii)" or "a(ii)"
  const text = `${item?.step || ""} ${item?.text || ""} ${item?.reason || ""}`;
  const match = text.match(/\(?[a-z]\)?\s*\(?[ivx]+\)?|\(?[a-z]\)?/i);

  return match ? normalizePartKey(match[0]) : "";
};

const getDeductedPartKeys = (gradingResult) => {
  const evaluations = gradingResult?.stepwise_evaluation || [];

  return evaluations
    .filter((step) => {
      const awarded = Number(step.marks_awarded || 0);
      const max = Number(step.max_marks || 0);
      return max > 0 && awarded < max;
    })
    .map(extractPartKey)
    .filter(Boolean);
};

const filterOfficialSolutionForDeductedMarks = (officialSolution, gradingResult) => {
  if (!officialSolution) return null;

  const deductedKeys = getDeductedPartKeys(gradingResult);

  if (!deductedKeys.length) {
    return officialSolution;
  }

  const filteredSteps = (officialSolution.steps || []).filter((step) => {
    const stepKey = extractPartKey(step);

    if (!stepKey) return false;

    return deductedKeys.some(
      (deductedKey) =>
        stepKey === deductedKey ||
        stepKey.includes(deductedKey) ||
        deductedKey.includes(stepKey)
    );
  });

  const filteredAnswerImages = getAnswerImages(officialSolution).filter((img) => {
    const imgKey = extractPartKey(img);

    if (!imgKey) return false;

    return deductedKeys.some(
      (deductedKey) =>
        imgKey === deductedKey ||
        imgKey.includes(deductedKey) ||
        deductedKey.includes(imgKey)
    );
  });

  if (!filteredSteps.length && !filteredAnswerImages.length) {
    return officialSolution;
  }

  return {
    ...officialSolution,
    steps: filteredSteps,
    answer_images: filteredAnswerImages,
  };
};

const fetchOfficialSolutionForCurrentStage = async () => {
  try {
    const stageImageUrls = getStageImageUrls(currentQuestions);

    const response = await apiFetch(
      `${process.env.REACT_APP_API_BASE_URL}/api/ai/explain-known`,
      {
        method: "POST",
        body: JSON.stringify({
          exercise_stage_id: currentStage.exercise_stage_id,
          question_ids: getCurrentQuestionIds(),
          question_images: stageImageUrls,
          language: language,
        }),
      }
    );

    const data = await response.json();
    console.log("OFFICIAL SOLUTION FULL RESULT:", data.result);
    console.log("OFFICIAL SOLUTION ANSWER IMAGES:", data.result?.answer_images);
    if (!response.ok || !data.success) {
      console.error("Failed to fetch official solution:", data.message);
      return null;
    }

    return data.result || null;
  } catch (error) {
    console.error("Official solution fetch error:", error);
    return null;
  }
};
const resetQuestionUi = () => {
  setSelectedFile(null);
  setSelectedImage(null);
  setFeedback(null);
  setIsSubmitting(false);
  setAnswerRevealed(false);
  setStartTime(Date.now());

  if (fileInputRef.current) {
    fileInputRef.current.value = "";
  }
};

const normalizeQuestionSequence = (stageQuestion) => {
  const sequence = safeJson(stageQuestion.sequence, []);
  const instructionsEn = stageQuestion.instructions_en || [];
  const tableData = stageQuestion.table_data || {};
  const imagePath = stageQuestion.image_path || "";

  let normalized =
    Array.isArray(sequence) && sequence.length > 0
      ? [...sequence]
      : instructionsEn.map((_, index) => `text_${index}`);

  const hasTable =
    tableData &&
    typeof tableData === "object" &&
    Object.keys(tableData).length > 0;

  if (hasTable && !normalized.some((item) => String(item).startsWith("table_"))) {
    const insertAfterFirstText = normalized.findIndex((item) => item === "text_0");
    normalized.splice(insertAfterFirstText >= 0 ? insertAfterFirstText + 1 : normalized.length, 0, "table_0");
  }

  if (imagePath && !normalized.some((item) => String(item).startsWith("image_"))) {
    normalized.push("image_0");
  }

  // Also ensure all instruction texts are included.
  instructionsEn.forEach((_, index) => {
    const key = `text_${index}`;
    if (!normalized.includes(key)) {
      normalized.push(key);
    }
  });

  return normalized;
};
const detectTableRowLanguage = (row) => {
  const text = (Array.isArray(row) ? row : [row])
    .map((cell) => String(cell || ""))
    .join(" ")
    .toLowerCase();

  const malayKeywords = [
    "ialah",
    "bagi",
    "semua",
    "gandaan",
    "kesimpulan",
    "premis",
    "faktor",
    "sepunya",
    "terbesar",
    "nombor",
    "dan",
    "atau",
    "rajah",
    "jadual",
    "pendapatan",
    "aktif",
    "pasif",
    "simpanan",
    "tetap",
    "bulanan",
    "dana",
    "kecemasan",
    "baki",
    "perbelanjaan",
    "ansuran",
    "kereta",
    "insurans",
    "pembiayaan",
    "rumah",
    "tidak tetap",
    "barangan",
    "dapur",
    "petrol",
    "utiliti",
    "pemberian",
    "ibu bapa",
    "bil telefon",
    "pendapatan",
"aktif",
"pasif",
"simpanan",
"tetap",
"bulanan",
"dana",
"kecemasan",
"baki",
"perbelanjaan",
"ansuran",
"kereta",
"insurans",
"pembiayaan",
"rumah",
"tidak tetap",
"barangan",
"dapur",
"petrol",
"utiliti",
"pemberian",
"ibu bapa",
"bil telefon",
"keluasan",
"tanah",
"anggaran",
"sewa",
"cukai",
"pintu",
"kadar",
"jumlah",
"meter persegi",
"sebulan"
  ];

  const englishKeywords = [
    " is ",
    " are ",
    "all ",
    "multiple",
    "multiples",
    "conclusion",
    "premise",
    "highest common factor",
    "factor of",
    "number",
    "and",
    "or",
    "diagram",
    "table",
    "income",
    "active income",
    "passive income",
    "savings",
    "fixed monthly savings",
    "emergency funds",
    "income balance",
    "expenses",
    "monthly fixed expenses",
    "car installment",
    "insurance",
    "housing loan",
    "monthly variable expenses",
    "groceries",
    "fuel",
    "home utilities",
    "giving to parents",
    "telephone bills",
    "income",
  "active income",
  "passive income",
  "savings",
  "fixed monthly savings",
  "emergency funds",
  "income balance",
  "expenses",
  "monthly fixed expenses",
  "car installment",
  "insurance",
  "housing loan",
  "monthly variable expenses",
  "groceries",
  "fuel",
  "home utilities",
  "giving to parents",
  "telephone bills",
  "land area",
  "estimated rent",
  "estimated rent for the land",
  "property assessment tax",
  "quit rent rate",
  "quit rent",
  "square metre",
  "monthly"
  ];

  const malayScore = malayKeywords.reduce(
    (score, keyword) => score + (text.includes(keyword) ? 1 : 0),
    0
  );

  const englishScore = englishKeywords.reduce(
    (score, keyword) => score + (text.includes(keyword) ? 1 : 0),
    0
  );

  if (malayScore > englishScore) return "ms";
  if (englishScore > malayScore) return "en";

  return "unknown";
};

const filterBilingualTableRows = (rows) => {
  if (!Array.isArray(rows) || rows.length <= 1) return rows;

  const filteredRows = [];
  let hasFiltered = false;

  for (let i = 0; i < rows.length; i += 1) {
    const currentRow = rows[i];
    const nextRow = rows[i + 1];

    if (nextRow) {
      const currentLang = detectTableRowLanguage(currentRow);
      const nextLang = detectTableRowLanguage(nextRow);

      const isBilingualPair =
        (currentLang === "ms" && nextLang === "en") ||
        (currentLang === "en" && nextLang === "ms");

      if (isBilingualPair) {
        filteredRows.push(
          isEnglish
            ? currentLang === "en"
              ? currentRow
              : nextRow
            : currentLang === "ms"
            ? currentRow
            : nextRow
        );

        hasFiltered = true;
        i += 1; // skip the paired row
        continue;
      }
    }

    filteredRows.push(currentRow);
  }

  return hasFiltered ? filteredRows : rows;
};
const buildStagesFromReviewVariant = (variant) => {
  const question = variant?.question || {};
  const markingScheme = variant?.marking_scheme || {};

  const rawStages =
    Array.isArray(question.stages) && question.stages.length > 0
      ? question.stages
      : [
          {
            stage_index: 1,
            ...question,
          },
        ];

  const builtReviewStages = rawStages.map((stageQuestion, index) => {
    const stageIndex = Number(stageQuestion.stage_index || index + 1);

    const schemeStage =
      markingScheme?.stages?.find(
        (stage) => Number(stage?.stage_index || 1) === stageIndex
      ) ||
      markingScheme?.stages?.[index] ||
      markingScheme ||
      {};

    const rawSubQuestions =
      Array.isArray(stageQuestion.questions) && stageQuestion.questions.length > 0
        ? stageQuestion.questions
        : Array.isArray(stageQuestion.subparts) && stageQuestion.subparts.length > 0
        ? stageQuestion.subparts
        : [stageQuestion];

    const normalizeLineKey = (line) =>
      String(line || "")
        .replace(/\s+/g, " ")
        .trim()
        .toLowerCase();
    const normalizeTableTextKey = (line) =>
      String(line || "")
        .replace(/\s+/g, " ")
        .replace(/\s*:\s*/g, ":")
        .trim()
        .toLowerCase();

    const getTableLineKeys = (tableData) => {
      const keys = new Set();

      if (!tableData || typeof tableData !== "object") return keys;

      Object.values(tableData).forEach((rows) => {
        if (!Array.isArray(rows)) return;

        rows.forEach((row) => {
          const cells = Array.isArray(row) ? row : [row];

          keys.add(normalizeTableTextKey(cells.join(" ")));
          keys.add(normalizeTableTextKey(cells.join("")));
        });
      });

      return keys;
    };

    const removeInstructionLinesAlreadyInTable = (lines, tableData) => {
      const tableKeys = getTableLineKeys(tableData);

      if (!tableKeys.size) return lines;

      return lines.filter((line) => {
        const key = normalizeTableTextKey(line);
        return !tableKeys.has(key);
      });
    };
    const allSubInstructionKeysEn = new Set(
      rawSubQuestions.flatMap((q) =>
        Array.isArray(q.instructions_en)
          ? q.instructions_en.map(normalizeLineKey)
          : []
      )
    );

    const allSubInstructionKeysMs = new Set(
      rawSubQuestions.flatMap((q) =>
        Array.isArray(q.instructions_ms)
          ? q.instructions_ms.map(normalizeLineKey)
          : []
      )
    );

    const rawStageIntroEn = Array.isArray(stageQuestion.instructions_en)
      ? stageQuestion.instructions_en
      : [];

    const rawStageIntroMs = Array.isArray(stageQuestion.instructions_ms)
      ? stageQuestion.instructions_ms
      : [];

    // Remove parent lines that are actually subpart commands.
    const stageIntroEn = rawStageIntroEn.filter(
      (line) => !allSubInstructionKeysEn.has(normalizeLineKey(line))
    );

    const stageIntroMs = rawStageIntroMs.filter(
      (line) => !allSubInstructionKeysMs.has(normalizeLineKey(line))
    );

    const mergeUniqueLines = (mainLines, subLines) => {
      const seen = new Set();

      return [...mainLines, ...subLines].filter((line) => {
        const key = normalizeLineKey(line);

        if (!key || seen.has(key)) return false;

        seen.add(key);
        return true;
      });
    };

    const reviewRows = rawSubQuestions.map((subQ, subIndex) => {
      const subInstructionsEn = Array.isArray(subQ.instructions_en)
        ? subQ.instructions_en
        : [];

      const subInstructionsMs = Array.isArray(subQ.instructions_ms)
        ? subQ.instructions_ms
        : [];

      let mergedInstructionsEn = mergeUniqueLines(stageIntroEn, subInstructionsEn);
      let mergedInstructionsMs = mergeUniqueLines(stageIntroMs, subInstructionsMs);
      
      const hasNonEmptyObject = (value) => {
        return (
          value &&
          typeof value === "object" &&
          !Array.isArray(value) &&
          Object.keys(value).length > 0
        );
      };

      const subSequence = Array.isArray(subQ.sequence) ? subQ.sequence : [];

      const subReferencesImage = subSequence.some((item) =>
        String(item).startsWith("image_")
      );

      const subReferencesTable = subSequence.some((item) =>
        String(item).startsWith("table_")
      );
      const stageSequence = Array.isArray(stageQuestion.sequence)
        ? stageQuestion.sequence
        : [];

      const stageReferencesTable = stageSequence.some((item) =>
        String(item).startsWith("table_")
      );
      const subImageUrls = Array.isArray(subQ.image_urls)
        ? subQ.image_urls.filter(Boolean)
        : [];

      const stageImageUrls = Array.isArray(stageQuestion.image_urls)
        ? stageQuestion.image_urls.filter(Boolean)
        : [];

      const inheritedImagePath =
        subQ.image_path ||
        subImageUrls[0] ||
        (subReferencesImage
          ? stageQuestion.image_path || stageImageUrls[0] || ""
          : "");

      const inheritedTableData = hasNonEmptyObject(subQ.table_data)
        ? subQ.table_data
        : (subReferencesTable || stageReferencesTable) &&
          hasNonEmptyObject(stageQuestion.table_data)
        ? stageQuestion.table_data
        : {};
      mergedInstructionsEn = removeInstructionLinesAlreadyInTable(
        mergedInstructionsEn,
        inheritedTableData
      );

      mergedInstructionsMs = removeInstructionLinesAlreadyInTable(
        mergedInstructionsMs,
        inheritedTableData
      );
      const inheritedGivenValues = {
        ...(hasNonEmptyObject(stageQuestion.given_values)
          ? stageQuestion.given_values
          : {}),
        ...(hasNonEmptyObject(subQ.given_values)
          ? subQ.given_values
          : {}),
      };

      const inheritedHasDiagram =
        subQ.has_diagram ||
        (inheritedImagePath ? 1 : 0) ||
        (hasNonEmptyObject(inheritedTableData) ? 1 : 0);

      const inheritedDiagramType =
        subQ.diagram_type ||
        stageQuestion.diagram_type ||
        "";

      let rawMergedSequence =
        Array.isArray(subQ.sequence) && subQ.sequence.length > 0
          ? [...subQ.sequence]
          : stageQuestion.sequence || [];

      // If parent stage has a shared table but subquestion sequence forgot table_0,
      // insert table_0 after text_0 so it can render.
      if (
        stageReferencesTable &&
        hasNonEmptyObject(inheritedTableData) &&
        !rawMergedSequence.some((item) => String(item).startsWith("table_"))
      ) {
        const text0Index = rawMergedSequence.indexOf("text_0");

        if (text0Index >= 0) {
          rawMergedSequence.splice(text0Index + 1, 0, "table_0");
        } else {
          rawMergedSequence.unshift("table_0");
        }
      }

      const mergedSequence = rawMergedSequence.filter((item) => {
        const itemText = String(item);

        if (itemText.startsWith("table_") && !hasNonEmptyObject(inheritedTableData)) {
          return false;
        }

        if (itemText.startsWith("image_") && !inheritedImagePath) {
          return false;
        }

        return true;
      });

      const mergedQuestion = {
        ...stageQuestion,
        ...subQ,
        instructions_en: mergedInstructionsEn,
        instructions_ms: mergedInstructionsMs,
        image_path: inheritedImagePath,
        table_data: inheritedTableData,
        given_values: inheritedGivenValues,
        has_diagram: inheritedHasDiagram,
        diagram_type: inheritedDiagramType,
        sequence: mergedSequence,
      };

      return {
        id: subQ.id || subQ.question_id || subQ.original_question_id || null,
        question_id: subQ.question_id || subQ.id || subQ.original_question_id || null,
        original_question_id:
          subQ.original_question_id || subQ.question_id || subQ.id || null,

        exercise_stage_id:
          subQ.exercise_stage_id ||
          subQ.original_exercise_stage_id ||
          stageQuestion?.exercise_stage_id ||
          "",

        original_exercise_stage_id:
          subQ.original_exercise_stage_id ||
          subQ.exercise_stage_id ||
          stageQuestion?.original_exercise_stage_id ||
          stageQuestion?.exercise_stage_id ||
          "",

        is_review_variant: true,
        review_variant_id: variant.variant_id,
        variant_stage_index: stageIndex,

        question_no: "Review",

        part: subQ.part ?? "",
        subpart: subQ.subpart ?? "",
        sub_subpart: subQ.sub_subpart ?? "",

        instructions_en: mergedInstructionsEn,
        instructions_ms: mergedInstructionsMs,
        sequence: normalizeQuestionSequence(mergedQuestion),

        table_data: inheritedTableData,
        given_values: inheritedGivenValues,

        has_diagram: inheritedHasDiagram,
        diagram_type: inheritedDiagramType,
        image_path: inheritedImagePath,
        image_urls: inheritedImagePath ? [inheritedImagePath] : [],

        display_marks:
          subQ.display_marks ||
          subQ.marks ||
          schemeStage?.questions?.[subIndex]?.max_score ||
          schemeStage?.subparts?.[subIndex]?.max_score ||
          1,

        difficulty:
          currentStage?.difficulty ||
          displayedDifficulty ||
          "Moderate",

        difficulty_level:
          currentStage?.difficulty_level ||
          currentQuestion?.difficulty_level ||
          3,
      };
    });

    const originalExerciseStageId =
      stageQuestion?.original_exercise_stage_id ||
      stageQuestion?.exercise_stage_id ||
      reviewRows?.[0]?.original_exercise_stage_id ||
      reviewRows?.[0]?.exercise_stage_id ||
      "";

    return {
      exercise_stage_id: `review_${variant.variant_id}_S${stageIndex}`,
      original_exercise_stage_id: originalExerciseStageId,

      stage_index: stageIndex,
      group_id:
        variant.source_mode === "group"
          ? `review_group_${variant.variant_id}`
          : null,
      source_group_id: variant.source_group_id || null,

      question_no: "Review",
      difficulty: currentStage?.difficulty || displayedDifficulty || "Moderate",
      difficulty_level:
        currentStage?.difficulty_level || currentQuestion?.difficulty_level || 3,

      questions: buildDisplayLabelsForStageQuestions(reviewRows),
    };
  });
  return variant.source_mode === "group"
    ? applyContinuousGroupPartLabels(builtReviewStages)
    : builtReviewStages;
};

  // ==================================================
  // AI DB GRADER INTEGRATION
  // ==================================================
  const handleSubmitMarking = async () => {
    if (!selectedFile) return;
    if (isSubmittingRef.current) return;

    isSubmittingRef.current = true;
    setIsSubmitting(true);
    setFeedback(null);

    logUserActivity("practiced_kertas2");

    const fileToBase64 = (file) => {
      return new Promise((resolve, reject) => {
        const reader = new FileReader();

        reader.onloadend = () => {
          resolve(reader.result);
        };

        reader.onerror = () => {
          reject(new Error("Failed to read selected image."));
        };

        reader.readAsDataURL(file);
      });
    };

    try {
      const base64data = await fileToBase64(selectedFile);

      const useKnownStageGrader =
        currentVariant && isOriginalGroupRetryVariant();

      const gradeUrl = useKnownStageGrader
        ? `${process.env.REACT_APP_API_BASE_URL}/api/ai/grade-known-stage`
        : currentVariant
        ? `${process.env.REACT_APP_API_BASE_URL}/api/review/grade-variant`
        : `${process.env.REACT_APP_API_BASE_URL}/api/ai/grade-known-stage`;

      const gradeBody = useKnownStageGrader
        ? {
            student_image: base64data,
            exercise_stage_id: getOriginalExerciseStageIdForReview(),
            question_ids: getOriginalQuestionIdsForReview(),
            language: language,
          }
        : currentVariant
        ? {
            student_image: base64data,
            variant_id: currentVariant.variant_id,
            variant_stage_index: Number(
              currentQuestion?.variant_stage_index ||
                currentStage?.stage_index ||
                currentIndex + 1
            ),
            is_variant_final_stage:
              currentIndex >= questionStages.length - 1 ? 1 : 0,
            language: language,
          }
        : {
            student_image: base64data,
            exercise_stage_id: currentStage.exercise_stage_id,
            question_ids: getCurrentQuestionIds(),
            language: language,
          };

      const response = await apiFetch(gradeUrl, {
        method: "POST",
        body: JSON.stringify(gradeBody),
      });

      const data = await response.json();
      const timeTaken = Math.floor((Date.now() - startTime) / 1000);

      if (!response.ok || !data.success) {
        console.error("Grading failed:", data.message || data);

        setFeedback({
          status: "wrong",
          explanation:
            data.message ||
            "Sorry, an error occurred while grading. Please try again.",
        });

        return;
      }

      setTotalAttempted((prev) => prev + 1);

      const toNumber = (value, fallback = 0) => {
        const n = Number(value);
        return Number.isFinite(n) ? n : fallback;
      };

      const getScoreInfoFromResult = (result) => {
        const evaluations = result?.stepwise_evaluation || [];

        const scoreFromSteps = evaluations.reduce(
          (sum, step) => sum + toNumber(step.marks_awarded, 0),
          0
        );

        const maxFromSteps = evaluations.reduce(
          (sum, step) => sum + toNumber(step.max_marks, 0),
          0
        );

        const score =
          result?.score !== undefined && result?.score !== null
            ? toNumber(result.score, scoreFromSteps)
            : scoreFromSteps;

        const maxScore =
          result?.max_score !== undefined && result?.max_score !== null
            ? toNumber(result.max_score, maxFromSteps)
            : result?.maxScore !== undefined && result?.maxScore !== null
            ? toNumber(result.maxScore, maxFromSteps)
            : maxFromSteps;

        return {
          score,
          maxScore,
        };
      };

      const result = data.result || {};
      const { score, maxScore } = getScoreInfoFromResult(result);

      const isFullMark = maxScore > 0 && score >= maxScore;
      const markingStatus = getMarkingStatus(score, maxScore);

      let officialSolution = null;

          // 2. Update score/streak
          updateGroupStageScore({
            score,
            maxScore,
            isFullMark,
            answerRevealed: 0,
          });

      if (isFullMark) {
        const newStreak = streak + 1;
        setStreak(newStreak);
        setCorrectAnswers((prev) => prev + 1);

        if (newStreak > highestStreak) {
          setHighestStreak(newStreak);
        }
      } else {
        setStreak(0);
      }

      if (markingStatus !== "correct") {
        if (currentVariant) {
          const variantStageIndex = Number(
            currentQuestion?.variant_stage_index ||
              currentStage?.stage_index ||
              currentIndex + 1
          );

          const variantStageScheme =
            currentVariant?.marking_scheme?.stages?.find(
              (stage) => Number(stage?.stage_index || 1) === variantStageIndex
            );

          officialSolution = {
            steps:
              variantStageScheme?.steps ||
              currentVariant?.marking_scheme?.steps ||
              [],
            final_answer:
              variantStageScheme?.final_answer ||
              currentVariant?.marking_scheme?.final_answer ||
              "",
            final_answers:
              variantStageScheme?.final_answers ||
              currentVariant?.marking_scheme?.final_answers ||
              {},
          };
        } else {
          officialSolution = await fetchOfficialSolutionForCurrentStage();

          officialSolution = filterOfficialSolutionForDeductedMarks(
            officialSolution,
            data.result
          );
        }
      }

      const attemptRecord = buildAttemptRecord({
        isCorrect: isFullMark,
        score,
        maxScore,
        answerRevealed: 0,
        timeTaken,
      });

      setAttemptsLog((prev) => [...prev, attemptRecord]);

      try {
        const saveData = await saveSingleAttempt(attemptRecord);
        console.log("SAVE ATTEMPT RESULT:", saveData);
      } catch (error) {
        console.error("Failed to save K2 attempt:", error);
      }

      setFeedback({
        status: markingStatus,
        explanation: {
          ...(data.result || {}),
          official_solution: officialSolution,
        },
      });
    } catch (error) {
      console.error("Submission failed:", error);

      setFeedback({
        status: "wrong",
        explanation:
          "Sorry, an error occurred while grading. Please try again.",
      });
    } finally {
      isSubmittingRef.current = false;
      setIsSubmitting(false);
    }
};
  const getCurrentMaxScore = () => {
    if (currentVariant) {
      const variantStageIndex = Number(
        currentQuestion?.variant_stage_index ||
        currentStage?.stage_index ||
        currentIndex + 1
      );

      const variantStageScheme = currentVariant?.marking_scheme?.stages?.find(
        (stage) => Number(stage?.stage_index || 1) === variantStageIndex
      );

      return (
        Number(variantStageScheme?.max_score || 0) ||
        Number(currentVariant?.marking_scheme?.max_score || 0) ||
        Number(currentQuestion?.display_marks || 0) ||
        0
      );
    }

    return (currentQuestions || []).reduce((sum, q) => {
      return sum + Number(q?.display_marks || q?.marks || 0);
    }, 0);
  };
  const handleShowDatabaseAnswer = async () => {
     if (isFetchingAnswerRef.current) return;

    isFetchingAnswerRef.current = true;
    setIsFetchingAnswer(true);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }

    if (cameraInputRef.current) {
      cameraInputRef.current.value = "";
    }
    try {
      const timeTaken = Math.floor((Date.now() - startTime) / 1000);
      const maxScore = getCurrentMaxScore();

      const clearAnswerUploadUi = () => {
        setSelectedFile(null);
        setSelectedImage(null);
        setAnswerRevealed(true);

        if (fileInputRef.current) {
          fileInputRef.current.value = "";
        }

        if (cameraInputRef.current) {
          cameraInputRef.current.value = "";
        }
      };

      // ==================================================
      // CASE 1: Review variant
      // Do NOT call /api/ai/explain-known
      // ==================================================
      if (currentVariant) {
        const attemptRecord = buildAttemptRecord({
          isCorrect: false,
          score: 0,
          maxScore,
          answerRevealed: 1,
          timeTaken,
        });

        setTotalAttempted((prev) => prev + 1);
        setStreak(0);
        setAttemptsLog((prev) => [...prev, attemptRecord]);

        try {
          await saveSingleAttempt(attemptRecord);
        } catch (error) {
          console.error("Failed to save stuck variant attempt:", error);
        }

        updateGroupStageScore({
          score: 0,
          maxScore,
          isFullMark: false,
          answerRevealed: 1,
        });

        clearAnswerUploadUi();

        // OPTION B:
        // If this review variant is actually the original group question,
        // call the normal DB explanation endpoint using original DB IDs.
        if (isOriginalGroupRetryVariant()) {
          const originalExerciseStageId = getOriginalExerciseStageIdForReview();
          const originalQuestionIds = getOriginalQuestionIdsForReview();
          const stageImageUrls = getStageImageUrls(currentQuestions);

          if (originalExerciseStageId) {
            const response = await apiFetch(
              `${process.env.REACT_APP_API_BASE_URL}/api/ai/explain-known`,
              {
                method: "POST",
                body: JSON.stringify({
                  exercise_stage_id: originalExerciseStageId,
                  question_ids: originalQuestionIds,
                  question_images: stageImageUrls,
                  language: language,
                }),
              }
            );

            const data = await response.json();

            if (response.ok && data.success) {
              setFeedback({
                status: "solution",
                explanation: data.result,
              });

              return;
            }

            console.error("Failed to fetch original retry explanation:", data);
          }
        }

        // Fallback for normal generated variants
        const variantStageIndex = Number(
          currentQuestion?.variant_stage_index ||
          currentStage?.stage_index ||
          currentIndex + 1
        );

        const variantStageScheme = currentVariant?.marking_scheme?.stages?.find(
          (stage) => Number(stage?.stage_index || 1) === variantStageIndex
        );

        const solutionSteps =
          variantStageScheme?.steps ||
          currentVariant?.marking_scheme?.steps ||
          [];

        const finalAnswer =
          variantStageScheme?.final_answer ||
          currentVariant?.marking_scheme?.final_answer ||
          "";

        const finalAnswers = pickFinalAnswerSource(
          variantStageScheme?.final_answers,
          currentVariant?.marking_scheme?.final_answers,
          currentVariant?.marking_scheme?.final_answer_by_part
        );

        setFeedback({
          status: "solution",
          explanation: {
            steps: solutionSteps,
            final_answer: finalAnswer,
            final_answers: finalAnswers,
            final_answer_by_part: finalAnswers,
            answer_revealed: 1,
          },
        });

        return;
      }

      // ==================================================
      // CASE 2: Original DB question
      // Call /api/ai/explain-known
      // ==================================================
      const stageImageUrls = getStageImageUrls(currentQuestions);

      const response = await apiFetch(
        `${process.env.REACT_APP_API_BASE_URL}/api/ai/explain-known`,
        {
          method: "POST",
          body: JSON.stringify({
            exercise_stage_id: currentStage.exercise_stage_id,
            question_ids: getCurrentQuestionIds(),
            question_images: stageImageUrls,
            language: language,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok || !data.success) {
        console.error("Failed to fetch answer:", data.message || data);

        setFeedback({
          status: "wrong",
          explanation:
            data.message ||
            (isEnglish
              ? "Sorry, the answer explanation could not be loaded."
              : "Maaf, penerangan jawapan tidak dapat dimuatkan."),
        });

        return;
      }

      const attemptRecord = buildAttemptRecord({
        isCorrect: false,
        score: 0,
        maxScore,
        answerRevealed: 1,
        timeTaken,
      });

      setTotalAttempted((prev) => prev + 1);
      setStreak(0);
      setAttemptsLog((prev) => [...prev, attemptRecord]);

      let saveData = null;

      try {
        saveData = await saveSingleAttempt(attemptRecord);
      } catch (error) {
        console.error("Failed to save show-answer attempt:", error);
      }

      updateGroupStageScore({
        score: 0,
        maxScore,
        isFullMark: false,
        answerRevealed: 1,
      });

      clearAnswerUploadUi();

      setFeedback({
        status: "solution",
        explanation: data.result,
      });
    } catch (error) {
      console.error("Error fetching answer:", error);

      setFeedback({
        status: "wrong",
        explanation: isEnglish
          ? "Sorry, an error occurred while loading the answer."
          : "Maaf, ralat berlaku semasa memuatkan jawapan.",
      });
    } finally {
      isFetchingAnswerRef.current = false;
      setIsFetchingAnswer(false);
    }
  };
  const handleNextQuestion = async () => {
    // If current returned item has multiple stages, finish those stages first.
    if (currentIndex < questionStages.length - 1) {
      setCurrentIndex((prev) => prev + 1);
      resetQuestionUi();
      return;
    }

    // After current normal/review item is fully completed,
    // ask backend what should come next.
    await fetchNextK2Item();
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

  const getEffectiveDifficultyLevel = () => {
    const level = Number(
      currentStage?.difficulty_level ||
      currentQuestion?.group_difficulty_level ||
      currentQuestion?.adaptive_difficulty_level ||
      currentQuestion?.difficulty_level ||
      3
    );

    return Number.isFinite(level) ? level : 3;
  };

  const displayedDifficulty = difficultyFromLevel(getEffectiveDifficultyLevel());
  const sharedIntroCount = getSharedIntroCount(currentQuestions);

  const sharedSequenceInfo =
    sharedIntroCount > 0
      ? getSharedSequenceInfo(currentQuestions[0], sharedIntroCount)
      : {
          sharedTextIndexes: new Set(),
          sharedTableIndexes: new Set(),
          sharedImageIndexes: new Set(),
          sharedSequenceItems: [],
        };

  const hasSharedStageContext = sharedSequenceInfo.sharedSequenceItems.length > 0;
  const diffColors =
    displayedDifficulty === "Easy"
      ? { bg: "#D1FAE5", text: "#065F46" }
      : displayedDifficulty === "Medium" || displayedDifficulty === "Moderate"
      ? { bg: "#FEF3C7", text: "#92400E" }
      : { bg: "#FEE2E2", text: "#991B1B" };

  const getAnswerImages = (explanation) => {
    if (!explanation) return [];

    let images =
      explanation.answer_images ||
      explanation.answer_image_paths ||
      explanation.answer_image_path ||
      [];

    if (typeof images === "string") {
      const parsed = safeJson(images, null);

      if (Array.isArray(parsed)) {
        images = parsed;
      } else {
        images = [{ url: images, title: "Official answer diagram" }];
      }
    }

    if (!Array.isArray(images)) {
      images = [images];
    }

    return images
      .map((img, index) => {
        if (typeof img === "string") {
          return {
            url: img,
            title: `Official answer diagram ${index + 1}`,
          };
        }

        return {
          url: img.url || img.answer_image_path || img.image_path,
          title: img.title || `Official answer diagram ${index + 1}`,
          subpart: img.subpart || img.display_subpart_label || "",
          display_subpart_label: img.display_subpart_label || img.subpart || "",
          original_subpart_label: img.original_subpart_label || "",
        };
      })
      .filter((img) => img.url);
  };
  const renderGroupScoreSummary = () => {
    const summary = getCurrentGroupScoreSummary();

    if (!summary || summary.stages.length <= 1) {
      return null;
    }

    return (
      <Paper
        elevation={0}
        sx={{
          p: 2.5,
          mb: 3,
          borderRadius: "16px",
          border: "1px solid #E5E7EB",
          bgcolor: "#FFFFFF",
        }}
      >
        <Typography variant="subtitle2" fontWeight="900" color="#111827" mb={1}>
          {isEnglish ? "Question Group Score Summary" : "Ringkasan Markah Kumpulan Soalan"}
        </Typography>

        <Typography variant="body2" color="#6B7280" mb={2}>
          {isEnglish
            ? `Question ${summary.question_no || ""} attempted stages so far`
            : `Soalan ${summary.question_no || ""} peringkat yang telah dijawab`}
        </Typography>

        {summary.stages.map((stage) => (
          <Box
            key={stage.exercise_stage_id}
            sx={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              py: 1,
              borderBottom: "1px dashed #E5E7EB",
            }}
          >
            <Typography variant="body2" fontWeight="bold" color="#374151">
              Stage {stage.stage_index}
            </Typography>

            <Chip
              size="small"
              label={`${stage.score} / ${stage.max_score}`}
              sx={{
                fontWeight: "bold",
                bgcolor: stage.is_correct ? "#D1FAE5" : "#FEE2E2",
                color: stage.is_correct ? "#065F46" : "#991B1B",
              }}
            />
          </Box>
        ))}

        <Box
          sx={{
            mt: 2,
            p: 1.5,
            borderRadius: "12px",
            bgcolor: summary.isGroupFullMark ? "#ECFDF5" : "#FEF3C7",
            border: `1px solid ${summary.isGroupFullMark ? "#A7F3D0" : "#FCD34D"}`,
          }}
        >
          <Typography
            variant="body1"
            fontWeight="900"
            color={summary.isGroupFullMark ? "#065F46" : "#92400E"}
          >
            {isEnglish ? "Total" : "Jumlah"}: {summary.totalScore} / {summary.totalMax}
          </Typography>

          <Typography variant="caption" color={summary.isGroupFullMark ? "#047857" : "#92400E"}>
            {summary.isGroupFullMark
              ? isEnglish
                ? "Full marks for this question group."
                : "Markah penuh untuk kumpulan soalan ini."
              : isEnglish
              ? "This group is not fully correct because at least one stage has mark deduction."
              : "Kumpulan ini belum sepenuhnya betul kerana sekurang-kurangnya satu peringkat ditolak markah."}
          </Typography>
        </Box>
      </Paper>
    );
  };
  const getAnswerImagesForStep = (explanation, step, idx) => {
    const images = getAnswerImages(explanation);

    if (!images.length) return [];

    const stepLabel = buildStepDisplayLabel(step, idx);
    const stepKey = normalizeAnswerKey(stepLabel);

    return images.filter((img) => {
      const imgLabel =
        img.display_subpart_label ||
        img.subpart ||
        img.original_subpart_label ||
        "";

      const imgKey = normalizeAnswerKey(imgLabel);

      // If the answer image has no label, show it under the first step only.
      if (!imgKey) {
        return idx === 0;
      }

      return imgKey === stepKey;
    });
  };

  const renderAnswerImageCards = (images, showTitle = false) => {
    if (!images || images.length === 0) return null;

    return (
      <Box sx={{ mt: 1.5 }}>
        {showTitle && (
          <Typography
            variant="subtitle2"
            fontWeight="bold"
            color="#1E40AF"
            mb={1.5}
          >
            {isEnglish ? "Official Answer Diagram" : "Rajah Jawapan Rasmi"}
          </Typography>
        )}

        {images.map((img, index) => (
          <Paper
            key={`${img.url}-${index}`}
            elevation={0}
            sx={{
              p: 2,
              mt: 1.5,
              mb: 1,
              border: "1px solid #BFDBFE",
              borderRadius: "12px",
              bgcolor: "#FFFFFF",
            }}
          >
            <Typography variant="body2" fontWeight="bold" color="#374151" mb={1}>
              {img.subpart ? `${img.subpart} - ` : ""}
              {img.title}
            </Typography>

            <Box sx={{ display: "flex", justifyContent: "center" }}>
              <img
                src={img.url}
                alt={img.title}
                style={{
                  maxWidth: "100%",
                  maxHeight: "420px",
                  borderRadius: "8px",
                  objectFit: "contain",
                  border: "1px solid #E5E7EB",
                }}
              />
            </Box>
          </Paper>
        ))}
      </Box>
    );
  };

  const renderAnswerImagesForStep = (explanation, step, idx) => {
    const images = getAnswerImagesForStep(explanation, step, idx);
    return renderAnswerImageCards(images, false);
  };
  const renderAnswerImages = (explanation) => {
    const images = getAnswerImages(explanation);

    if (!images.length) return null;

    return (
      <Box sx={{ mt: 3 }}>
        <Typography variant="subtitle2" fontWeight="bold" color="#1E40AF" mb={1.5}>
          {isEnglish ? "Official Answer Diagram" : "Rajah Jawapan Rasmi"}
        </Typography>

        {images.map((img, index) => (
          <Paper
            key={`${img.url}-${index}`}
            elevation={0}
            sx={{
              p: 2,
              mb: 2,
              border: "1px solid #BFDBFE",
              borderRadius: "12px",
              bgcolor: "#FFFFFF",
            }}
          >
            <Typography variant="body2" fontWeight="bold" color="#374151" mb={1}>
              {img.subpart ? `${img.subpart} - ` : ""}
              {img.title}
            </Typography>

            <Box sx={{ display: "flex", justifyContent: "center" }}>
              <img
                src={img.url}
                alt={img.title}
                style={{
                  maxWidth: "100%",
                  maxHeight: "420px",
                  borderRadius: "8px",
                  objectFit: "contain",
                  border: "1px solid #E5E7EB",
                }}
              />
            </Box>
          </Paper>
        ))}
      </Box>
    );
  };
  const pickLanguageLine = (value) => {
    const textValue = String(value ?? "");

    if (!textValue.includes("\n")) {
      return textValue;
    }

    const lines = textValue
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean);

    if (lines.length === 0) return textValue;

    // Common parser output:
    // Malay first, English second
    if (lines.length === 2) {
      return isEnglish ? lines[1] : lines[0];
    }

    return isEnglish ? lines[lines.length - 1] : lines[0];
  };

  const localizeTableCell = (cell) => {
    if (Array.isArray(cell)) {
      return cell.map(localizeTableCell);
    }

    return pickLanguageLine(cell);
  };

  const normalizeTableForDisplay = (rawTableData) => {
    const tableData = safeJson(rawTableData, rawTableData);

    if (!tableData) return [];

    // Case 1:
    // { title: "Jadual 2\nTable 2", headers: [...] }
    if (
      typeof tableData === "object" &&
      !Array.isArray(tableData) &&
      (tableData.headers || tableData.rows || tableData.data)
    ) {
      return [
        {
          title: pickLanguageLine(tableData.title || ""),
          rows: (tableData.headers || tableData.rows || tableData.data || []).map((row) =>
            Array.isArray(row)
              ? row.map(localizeTableCell)
              : [localizeTableCell(row)]
          ),
        },
      ];
    }

    // Case 2:
    // { "Jadual 2\nTable 2": [[...], [...]] }
    if (typeof tableData === "object" && !Array.isArray(tableData)) {
      return Object.entries(tableData).map(([title, rows]) => ({
        title: pickLanguageLine(title),
        rows: Array.isArray(rows)
          ? filterBilingualTableRows(
              rows.map((row) =>
                Array.isArray(row)
                  ? row.map(localizeTableCell)
                  : [localizeTableCell(row)]
              )
            )
          : [],
      }));
    }

  // Case 3:
  // [[...], [...]]
  if (Array.isArray(tableData)) {
    return [
      {
        title: "",
        rows: filterBilingualTableRows(
          tableData.map((row) =>
            Array.isArray(row)
              ? row.map(localizeTableCell)
              : [localizeTableCell(row)]
          )
        ),
      },
    ];
  }

  return [];
};
  const renderTable = (tableTitle, tableRows, key) => {
    if (!Array.isArray(tableRows)) return null;

    return (
      <Box key={key} sx={{ my: 3, overflowX: "auto" }}>
        {tableTitle && (
          <Typography variant="subtitle2" fontWeight="bold" sx={{ mb: 1 }}>
            {tableTitle}
          </Typography>
        )}

        <Box
          component="table"
          sx={{
            width: "100%",
            borderCollapse: "collapse",
            bgcolor: "white",
            "& td, & th": {
              border: "1px solid #D1D5DB",
              p: 1.2,
              textAlign: "center",
              fontSize: "14px",
            },
            "& tr:first-of-type td": {
              fontWeight: "bold",
              bgcolor: "#F3F4F6",
            },
          }}
        >
          <tbody>
            {tableRows.map((row, rowIndex) => (
              <tr key={rowIndex}>
                {(Array.isArray(row) ? row : [row]).map((cell, cellIndex) => (
                  <td key={cellIndex}>{cell}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </Box>
      </Box>
    );
  };

  const renderQuestionContent = (q, options = {}) => {
    const hiddenTextIndexes = options.hiddenTextIndexes || new Set();
    const hiddenTableIndexes = options.hiddenTableIndexes || new Set();
    const hiddenImageIndexes = options.hiddenImageIndexes || new Set();
    const onlySequenceItems = options.onlySequenceItems || null;
    const sequence = safeJson(q.sequence, []);
    const instructionsEn = safeJson(q.instructions_en, []);
    const instructionsMs = safeJson(q.instructions_ms, []);
    const tableData = safeJson(q.table_data, {});

    const instructions = isEnglish ? instructionsEn : instructionsMs;
    const tableEntries = normalizeTableForDisplay(tableData);

    if (!sequence || sequence.length === 0) {
      return instructions.map((line, index) => (
        <Typography
          key={index}
          variant="h6"
          fontWeight="500"
          color="#111827"
          sx={{ lineHeight: 1.6, whiteSpace: "pre-line", mb: 2 }}
        >
          {renderInlineMath(line)}
        </Typography>
      ));
    }

    return sequence.map((item, index) => {
        if (onlySequenceItems && !onlySequenceItems.has(item)) {
          return null;
        }
      if (item.startsWith("text_")) {
        const textIndex = parseInt(item.split("_")[1], 10);
        if (hiddenTextIndexes.has(textIndex)) return null;
        const textContent = instructions[textIndex] || "";

        if (!textContent) return null;

        return (
          <Typography
            key={index}
            variant="h6"
            fontWeight="500"
            color="#111827"
            sx={{ lineHeight: 1.6, whiteSpace: "pre-line", mb: 2 }}
          >
            {renderInlineMath(textContent)}
          </Typography>
        );
      }

      if (item.startsWith("table_")) {
        const tableIndex = parseInt(item.split("_")[1], 10);
        if (hiddenTableIndexes.has(tableIndex)) return null;
        const tableEntry = tableEntries[tableIndex];

        if (!tableEntry) return null;

        return renderTable(tableEntry.title, tableEntry.rows, index);
      }

      if (item.startsWith("image_")) {
        const imageIndex = parseInt(item.split("_")[1], 10);
        if (hiddenImageIndexes.has(imageIndex)) return null;

        const imgUrl =
          q.image_urls?.[imageIndex] ||
          q.image_path ||
          q.image_url ||
          q._diagram_image_path ||
          null;

        if (!imgUrl) return null;

        return (
          <Box
            key={index}
            sx={{ mt: 2, mb: 3, display: "flex", justifyContent: "center" }}
          >
            <img
              src={imgUrl}
              alt={`Question Diagram ${imageIndex + 1}`}
              style={{
                maxWidth: "100%",
                maxHeight: "400px",
                borderRadius: "8px",
                objectFit: "contain",
              }}
            />
          </Box>
        );
      }

      return null;
    });
  };

  return (
    <Box sx={{ minHeight: "100vh", bgcolor: "#f9fbfd", pb: 6 }}>
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
        <Box sx={{ display: "flex", alignItems: "center", gap: 1, minWidth: 0, flex: 1 }}>
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

        <Box sx={{ display: "flex", gap: 1, alignItems: "center", flexShrink: 0 }}>
          <Chip
            icon={<AutoGraphIcon style={{ color: diffColors.text, fontSize: "15px" }} />}
            label={difficultyLabel(displayedDifficulty)}
            sx={{
              bgcolor: diffColors.bg,
              color: diffColors.text,
              fontWeight: "bold",
              borderRadius: "8px",
              height: 36,
              "& .MuiChip-label": { px: 1, fontSize: "12px" },
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
              "& .MuiChip-label": { px: 1, fontSize: "12px" },
            }}
          />
        </Box>
      </Box>

      <Container maxWidth="md" sx={{ mt: 5 }}>
        
        {/* Main Question Display & Upload Area */}
        {isLoading ? (
          <Box sx={{ display: "flex", justifyContent: "center", alignItems: "center", height: "300px" }}>
            <CircularProgress />
          </Box>
        ) : !currentQuestion ? (
          <Box sx={{ textAlign: "center", mt: 8, mb: 8 }}>
            <Typography variant="h5" color="textSecondary" mb={2}>
              {text.noQuestions}
            </Typography>
            <Button variant="contained" onClick={() => navigate('/practice')} sx={{ bgcolor: "#3855c0", borderRadius: "10px" }}>
              {text.goBack}
            </Button>
          </Box>
        ) : (
          <>
            <Paper
              elevation={0}
              sx={{
                p: { xs: 3, md: 5 },
                borderRadius: "20px",
                border: "1px solid #E5E7EB",
                mb: 4,
                bgcolor: "white",
              }}
            >
              <Box
                sx={{
                  mb: 3,
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  gap: 2,
                  flexWrap: "wrap",
                }}
              >
                <Typography variant="h5" fontWeight="900" color="#111827">
                  Question {displayQuestionNo || currentQuestion?.question_no}
                </Typography>
              </Box>

              {hasSharedStageContext && (
                <Box
                  sx={{
                    mb: 4,
                    pb: 3,
                    borderBottom: "1px solid #E5E7EB",
                  }}
                >
                  {renderQuestionContent(currentQuestions[0], {
                    onlySequenceItems: new Set(sharedSequenceInfo.sharedSequenceItems),
                  })}
                </Box>
              )}

              {/* Subparts shown below without repeated shared intro */}
              {currentQuestions.map((q, index) => {
                const partLabel = getDisplayPartLabel(q, index);

                return (
                  <Box key={q.id || q.question_id || index} sx={{ mb: 3 }}>
                    {partLabel && (
                      <Typography
                        variant="subtitle1"
                        fontWeight="900"
                        color="#3855c0"
                        sx={{ mb: 1 }}
                      >
                        Part {partLabel}
                      </Typography>
                    )}

                    {renderQuestionContent(q, {
                      hiddenTextIndexes: sharedSequenceInfo.sharedTextIndexes,
                      hiddenTableIndexes: sharedSequenceInfo.sharedTableIndexes,
                      hiddenImageIndexes: sharedSequenceInfo.sharedImageIndexes,
                    })}
                  </Box>
                );
              })}
            </Paper>

            {/* Upload & Drag Drop Area */}
            {!answerRevealed && (
            <Paper
              elevation={0}
              sx={{
                p: 4,
                borderRadius: "20px",
                border: "2px dashed",
                mb: 4,
                borderColor: isDragging ? "#3855c0" : feedback ? "transparent" : "#E5E7EB",
                backgroundColor: isDragging ? "#F0F4FF" : feedback ? "transparent" : "#ffffff",
                transition: "all 0.2s ease",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                textAlign: "center",
                position: "relative",
              }}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
             >
              {!selectedImage ? (
                <>
                  <Box sx={{ p: 3, bgcolor: "#F3F4F6", borderRadius: "50%", mb: 2 }}>
                    <CloudUploadOutlinedIcon sx={{ fontSize: 40, color: "#6B7280" }} />
                  </Box>

                  <Typography variant="h6" fontWeight="bold" mb={1}>
                    {text.dragDrop}
                  </Typography>

                  <Typography variant="body2" color="textSecondary" mb={3} sx={{ maxWidth: "400px" }}>
                    {text.uploadDesc}
                  </Typography>

                  <Box sx={{ display: "flex", gap: 2, flexWrap: "wrap", justifyContent: "center" }}>
                  <Button
                    variant="contained"
                    disabled={isUploadLocked}
                    onClick={() => {
                      if (isUploadLocked || isFetchingAnswerRef.current) return;
                      fileInputRef.current.click();
                    }}
                    sx={{
                      bgcolor: "#3855c0",
                      borderRadius: "10px",
                      textTransform: "none",
                      fontWeight: "bold",
                    }}
                  >
                    {text.browse}
                  </Button>

                  <Button
                    variant="outlined"
                    disabled={isUploadLocked}
                    startIcon={<PhotoCameraOutlinedIcon />}
                    onClick={() => {
                      if (isUploadLocked || isFetchingAnswerRef.current) return;
                      cameraInputRef.current.click();
                    }}
                    sx={{
                      borderRadius: "10px",
                      textTransform: "none",
                      fontWeight: "bold",
                    }}
                  >
                    {text.camera}
                  </Button>
                </Box>

                {/* Existing file input for browsing */}
                <input
                  type="file"
                  hidden
                  ref={fileInputRef}
                  accept="image/*"
                  disabled={isUploadLocked}
                  onChange={handleFileChange}
                />

                <input
                  type="file"
                  hidden
                  ref={cameraInputRef}
                  accept="image/*"
                  capture="environment"
                  disabled={isUploadLocked}
                  onChange={handleFileChange}
                />
                </>
              ) : (
                <>
                  <Typography
                    variant="subtitle2"
                    fontWeight="bold"
                    color="textSecondary"
                    align="left"
                    width="100%"
                    mb={1}
                    textTransform="uppercase"
                  >
                    {text.yourAnswerSheet}
                  </Typography>

                  <Box
                    sx={{
                      width: "100%",
                      maxHeight: "350px",
                      overflow: "hidden",
                      borderRadius: "12px",
                      border: "1px solid #E5E7EB",
                      mb: 3,
                    }}
                  >
                    <img src={selectedImage} alt="Student working" style={{ width: "100%", height: "100%", objectFit: "cover" }} />
                  </Box>

                  {!feedback && (
                    <Box sx={{ display: "flex", gap: 2, width: "100%" }}>
                      <Button
                        variant="outlined"
                        color="error"
                        fullWidth
                        startIcon={<DeleteOutlineIcon />}
                        onClick={clearImage}
                        disabled={isSubmitting || isFetchingAnswer}
                        sx={{ borderRadius: "10px", textTransform: "none", fontWeight: "bold" }}
                      >
                        {text.remove}
                      </Button>

                      <Button
                        variant="contained"
                        fullWidth
                        startIcon={isSubmitting ? <CircularProgress size={20} color="inherit" /> : <DocumentScannerIcon />}
                        onClick={handleSubmitMarking}
                        disabled={isSubmitting || isFetchingAnswer}
                        sx={{
                          bgcolor: "#1ac089",
                          "&:hover": { bgcolor: "#159c6f" },
                          borderRadius: "10px",
                          textTransform: "none",
                          fontWeight: "bold",
                        }}
                      >
                        {isSubmitting ? text.aiMarking : text.submitBtn}
                      </Button>
                    </Box>
                  )}
                </>
              )}

              {/* Fallback Boxed Hint Button */}
              {!feedback && (
                <Box sx={{ width: "100%", display: "flex", flexDirection: "column", alignItems: "center", mt: 3 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', width: '100%', maxWidth: '300px', mb: 3 }}>
                      <Box sx={{ flex: 1, height: '1px', bgcolor: '#E5E7EB' }} />
                      <Typography variant="caption" sx={{ px: 2, color: '#9CA3AF', fontWeight: 600, textTransform: "uppercase" }}>
                        {isEnglish ? "OR" : "ATAU"}
                      </Typography>
                      <Box sx={{ flex: 1, height: '1px', bgcolor: '#E5E7EB' }} />
                  </Box>
                  
                  <Button
                    variant="outlined"
                    onClick={handleShowDatabaseAnswer}
                    disabled={isFetchingAnswer || isSubmitting || answerRevealed}
                    startIcon={isFetchingAnswer ? <CircularProgress size={16} color="inherit" /> : <LightbulbOutlinedIcon />}
                    sx={{
                      color: "#4B5563",
                      borderColor: "#D1D5DB",
                      borderWidth: "2px", 
                      backgroundColor: "#ffffff",
                      "&:hover": { 
                        borderColor: "#3855c0", 
                        color: "#3855c0", 
                        backgroundColor: "#F0F4FF",
                        borderWidth: "2px", 
                      },
                      borderRadius: "12px", 
                      textTransform: "none",
                      fontWeight: "bold",
                      px: 4,
                      py: 1.2,
                      boxShadow: "0 2px 4px rgba(0,0,0,0.02)" 
                    }}
                  >
                    {isFetchingAnswer ? "Fetching..." : `Stuck? ${text.showDbAnswerBtn}`}
                  </Button>
                  {ENABLE_TEST_SKIP && (
                    <Button
                      variant="outlined"
                      color="warning"
                      onClick={handleSkipForTesting}
                      sx={{
                        mt: 2,
                        borderRadius: "12px",
                        textTransform: "none",
                        fontWeight: "bold",
                      }}
                    >
                      Skip Question (Testing)
                    </Button>
                  )}
                </Box>
              )}
            </Paper>
            )}
          </>
        )}
      {renderFeedbackPanel()}
      </Container>
      
      {/* Dialogs & Summary */}
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
              fetchNextK2Item();
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
        PaperProps={{ sx: { borderRadius: "20px", padding: 1, maxWidth: "400px" } }}
      >
        <DialogTitle sx={{ fontWeight: "bold", color: "#111827", pb: 1 }}>{text.exitTitle}</DialogTitle>
        <DialogContent>
          <DialogContentText sx={{ color: "#4B5563" }}>{text.exitDesc}</DialogContentText>
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
          <Button onClick={() => setOpenExitDialog(false)} sx={{ color: "#6B7280", fontWeight: "bold", textTransform: "none" }}>
            {text.cancelBtn}
          </Button>
          <Button
            onClick={handleConfirmExit}
            variant="contained"
            disableElevation
            sx={{ bgcolor: "#3855c0", "&:hover": { bgcolor: "#2d4499" }, borderRadius: "10px", fontWeight: "bold", textTransform: "none" }}
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
            numberOfPieces={500}
            gravity={0.15}
            style={{ zIndex: 99999, position: "fixed", top: 0, left: 0, pointerEvents: "none" }}
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

export default PracticePageKertas2;