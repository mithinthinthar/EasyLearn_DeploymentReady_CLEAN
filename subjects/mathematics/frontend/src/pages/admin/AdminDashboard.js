import React, { useEffect, useMemo, useRef, useState } from "react";
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Divider,
  FormControl,
  InputAdornment,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Stack,
  Tab,
  Tabs,
  TextField,
  Typography,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  Autocomplete,
} from "@mui/material";
import VisibilityOutlinedIcon from "@mui/icons-material/VisibilityOutlined";
import CloseIcon from "@mui/icons-material/Close";
import DashboardOutlinedIcon from "@mui/icons-material/DashboardOutlined";
import QuizOutlinedIcon from "@mui/icons-material/QuizOutlined";
import GroupOutlinedIcon from "@mui/icons-material/GroupOutlined";
import UploadFileOutlinedIcon from "@mui/icons-material/UploadFileOutlined";
import SearchOutlinedIcon from "@mui/icons-material/SearchOutlined";
import BlockOutlinedIcon from "@mui/icons-material/BlockOutlined";
import CheckCircleOutlineOutlinedIcon from "@mui/icons-material/CheckCircleOutlineOutlined";
import DeleteOutlineOutlinedIcon from "@mui/icons-material/DeleteOutlineOutlined";
import PersonAddAltOutlinedIcon from "@mui/icons-material/PersonAddAltOutlined";
import katex from "katex";
import "katex/dist/katex.min.css";

import { apiFetch } from "../../utils/apiFetch";
import { getEasyLearnmbols } from "../../utils/mathSymbols";

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL;

const emptyOverview = {
  total_students: 0,
  total_parents: 0,
  total_questions: 0,
  total_attempts: 0,
  total_sessions: 0,
  total_chat_messages: 0,
  recent_activity: [],
  weak_topics: [],
};

const paperOptions = [
  { value: "all", label: "All Papers" },
  { value: "kertas1", label: "Kertas 1" },
  { value: "kertas2", label: "Kertas 2" },
];

const roleOptions = [
  { value: "all", label: "All Roles" },
  { value: "student", label: "Students" },
  { value: "parent", label: "Parents" },
  { value: "admin", label: "Admins" },
];

const chapterOptionsByForm = {
  Foundation: [
    "Numbers and Arithmetic",
    "Basic Algebra",
    "Measurement",
    "Geometry",
    "Statistics",
  ],
  "Form 4": [
    "F4C1: Quadratic Functions and Equations in One Variable",
    "F4C2: Number Bases",
    "F4C3: Logical Reasoning",
    "F4C4: Operations on Sets",
    "F4C5: Network in Graph Theory",
    "F4C6: Linear Inequalities in Two Variables",
    "F4C7: Graphs of Motion",
    "F4C8: Measures of Dispersion for Ungrouped Data",
    "F4C9: Probability of Combined Events",
    "F4C10: Consumer Mathematics: Financial Management",
  ],
  "Form 5": [
    "F5C1: Variation",
    "F5C2: Matrices",
    "F5C3: Consumer Mathematics: Insurance",
    "F5C4: Consumer Mathematics: Taxation",
    "F5C5: Congruency, Enlargement and Combined Transformations",
    "F5C6: Ratios and Graphs of Trigonometric Functions",
    "F5C7: Measures of Dispersion for Grouped Data",
    "F5C8: Mathematical Modeling",
  ],
};

const statusOptions = [
  { value: "all", label: "All Status" },
  { value: "active", label: "Active" },
  { value: "inactive", label: "Inactive" },
];

const AdminDashboard = () => {
  const user = JSON.parse(localStorage.getItem("user")) || {};

  const [activeTab, setActiveTab] = useState("overview");
  const [overview, setOverview] = useState(emptyOverview);
  const [questions, setQuestions] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState(null);

  const draftErrorRef = useRef(null);
  const [questionDetailOpen, setQuestionDetailOpen] = useState(false);
  const [selectedQuestionDetail, setSelectedQuestionDetail] = useState(null);
  const [selectedQuestionSchemes, setSelectedQuestionSchemes] = useState([]);
  const [questionDetailLoading, setQuestionDetailLoading] = useState(false);
  const [questionEditText, setQuestionEditText] = useState("");
  const [questionEditSaving, setQuestionEditSaving] = useState(false);
  const [questionEditErrors, setQuestionEditErrors] = useState([]);
  const [questionEditSuccess, setQuestionEditSuccess] = useState("");

  const [userDetailOpen, setUserDetailOpen] = useState(false);
  const [selectedUserDetail, setSelectedUserDetail] = useState(null);
  const [selectedUserStats, setSelectedUserStats] = useState(null);
  const [userDetailLoading, setUserDetailLoading] = useState(false);

  const [selectedPdfFile, setSelectedPdfFile] = useState(null);
  const [selectedMarkingPdfFile, setSelectedMarkingPdfFile] = useState(null);
  const [isParsingPdf, setIsParsingPdf] = useState(false);

  const [importBatches, setImportBatches] = useState([]);
  const [batchDetailOpen, setBatchDetailOpen] = useState(false);
  const [selectedBatch, setSelectedBatch] = useState(null);
  const [batchItems, setBatchItems] = useState([]);
  const [activeDraftItem, setActiveDraftItem] = useState(null);
  const [draftEditorText, setDraftEditorText] = useState("");
  const [batchLoading, setBatchLoading] = useState(false);
  const [draftSaving, setDraftSaving] = useState(false);
  const [uploadingImageItemId, setUploadingImageItemId] = useState(null);

  const [parsingStartTime, setParsingStartTime] = useState(null);
  const [parsingElapsed, setParsingElapsed] = useState(0);
  const [draftValidationErrors, setDraftValidationErrors] = useState([]);
  const [addAdminResetLink, setAddAdminResetLink] = useState("");

  const formOptions = ["Foundation", "Form 4", "Form 5"];
  const difficultyOptions = ["Easy", "Moderate", "Hard"];

  const [deleteImageDialogOpen, setDeleteImageDialogOpen] = useState(false);
  const [imageItemToDelete, setImageItemToDelete] = useState(null);

  const [addAdminOpen, setAddAdminOpen] = useState(false);
  const [addAdminSaving, setAddAdminSaving] = useState(false);
  const [addAdminForm, setAddAdminForm] = useState({
    name: "",
    email: "",
  });

  const [importMeta, setImportMeta] = useState({
    title: "",
    exam_name: "SPM Trial",
    year: new Date().getFullYear().toString(),
    question_start_page: "1",
    question_end_page: "",
    marking_start_page: "1",
    marking_end_page: "",
  });

  const [questionFilters, setQuestionFilters] = useState({
    search: "",
    paper_type: "all",
    status: "all",
    form: "all",
    difficulty: "all",
  });

  const [userFilters, setUserFilters] = useState({
    search: "",
    role: "all",
    status: "all",
  });

  const scrollToDraftErrors = () => {
    setTimeout(() => {
      draftErrorRef.current?.scrollIntoView({
        behavior: "smooth",
        block: "center",
      });
    }, 100);
  };

  const [symbolTarget, setSymbolTarget] = useState({
    type: "instruction",
    field: "instructions_en",
  });
  const [selectedImportType, setSelectedImportType] = useState("kertas1");
  const [selectedPdfName, setSelectedPdfName] = useState("");

  const [reviewVariants, setReviewVariants] = useState([]);
  const [reviewVariantFilters, setReviewVariantFilters] = useState({
    search: "",
    variant_type: "all",
  });

  const [reviewVariantDetailOpen, setReviewVariantDetailOpen] = useState(false);
  const [selectedReviewVariant, setSelectedReviewVariant] = useState(null);
  const [reviewVariantLoading, setReviewVariantLoading] = useState(false);
  const [reviewVariantSaving, setReviewVariantSaving] = useState(false);
  const [reviewVariantQuestionText, setReviewVariantQuestionText] = useState("");
  const [reviewVariantSchemeText, setReviewVariantSchemeText] = useState("");

  const showMessage = (type, text) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 3500);
  };

  const fetchOverview = async () => {
    try {
      const response = await apiFetch(`${API_BASE_URL}/api/admin/overview`);
      const data = await response.json().catch(() => ({}));

      if (response.ok && data.success) {
        setOverview({ ...emptyOverview, ...(data.overview || {}) });
      }
    } catch (error) {
      console.warn("Admin overview endpoint not ready yet:", error);
    }
  };

  const getChapterOptions = (draftJson) => {
    const formValue = draftJson.form || draftJson.verified_form || "";

    return chapterOptionsByForm[formValue] || [
      ...chapterOptionsByForm.Foundation,
      ...chapterOptionsByForm["Form 4"],
      ...chapterOptionsByForm["Form 5"],
    ];
  };
  
  const fetchQuestions = async () => {
    try {
      const params = new URLSearchParams();

      if (questionFilters.search) {
        params.set("search", questionFilters.search);
      }

      if (questionFilters.paper_type !== "all") {
        params.set("paper_type", questionFilters.paper_type);
      }

      if (questionFilters.status !== "all") {
        params.set("status", questionFilters.status);
      }

      if (questionFilters.form !== "all") {
        params.set("form", questionFilters.form);
      }

      if (questionFilters.difficulty !== "all") {
        params.set("difficulty", questionFilters.difficulty);
      }

      const response = await apiFetch(
        `${API_BASE_URL}/api/admin/questions?${params.toString()}`
      );

      const data = await response.json().catch(() => ({}));

      if (!response.ok || !data.success) {
        throw new Error(data.message || "Failed to load questions.");
      }

      setQuestions(data.questions || []);
    } catch (error) {
      showMessage("error", error.message);
    }
  };

  const getBatchReviewSummary = () => {
    const total = batchItems.length;

    const approvedCount = batchItems.filter(
      (item) => item.status === "approved"
    ).length;

    const skippedCount = batchItems.filter(
      (item) => item.status === "skipped"
    ).length;

    const savedCount = batchItems.filter(
      (item) => item.status === "saved"
    ).length;

    const reviewedCount = approvedCount + skippedCount + savedCount;
    const pendingCount = Math.max(total - reviewedCount, 0);

    return {
      total,
      approvedCount,
      skippedCount,
      savedCount,
      reviewedCount,
      pendingCount,
      canCompleteReview: total > 0 && pendingCount === 0,
    };
  };

  const fetchUsers = async () => {
    try {
      const params = new URLSearchParams();

      if (userFilters.search) {
        params.set("search", userFilters.search);
      }

      if (userFilters.role !== "all") {
        params.set("role", userFilters.role);
      }

      if (userFilters.status !== "all") {
        params.set("status", userFilters.status);
      }

      const response = await apiFetch(
        `${API_BASE_URL}/api/admin/users?${params.toString()}`
      );
      const data = await response.json().catch(() => ({}));

      if (response.ok && data.success) {
        setUsers(data.users || []);
      }
    } catch (error) {
      console.warn("Admin users endpoint not ready yet:", error);
    }
  };

  useEffect(() => {
    if (!isParsingPdf || !parsingStartTime) return;

    const timer = setInterval(() => {
      setParsingElapsed(Math.floor((Date.now() - parsingStartTime) / 1000));
    }, 1000);

    return () => clearInterval(timer);
  }, [isParsingPdf, parsingStartTime]);

  useEffect(() => {
    const initialiseAdmin = async () => {
      setLoading(true);
      await Promise.all([
        fetchOverview(),
        fetchQuestions(),
        fetchUsers(),
        fetchImportBatches(),
        fetchReviewVariants(),
      ]);
      setLoading(false);
    };

    initialiseAdmin();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (activeTab === "questions") {
      fetchQuestions();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [questionFilters, activeTab]);

  useEffect(() => {
    if (activeTab === "users") {
      fetchUsers();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userFilters, activeTab]);


  useEffect(() => {
    if (activeTab === "variants") {
      fetchReviewVariants();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reviewVariantFilters, activeTab]);

  const adminEasyLearnmbols = useMemo(() => getEasyLearnmbols("en"), []);

  const appendSymbolToInstruction = (field, symbol) => {
    updateDraftJson((current) => {
      const currentText = getDraftInstructionText(current, field);

      return {
        ...current,
        [field]: currentText ? [currentText + symbol] : [symbol],
      };
    });
  };

  const appendSymbolToOption = (label, textField, symbol) => {
    updateDraftJson((current) => {
      const options = Array.isArray(current.options) ? [...current.options] : [];

      const index = options.findIndex(
        (option) => String(option.label || "").toUpperCase() === label
      );

      if (index >= 0) {
        options[index] = {
          ...options[index],
          [textField]: `${options[index][textField] || ""}${symbol}`,
        };
      }

      return {
        ...current,
        options,
      };
    });
  };

  const handleInsertEasyLearnmbol = (symbolItem) => {
    const insertValue = symbolItem?.insert || "";

    if (!insertValue) return;

    if (symbolTarget.type === "instruction") {
      appendSymbolToInstruction(symbolTarget.field, insertValue);
      return;
    }

    if (symbolTarget.type === "option") {
      appendSymbolToOption(symbolTarget.label, symbolTarget.field, insertValue);
    }
  };

  const overviewCards = useMemo(
    () => [
      { label: "Students", value: overview.total_students, color: "#3855c0" },
      { label: "Parents", value: overview.total_parents, color: "#0F766E" },
      { label: "Questions", value: overview.total_questions, color: "#C2410C" },
      { label: "Attempts", value: overview.total_attempts, color: "#7C3AED" },
      {
        label: "Practice Sessions",
        value: overview.total_sessions,
        color: "#2563EB",
      },
      {
        label: "Chat Messages",
        value: overview.total_chat_messages,
        color: "#DC2626",
      },
    ],
    [overview]
  );

  const handleQuestionStatusToggle = async (question) => {
    const nextActive = Number(question.is_active ?? 1) === 1 ? 0 : 1;

    try {
      const response = await apiFetch(
        `${API_BASE_URL}/api/admin/questions/${question.id}/status`,
        {
          method: "PATCH",
          body: JSON.stringify({ is_active: nextActive }),
        }
      );

      const data = await response.json().catch(() => ({}));

      if (!response.ok || !data.success) {
        throw new Error(data.message || "Failed to update question status.");
      }

      showMessage(
        "success",
        nextActive ? "Question reactivated." : "Question deactivated."
      );

      fetchQuestions();
      fetchOverview();
    } catch (error) {
      showMessage("error", error.message);
    }
  };

  const handleUserStatusToggle = async (targetUser) => {
    if (targetUser.id === user.id) {
      showMessage("warning", "You cannot deactivate your own admin account.");
      return;
    }

    const nextActive = Number(targetUser.is_active ?? 1) === 1 ? 0 : 1;

    try {
      const response = await apiFetch(
        `${API_BASE_URL}/api/admin/users/${targetUser.id}/status`,
        {
          method: "PATCH",
          body: JSON.stringify({ is_active: nextActive }),
        }
      );

      const data = await response.json().catch(() => ({}));

      if (!response.ok || !data.success) {
        throw new Error(data.message || "Failed to update user status.");
      }

      showMessage(
        "success",
        nextActive ? "User reactivated." : "User deactivated."
      );

      fetchUsers();
      fetchOverview();
    } catch (error) {
      showMessage("error", error.message);
    }
  };

  const handleImportPdf = async () => {
    if (!selectedPdfFile) {
      showMessage("warning", "Please select a question PDF first.");
      return;
    }

    if (!selectedMarkingPdfFile) {
      showMessage(
        "warning",
        selectedImportType === "kertas1"
          ? "Please select the K1 answer key / marking PDF."
          : "Please select the K2 marking scheme PDF."
      );
      return;
    }

    try {
      setIsParsingPdf(true);
      setParsingStartTime(Date.now());
      setParsingElapsed(0);

      const formData = new FormData();
      formData.append("question_pdf", selectedPdfFile);
      formData.append("marking_pdf", selectedMarkingPdfFile);
      formData.append(
        "title",
        importMeta.title || selectedPdfFile.name.replace(".pdf", "")
      );
      formData.append("exam_name", importMeta.exam_name || "SPM Trial");
      formData.append("year", importMeta.year || new Date().getFullYear().toString());
      formData.append("question_start_page", importMeta.question_start_page || "1");
      formData.append("marking_start_page", importMeta.marking_start_page || "1");

      if (importMeta.question_end_page) {
        formData.append("question_end_page", importMeta.question_end_page);
      }

      if (importMeta.marking_end_page) {
        formData.append("marking_end_page", importMeta.marking_end_page);
      }

      const endpoint =
        selectedImportType === "kertas2"
          ? `${API_BASE_URL}/api/admin/import/k2/parse-draft`
          : `${API_BASE_URL}/api/admin/import/k1/parse-draft`;

      const response = await apiFetch(endpoint, {
        method: "POST",
        body: formData,
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok || !data.success) {
        throw new Error(
          data.message ||
            `Failed to parse ${selectedImportType === "kertas2" ? "K2" : "K1"} PDF.`
        );
      }

      showMessage(
        "success",
        `${selectedImportType === "kertas2" ? "K2" : "K1"} parsed successfully. ${
          data.total_questions || 0
        } draft item(s) created.`
      );

      await fetchImportBatches();

      if (data.batch_id) {
        await handleOpenImportBatch(data.batch_id);
      }

      setSelectedPdfFile(null);
      setSelectedMarkingPdfFile(null);
      setSelectedPdfName("");
    } catch (error) {
      showMessage("error", error.message);
    } finally {
      setIsParsingPdf(false);
      setParsingStartTime(null);
    }
  };

  const renderStatusChip = (isActive) => {
    const active = Number(isActive ?? 1) === 1;

    return (
      <Chip
        size="small"
        label={active ? "Active" : "Inactive"}
        sx={{
          bgcolor: active ? "#ECFDF5" : "#FEF2F2",
          color: active ? "#047857" : "#DC2626",
          border: `1px solid ${active ? "#A7F3D0" : "#FECACA"}`,
          fontWeight: 800,
        }}
      />
    );
  };

  const renderImportBatchesPanel = () => (
    <Paper
      elevation={0}
      sx={{
        p: 3,
        borderRadius: "18px",
        border: "1px solid #E5E7EB",
        mb: 3,
      }}
    >
      <Box
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          gap: 2,
          mb: 2,
        }}
      >
        <Box>
          <Typography variant="h6" fontWeight="900">
            Import Drafts
          </Typography>

          <Typography variant="body2" color="text.secondary">
            Review parsed PDF questions before saving them into the question bank.
          </Typography>
        </Box>

        <Button
          variant="outlined"
          onClick={fetchImportBatches}
          sx={{
            borderRadius: "12px",
            textTransform: "none",
            fontWeight: "800",
          }}
        >
          Refresh
        </Button>
      </Box>

      <Stack gap={1.5}>
        {importBatches.length === 0 ? (
          <Alert severity="info" sx={{ borderRadius: "12px" }}>
            No import drafts yet. After parsing a PDF, the draft batch will appear here.
          </Alert>
        ) : (
          importBatches.map((batch) => (
            <Paper
              key={batch.batch_id}
              elevation={0}
              sx={{
                p: 2,
                borderRadius: "14px",
                border: "1px solid #E5E7EB",
                bgcolor: "#ffffff",
              }}
            >
              <Box
                sx={{
                  display: "flex",
                  justifyContent: "space-between",
                  gap: 2,
                  alignItems: "center",
                }}
              >
                <Box sx={{ minWidth: 0 }}>
                  <Typography fontWeight="900" color="#111827" noWrap>
                    {batch.title}
                  </Typography>

                  <Typography variant="body2" color="text.secondary" noWrap>
                    {batch.original_file_name || "No file name"}
                  </Typography>

                  <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap", mt: 1 }}>
                    <Chip size="small" label={batch.paper_type} />
                    <Chip size="small" label={batch.status} />
                    <Chip size="small" label={`${batch.total_items || 0} items`} />
                  </Box>
                </Box>

                <Button
                  variant="contained"
                  onClick={() => handleOpenImportBatch(batch.batch_id)}
                  sx={{
                    bgcolor: "#3855c0",
                    borderRadius: "10px",
                    textTransform: "none",
                    fontWeight: "800",
                    flexShrink: 0,
                    "&:hover": { bgcolor: "#2d4499" },
                  }}
                >
                  Review
                </Button>
              </Box>
            </Paper>
          ))
        )}
      </Stack>
    </Paper>
  );

  const validateDraftBeforeApprove = (draftJson, paperType = "kertas1") => {
    const errors = [];

    if (!String(draftJson.question_no || "").trim()) {
      errors.push("Question number is required.");
    }

    if (!String(draftJson.form || draftJson.verified_form || "").trim()) {
      errors.push("Form is required.");
    }

    if (!String(draftJson.chapter || draftJson.verified_chapter || "").trim()) {
      errors.push("Chapter is required.");
    }

    if (!String(draftJson.difficulty || "").trim()) {
      errors.push("Difficulty is required.");
    }

    const instructionsEn = getDraftInstructionText(draftJson, "instructions_en");
    const instructionsMs = getDraftInstructionText(draftJson, "instructions_ms");

    if (!instructionsEn && !instructionsMs) {
      errors.push("Question text is required.");
    }

    if (paperType === "kertas1") {
      if (!["A", "B", "C", "D"].includes(String(draftJson.correct_option || "").toUpperCase())) {
        errors.push("Correct answer must be A, B, C, or D.");
      }

      const options = Array.isArray(draftJson.options) ? draftJson.options : [];

      ["A", "B", "C", "D"].forEach((label) => {
        const option = options.find(
          (item) => String(item.label || "").toUpperCase() === label
        );

        if (!option) {
          errors.push(`Option ${label} is required.`);
          return;
        }

        if (!option.text_en && !option.text_ms && !option.image_path) {
          errors.push(`Option ${label} must have text or image.`);
        }
      });
    }

    if (paperType === "kertas2") {
      const scheme = draftJson.marking_scheme;

      if (!scheme || typeof scheme !== "object") {
        errors.push("K2 marking scheme is required.");
      } else {
        if (!Array.isArray(scheme.steps) || scheme.steps.length === 0) {
          errors.push("K2 marking scheme should contain at least one marking step.");
        }

        if (!Number(draftJson.display_marks || draftJson.marks || scheme.subpart_marks || 0)) {
          errors.push("K2 marks/display marks is required.");
        }
      }
    }

    return errors;
  };

  const handleOpenQuestionDetail = async (question) => {
    setQuestionDetailOpen(true);
    setQuestionDetailLoading(true);
    setSelectedQuestionDetail(null);
    setSelectedQuestionSchemes([]);

    try {
      const response = await apiFetch(
        `${API_BASE_URL}/api/admin/questions/${question.id}`
      );

      const data = await response.json().catch(() => ({}));

      if (!response.ok || !data.success) {
        throw new Error(data.message || "Failed to load question detail.");
      }

      setSelectedQuestionDetail(data.question || null);
      setSelectedQuestionSchemes(data.marking_schemes || []);
      const editJson = buildQuestionEditJson(
        data.question || null,
        data.marking_schemes || []
      );

      setQuestionEditText(JSON.stringify(editJson, null, 2));
      setQuestionEditErrors([]);
      setQuestionEditSuccess("");
    } catch (error) {
      showMessage("error", error.message);
      setQuestionDetailOpen(false);
    } finally {
      setQuestionDetailLoading(false);
    }
  };

  const handleOpenUserDetail = async (targetUser) => {
    setUserDetailOpen(true);
    setUserDetailLoading(true);
    setSelectedUserDetail(null);
    setSelectedUserStats(null);

    try {
      const response = await apiFetch(
        `${API_BASE_URL}/api/admin/users/${targetUser.id}`
      );

      const data = await response.json().catch(() => ({}));

      if (!response.ok || !data.success) {
        throw new Error(data.message || "Failed to load user detail.");
      }

      setSelectedUserDetail({
        ...(data.user || {}),
        linked_students: data.linked_students || [],
      });
      setSelectedUserStats(data.stats || null);
    } catch (error) {
      showMessage("error", error.message);
      setUserDetailOpen(false);
    } finally {
      setUserDetailLoading(false);
    }
  };

  const getActiveDraftJson = () => {
    try {
      return JSON.parse(draftEditorText || "{}");
    } catch {
      return {};
    }
  };

  const updateDraftJson = (updater) => {
    const current = getActiveDraftJson();
    const next = updater({ ...current });
    setDraftEditorText(JSON.stringify(next, null, 2));
  };

  const updateDraftField = (field, value) => {
    updateDraftJson((current) => ({
      ...current,
      [field]: value,
    }));
  };

  const updateDraftFields = (fields) => {
    updateDraftJson((current) => ({
      ...current,
      ...fields,
    }));
  };

  const updateDraftInstruction = (field, value) => {
    updateDraftJson((current) => ({
      ...current,
      [field]: value
        .split("\n")
        .map((line) => line.trim())
        .filter(Boolean),
    }));
  };

  const updateDraftOption = (label, textField, value) => {
    updateDraftJson((current) => {
      const options = Array.isArray(current.options) ? [...current.options] : [];

      const index = options.findIndex(
        (option) => String(option.label || "").toUpperCase() === label
      );

      if (index >= 0) {
        options[index] = {
          ...options[index],
          [textField]: value,
        };
      } else {
        options.push({
          label,
          text_en: textField === "text_en" ? value : "",
          text_ms: textField === "text_ms" ? value : "",
          has_image: false,
          image_path: "",
        });
      }

      return {
        ...current,
        options,
      };
    });
  };

  const getDraftInstructionText = (draftJson, field) => {
    const value = draftJson[field];

    if (Array.isArray(value)) {
      return value.join("\n");
    }

    return value || "";
  };

  const getDraftOptionValue = (draftJson, label, field) => {
    const options = Array.isArray(draftJson.options) ? draftJson.options : [];
    const option = options.find(
      (item) => String(item.label || "").toUpperCase() === label
    );

    return option?.[field] || "";
  };

  const formatJsonPreview = (value) => {
    if (!value) return "-";

    if (typeof value === "string") {
      return value;
    }

    try {
      return JSON.stringify(value, null, 2);
    } catch {
      return String(value);
    }
  };

  const getQuestionPreviewText = (question) => {
    const raw =
      question?.instructions_en ||
      question?.question_json?.instructions_en ||
      "";

    let text = "";

    if (Array.isArray(raw)) {
      text = raw.find((item) => String(item || "").trim()) || "";
    } else if (typeof raw === "string") {
      try {
        const parsed = JSON.parse(raw);
        if (Array.isArray(parsed)) {
          text = parsed.find((item) => String(item || "").trim()) || "";
        } else {
          text = raw;
        }
      } catch {
        text = raw;
      }
    }

    text = String(text || "")
      .replace(/\s+/g, " ")
      .trim();

    if (!text) return "No question text preview available.";

    return text.length > 160 ? `${text.slice(0, 160).trim()}...` : text;
  };

  const getQuestionListLabel = (question) => {
    const questionNo = question?.question_no || question?.id || "";

    const part = String(question?.part || "").trim();
    const subpart = String(question?.subpart || "").trim();
    const subSubpart = String(question?.sub_subpart || "").trim();

    let label = `Q${questionNo}`;

    if (part) {
      label += `(${part})`;
    }

    if (subpart) {
      label += `(${subpart})`;
    }

    if (subSubpart) {
      label += `(${subSubpart})`;
    }

    return label;
  };

  const buildQuestionEditJson = (question, schemes = []) => {
    if (!question) return {};

    const firstScheme =
      Array.isArray(schemes) && schemes.length > 0 ? schemes[0] : null;

    const rawCorrectOption =
      question.correct_option ||
      question.answer ||
      firstScheme?.correct_option ||
      firstScheme?.final_answer ||
      firstScheme?.answer_value ||
      "";

    const normalizedCorrectOption = String(rawCorrectOption || "")
      .trim()
      .toUpperCase();

    const safeCorrectOption = ["A", "B", "C", "D"].includes(normalizedCorrectOption)
      ? normalizedCorrectOption
      : "";

    return {
      id: question.id,
      paper_id: question.paper_id,
      paper_type: question.paper_type || "",

      question_no: question.question_no || "",
      correct_option: safeCorrectOption,
      part: question.part || "",
      subpart: question.subpart || "",
      sub_subpart: question.sub_subpart || "",

      question_type: question.question_type || "",
      form: question.form || question.verified_form || "",
      chapter: question.chapter || question.verified_chapter || "",
      verified_form: question.verified_form || question.form || "",
      verified_chapter: question.verified_chapter || question.chapter || "",

      difficulty: question.difficulty || "Moderate",
      difficulty_level: question.difficulty_level || 3,

      instructions_en: Array.isArray(question.instructions_en)
        ? question.instructions_en
        : question.instructions_en
        ? [question.instructions_en]
        : [],

      instructions_ms: Array.isArray(question.instructions_ms)
        ? question.instructions_ms
        : question.instructions_ms
        ? [question.instructions_ms]
        : [],

      options: Array.isArray(question.options) ? question.options : [],

      image_path: question.image_path || "",

      group_id: question.group_id || "",
      group_form: question.group_form || "",
      group_chapter: question.group_chapter || "",
      group_difficulty_level: question.group_difficulty_level || 3,
      exercise_stage_id: question.exercise_stage_id || "",
      stage_index: question.stage_index || 1,
      unlock_after_stage_id: question.unlock_after_stage_id || "",
      display_marks: question.display_marks || question.marks || 0,
      marks_source: question.marks_source || "",

      table_data: question.table_data || {},
      given_values: question.given_values || {},
      sequence: question.sequence || [],

      marking_scheme: firstScheme || null,
    };
  };

  const getQuestionEditJson = () => {
    try {
      return JSON.parse(questionEditText || "{}");
    } catch {
      return {};
    }
  };

  const updateQuestionEditJson = (updater) => {
    const current = getQuestionEditJson();
    const next = updater({ ...current });
    setQuestionEditText(JSON.stringify(next, null, 2));
  };

  const updateQuestionEditField = (field, value) => {
    updateQuestionEditJson((current) => ({
      ...current,
      [field]: value,
    }));
  };

  const updateQuestionEditFields = (fields) => {
    updateQuestionEditJson((current) => ({
      ...current,
      ...fields,
    }));
  };

  const updateQuestionEditInstruction = (field, value) => {
    updateQuestionEditJson((current) => ({
      ...current,
      [field]: value
        .split("\n")
        .map((line) => line.trim())
        .filter(Boolean),
    }));
  };

  const updateQuestionEditOption = (label, textField, value) => {
    updateQuestionEditJson((current) => {
      const options = Array.isArray(current.options) ? [...current.options] : [];

      const index = options.findIndex(
        (option) => String(option.label || "").toUpperCase() === label
      );

      if (index >= 0) {
        options[index] = {
          ...options[index],
          [textField]: value,
        };
      } else {
        options.push({
          label,
          text_en: textField === "text_en" ? value : "",
          text_ms: textField === "text_ms" ? value : "",
          has_image: false,
          image_path: "",
        });
      }

      return {
        ...current,
        options,
      };
    });
  };

  const plainMathToLatex = (text) => {
    let value = String(text || "").trim();

    if (!value) return "";

    value = value
      .replace(/≤/g, "\\le ")
      .replace(/≥/g, "\\ge ")
      .replace(/≠/g, "\\ne ")
      .replace(/×/g, "\\times ")
      .replace(/÷/g, "\\div ")
      .replace(/π/g, "\\pi ")
      .replace(/θ/g, "\\theta ")
      .replace(/σ/g, "\\sigma ")
      .replace(/²/g, "^2")
      .replace(/³/g, "^3");

    // sqrt(16) -> \sqrt{16}
    value = value.replace(/sqrt\s*\(([^)]+)\)/gi, "\\sqrt{$1}");

    // √16 -> \sqrt{16}
    value = value.replace(/√\s*([A-Za-z0-9.]+)/g, "\\sqrt{$1}");

    // 1/2 or 12/25 -> \frac{1}{2}
    // Keep this conservative so it does not destroy normal text.
    value = value.replace(
      /(?<![A-Za-z])(\d+(?:\.\d+)?)\s*\/\s*(\d+(?:\.\d+)?)(?![A-Za-z])/g,
      "\\frac{$1}{$2}"
    );

    return value;
  };

  const isPureMathLine = (text) => {
    const value = String(text || "").trim();

    if (!value) return false;

    // If it already contains LaTeX commands, treat as math.
    if (/\\(sqrt|frac|times|div|le|ge|pi|theta|sigma|begin|end)/.test(value)) {
      return true;
    }

    const words = value.match(/[A-Za-z]{3,}/g) || [];
    const mathSymbols = /(\^|_|=|<=|>=|≤|≥|√|sqrt|\+|-|\*|\/)/.test(value);

    if (mathSymbols && words.length <= 2) return true;

    if (/^[0-9\s().+\-*/^=<>≤≥{}]+$/.test(value)) return true;

    return false;
  };

  const balanceLatexBraces = (text) => {
    let value = String(text || "");
    let balance = 0;
    let result = "";

    for (const char of value) {
      if (char === "{") {
        balance += 1;
        result += char;
        continue;
      }

      if (char === "}") {
        if (balance > 0) {
          balance -= 1;
          result += char;
        }
        continue;
      }

      result += char;
    }

    return result;
  };

  const cleanLatexInput = (text) => {
    let value = String(text || "").trim();

    // Fix common parser mistake:
    // \sqrt{179\frac{2}{3} \times ...}
    // becomes:
    // \sqrt{179} \times \frac{2}{3} \times ...
    value = value.replace(
      /\\sqrt\{([^{}\\]+)(\\frac\{[^{}]+\}\{[^{}]+\})/g,
      "\\sqrt{$1} \\times $2"
    );

    // Remove extra unmatched closing braces.
    value = balanceLatexBraces(value);

    return value;
  };

  const renderKatexSpan = (plainText) => {
    const cleaned = cleanLatexInput(plainText);
    const latex = plainMathToLatex(cleaned);

    try {
      return katex.renderToString(latex, {
        throwOnError: false,
        displayMode: false,
        strict: false,
      });
    } catch {
      return katex.renderToString("\\text{" + String(plainText || "") + "}", {
        throwOnError: false,
        displayMode: false,
        strict: false,
      });
    }
  };

  const renderMixedLatexPreview = (text) => {
    const value = String(text || "");

    if (!value.trim()) {
      return (
        <Typography variant="body2" color="text.secondary">
          Type the marking answer below to preview it here.
        </Typography>
      );
    }

    const lines = value.split("\n");

    return (
      <Box sx={{ whiteSpace: "pre-wrap", lineHeight: 1.8 }}>
        {lines.map((line, lineIndex) => {
          if (isPureMathLine(line)) {
            return (
              <Box key={lineIndex} sx={{ overflowX: "auto" }}>
                <span
                  dangerouslySetInnerHTML={{
                    __html: renderKatexSpan(line),
                  }}
                />
              </Box>
            );
          }

          // Mixed sentence mode:
          // only render explicit $...$ or obvious math snippets.
          const parts = [];
          const regex =
            /(\$[^$]+\$|sqrt\s*\([^)]+\)|√\s*\S+|\b\d+\s*\/\s*\d+\b|\b\d+(?:\.\d+)?\s*[A-Za-z]+\^\{?-?\d+\}?|[A-Za-z]\^\{?-?\d+\}?|[A-Za-z0-9().]+\s*(?:=|<=|>=|≤|≥|<|>)\s*[A-Za-z0-9().+\-*/^{}]+)/gi;

          let lastIndex = 0;
          let match;

          while ((match = regex.exec(line)) !== null) {
            if (match.index > lastIndex) {
              parts.push({
                type: "text",
                value: line.slice(lastIndex, match.index),
              });
            }

            parts.push({
              type: "math",
              value: match[0].replace(/^\$/, "").replace(/\$$/, ""),
            });

            lastIndex = regex.lastIndex;
          }

          if (lastIndex < line.length) {
            parts.push({
              type: "text",
              value: line.slice(lastIndex),
            });
          }

          return (
            <Box key={lineIndex}>
              {parts.map((part, partIndex) => {
                if (part.type === "math") {
                  return (
                    <span
                      key={partIndex}
                      dangerouslySetInnerHTML={{
                        __html: renderKatexSpan(part.value),
                      }}
                    />
                  );
                }

                return <span key={partIndex}>{part.value}</span>;
              })}
            </Box>
          );
        })}
      </Box>
    );
  };

  const updateK2MarkingStep = (stepIndex, field, value) => {
    updateDraftJson((current) => {
      const markingScheme =
        current.marking_scheme && typeof current.marking_scheme === "object"
          ? { ...current.marking_scheme }
          : {};

      const steps = Array.isArray(markingScheme.steps)
        ? [...markingScheme.steps]
        : [];

      const existingStep = steps[stepIndex] || {
        step_no: stepIndex + 1,
        label: "",
        marks: 0,
        required: true,
        answer: "",
        keywords: [],
      };

      steps[stepIndex] = {
        ...existingStep,
        [field]: field === "marks" ? Number(value || 0) : value,
      };

      markingScheme.steps = steps;

      return {
        ...current,
        marking_scheme: markingScheme,
      };
    });
  };

  const updateK2MarkingSchemeField = (field, value) => {
    updateDraftJson((current) => ({
      ...current,
      marking_scheme: {
        ...(current.marking_scheme || {}),
        [field]: value,
      },
    }));
  };

  const updateQuestionK2MarkingStep = (stepIndex, field, value) => {
    updateQuestionEditJson((current) => {
      const markingScheme =
        current.marking_scheme && typeof current.marking_scheme === "object"
          ? { ...current.marking_scheme }
          : {};

      const steps = Array.isArray(markingScheme.steps)
        ? [...markingScheme.steps]
        : [];

      const existingStep = steps[stepIndex] || {
        step_no: stepIndex + 1,
        label: "",
        marks: 0,
        required: true,
        answer: "",
        keywords: [],
      };

      steps[stepIndex] = {
        ...existingStep,
        [field]: field === "marks" ? Number(value || 0) : value,
      };

      markingScheme.steps = steps;

      return {
        ...current,
        marking_scheme: markingScheme,
      };
    });
  };

  const updateQuestionK2MarkingSchemeField = (field, value) => {
    updateQuestionEditJson((current) => ({
      ...current,
      marking_scheme: {
        ...(current.marking_scheme || {}),
        [field]: value,
      },
    }));
  };

  const getItemDraftJson = (item) => {
    const raw = item?.admin_edited_json || item?.parsed_json || {};

    if (typeof raw === "string") {
      try {
        return JSON.parse(raw);
      } catch {
        return {};
      }
    }

    return raw && typeof raw === "object" ? raw : {};
  };

  const getDraftPartLabel = (draftJson, fallbackItem = {}) => {
    const questionNo =
      draftJson.question_no || fallbackItem.question_no || fallbackItem.item_id || "";

    const part = draftJson.part || fallbackItem.part || "";
    const subpart = draftJson.subpart || fallbackItem.subpart || "";
    const subSubpart = draftJson.sub_subpart || "";

    return `Q${questionNo}${part ? `(${part})` : ""}${subpart ? `(${subpart})` : ""}${subSubpart ? `(${subSubpart})` : ""}`;
  };

  const getGroupedBatchItems = () => {
    if (selectedBatch?.paper_type !== "kertas2") {
      return {
        Ungrouped: batchItems,
      };
    }

    return batchItems.reduce((groups, item) => {
      const draftJson = getItemDraftJson(item);

      const stageKey =
        draftJson.exercise_stage_id ||
        `${draftJson.group_id || "ungrouped"}_stage_${draftJson.stage_index || 1}`;

      if (!groups[stageKey]) {
        groups[stageKey] = [];
      }

      groups[stageKey].push(item);
      return groups;
    }, {});
  };

  const renderK2MarkingSchemePreview = (
    draftJson,
    updateStepFn = updateK2MarkingStep,
    updateSchemeFieldFn = updateK2MarkingSchemeField
  ) => {
    const scheme = draftJson?.marking_scheme;

    if (!scheme || typeof scheme !== "object") {
      return (
        <Alert severity="warning" sx={{ borderRadius: "12px" }}>
          No marking scheme linked to this K2 item. You may still save the draft,
          but approval requires a marking scheme.
        </Alert>
      );
    }

    const steps = Array.isArray(scheme.steps) ? scheme.steps : [];
    const notes = Array.isArray(scheme.notes) ? scheme.notes : [];
    const conditionalRules = Array.isArray(scheme.conditional_marking_rules)
      ? scheme.conditional_marking_rules
      : [];

    return (
      <Paper
        elevation={0}
        sx={{
          p: 2,
          borderRadius: "14px",
          border: "1px solid #E5E7EB",
          bgcolor: "#F9FAFB",
        }}
      >
        <Typography fontWeight="900" mb={1}>
          K2 Marking Scheme
        </Typography>

        <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap", mb: 2 }}>
          <Chip size="small" label={`Marks: ${scheme.subpart_marks || draftJson.display_marks || draftJson.marks || "-"}`} />
          <Chip size="small" label={`Answer type: ${scheme.answer_type || "-"}`} />
          {scheme.method && <Chip size="small" label={`Method: ${scheme.method}`} />}
          {scheme.units && <Chip size="small" label={`Units: ${scheme.units}`} />}
        </Box>

        <Typography variant="body2" fontWeight="900">
          Final Answer
        </Typography>

        <Typography variant="body2" fontWeight="900">
          Final Answer Live Preview
        </Typography>

        <Box
          sx={{
            mt: 0.75,
            mb: 1.5,
            p: 1.25,
            borderRadius: "10px",
            border: "1px solid #D1D5DB",
            bgcolor: "#F8FAFC",
            overflowX: "auto",
          }}
        >
          {scheme.final_answer ? (
            renderMixedLatexPreview(
              typeof scheme.final_answer === "object"
                ? JSON.stringify(scheme.final_answer)
                : scheme.final_answer
            )
          ) : (
            <Typography variant="body2" color="text.secondary">
              Type the final answer below to preview it here.
            </Typography>
          )}
        </Box>

        <TextField
          size="small"
          label="Final Answer"
          helperText="Type normally, e.g. x = 3, 1/2, sqrt(25), y >= 2"
          value={
            typeof scheme.final_answer === "object"
              ? JSON.stringify(scheme.final_answer, null, 2)
              : scheme.final_answer || ""
          }
          onChange={(e) =>
            updateSchemeFieldFn("final_answer", e.target.value)
          }
          multiline
          minRows={2}
          fullWidth
          sx={{ mb: 2 }}
        />

        <Typography variant="body2" fontWeight="900" mb={1}>
          Step-by-step Marks
        </Typography>

        {steps.length === 0 ? (
          <Typography variant="body2" color="text.secondary">
            No marking steps extracted.
          </Typography>
        ) : (
          <Stack gap={1}>
            {steps.map((step, index) => {
              const answerText = Array.isArray(step.answer)
                ? step.answer.join("\n")
                : step.answer || "";

              return (
                <Box
                  key={index}
                  sx={{
                    p: 1.5,
                    borderRadius: "10px",
                    border: "1px solid #E5E7EB",
                    bgcolor: "#ffffff",
                  }}
                >
                  <Box
                    sx={{
                      display: "grid",
                      gridTemplateColumns: { xs: "1fr", md: "1fr 110px" },
                      gap: 1.5,
                      mb: 1.5,
                    }}
                  >
                    <TextField
                      size="small"
                      label={`Step ${step.step_no || index + 1} label`}
                      value={step.label || ""}
                      onChange={(e) =>
                        updateStepFn(index, "label", e.target.value)
                      }
                      fullWidth
                    />

                    <TextField
                      size="small"
                      label="Marks"
                      type="number"
                      value={step.marks ?? 0}
                      onChange={(e) =>
                        updateStepFn(index, "marks", e.target.value)
                      }
                      fullWidth
                    />
                  </Box>

                  <Typography variant="caption" fontWeight="900" color="text.secondary">
                    Live LaTeX Preview
                  </Typography>

                  <Box
                    sx={{
                      mt: 0.75,
                      mb: 1.5,
                      p: 1.25,
                      borderRadius: "10px",
                      border: "1px solid #D1D5DB",
                      bgcolor: "#F8FAFC",
                      minHeight: 42,
                      overflowX: "auto",
                    }}
                  >
                    {answerText ? (
                      renderMixedLatexPreview(answerText)
                    ) : (
                      <Typography variant="body2" color="text.secondary">
                        Type the marking answer below to preview it here.
                      </Typography>
                    )}
                  </Box>

                  <TextField
                    size="small"
                    label="Step answer / marking point"
                    helperText="Type normally, e.g. x^2 + 2x = 8, sqrt(16), 1/2, x >= 3"
                    value={answerText}
                    onChange={(e) =>
                      updateStepFn(index, "answer", e.target.value)
                    }
                    multiline
                    minRows={2}
                    fullWidth
                  />

                  <TextField
                    size="small"
                    label="Keywords"
                    helperText="Separate keywords using commas"
                    value={Array.isArray(step.keywords) ? step.keywords.join(", ") : ""}
                    onChange={(e) =>
                      updateStepFn(
                        index,
                        "keywords",
                        e.target.value
                          .split(",")
                          .map((item) => item.trim())
                          .filter(Boolean)
                      )
                    }
                    sx={{ mt: 1.5 }}
                    fullWidth
                  />
                </Box>
              );
            })}
          </Stack>
        )}

        {conditionalRules.length > 0 && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="body2" fontWeight="900" mb={1}>
              Conditional Marking Rules
            </Typography>

            <Stack gap={1}>
              {conditionalRules.map((rule, index) => (
                <Box
                  key={index}
                  sx={{
                    p: 1.25,
                    borderRadius: "10px",
                    border: "1px solid #E5E7EB",
                    bgcolor: "#ffffff",
                  }}
                >
                  <Typography variant="body2">
                    <b>Condition:</b> {rule.condition || "-"}
                  </Typography>
                  <Typography variant="body2">
                    <b>Action:</b> {rule.action || "-"}
                  </Typography>
                </Box>
              ))}
            </Stack>
          </Box>
        )}

        {notes.length > 0 && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="body2" fontWeight="900" mb={1}>
              Notes
            </Typography>

            <Box component="ul" sx={{ pl: 2.5, m: 0 }}>
              {notes.map((note, index) => (
                <li key={index}>
                  <Typography variant="body2">{note}</Typography>
                </li>
              ))}
            </Box>
          </Box>
        )}
      </Paper>
    );
  };


  const fetchImportBatches = async () => {
    try {
      const response = await apiFetch(`${API_BASE_URL}/api/admin/import-batches`);
      const data = await response.json().catch(() => ({}));

      if (response.ok && data.success) {
        setImportBatches(data.batches || []);
      }
    } catch (error) {
      console.warn("Import batches endpoint not ready:", error);
    }
  };

  const handleOpenImportBatch = async (batchId, preferredItemId = null) => {
    setBatchDetailOpen(true);
    setBatchLoading(true);
    setSelectedBatch(null);
    setBatchItems([]);
    setActiveDraftItem(null);
    setDraftEditorText("");
    setDraftValidationErrors([]);

    try {
      const response = await apiFetch(
        `${API_BASE_URL}/api/admin/import-batches/${batchId}`
      );

      const data = await response.json().catch(() => ({}));

      if (!response.ok || !data.success) {
        throw new Error(data.message || "Failed to load import batch.");
      }

      const items = data.items || [];

      setSelectedBatch(data.batch || null);
      setBatchItems(items);

      const selectedItem =
        items.find((item) => Number(item.item_id) === Number(preferredItemId)) ||
        items[0] ||
        null;

      setActiveDraftItem(selectedItem);

      if (selectedItem) {
        setDraftEditorText(
          JSON.stringify(selectedItem.admin_edited_json || {}, null, 2)
        );
      }
    } catch (error) {
      showMessage("error", error.message);
      setBatchDetailOpen(false);
    } finally {
      setBatchLoading(false);
    }
  };

  const handleSelectDraftItem = (item) => {
    setActiveDraftItem(item);
    setDraftEditorText(JSON.stringify(item.admin_edited_json || {}, null, 2));
    setDraftValidationErrors([]);
  };

  const handleSaveDraftItem = async (status = "draft") => {
    if (!activeDraftItem) return;

    let parsedJson;

    try {
      parsedJson = JSON.parse(draftEditorText);

      if (status === "approved") {
        const errors = validateDraftBeforeApprove(parsedJson, selectedBatch?.paper_type);

        if (errors.length > 0) {
          setDraftValidationErrors(errors);
          showMessage("error", errors[0]);
          scrollToDraftErrors();
          return;
        }
      }

      setDraftValidationErrors([]);
    } catch (error) {
        setDraftValidationErrors(["Invalid JSON. Please fix it before saving."]);
        showMessage("error", "Invalid JSON. Please fix it before saving.");
        scrollToDraftErrors();
        return;
      }
    
    try {
      setDraftSaving(true);

      const response = await apiFetch(
        `${API_BASE_URL}/api/admin/import-items/${activeDraftItem.item_id}`,
        {
          method: "PATCH",
          body: JSON.stringify({
            status,
            admin_edited_json: parsedJson,
            admin_notes: activeDraftItem.admin_notes || "",
          }),
        }
      );

      const data = await response.json().catch(() => ({}));

      if (!response.ok || !data.success) {
        throw new Error(data.message || "Failed to update draft item.");
      }

      showMessage(
        "success",
        status === "approved"
          ? "Draft item approved."
          : status === "skipped"
          ? "Draft item skipped."
          : "Draft item saved."
      );

      if (selectedBatch?.batch_id) {
        await handleOpenImportBatch(selectedBatch.batch_id, activeDraftItem.item_id);
      }
    } catch (error) {
      showMessage("error", error.message);
    } finally {
      setDraftSaving(false);
    }
  };
  
  const handleSaveApprovedBatch = async () => {
    if (!selectedBatch?.batch_id) {
      showMessage("warning", "No import batch selected.");
      return;
    }

    const summary = getBatchReviewSummary();

    if (!summary.canCompleteReview) {
      setDraftValidationErrors([
        `${summary.pendingCount} question(s) still need to be approved or skipped before completing this import.`,
      ]);
      scrollToDraftErrors();
      return;
    }

    try {
      setDraftSaving(true);

      const response = await apiFetch(
        `${API_BASE_URL}/api/admin/import-batches/${selectedBatch.batch_id}/${
          selectedBatch.paper_type === "kertas2" ? "save-approved-k2" : "save-approved-k1"
        }`,
        {
          method: "POST",
        }
      );

      const data = await response.json().catch(() => ({}));

      if (!response.ok || !data.success) {
        throw new Error(data.message || "Failed to save approved draft.");
      }

      showMessage(
        "success",
        `${data.saved_count || 0} approved question(s) imported. Draft review completed.`
      );

      setBatchDetailOpen(false);
      setSelectedBatch(null);
      setBatchItems([]);
      setActiveDraftItem(null);
      setDraftEditorText("");
      setDraftValidationErrors([]);

      await fetchQuestions();
      await fetchOverview();
      await fetchImportBatches();
    } catch (error) {
      showMessage("error", error.message);
    } finally {
      setDraftSaving(false);
    }
  };

  const handleAskDeleteDraftImage = (item) => {
    setImageItemToDelete(item);
    setDeleteImageDialogOpen(true);
  };

  const handleConfirmDeleteDraftImage = async () => {
    if (!imageItemToDelete) return;

    try {
      setUploadingImageItemId(imageItemToDelete.item_id);

      const response = await apiFetch(
        `${API_BASE_URL}/api/admin/import-items/${imageItemToDelete.item_id}/image`,
        {
          method: "DELETE",
        }
      );

      const data = await response.json().catch(() => ({}));

      if (!response.ok || !data.success) {
        throw new Error(data.message || "Failed to remove image.");
      }

      showMessage("success", "Image removed successfully.");

      setDeleteImageDialogOpen(false);

      if (selectedBatch?.batch_id) {
        await handleOpenImportBatch(
          selectedBatch.batch_id,
          imageItemToDelete.item_id
        );
      }

      setImageItemToDelete(null);
    } catch (error) {
      showMessage("error", error.message);
    } finally {
      setUploadingImageItemId(null);
    }
  };

  const validateSavedQuestionBeforeUpdate = (questionJson) => {
    const errors = [];

    if (!String(questionJson.question_no || "").trim()) {
      errors.push("Question number is required.");
    }

    if (!String(questionJson.form || questionJson.verified_form || "").trim()) {
      errors.push("Form is required.");
    }

    if (!String(questionJson.chapter || questionJson.verified_chapter || "").trim()) {
      errors.push("Chapter is required.");
    }

    const instructionsEn = getDraftInstructionText(questionJson, "instructions_en");
    const instructionsMs = getDraftInstructionText(questionJson, "instructions_ms");

    if (!instructionsEn && !instructionsMs) {
      errors.push("Question text is required.");
    }

    if (questionJson.question_type === "mcq") {
      const options = Array.isArray(questionJson.options) ? questionJson.options : [];

      ["A", "B", "C", "D"].forEach((label) => {
        const option = options.find(
          (item) => String(item.label || "").toUpperCase() === label
        );

        if (!option) {
          errors.push(`Option ${label} is required.`);
        }
      });
    }

    return errors;
  };

  const handleSaveQuestionEdit = async () => {
    if (!selectedQuestionDetail?.id) return;

    let questionJson;

    try {
      questionJson = JSON.parse(questionEditText || "{}");
    } catch {
      setQuestionEditErrors(["Invalid JSON. Please fix it before saving."]);
      showMessage("error", "Invalid JSON. Please fix it before saving.");
      return;
    }

    const errors = validateSavedQuestionBeforeUpdate(questionJson);

    if (errors.length > 0) {
      setQuestionEditErrors(errors);
      showMessage("error", errors[0]);
      return;
    }

    setQuestionEditErrors([]);
    setQuestionEditSuccess("");
    try {
      setQuestionEditSaving(true);

      const response = await apiFetch(
        `${API_BASE_URL}/api/admin/questions/${selectedQuestionDetail.id}`,
        {
          method: "PATCH",
          body: JSON.stringify({
            question: questionJson,
            marking_scheme: questionJson.marking_scheme || null,
          }),
        }
      );

      const data = await response.json().catch(() => ({}));

      if (!response.ok || !data.success) {
        throw new Error(data.message || "Failed to update question.");
      }

      setQuestionEditSuccess("Question updated successfully.");
      showMessage("success", "Question updated successfully.");

      await fetchQuestions();
      await fetchOverview();
      await handleOpenQuestionDetail({ id: selectedQuestionDetail.id });

      setQuestionEditSuccess("Question updated successfully.");
    } catch (error) {
      setQuestionEditErrors([error.message]);
      setQuestionEditSuccess("");
      showMessage("error", error.message);
    } finally {
      setQuestionEditSaving(false);
    }
  };

  const handleReplaceDraftImage = async (item, file) => {
    if (!item || !file) return;

    try {
      setUploadingImageItemId(item.item_id);

      const formData = new FormData();
      formData.append("image", file);

      const response = await apiFetch(
        `${API_BASE_URL}/api/admin/import-items/${item.item_id}/image`,
        {
          method: "POST",
          body: formData,
        }
      );

      const data = await response.json().catch(() => ({}));

      if (!response.ok || !data.success) {
        throw new Error(data.message || "Failed to upload replacement image.");
      }

      showMessage("success", "Image replaced successfully.");

      if (selectedBatch?.batch_id) {
        await handleOpenImportBatch(selectedBatch.batch_id, item.item_id);
      }
    } catch (error) {
      showMessage("error", error.message);
    } finally {
      setUploadingImageItemId(null);
    }
  };

  const getReviewVariantPreviewText = (variant) => {
    const questionJson = variant?.question_json || {};

    const raw =
      questionJson.instructions_en ||
      questionJson.question?.instructions_en ||
      questionJson.questions?.[0]?.instructions_en ||
      "";

    let text = "";

    if (Array.isArray(raw)) {
      text = raw.find((item) => String(item || "").trim()) || "";
    } else {
      text = String(raw || "");
    }

    text = text.replace(/\s+/g, " ").trim();

    if (!text) return "No generated question preview available.";

    return text.length > 160 ? `${text.slice(0, 160).trim()}...` : text;
  };

 const fetchReviewVariants = async () => {
  try {
    const params = new URLSearchParams();

    if (reviewVariantFilters.search) {
      params.set("search", reviewVariantFilters.search);
    }

    if (reviewVariantFilters.variant_type !== "all") {
      params.set("variant_type", reviewVariantFilters.variant_type);
    }

    const response = await apiFetch(
      `${API_BASE_URL}/api/admin/review-variants?${params.toString()}`
    );

    const data = await response.json().catch(() => ({}));

    if (!response.ok || !data.success) {
      throw new Error(data.message || "Failed to load review variants.");
    }

    setReviewVariants(data.variants || []);
  } catch (error) {
    showMessage("error", error.message);
  }
};

  const handleOpenReviewVariantDetail = async (variant) => {
    setReviewVariantDetailOpen(true);
    setReviewVariantLoading(true);
    setSelectedReviewVariant(null);
    setReviewVariantQuestionText("");
    setReviewVariantSchemeText("");

    try {
      const response = await apiFetch(
        `${API_BASE_URL}/api/admin/review-variants/${variant.variant_id}`
      );

      const data = await response.json().catch(() => ({}));

      if (!response.ok || !data.success) {
        throw new Error(data.message || "Failed to load review variant detail.");
      }

      const loadedVariant = data.variant || null;

      setSelectedReviewVariant(loadedVariant);
      setReviewVariantQuestionText(
        JSON.stringify(loadedVariant?.question_json || {}, null, 2)
      );
      setReviewVariantSchemeText(
        JSON.stringify(loadedVariant?.marking_scheme_json || {}, null, 2)
      );
    } catch (error) {
      showMessage("error", error.message);
      setReviewVariantDetailOpen(false);
    } finally {
      setReviewVariantLoading(false);
    }
  };


  const getVariantQuestionJson = () => {
    try {
      return JSON.parse(reviewVariantQuestionText || "{}");
    } catch {
      return {};
    }
  };

  const getVariantSchemeJson = () => {
    try {
      return JSON.parse(reviewVariantSchemeText || "{}");
    } catch {
      return {};
    }
  };

  const handleSaveReviewVariantEdit = async () => {
    if (!selectedReviewVariant?.variant_id) return;

    let questionJson;
    let schemeJson;

    try {
      questionJson = JSON.parse(reviewVariantQuestionText || "{}");
      schemeJson = JSON.parse(reviewVariantSchemeText || "{}");
    } catch {
      showMessage("error", "Invalid JSON. Please fix before saving.");
      return;
    }

    try {
      setReviewVariantSaving(true);

      const response = await apiFetch(
        `${API_BASE_URL}/api/admin/review-variants/${selectedReviewVariant.variant_id}`,
        {
          method: "PATCH",
          body: JSON.stringify({
            question_json: questionJson,
            marking_scheme_json: schemeJson,
          }),
        }
      );

      const data = await response.json().catch(() => ({}));

      if (!response.ok || !data.success) {
        throw new Error(data.message || "Failed to update review variant.");
      }

      showMessage("success", "Review variant updated successfully.");
      await fetchReviewVariants();
      await handleOpenReviewVariantDetail(selectedReviewVariant);
    } catch (error) {
      showMessage("error", error.message);
    } finally {
      setReviewVariantSaving(false);
    }
  };

  const handleCreateAdmin = async () => {
    const name = String(addAdminForm.name || "").trim();
    const email = String(addAdminForm.email || "").trim();

    if (!name || !email) {
      showMessage("warning", "Please enter admin name and email.");
      return;
    }

    try {
      setAddAdminSaving(true);

      const response = await apiFetch(`${API_BASE_URL}/api/admin/users/admin`, {
        method: "POST",
        body: JSON.stringify({
          name,
          email,
        }),
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok || !data.success) {
        throw new Error(data.message || "Failed to add admin.");
      }

      showMessage("success", "Admin account added. Admin can reset temporary password through reset link.");
      setAddAdminResetLink(data.password_reset_link || "");
      setAddAdminOpen(false);
      setAddAdminForm({
        name: "",
        email: "",
      });

      await fetchUsers();
      await fetchOverview();
    } catch (error) {
      showMessage("error", error.message);
    } finally {
      setAddAdminSaving(false);
    }
  };

  const OverviewDoughnut = ({ students, parents }) => {
    const total = Number(students || 0) + Number(parents || 0);
    const studentPercent = total > 0 ? Number(students || 0) / total : 0;

    const radius = 52;
    const circumference = 2 * Math.PI * radius;
    const studentDash = studentPercent * circumference;

    return (
      <Box sx={{ display: "flex", alignItems: "center", gap: 3, flexWrap: "wrap" }}>
        <Box sx={{ position: "relative", width: 150, height: 150 }}>
          <svg width="150" height="150" viewBox="0 0 150 150">
            <circle
              cx="75"
              cy="75"
              r={radius}
              fill="none"
              stroke="#D1FAE5"
              strokeWidth="18"
            />
            <circle
              cx="75"
              cy="75"
              r={radius}
              fill="none"
              stroke="#5775e4"
              strokeWidth="18"
              strokeDasharray={`${studentDash} ${circumference}`}
              strokeLinecap="round"
              transform="rotate(-90 75 75)"
            />
          </svg>

          <Box
            sx={{
              position: "absolute",
              inset: 0,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              flexDirection: "column",
            }}
          >
            <Typography fontWeight="900" fontSize={26}>
              {total}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              users
            </Typography>
          </Box>
        </Box>

        <Stack gap={1}>
          <Box>
            <Typography variant="body2" color="text.secondary">
              Students
            </Typography>
            <Typography fontWeight="900" color="#3855c0">
              {students || 0}
            </Typography>
          </Box>

          <Box>
            <Typography variant="body2" color="text.secondary">
              Parents
            </Typography>
            <Typography fontWeight="900" color="#047857">
              {parents || 0}
            </Typography>
          </Box>
        </Stack>
      </Box>
    );
  };

  const ComparisonBar = ({ leftLabel, leftValue, rightLabel, rightValue }) => {
    const left = Number(leftValue || 0);
    const right = Number(rightValue || 0);
    const total = left + right;
    const leftPercent = total > 0 ? (left / total) * 100 : 50;
    const rightPercent = total > 0 ? (right / total) * 100 : 50;

    return (
      <Box>
        <Box sx={{ display: "flex", justifyContent: "space-between", mb: 1 }}>
          <Typography fontWeight="900">
            {leftLabel}: {left}
          </Typography>
          <Typography fontWeight="900">
            {rightLabel}: {right}
          </Typography>
        </Box>

        <Box
          sx={{
            height: 18,
            borderRadius: "999px",
            overflow: "hidden",
            display: "flex",
            bgcolor: "#E5E7EB",
          }}
        >
          <Box sx={{ width: `${leftPercent}%`, bgcolor: "#fdf25a" }} />
          <Box sx={{ width: `${rightPercent}%`, bgcolor: "#fa9146" }} />
        </Box>

        <Typography variant="caption" color="text.secondary">
          Total: {total}
        </Typography>
      </Box>
    );
  };

  const TopicUsageChart = ({ data }) => {
    const rows = Array.isArray(data) ? data : [];
    const maxValue = Math.max(...rows.map((row) => Number(row.total_attempts || 0)), 1);

    if (rows.length === 0) {
      return (
        <Typography color="text.secondary">
          No topic usage data yet.
        </Typography>
      );
    }

    return (
      <Stack gap={1.5}>
        {rows.map((row, index) => {
          const total = Number(row.total_attempts || 0);
          const k1 = Number(row.k1_attempts || 0);
          const k2 = Number(row.k2_attempts || 0);
          const width = (total / maxValue) * 100;
          const k1Percent = total > 0 ? (k1 / total) * 100 : 0;
          const k2Percent = total > 0 ? (k2 / total) * 100 : 0;

          return (
            <Box key={`${row.topic_name}-${index}`}>
              <Box sx={{ display: "flex", justifyContent: "space-between", gap: 2 }}>
                <Typography
                  variant="body2"
                  fontWeight="800"
                  sx={{
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                  }}
                >
                  {row.topic_name}
                </Typography>

                <Typography variant="caption" color="text.secondary">
                  {total} use(s)
                </Typography>
              </Box>

              <Box
                sx={{
                  mt: 0.5,
                  width: `${width}%`,
                  minWidth: total > 0 ? "40px" : "0px",
                  height: 12,
                  borderRadius: "999px",
                  overflow: "hidden",
                  display: "flex",
                  bgcolor: "#E5E7EB",
                }}
              >
                <Box sx={{ width: `${k1Percent}%`, bgcolor: "#fff460" }} />
                <Box sx={{ width: `${k2Percent}%`, bgcolor: "#fd9a53" }} />
              </Box>
            </Box>
          );
        })}

        <Box sx={{ display: "flex", gap: 2, mt: 1 }}>
          <Chip size="small" label="Kertas 1" sx={{ bgcolor: "#EEF2FF", fontWeight: 800 }} />
          <Chip size="small" label="Kertas 2" sx={{ bgcolor: "#FFF7ED", fontWeight: 800 }} />
        </Box>
      </Stack>
    );
  };

  const renderOverview = () => {
    const questionBreakdown = overview.question_breakdown || {};
    const attemptBreakdown = overview.attempt_breakdown || {};
    const weakTopics = overview.weak_topics || [];
    const topicUsage = overview.topic_usage || [];

    return (
      <Box>
        <Box
          sx={{
            display: "grid",
            gridTemplateColumns: { xs: "1fr", lg: "1fr 1fr 1fr" },
            gap: 2.5,
            mb: 3,
          }}
        >
          <Paper
            elevation={0}
            sx={{
              p: 3,
              borderRadius: "18px",
              border: "1px solid #E5E7EB",
            }}
          >
            <Typography variant="h6" fontWeight="900" mb={2}>
              Student and Parent Users
            </Typography>

            <OverviewDoughnut
              students={overview.total_students}
              parents={overview.total_parents}
            />
          </Paper>

          <Paper
            elevation={0}
            sx={{
              p: 3,
              borderRadius: "18px",
              border: "1px solid #E5E7EB",
            }}
          >
            <Typography variant="h6" fontWeight="900">
              Question Bank
            </Typography>

            <Typography variant="h3" fontWeight="900" color="#3855c0" sx={{ mt: 1 }}>
              {overview.total_questions || 0}
            </Typography>

            <Typography color="text.secondary" mb={2}>
              active questions
            </Typography>

            <ComparisonBar
              leftLabel="Kertas 1"
              leftValue={questionBreakdown.kertas1}
              rightLabel="Kertas 2"
              rightValue={questionBreakdown.kertas2}
            />
          </Paper>

          <Paper
            elevation={0}
            sx={{
              p: 3,
              borderRadius: "18px",
              border: "1px solid #E5E7EB",
            }}
          >
            <Typography variant="h6" fontWeight="900" mb={2}>
              Attempt Usage
            </Typography>

            <ComparisonBar
              leftLabel="Kertas 1"
              leftValue={attemptBreakdown.kertas1}
              rightLabel="Kertas 2"
              rightValue={attemptBreakdown.kertas2}
            />

            <Typography variant="h4" fontWeight="900" color="#111827" sx={{ mt: 2 }}>
              {overview.total_attempts || 0}
            </Typography>

            <Typography color="text.secondary">
              total attempts
            </Typography>
          </Paper>
        </Box>

        <Box
          sx={{
            display: "grid",
            gridTemplateColumns: { xs: "1fr", lg: "1fr 1fr" },
            gap: 2.5,
          }}
        >
          <Paper
            elevation={0}
            sx={{
              p: 3,
              borderRadius: "18px",
              border: "1px solid #E5E7EB",
            }}
          >
            <Typography variant="h6" fontWeight="900" mb={2}>
              Weak Topics Overall
            </Typography>

            {weakTopics.length === 0 ? (
              <Typography color="text.secondary">
                No weak topic data yet.
              </Typography>
            ) : (
              <Stack gap={1.5}>
                {weakTopics.map((topic, index) => {
                  const accuracy = Number(topic.accuracy || 0);

                  return (
                    <Box
                      key={`${topic.topic_name}-${index}`}
                      sx={{
                        p: 1.5,
                        borderRadius: "14px",
                        bgcolor: "#F9FAFB",
                        border: "1px solid #E5E7EB",
                      }}
                    >
                      <Box sx={{ display: "flex", justifyContent: "space-between", gap: 2 }}>
                        <Typography fontWeight="900">
                          {topic.topic_name}
                        </Typography>

                        <Chip
                          size="small"
                          label={`${accuracy}%`}
                          color={accuracy < 50 ? "error" : accuracy < 70 ? "warning" : "success"}
                          sx={{ fontWeight: 900 }}
                        />
                      </Box>

                      <Box
                        sx={{
                          mt: 1,
                          height: 8,
                          borderRadius: "999px",
                          bgcolor: "#E5E7EB",
                          overflow: "hidden",
                        }}
                      >
                        <Box
                          sx={{
                            height: "100%",
                            width: `${Math.min(Math.max(accuracy, 0), 100)}%`,
                            bgcolor:
                              accuracy < 50
                                ? "#DC2626"
                                : accuracy < 70
                                ? "#F59E0B"
                                : "#059669",
                          }}
                        />
                      </Box>

                      <Typography variant="caption" color="text.secondary">
                        Attempts: {topic.attempts_count || 0} · K1:{" "}
                        {topic.k1_attempts || 0} · K2: {topic.k2_attempts || 0}
                      </Typography>
                    </Box>
                  );
                })}
              </Stack>
            )}
          </Paper>

          <Paper
            elevation={0}
            sx={{
              p: 3,
              borderRadius: "18px",
              border: "1px solid #E5E7EB",
            }}
          >
            <Typography variant="h6" fontWeight="900" mb={2}>
              Overall Topic Usage
            </Typography>

            <TopicUsageChart data={topicUsage} />
          </Paper>
        </Box>
      </Box>
    );
  };

  const renderQuestionImportPanel = () => (
    <Paper
      elevation={0}
      sx={{
        p: 3,
        borderRadius: "18px",
        border: "1px solid #E5E7EB",
        mb: 3,
      }}
    >
      <Box
        sx={{
          display: "flex",
          justifyContent: "space-between",
          gap: 2,
          flexWrap: "wrap",
          mb: 2,
        }}
      >
        <Box>
          <Typography variant="h6" fontWeight="900">
            Add Questions from PDF
          </Typography>

          <Typography variant="body2" color="text.secondary">
            Import PDF into draft, review or edit extracted questions, then save
            confirmed items.
          </Typography>
        </Box>
      </Box>

      <Box
        sx={{
          display: "grid",
          gridTemplateColumns: { xs: "1fr", md: "180px 1fr 1fr auto" },
          gap: 2,
          alignItems: "center",
        }}
      >
        <FormControl size="small" fullWidth>
          <InputLabel>Paper</InputLabel>
          <Select
            label="Paper"
            value={selectedImportType}
            onChange={(e) => setSelectedImportType(e.target.value)}
          >
            <MenuItem value="kertas1">Kertas 1</MenuItem>
            <MenuItem value="kertas2">Kertas 2</MenuItem>
          </Select>
        </FormControl>

        <Button
          component="label"
          variant="outlined"
          startIcon={<UploadFileOutlinedIcon />}
          sx={{
            justifyContent: "flex-start",
            borderRadius: "12px",
            textTransform: "none",
            fontWeight: "800",
            minHeight: 40,
          }}
        >
          {selectedPdfName || "Select question PDF"}

          <input
            hidden
            type="file"
            accept="application/pdf"
            onChange={(e) => {
              const file = e.target.files?.[0] || null;
              setSelectedPdfFile(file);
              setSelectedPdfName(file?.name || "");
            }}
          />
        </Button>

        <Button
          component="label"
          variant="outlined"
          startIcon={<UploadFileOutlinedIcon />}
          sx={{
            justifyContent: "flex-start",
            borderRadius: "12px",
            textTransform: "none",
            fontWeight: "800",
            minHeight: 40,
          }}
        >
          {selectedMarkingPdfFile?.name ||
            (selectedImportType === "kertas2"
              ? "Select K2 marking scheme PDF"
              : "Select answer key / marking PDF")}

          <input
            hidden
            type="file"
            accept="application/pdf"
            onChange={(e) => {
              const file = e.target.files?.[0] || null;
              setSelectedMarkingPdfFile(file);
            }}
          />
        </Button>

        <Button
          variant="contained"
          onClick={handleImportPdf}
          disabled={isParsingPdf}
          sx={{
            bgcolor: "#3855c0",
            borderRadius: "12px",
            textTransform: "none",
            fontWeight: "900",
            px: 3,
            "&:hover": { bgcolor: "#2d4499" },
          }}
        >
          {isParsingPdf ? "Parsing..." : "Parse as Draft"}
        </Button>
      </Box>

      <Box
        sx={{
          display: "grid",
          gridTemplateColumns: {
            xs: "1fr",
            md: "1.5fr 1fr 120px 150px 150px 150px 150px",
          },
          gap: 1.5,
          mt: 2,
        }}
      >
        <TextField
          size="small"
          label="Paper Title"
          value={importMeta.title}
          onChange={(e) =>
            setImportMeta((prev) => ({
              ...prev,
              title: e.target.value,
            }))
          }
        />

        <TextField
          size="small"
          label="Exam Name"
          value={importMeta.exam_name}
          onChange={(e) =>
            setImportMeta((prev) => ({
              ...prev,
              exam_name: e.target.value,
            }))
          }
        />

        <TextField
          size="small"
          label="Year"
          value={importMeta.year}
          onChange={(e) =>
            setImportMeta((prev) => ({
              ...prev,
              year: e.target.value,
            }))
          }
        />

        <TextField
          size="small"
          label="Ques Page Start"
          type="number"
          value={importMeta.question_start_page}
          onChange={(e) =>
            setImportMeta((prev) => ({
              ...prev,
              question_start_page: e.target.value,
            }))
          }
        />

        <TextField
          size="small"
          label="Ques Page End"
          type="number"
          value={importMeta.question_end_page}
          onChange={(e) =>
            setImportMeta((prev) => ({
              ...prev,
              question_end_page: e.target.value,
            }))
          }
        />

        <TextField
          size="small"
          label="Mark Page Start"
          type="number"
          value={importMeta.marking_start_page}
          onChange={(e) =>
            setImportMeta((prev) => ({
              ...prev,
              marking_start_page: e.target.value,
            }))
          }
        />

        <TextField
          size="small"
          label="Mark Page End"
          type="number"
          value={importMeta.marking_end_page}
          onChange={(e) =>
            setImportMeta((prev) => ({
              ...prev,
              marking_end_page: e.target.value,
            }))
          }
        />
      </Box>

      {isParsingPdf && (
        <Alert
          severity="info"
          sx={{
            mt: 2,
            borderRadius: "12px",
            display: "flex",
            alignItems: "center",
          }}
          icon={<CircularProgress size={18} />}
        >
          Parsing PDF... This may take a few minutes. Elapsed time: {parsingElapsed}s.
          Please do not refresh this page.
        </Alert>
      )}

      {selectedImportType === "kertas2" && (
        <Alert severity="info" sx={{ mt: 2, borderRadius: "12px" }}>
          K2 import will parse the question PDF together with the marking scheme PDF.
          Each subpart will appear as a draft item, while grouped questions are shown
          together during review.
        </Alert>
      )}
    </Paper>
  );

  const renderQuestions = () => (
    <Box>
      {renderQuestionImportPanel()}
      {renderImportBatchesPanel()}

      <Paper
        elevation={0}
        sx={{
          p: 3,
          borderRadius: "18px",
          border: "1px solid #E5E7EB",
        }}
      >
        <Box sx={{ mb: 2 }}>
          <Box>
            <Typography variant="h6" fontWeight="900">
              Question Bank
            </Typography>

            <Typography variant="body2" color="text.secondary">
              Search, filter, edit, or deactivate questions.
            </Typography>
          </Box>
        </Box>

        <Box
          sx={{
            display: "grid",
            gridTemplateColumns: {
              xs: "1fr",
              md: "1fr 150px 150px 150px 160px auto",
            },
            gap: 1.5,
            alignItems: "center",
            mb: 3,
          }}
        >
          <TextField
            size="small"
            placeholder="Search question, chapter, or form"
            value={questionFilters.search}
            onChange={(e) =>
              setQuestionFilters((prev) => ({
                ...prev,
                search: e.target.value,
              }))
            }
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchOutlinedIcon />
                </InputAdornment>
              ),
            }}
          />

          <FormControl size="small" fullWidth>
            <InputLabel>Paper</InputLabel>
            <Select
              label="Paper"
              value={questionFilters.paper_type}
              onChange={(e) =>
                setQuestionFilters((prev) => ({
                  ...prev,
                  paper_type: e.target.value,
                }))
              }
            >
              <MenuItem value="all">All Papers</MenuItem>
              <MenuItem value="kertas1">Kertas 1</MenuItem>
              <MenuItem value="kertas2">Kertas 2</MenuItem>
            </Select>
          </FormControl>

          <FormControl size="small" fullWidth>
            <InputLabel>Status</InputLabel>
            <Select
              label="Status"
              value={questionFilters.status}
              onChange={(e) =>
                setQuestionFilters((prev) => ({
                  ...prev,
                  status: e.target.value,
                }))
              }
            >
              <MenuItem value="all">All Status</MenuItem>
              <MenuItem value="active">Active</MenuItem>
              <MenuItem value="inactive">Inactive</MenuItem>
            </Select>
          </FormControl>

          <FormControl size="small" fullWidth>
            <InputLabel>Form</InputLabel>
            <Select
              label="Form"
              value={questionFilters.form}
              onChange={(e) =>
                setQuestionFilters((prev) => ({
                  ...prev,
                  form: e.target.value,
                }))
              }
            >
              <MenuItem value="all">All Forms</MenuItem>
              {formOptions.map((form) => (
                <MenuItem key={form} value={form}>
                  {form}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <FormControl size="small" fullWidth>
            <InputLabel>Difficulty</InputLabel>
            <Select
              label="Difficulty"
              value={questionFilters.difficulty}
              onChange={(e) =>
                setQuestionFilters((prev) => ({
                  ...prev,
                  difficulty: e.target.value,
                }))
              }
            >
              <MenuItem value="all">All Difficulty</MenuItem>
              {difficultyOptions.map((difficulty) => (
                <MenuItem key={difficulty} value={difficulty}>
                  {difficulty}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <Button
            variant="outlined"
            onClick={() =>
              setQuestionFilters({
                search: "",
                paper_type: "all",
                status: "all",
                form: "all",
                difficulty: "all",
              })
            }
            sx={{
              borderRadius: "10px",
              textTransform: "none",
              fontWeight: "800",
              whiteSpace: "nowrap",
            }}
          >
            Clear
          </Button>
        </Box>

        <Stack gap={1.5}>
          {questions.length === 0 ? (
            <Alert severity="info" sx={{ borderRadius: "12px" }}>
              No questions loaded.
            </Alert>
          ) : (
            questions.map((question) => (
              <Paper
                key={question.id}
                elevation={0}
                sx={{
                  p: 2,
                  borderRadius: "14px",
                  border: "1px solid #E5E7EB",
                }}
              >
                <Box
                  sx={{
                    display: "flex",
                    justifyContent: "space-between",
                    gap: 2,
                    alignItems: "flex-start",
                  }}
                >
                  <Box sx={{ minWidth: 0 }}>
                    <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap", mb: 1 }}>
                      <Chip size="small" label={question.paper_type || "question"} />

                      <Chip
                        size="small"
                        label={question.form || question.verified_form || "Form -"}
                      />

                      {question.part && (
                        <Chip size="small" label={`Part (${question.part})`} />
                      )}

                      {question.subpart && (
                        <Chip size="small" label={`Subpart (${question.subpart})`} />
                      )}

                      {question.sub_subpart && (
                        <Chip size="small" label={`Sub-subpart (${question.sub_subpart})`} />
                      )}

                      {renderStatusChip(question.is_active)}
                    </Box>

                    <Typography
                      fontWeight="900"
                      sx={{
                        maxWidth: "900px",
                        display: "-webkit-box",
                        WebkitLineClamp: 2,
                        WebkitBoxOrient: "vertical",
                        overflow: "hidden",
                      }}
                    >
                      {getQuestionListLabel(question)}: {getQuestionPreviewText(question)}
                    </Typography>

                    <Typography variant="body2" color="text.secondary" sx={{ mt: 0.75 }}>
                      {question.chapter || question.verified_chapter || "No chapter"}
                    </Typography>
                  </Box>

                  <Box sx={{ display: "flex", gap: 1, flexShrink: 0 }}>
                    <Button
                      size="small"
                      variant="contained"
                      startIcon={<VisibilityOutlinedIcon />}
                      onClick={() => handleOpenQuestionDetail(question)}
                      sx={{
                        bgcolor: "#3855c0",
                        borderRadius: "10px",
                        textTransform: "none",
                        fontWeight: "800",
                        "&:hover": { bgcolor: "#2d4499" },
                      }}
                    >
                      View / Edit
                    </Button>

                    <Button
                      size="small"
                      variant="outlined"
                      color={Number(question.is_active ?? 1) === 1 ? "error" : "success"}
                      startIcon={
                        Number(question.is_active ?? 1) === 1 ? (
                          <BlockOutlinedIcon />
                        ) : (
                          <CheckCircleOutlineOutlinedIcon />
                        )
                      }
                      onClick={() => handleQuestionStatusToggle(question)}
                      sx={{
                        borderRadius: "10px",
                        textTransform: "none",
                        fontWeight: "800",
                      }}
                    >
                      {Number(question.is_active ?? 1) === 1 ? "Deactivate" : "Reactivate"}
                    </Button>
                  </Box>
                </Box>
              </Paper>
            ))
          )}
        </Stack>
      </Paper>
    </Box>
  );

  const renderReviewVariantBasicPreview = () => {
    const questionJson = getVariantQuestionJson();
    const schemeJson = getVariantSchemeJson();

    const instructionsEn = getDraftInstructionText(questionJson, "instructions_en");
    const instructionsMs = getDraftInstructionText(questionJson, "instructions_ms");

    const options = Array.isArray(questionJson.options) ? questionJson.options : [];
    const steps = Array.isArray(schemeJson.steps) ? schemeJson.steps : [];

    const formatFinalAnswers = () => {
      if (schemeJson.final_answer) {
        return typeof schemeJson.final_answer === "object"
          ? JSON.stringify(schemeJson.final_answer)
          : String(schemeJson.final_answer);
      }

      if (schemeJson.answer_value) {
        return String(schemeJson.answer_value);
      }

      if (schemeJson.correct_option) {
        return String(schemeJson.correct_option);
      }

      if (schemeJson.final_answers && typeof schemeJson.final_answers === "object") {
        return Object.entries(schemeJson.final_answers)
          .map(([part, answer]) => `${part}: ${answer}`)
          .join(" | ");
      }

      return "-";
    };

    const getStepTitle = (step, index) => {
      const partLabel = step.display_subpart_label
        ? `${step.display_subpart_label} `
        : "";

      return `${partLabel}Step ${step.step_no || index + 1}: ${
        step.label || step.step || "Marking point"
      }`;
    };

    const getStepContent = (step) => {
      const lines = [];

      if (step.text) {
        lines.push(step.text);
      }

      if (step.answer) {
        lines.push(
          Array.isArray(step.answer) ? step.answer.join(", ") : String(step.answer)
        );
      }

      if (step.math) {
        lines.push(step.math);
      }

      if (step.keywords && Array.isArray(step.keywords) && step.keywords.length > 0) {
        lines.push(`Keywords: ${step.keywords.join(", ")}`);
      }

      return lines.join("\n");
    };

    return (
      <Stack gap={2}>
        <TextField
          label="Instruction English"
          value={instructionsEn}
          multiline
          minRows={3}
          fullWidth
          InputProps={{ readOnly: true }}
        />

        <TextField
          label="Instruction Bahasa Melayu"
          value={instructionsMs}
          multiline
          minRows={3}
          fullWidth
          InputProps={{ readOnly: true }}
        />

        {options.length > 0 && (
          <Paper
            elevation={0}
            sx={{
              p: 2,
              borderRadius: "12px",
              border: "1px solid #E5E7EB",
            }}
          >
            <Typography fontWeight="900" mb={1}>
              Options
            </Typography>

            <Stack gap={1}>
              {options.map((option) => (
                <Box
                  key={option.label}
                  sx={{
                    p: 1.25,
                    borderRadius: "10px",
                    bgcolor: "#F9FAFB",
                    border: "1px solid #E5E7EB",
                  }}
                >
                  <Typography fontWeight="900">
                    Option {option.label}
                  </Typography>

                  <Typography variant="body2">
                    EN: {option.text_en || "-"}
                  </Typography>

                  <Typography variant="body2" color="text.secondary">
                    BM: {option.text_ms || "-"}
                  </Typography>
                </Box>
              ))}
            </Stack>
          </Paper>
        )}

        <Paper
          elevation={0}
          sx={{
            p: 2,
            borderRadius: "12px",
            border: "1px solid #E5E7EB",
          }}
        >
          <Typography fontWeight="900" mb={1}>
            Marking Scheme
          </Typography>

          <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap", mb: 1.5 }}>
            <Chip size="small" label={`Final answer: ${formatFinalAnswers()}`} />
            <Chip
              size="small"
              label={`Answer type: ${schemeJson.answer_type || schemeJson.type || "-"}`}
            />
            <Chip
              size="small"
              label={`Marks: ${
                schemeJson.subpart_marks ||
                schemeJson.question_total_marks ||
                schemeJson.max_score ||
                "-"
              }`}
            />
          </Box>

          {steps.length === 0 ? (
            <Typography variant="body2" color="text.secondary">
              No marking steps available.
            </Typography>
          ) : (
            <Stack gap={1}>
              {steps.map((step, index) => {
                const stepContent = getStepContent(step);

                return (
                  <Box
                    key={index}
                    sx={{
                      p: 1.25,
                      borderRadius: "10px",
                      bgcolor: "#F9FAFB",
                      border: "1px solid #E5E7EB",
                    }}
                  >
                    <Typography fontWeight="900" mb={0.75}>
                      {getStepTitle(step, index)}
                    </Typography>

                    {stepContent ? (
                      <Box sx={{ whiteSpace: "pre-wrap" }}>
                        {renderMixedLatexPreview(stepContent)}
                      </Box>
                    ) : (
                      <Typography variant="body2" color="text.secondary">
                        -
                      </Typography>
                    )}

                    <Typography variant="caption" color="text.secondary">
                      Marks: {step.marks ?? "-"}
                    </Typography>
                  </Box>
                );
              })}
            </Stack>
          )}
        </Paper>
      </Stack>
    );
  };

  const renderReviewVariants = () => (
    <Paper
      elevation={0}
      sx={{
        p: 3,
        borderRadius: "18px",
        border: "1px solid #E5E7EB",
      }}
    >
      <Box sx={{ mb: 2 }}>
        <Typography variant="h6" fontWeight="900">
          AI Review Variants
        </Typography>

        <Typography variant="body2" color="text.secondary">
          View AI-generated review questions and edit their JSON when needed.
        </Typography>
      </Box>

      <Box
        sx={{
          display: "grid",
          gridTemplateColumns: {
            xs: "1fr",
            md: "1fr 220px auto",
          },
          gap: 1.5,
          alignItems: "center",
          mb: 3,
        }}
      >
        <TextField
          size="small"
          placeholder="Search generated question or type"
          value={reviewVariantFilters.search}
          onChange={(e) =>
            setReviewVariantFilters((prev) => ({
              ...prev,
              search: e.target.value,
            }))
          }
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchOutlinedIcon />
              </InputAdornment>
            ),
          }}
        />

        <FormControl size="small" fullWidth>
          <InputLabel>Variant Type</InputLabel>
          <Select
            label="Variant Type"
            value={reviewVariantFilters.variant_type}
            onChange={(e) =>
              setReviewVariantFilters((prev) => ({
                ...prev,
                variant_type: e.target.value,
              }))
            }
          >
            <MenuItem value="all">All Types</MenuItem>
            <MenuItem value="number_variant">Number Variant</MenuItem>
            <MenuItem value="same_diagram_followup">Same Diagram</MenuItem>
            <MenuItem value="k1_mcq_variant">K1 MCQ Variant</MenuItem>
          </Select>
        </FormControl>

        <Button
          variant="outlined"
          onClick={() =>
            setReviewVariantFilters({
              search: "",
              variant_type: "all",
            })
          }
          sx={{
            borderRadius: "10px",
            textTransform: "none",
            fontWeight: "800",
            whiteSpace: "nowrap",
          }}
        >
          Clear
        </Button>
      </Box>

      <Stack gap={1.5}>
        {reviewVariants.length === 0 ? (
          <Alert severity="info" sx={{ borderRadius: "12px" }}>
            No AI review variants found.
          </Alert>
        ) : (
          reviewVariants.map((variant) => (
            <Paper
              key={variant.variant_id}
              elevation={0}
              sx={{
                p: 2,
                borderRadius: "14px",
                border: "1px solid #E5E7EB",
              }}
            >
              <Box
                sx={{
                  display: "flex",
                  justifyContent: "space-between",
                  gap: 2,
                  alignItems: "flex-start",
                }}
              >
                <Box sx={{ minWidth: 0 }}>
                  <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap", mb: 1 }}>
                    <Chip size="small" label={`#${variant.variant_id}`} />
                    <Chip size="small" label={variant.variant_type || "variant"} />
                    <Chip size="small" label={variant.source_mode || "source"} />
                    <Chip size="small" label={variant.status || "status"} />
                    <Chip size="small" label={variant.language || "language"} />
                  </Box>

                  <Typography
                    fontWeight="900"
                    sx={{
                      maxWidth: "900px",
                      display: "-webkit-box",
                      WebkitLineClamp: 2,
                      WebkitBoxOrient: "vertical",
                      overflow: "hidden",
                    }}
                  >
                    {getReviewVariantPreviewText(variant)}
                  </Typography>

                  <Typography variant="body2" color="text.secondary" sx={{ mt: 0.75 }}>
                    Source: {variant.source_key || "-"} · Student:{" "}
                    {variant.student_name || `User ${variant.user_id}`}
                  </Typography>
                </Box>

                <Button
                  size="small"
                  variant="contained"
                  startIcon={<VisibilityOutlinedIcon />}
                  onClick={() => handleOpenReviewVariantDetail(variant)}
                  sx={{
                    bgcolor: "#3855c0",
                    borderRadius: "10px",
                    textTransform: "none",
                    fontWeight: "800",
                    flexShrink: 0,
                    "&:hover": { bgcolor: "#2d4499" },
                  }}
                >
                  View / Edit
                </Button>
              </Box>
            </Paper>
          ))
        )}
      </Stack>
    </Paper>
  );

  const renderUsers = () => (
    <Paper
      elevation={0}
      sx={{
        p: 3,
        borderRadius: "18px",
        border: "1px solid #E5E7EB",
      }}
    >
    <Box
      sx={{
        display: "flex",
        justifyContent: "space-between",
        gap: 2,
        flexWrap: "wrap",
        mb: 2.5,
      }}
    >
      <Box>
        <Typography variant="h6" fontWeight="900">
          User Management
        </Typography>

        <Typography variant="body2" color="text.secondary">
          Search users, view account details, and manage admin access.
        </Typography>
      </Box>

      <Button
        variant="contained"
        startIcon={<PersonAddAltOutlinedIcon />}
        onClick={() => {
          setAddAdminResetLink("");
          setAddAdminOpen(true);
        }}
        sx={{
          bgcolor: "#3855c0",
          borderRadius: "12px",
          textTransform: "none",
          fontWeight: "900",
          "&:hover": { bgcolor: "#2d4499" },
        }}
      >
        Add Admin
      </Button>
    </Box>
      <Box
        sx={{
          display: "grid",
          gridTemplateColumns: { xs: "1fr", md: "1fr 170px 170px" },
          gap: 2,
          mb: 2.5,
        }}
      >
        <TextField
          size="small"
          placeholder="Search name or email"
          value={userFilters.search}
          onChange={(e) =>
            setUserFilters((prev) => ({
              ...prev,
              search: e.target.value,
            }))
          }
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchOutlinedIcon sx={{ color: "#9CA3AF" }} />
              </InputAdornment>
            ),
          }}
        />

        <FormControl size="small" fullWidth>
          <InputLabel>Role</InputLabel>
          <Select
            label="Role"
            value={userFilters.role}
            onChange={(e) =>
              setUserFilters((prev) => ({
                ...prev,
                role: e.target.value,
              }))
            }
          >
            {roleOptions.map((option) => (
              <MenuItem key={option.value} value={option.value}>
                {option.label}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        <FormControl size="small" fullWidth>
          <InputLabel>Status</InputLabel>
          <Select
            label="Status"
            value={userFilters.status}
            onChange={(e) =>
              setUserFilters((prev) => ({
                ...prev,
                status: e.target.value,
              }))
            }
          >
            {statusOptions.map((option) => (
              <MenuItem key={option.value} value={option.value}>
                {option.label}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </Box>

      <Stack gap={1.5}>
        {users.length === 0 ? (
          <Alert severity="info" sx={{ borderRadius: "12px" }}>
            No users loaded yet. Connect /api/admin/users next, then this list
            will populate automatically.
          </Alert>
        ) : (
          users.map((targetUser) => (
            <Paper
              key={targetUser.id}
              elevation={0}
              sx={{
                p: 2,
                borderRadius: "14px",
                border: "1px solid #E5E7EB",
              }}
            >
              <Box
                sx={{
                  display: "flex",
                  justifyContent: "space-between",
                  gap: 2,
                  alignItems: "center",
                }}
              >
                <Box sx={{ minWidth: 0 }}>
                  <Typography fontWeight="900" color="#111827" noWrap>
                    {targetUser.name || "Unnamed User"}
                  </Typography>

                  <Typography variant="body2" color="text.secondary" noWrap>
                    {targetUser.email}
                  </Typography>

                  <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap", mt: 1 }}>
                    <Chip size="small" label={targetUser.role} />
                    {renderStatusChip(targetUser.is_active)}
                  </Box>
                </Box>

                <Box sx={{ display: "flex", gap: 1, flexShrink: 0 }}>
                  <Button
                    size="small"
                    variant="contained"
                    startIcon={<VisibilityOutlinedIcon />}
                    onClick={() => handleOpenUserDetail(targetUser)}
                    sx={{
                      bgcolor: "#3855c0",
                      borderRadius: "10px",
                      textTransform: "none",
                      fontWeight: "800",
                      "&:hover": { bgcolor: "#2d4499" },
                    }}
                  >
                    View
                  </Button>

                  <Button
                    size="small"
                    variant="outlined"
                    color={Number(targetUser.is_active ?? 1) === 1 ? "error" : "success"}
                    startIcon={
                      Number(targetUser.is_active ?? 1) === 1 ? (
                        <BlockOutlinedIcon />
                      ) : (
                        <CheckCircleOutlineOutlinedIcon />
                      )
                    }
                    onClick={() => handleUserStatusToggle(targetUser)}
                    sx={{
                      borderRadius: "10px",
                      textTransform: "none",
                      fontWeight: "800",
                    }}
                  >
                    {Number(targetUser.is_active ?? 1) === 1 ? "Deactivate" : "Reactivate"}
                  </Button>
                </Box>
              </Box>
            </Paper>
          ))
        )}
      </Stack>
    </Paper>
  );

  return (
    <Box sx={{ minHeight: "100vh", bgcolor: "#F8FAFC", p: { xs: 2, md: 4 } }}>
      <Box sx={{ maxWidth: 1200, mx: "auto" }}>
        <Box
          sx={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
            gap: 2,
            mb: 3,
          }}
        >
          <Box>
            <Typography variant="h4" fontWeight="900" color="#111827">
              Admin Dashboard
            </Typography>

            <Typography color="text.secondary">
              Welcome, {user?.name || "Admin"}. Manage EasyLearn question bank and
              users here.
            </Typography>
          </Box>

        </Box>

        {message && (
          <Alert severity={message.type} sx={{ mb: 2.5, borderRadius: "12px" }}>
            {message.text}
          </Alert>
        )}

        <Paper
          elevation={0}
          sx={{
            borderRadius: "18px",
            border: "1px solid #E5E7EB",
            mb: 3,
            overflow: "hidden",
          }}
        >
          <Tabs
            value={activeTab}
            onChange={(e, value) => setActiveTab(value)}
            variant="scrollable"
            scrollButtons="auto"
            sx={{ px: 1, bgcolor: "#ffffff" }}
          >
            <Tab
              value="overview"
              icon={<DashboardOutlinedIcon />}
              iconPosition="start"
              label="Overview"
            />
            <Tab
              value="questions"
              icon={<QuizOutlinedIcon />}
              iconPosition="start"
              label="Questions"
            />
            <Tab
              value="variants"
              icon={<QuizOutlinedIcon />}
              iconPosition="start"
              label="AI Variants"
            />
            <Tab
              value="users"
              icon={<GroupOutlinedIcon />}
              iconPosition="start"
              label="Users"
            />
          </Tabs>
        </Paper>

        {loading ? (
          <Box sx={{ display: "flex", justifyContent: "center", py: 8 }}>
            <CircularProgress />
          </Box>
        ) : (
          <>
            {activeTab === "overview" && renderOverview()}
            {activeTab === "questions" && renderQuestions()}
            {activeTab === "variants" && renderReviewVariants()}
            {activeTab === "users" && renderUsers()}
          </>
        )}
      </Box>
    <Dialog
      open={questionDetailOpen}
      onClose={() => setQuestionDetailOpen(false)}
      maxWidth="md"
      fullWidth
      PaperProps={{ sx: { borderRadius: "20px" } }}
    >
      <DialogTitle
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          fontWeight: 900,
        }}
      >
        Question Detail

        <IconButton onClick={() => setQuestionDetailOpen(false)}>
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      <DialogContent dividers>
        {questionDetailLoading ? (
          <Box sx={{ display: "flex", justifyContent: "center", py: 5 }}>
            <CircularProgress />
          </Box>
        ) : !selectedQuestionDetail ? (
          <Alert severity="info">No question detail loaded.</Alert>
        ) : (
          (() => {
            const questionJson = getQuestionEditJson();
            const normalizedPaperType = String(
              selectedQuestionDetail?.paper_type || questionJson.paper_type || ""
            ).toLowerCase();

            const normalizedQuestionType = String(
              questionJson.question_type || ""
            ).toLowerCase();

            const isK2 =
              normalizedPaperType === "kertas2" ||
              (normalizedPaperType !== "kertas1" && normalizedQuestionType !== "mcq");

            return (
              <Stack gap={2.5}>
                <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap" }}>
                  <Chip label={`Q${questionJson.question_no || selectedQuestionDetail.id}`} />
                  <Chip label={isK2 ? "Kertas 2" : "Kertas 1"} />
                  <Chip label={questionJson.verified_form || questionJson.form || "No Form"} />
                  <Chip
                    label={
                      Number(selectedQuestionDetail.is_active ?? 1) === 1
                        ? "Active"
                        : "Inactive"
                    }
                    color={Number(selectedQuestionDetail.is_active ?? 1) === 1 ? "success" : "error"}
                  />
                </Box>

                {questionEditErrors.length > 0 && (
                  <Alert severity="error" sx={{ borderRadius: "12px" }}>
                    <Typography fontWeight="900" mb={0.5}>
                      Please fix before saving:
                    </Typography>

                    <Box component="ul" sx={{ pl: 2.5, m: 0 }}>
                      {questionEditErrors.map((error, index) => (
                        <li key={index}>
                          <Typography variant="body2">{error}</Typography>
                        </li>
                      ))}
                    </Box>
                  </Alert>
                )}
                {questionEditSuccess && (
                  <Alert severity="success" sx={{ borderRadius: "12px" }}>
                    {questionEditSuccess}
                  </Alert>
                )}

                <Box
                  sx={{
                    display: "grid",
                    gridTemplateColumns: {
                      xs: "1fr",
                      md: isK2
                        ? "120px 1fr 1fr 160px"
                        : "120px 1fr 1fr 160px 160px",
                    },
                    gap: 1.5,
                  }}
                >
                  <TextField
                    size="small"
                    label="Question No"
                    value={questionJson.question_no || ""}
                    onChange={(e) =>
                      updateQuestionEditField("question_no", e.target.value)
                    }
                  />

                  <FormControl size="small" fullWidth>
                    <InputLabel>Form</InputLabel>
                    <Select
                      label="Form"
                      value={questionJson.form || questionJson.verified_form || ""}
                      onChange={(e) =>
                        updateQuestionEditFields({
                          form: e.target.value,
                          verified_form: e.target.value,
                        })
                      }
                    >
                      {formOptions.map((form) => (
                        <MenuItem key={form} value={form}>
                          {form}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>

                  <Autocomplete
                    freeSolo
                    size="small"
                    options={getChapterOptions(questionJson)}
                    value={questionJson.chapter || questionJson.verified_chapter || ""}
                    onChange={(event, newValue) =>
                      updateQuestionEditFields({
                        chapter: newValue || "",
                        verified_chapter: newValue || "",
                      })
                    }
                    onInputChange={(event, newInputValue) =>
                      updateQuestionEditFields({
                        chapter: newInputValue || "",
                        verified_chapter: newInputValue || "",
                      })
                    }
                    renderInput={(params) => (
                      <TextField {...params} label="Chapter" />
                    )}
                  />

                  <FormControl size="small" fullWidth>
                    <InputLabel>Difficulty</InputLabel>
                    <Select
                      label="Difficulty"
                      value={questionJson.difficulty || ""}
                      onChange={(e) =>
                        updateQuestionEditField("difficulty", e.target.value)
                      }
                    >
                      {difficultyOptions.map((difficulty) => (
                        <MenuItem key={difficulty} value={difficulty}>
                          {difficulty}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>

                  {!isK2 && (
                    <FormControl size="small" fullWidth>
                      <InputLabel>Correct Answer</InputLabel>
                      <Select
                        label="Correct Answer"
                        value={questionJson.correct_option || ""}
                        onChange={(e) =>
                          updateQuestionEditField("correct_option", e.target.value)
                        }
                      >
                        {["A", "B", "C", "D"].map((option) => (
                          <MenuItem key={option} value={option}>
                            {option}
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  )}
                </Box>

                {isK2 && (
                  <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap" }}>
                    <Chip size="small" label={questionJson.group_id || "No group"} />
                    <Chip size="small" label={`Stage ${questionJson.stage_index || 1}`} />
                    <Chip size="small" label={questionJson.exercise_stage_id || "No stage id"} />
                    {questionJson.group_chapter && (
                      <Chip size="small" label={questionJson.group_chapter} />
                    )}
                  </Box>
                )}

                <TextField
                  label="Question Text English"
                  value={getDraftInstructionText(questionJson, "instructions_en")}
                  onChange={(e) =>
                    updateQuestionEditInstruction("instructions_en", e.target.value)
                  }
                  multiline
                  minRows={3}
                  fullWidth
                />

                <TextField
                  label="Question Text Bahasa Melayu"
                  value={getDraftInstructionText(questionJson, "instructions_ms")}
                  onChange={(e) =>
                    updateQuestionEditInstruction("instructions_ms", e.target.value)
                  }
                  multiline
                  minRows={3}
                  fullWidth
                />

                {questionJson.image_path && (
                  <Paper
                    elevation={0}
                    sx={{
                      p: 2,
                      borderRadius: "14px",
                      border: "1px solid #E5E7EB",
                    }}
                  >
                    <Typography fontWeight="900" mb={1}>
                      Question Image
                    </Typography>

                    <Box sx={{ display: "flex", justifyContent: "center" }}>
                      <img
                        src={questionJson.image_path}
                        alt="Question"
                        style={{
                          maxWidth: "100%",
                          maxHeight: "300px",
                          objectFit: "contain",
                          borderRadius: "12px",
                          border: "1px solid #E5E7EB",
                        }}
                      />
                    </Box>
                  </Paper>
                )}

                {isK2 ? (
                  renderK2MarkingSchemePreview(
                    questionJson,
                    updateQuestionK2MarkingStep,
                    updateQuestionK2MarkingSchemeField
                  )
                ) : (
                  <>
                    <Typography fontWeight="900">Options</Typography>

                    {["A", "B", "C", "D"].map((label) => (
                      <Paper
                        key={label}
                        elevation={0}
                        sx={{
                          p: 2,
                          borderRadius: "12px",
                          border: "1px solid #E5E7EB",
                          bgcolor: "#F9FAFB",
                        }}
                      >
                        <Typography fontWeight="900" mb={1}>
                          Option {label}
                        </Typography>

                        <Box
                          sx={{
                            display: "grid",
                            gridTemplateColumns: { xs: "1fr", md: "1fr 1fr" },
                            gap: 1.5,
                          }}
                        >
                          <TextField
                            size="small"
                            label={`Option ${label} English`}
                            value={getDraftOptionValue(questionJson, label, "text_en")}
                            onChange={(e) =>
                              updateQuestionEditOption(label, "text_en", e.target.value)
                            }
                            fullWidth
                          />

                          <TextField
                            size="small"
                            label={`Option ${label} BM`}
                            value={getDraftOptionValue(questionJson, label, "text_ms")}
                            onChange={(e) =>
                              updateQuestionEditOption(label, "text_ms", e.target.value)
                            }
                            fullWidth
                          />
                        </Box>
                      </Paper>
                    ))}
                  </>
                )}

                <Box
                  component="details"
                  sx={{
                    p: 2,
                    borderRadius: "12px",
                    border: "1px solid #E5E7EB",
                    bgcolor: "#F9FAFB",
                  }}
                >
                  <Typography
                    component="summary"
                    fontWeight="900"
                    sx={{ cursor: "pointer" }}
                  >
                    Advanced JSON View
                  </Typography>

                  <TextField
                    value={questionEditText}
                    onChange={(e) => setQuestionEditText(e.target.value)}
                    multiline
                    minRows={8}
                    fullWidth
                    helperText="Only edit this if you need to adjust technical fields."
                    sx={{
                      mt: 2,
                      "& textarea": {
                        fontFamily: "Consolas, Monaco, 'Courier New', monospace",
                        fontSize: "13px",
                      },
                    }}
                  />
                </Box>
              </Stack>
            );
          })()
        )}
      </DialogContent>

      <DialogActions sx={{ px: 3, py: 2 }}>
        <Button
          variant="contained"
          disabled={questionEditSaving || questionDetailLoading || !selectedQuestionDetail}
          onClick={handleSaveQuestionEdit}
          sx={{
            bgcolor: "#3855c0",
            borderRadius: "10px",
            textTransform: "none",
            fontWeight: "900",
            "&:hover": { bgcolor: "#2d4499" },
          }}
        >
          {questionEditSaving ? "Saving..." : "Save Changes"}
        </Button>

        <Button
          onClick={() => setQuestionDetailOpen(false)}
          sx={{ textTransform: "none", fontWeight: 800 }}
        >
          Close
        </Button>
      </DialogActions>
    </Dialog>
    <Dialog
      open={userDetailOpen}
      onClose={() => setUserDetailOpen(false)}
      maxWidth="sm"
      fullWidth
      PaperProps={{ sx: { borderRadius: "20px" } }}
    >
      <DialogTitle
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          fontWeight: 900,
        }}
      >
        User Detail

        <IconButton onClick={() => setUserDetailOpen(false)}>
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      <DialogContent dividers>
        {userDetailLoading ? (
          <Box sx={{ display: "flex", justifyContent: "center", py: 5 }}>
            <CircularProgress />
          </Box>
        ) : !selectedUserDetail ? (
          <Alert severity="info">No user detail loaded.</Alert>
        ) : (
          <Stack gap={2.5}>
            <Paper elevation={0} sx={{ p: 2, borderRadius: "14px", border: "1px solid #E5E7EB" }}>
              <Typography variant="h6" fontWeight="900">
                {selectedUserDetail.name || "Unnamed User"}
              </Typography>

              <Typography color="text.secondary">
                {selectedUserDetail.email}
              </Typography>

              <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap", mt: 1.5 }}>
                <Chip label={selectedUserDetail.role} />
                <Chip label={selectedUserDetail.language || "No language"} />
                <Chip
                  label={
                    Number(selectedUserDetail.is_active ?? 1) === 1
                      ? "Active"
                      : "Inactive"
                  }
                  color={Number(selectedUserDetail.is_active ?? 1) === 1 ? "success" : "error"}
                />
              </Box>
            </Paper>

            <Paper elevation={0} sx={{ p: 2, borderRadius: "14px", border: "1px solid #E5E7EB" }}>
              <Typography fontWeight="900" mb={1}>Account Information</Typography>

              <Typography variant="body2">
                Auth Provider: {selectedUserDetail.auth_provider || "-"}
              </Typography>

              <Typography variant="body2">
                Student Code: {selectedUserDetail.student_code || "-"}
              </Typography>

              <Typography variant="body2">
                Created At: {selectedUserDetail.created_at || "-"}
              </Typography>
            </Paper>

            {selectedUserDetail.role === "parent" && (
              <Paper
                elevation={0}
                sx={{
                  p: 2,
                  borderRadius: "14px",
                  border: "1px solid #E5E7EB",
                }}
              >
                <Typography fontWeight="900" mb={1}>
                  Linked Students
                </Typography>

                {(selectedUserDetail.linked_students || []).length === 0 ? (
                  <Typography color="text.secondary">
                    No student currently linked to this parent.
                  </Typography>
                ) : (
                  <Stack gap={1}>
                    {selectedUserDetail.linked_students.map((student) => (
                      <Box
                        key={student.link_id || student.student_id}
                        sx={{
                          p: 1.5,
                          borderRadius: "12px",
                          bgcolor: "#F9FAFB",
                          border: "1px solid #E5E7EB",
                        }}
                      >
                        <Typography fontWeight="900">
                          {student.nickname || student.student_name || "Unnamed Student"}
                        </Typography>

                        <Typography variant="body2" color="text.secondary">
                          {student.student_email || "-"}
                        </Typography>

                        <Typography variant="caption" color="text.secondary">
                          Student Code: {student.student_code || "-"} · Linked at:{" "}
                          {student.linked_at || "-"}
                        </Typography>
                      </Box>
                    ))}
                  </Stack>
                )}
              </Paper>
            )}

            {selectedUserDetail.role === "student" && selectedUserStats && (
              <Paper elevation={0} sx={{ p: 2, borderRadius: "14px", border: "1px solid #E5E7EB" }}>
                <Typography fontWeight="900" mb={1}>Learning Summary</Typography>

                <Box
                  sx={{
                    display: "grid",
                    gridTemplateColumns: "repeat(2, 1fr)",
                    gap: 1.5,
                  }}
                >
                  <Box sx={{ p: 1.5, borderRadius: "12px", bgcolor: "#EEF2FF" }}>
                    <Typography variant="caption" color="text.secondary">
                      Attempts
                    </Typography>
                    <Typography variant="h6" fontWeight="900">
                      {selectedUserStats.total_attempts || 0}
                    </Typography>
                  </Box>

                  <Box sx={{ p: 1.5, borderRadius: "12px", bgcolor: "#ECFDF5" }}>
                    <Typography variant="caption" color="text.secondary">
                      Accuracy
                    </Typography>
                    <Typography variant="h6" fontWeight="900">
                      {selectedUserStats.overall_accuracy || 0}%
                    </Typography>
                  </Box>

                  <Box sx={{ p: 1.5, borderRadius: "12px", bgcolor: "#FFF7ED" }}>
                    <Typography variant="caption" color="text.secondary">
                      Sessions
                    </Typography>
                    <Typography variant="h6" fontWeight="900">
                      {selectedUserStats.total_sessions || 0}
                    </Typography>
                  </Box>

                  <Box sx={{ p: 1.5, borderRadius: "12px", bgcolor: "#FDF2F8" }}>
                    <Typography variant="caption" color="text.secondary">
                      Last Practice
                    </Typography>
                    <Typography variant="body2" fontWeight="900">
                      {selectedUserStats.last_practice_at || "-"}
                    </Typography>
                  </Box>
                </Box>
              </Paper>
            )}
          </Stack>
        )}
      </DialogContent>

      <DialogActions sx={{ px: 3, py: 2 }}>
        <Button
          onClick={() => setUserDetailOpen(false)}
          sx={{ textTransform: "none", fontWeight: 800 }}
        >
          Close
        </Button>
      </DialogActions>
    </Dialog>
    <Dialog
      open={batchDetailOpen}
      onClose={() => setBatchDetailOpen(false)}
      maxWidth="lg"
      fullWidth
      PaperProps={{ sx: { borderRadius: "20px" } }}
    >
      <DialogTitle
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          fontWeight: 900,
        }}
      >
        Import Draft Review

        <IconButton onClick={() => setBatchDetailOpen(false)}>
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      <DialogContent dividers>
        {batchLoading ? (
          <Box sx={{ display: "flex", justifyContent: "center", py: 6 }}>
            <CircularProgress />
          </Box>
        ) : !selectedBatch ? (
          <Alert severity="info">No batch selected.</Alert>
        ) : (
          <Box
            sx={{
              display: "grid",
              gridTemplateColumns: { xs: "1fr", md: "320px 1fr" },
              gap: 2.5,
            }}
          >
            <Paper
              elevation={0}
              sx={{
                p: 2,
                borderRadius: "14px",
                border: "1px solid #E5E7EB",
                maxHeight: "70vh",
                overflow: "auto",
              }}
            >
              <Typography fontWeight="900" mb={1}>
                {selectedBatch.title}
              </Typography>

              <Typography variant="body2" color="text.secondary" mb={2}>
                {batchItems.length} draft items
              </Typography>

              {(() => {
                const summary = getBatchReviewSummary();

                return (
                  <Alert
                    severity={summary.canCompleteReview ? "success" : "info"}
                    sx={{ borderRadius: "12px", mb: 2 }}
                  >
                    Reviewed {summary.reviewedCount}/{summary.total} questions.
                    {summary.pendingCount > 0
                      ? ` ${summary.pendingCount} question(s) still need to be approved or skipped.`
                      : " All questions have been reviewed."}
                  </Alert>
                );
              })()}

              <Stack gap={1.5}>
                {Object.entries(getGroupedBatchItems()).map(([groupKey, items]) => (
                  <Box key={groupKey}>
                    {selectedBatch?.paper_type === "kertas2" && (
                      <Typography
                        variant="caption"
                        fontWeight="900"
                        color="#3855c0"
                        sx={{ display: "block", mb: 0.75 }}
                      >
                        {groupKey}
                      </Typography>
                    )}

                    <Stack gap={1}>
                      {items.map((item) => {
                        const draftJson = getItemDraftJson(item);
                        const isActive = activeDraftItem?.item_id === item.item_id;

                        return (
                          <Box
                            key={item.item_id}
                            onClick={() => handleSelectDraftItem(item)}
                            sx={{
                              p: 1.5,
                              borderRadius: "12px",
                              border: isActive
                                ? "1px solid #3855c0"
                                : "1px solid #E5E7EB",
                              bgcolor: isActive ? "#EEF2FF" : "#ffffff",
                              cursor: "pointer",
                              "&:hover": {
                                bgcolor: isActive ? "#EEF2FF" : "#F9FAFB",
                              },
                            }}
                          >
                            <Typography fontWeight="900">
                              {getDraftPartLabel(draftJson, item)}
                            </Typography>

                            {selectedBatch?.paper_type === "kertas2" && (
                              <Typography variant="caption" color="text.secondary">
                                {draftJson.verified_chapter ||
                                  draftJson.chapter ||
                                  "No chapter"}{" "}
                                · {draftJson.display_marks || draftJson.marks || 0} mark(s)
                              </Typography>
                            )}

                            <Box
                              sx={{
                                display: "flex",
                                gap: 1,
                                flexWrap: "wrap",
                                mt: 0.8,
                              }}
                            >
                              <Chip size="small" label={item.status} />
                              {item.image_url && <Chip size="small" label="Image" />}
                              {selectedBatch?.paper_type === "kertas2" &&
                                draftJson.marking_scheme && (
                                  <Chip size="small" label="Scheme" />
                                )}
                            </Box>
                          </Box>
                        );
                      })}
                    </Stack>
                  </Box>
                ))}
              </Stack>
            </Paper>

            <Paper
              elevation={0}
              sx={{
                p: 2,
                borderRadius: "14px",
                border: "1px solid #E5E7EB",
                minWidth: 0,
              }}
            >
              {!activeDraftItem ? (
                <Alert severity="info">Select one draft item to review.</Alert>
              ) : (
                <Stack gap={2}>
                  <Box
                    sx={{
                      display: "flex",
                      justifyContent: "space-between",
                      gap: 2,
                      flexWrap: "wrap",
                      alignItems: "center",
                    }}
                  >
                    <Box>
                      <Typography variant="h6" fontWeight="900">
                        {(() => {
                          const activeJson = getActiveDraftJson();

                          return (
                            <Typography variant="h6" fontWeight="900">
                              {getDraftPartLabel(activeJson, activeDraftItem)}
                            </Typography>
                          );
                        })()}
                      </Typography>

                      <Typography variant="body2" color="text.secondary">
                        Review the extracted question details, then save or approve this draft item.
                      </Typography>
                    </Box>

                    <Chip label={activeDraftItem.status} />
                  </Box>

                  {draftValidationErrors.length > 0 && (
                    <Alert
                      ref={draftErrorRef}
                      severity="error"
                      sx={{ borderRadius: "12px" }}
                    >
                      <Typography fontWeight="900" mb={0.5}>
                        Please fix before approving:
                      </Typography>

                      <Box component="ul" sx={{ pl: 2.5, m: 0 }}>
                        {draftValidationErrors.map((error, index) => (
                          <li key={index}>
                            <Typography variant="body2">{error}</Typography>
                          </li>
                        ))}
                      </Box>
                    </Alert>
                  )}
                  {activeDraftItem.image_url && (
                    <Box>
                      <Typography fontWeight="900" mb={1}>
                        Extracted / Uploaded Image
                      </Typography>

                      <Box sx={{ display: "flex", justifyContent: "center" }}>
                        <img
                          src={activeDraftItem.image_url}
                          alt="Draft question"
                          style={{
                            maxWidth: "100%",
                            maxHeight: "260px",
                            objectFit: "contain",
                            borderRadius: "12px",
                            border: "1px solid #E5E7EB",
                          }}
                        />
                      </Box>
                    </Box>
                  )}

                  <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap", alignItems: "center" }}>
                    <Button
                      component="label"
                      variant="outlined"
                      startIcon={<UploadFileOutlinedIcon />}
                      disabled={uploadingImageItemId === activeDraftItem.item_id}
                      sx={{
                        borderRadius: "12px",
                        textTransform: "none",
                        fontWeight: "800",
                        alignSelf: "flex-start",
                      }}
                    >
                      {uploadingImageItemId === activeDraftItem.item_id
                        ? "Uploading..."
                        : "Replace Image"}

                      <input
                        hidden
                        type="file"
                        accept="image/*"
                        onChange={(e) => {
                          const file = e.target.files?.[0] || null;
                          if (file) {
                            handleReplaceDraftImage(activeDraftItem, file);
                          }
                        }}
                      />
                    </Button>

                    {(activeDraftItem.image_url ||
                      getActiveDraftJson().image_path ||
                      getActiveDraftJson().diagram_path) && (
                      <IconButton
                        color="error"
                        disabled={uploadingImageItemId === activeDraftItem.item_id}
                        onClick={() => handleAskDeleteDraftImage(activeDraftItem)}
                        sx={{
                          border: "1px solid #FECACA",
                          borderRadius: "12px",
                          width: 34,
                          height: 34,
                        }}
                      >
                        <DeleteOutlineOutlinedIcon />
                      </IconButton>
                    )}
                  </Box>


                  {(() => {
                    const draftJson = getActiveDraftJson();

                    return (
                      <Stack gap={2}>
                      <Box
                        sx={{
                          display: "grid",
                          gridTemplateColumns: {
                            xs: "1fr",
                            md:
                              selectedBatch?.paper_type === "kertas2"
                                ? "120px 1fr 1fr 160px"
                                : "120px 1fr 1fr 160px 160px",
                          },
                          gap: 1.5,
                        }}
                      >
                        <TextField
                          size="small"
                          label="Question No"
                          value={draftJson.question_no || ""}
                          onChange={(e) => updateDraftField("question_no", e.target.value)}
                        />

                        <FormControl size="small" fullWidth>
                          <InputLabel>Form</InputLabel>
                          <Select
                            label="Form"
                            value={draftJson.form || draftJson.verified_form || ""}
                            onChange={(e) =>
                              updateDraftFields({
                                form: e.target.value,
                                verified_form: e.target.value,
                              })
                            }
                          >
                            {formOptions.map((form) => (
                              <MenuItem key={form} value={form}>
                                {form}
                              </MenuItem>
                            ))}
                          </Select>
                        </FormControl>

                        <Autocomplete
                          freeSolo
                          size="small"
                          options={getChapterOptions(draftJson)}
                          value={draftJson.chapter || draftJson.verified_chapter || ""}
                          onChange={(event, newValue) =>
                            updateDraftFields({
                              chapter: newValue || "",
                              verified_chapter: newValue || "",
                            })
                          }
                          onInputChange={(event, newInputValue) =>
                            updateDraftFields({
                              chapter: newInputValue || "",
                              verified_chapter: newInputValue || "",
                            })
                          }
                          renderInput={(params) => (
                            <TextField {...params} label="Chapter" />
                          )}
                        />

                        <FormControl size="small" fullWidth>
                          <InputLabel>Difficulty</InputLabel>
                          <Select
                            label="Difficulty"
                            value={draftJson.difficulty || ""}
                            onChange={(e) => updateDraftField("difficulty", e.target.value)}
                          >
                            {difficultyOptions.map((difficulty) => (
                              <MenuItem key={difficulty} value={difficulty}>
                                {difficulty}
                              </MenuItem>
                            ))}
                          </Select>
                        </FormControl>

                        {selectedBatch?.paper_type !== "kertas2" && (
                          <FormControl size="small" fullWidth>
                            <InputLabel>Correct Answer</InputLabel>
                            <Select
                              label="Correct Answer"
                              value={draftJson.correct_option || ""}
                              onChange={(e) => updateDraftField("correct_option", e.target.value)}
                            >
                              {["A", "B", "C", "D"].map((option) => (
                                <MenuItem key={option} value={option}>
                                  {option}
                                </MenuItem>
                              ))}
                            </Select>
                          </FormControl>
                        )}
                      </Box>

                        {selectedBatch?.paper_type === "kertas2" && (
                          <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap" }}>
                            <Chip size="small" label={draftJson.group_id || "No group"} />
                            <Chip size="small" label={`Stage ${draftJson.stage_index || 1}`} />
                            <Chip
                              size="small"
                              label={draftJson.exercise_stage_id || "No stage id"}
                            />
                            {draftJson.group_form && (
                              <Chip size="small" label={draftJson.group_form} />
                            )}
                            {draftJson.group_chapter && (
                              <Chip size="small" label={draftJson.group_chapter} />
                            )}
                            {draftJson.unlock_after_stage_id && (
                              <Chip
                                size="small"
                                label={`Unlock after ${draftJson.unlock_after_stage_id}`}
                              />
                            )}
                          </Box>
                        )}
                        <Box>
                          <Typography fontWeight="900" mb={1}>
                            Math Symbols
                          </Typography>

                          <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap" }}>
                            {adminEasyLearnmbols.map((symbolItem) => (
                              <Button
                                key={symbolItem.label}
                                size="small"
                                variant="outlined"
                                title={symbolItem.title}
                                onClick={() => handleInsertEasyLearnmbol(symbolItem)}
                                sx={{
                                  minWidth: 38,
                                  borderRadius: "10px",
                                  fontWeight: 900,
                                  textTransform: "none",
                                }}
                              >
                                {symbolItem.label}
                              </Button>
                            ))}
                          </Box>
                        </Box>

                        <TextField
                          label="Question Text English"
                          value={getDraftInstructionText(draftJson, "instructions_en")}
                          onChange={(e) =>
                            updateDraftInstruction("instructions_en", e.target.value)
                          }
                          onFocus={() =>
                            setSymbolTarget({
                              type: "instruction",
                              field: "instructions_en",
                            })
                          }
                          multiline
                          minRows={3}
                          fullWidth
                        />

                        <TextField
                          label="Question Text Bahasa Melayu"
                          value={getDraftInstructionText(draftJson, "instructions_ms")}
                          onChange={(e) =>
                            updateDraftInstruction("instructions_ms", e.target.value)
                          }
                          onFocus={() =>
                            setSymbolTarget({
                              type: "instruction",
                              field: "instructions_ms",
                            })
                          }
                          multiline
                          minRows={3}
                          fullWidth
                        />

                        {selectedBatch?.paper_type === "kertas2" ? (
                          renderK2MarkingSchemePreview(draftJson)
                        ) : (
                          <>
                            <Typography fontWeight="900">Options</Typography>

                            {["A", "B", "C", "D"].map((label) => (
                              <Paper
                                key={label}
                                elevation={0}
                                sx={{
                                  p: 2,
                                  borderRadius: "12px",
                                  border: "1px solid #E5E7EB",
                                  bgcolor: "#F9FAFB",
                                }}
                              >
                                <Typography fontWeight="900" mb={1}>
                                  Option {label}
                                </Typography>

                                <Box
                                  sx={{
                                    display: "grid",
                                    gridTemplateColumns: { xs: "1fr", md: "1fr 1fr" },
                                    gap: 1.5,
                                  }}
                                >
                                  <TextField
                                    size="small"
                                    label={`Option ${label} English`}
                                    value={getDraftOptionValue(draftJson, label, "text_en")}
                                    onFocus={() =>
                                      setSymbolTarget({
                                        type: "option",
                                        label,
                                        field: "text_en",
                                      })
                                    }
                                    onChange={(e) =>
                                      updateDraftOption(label, "text_en", e.target.value)
                                    }
                                    fullWidth
                                  />

                                  <TextField
                                    size="small"
                                    label={`Option ${label} BM`}
                                    value={getDraftOptionValue(draftJson, label, "text_ms")}
                                    onFocus={() =>
                                      setSymbolTarget({
                                        type: "option",
                                        label,
                                        field: "text_ms",
                                      })
                                    }
                                    onChange={(e) =>
                                      updateDraftOption(label, "text_ms", e.target.value)
                                    }
                                    fullWidth
                                  />
                                </Box>
                              </Paper>
                            ))}
                          </>
                        )}

                        <Box>
                          <Box
                            component="details"
                            sx={{
                              p: 2,
                              borderRadius: "12px",
                              border: "1px solid #E5E7EB",
                              bgcolor: "#F9FAFB",
                            }}
                          >
                            <Typography
                              component="summary"
                              fontWeight="900"
                              sx={{ cursor: "pointer" }}
                            >
                              Advanced JSON View 
                            </Typography>

                            <TextField
                              value={draftEditorText}
                              onChange={(e) => setDraftEditorText(e.target.value)}
                              multiline
                              minRows={8}
                              fullWidth
                              helperText="Only edit this if you need to adjust technical fields."
                              sx={{
                                mt: 2,
                                "& textarea": {
                                  fontFamily: "Consolas, Monaco, 'Courier New', monospace",
                                  fontSize: "13px",
                                },
                              }}
                            />
                          </Box>
                        </Box>
                      </Stack>
                    );
                  })()}

                  <Box
                    sx={{
                      display: "flex",
                      justifyContent: "space-between",
                      gap: 1,
                      flexWrap: "wrap",
                    }}
                  >
                    <Button
                      variant="outlined"
                      color="error"
                      disabled={draftSaving}
                      onClick={() => handleSaveDraftItem("skipped")}
                      sx={{
                        borderRadius: "10px",
                        textTransform: "none",
                        fontWeight: "800",
                      }}
                    >
                      Skip
                    </Button>

                    <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap" }}>
                      <Button
                        variant="outlined"
                        disabled={draftSaving}
                        onClick={() => handleSaveDraftItem("draft")}
                        sx={{
                          borderRadius: "10px",
                          textTransform: "none",
                          fontWeight: "800",
                        }}
                      >
                        Save Draft
                      </Button>

                      <Button
                        variant="contained"
                        disabled={draftSaving}
                        onClick={() => handleSaveDraftItem("approved")}
                        sx={{
                          bgcolor: "#3855c0",
                          borderRadius: "10px",
                          textTransform: "none",
                          fontWeight: "900",
                          "&:hover": { bgcolor: "#2d4499" },
                        }}
                      >
                        Approve
                      </Button>
                    </Box>
                  </Box>
                </Stack>
              )}
            </Paper>
          </Box>
        )}
      </DialogContent>

      <DialogActions sx={{ px: 3, py: 2 }}>
        <Button
          variant="contained"
          onClick={() => handleSaveApprovedBatch()}
          disabled={
            !selectedBatch ||
            draftSaving ||
            !getBatchReviewSummary().canCompleteReview
          }
          sx={{
            bgcolor: "#3855c0",
            borderRadius: "10px",
            textTransform: "none",
            fontWeight: "900",
            "&:hover": { bgcolor: "#2d4499" },
          }}
        >
          {draftSaving ? "Saving..." : "Complete Review & Import Approved"}
        </Button>

        <Button
          onClick={() => setBatchDetailOpen(false)}
          sx={{ textTransform: "none", fontWeight: 800 }}
        >
          Close
        </Button>
      </DialogActions>
    </Dialog>
    <Dialog
      open={deleteImageDialogOpen}
      onClose={() => setDeleteImageDialogOpen(false)}
      maxWidth="xs"
      fullWidth
      PaperProps={{ sx: { borderRadius: "18px" } }}
    >
      <DialogTitle fontWeight="900">
        Remove Image?
      </DialogTitle>

      <DialogContent>
        <Typography color="text.secondary">
          This image will be removed from the draft question. You can still upload a
          new image later if needed.
        </Typography>
      </DialogContent>

      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button
          onClick={() => setDeleteImageDialogOpen(false)}
          sx={{ textTransform: "none", fontWeight: 800 }}
        >
          Cancel
        </Button>

        <Button
          variant="contained"
          color="error"
          onClick={handleConfirmDeleteDraftImage}
          disabled={
            imageItemToDelete &&
            uploadingImageItemId === imageItemToDelete.item_id
          }
          sx={{
            borderRadius: "10px",
            textTransform: "none",
            fontWeight: "900",
          }}
        >
          Remove
        </Button>
      </DialogActions>
    </Dialog>
    <Dialog
      open={reviewVariantDetailOpen}
      onClose={() => setReviewVariantDetailOpen(false)}
      fullWidth
      maxWidth="lg"
    >
      <DialogTitle
        sx={{
          fontWeight: 900,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        AI Review Variant Detail

        <IconButton onClick={() => setReviewVariantDetailOpen(false)}>
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      <DialogContent dividers>
        {reviewVariantLoading ? (
          <Box sx={{ display: "flex", justifyContent: "center", py: 5 }}>
            <CircularProgress />
          </Box>
        ) : !selectedReviewVariant ? (
          <Alert severity="info">No review variant selected.</Alert>
        ) : (
          <Stack gap={2.5}>
            <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap" }}>
              <Chip label={`#${selectedReviewVariant.variant_id}`} />
              <Chip label={selectedReviewVariant.variant_type || "variant"} />
              <Chip label={selectedReviewVariant.source_mode || "source"} />
              <Chip label={selectedReviewVariant.status || "status"} />
              <Chip label={selectedReviewVariant.language || "language"} />
            </Box>

            {renderReviewVariantBasicPreview()}

            <Box
              component="details"
              sx={{
                p: 2,
                borderRadius: "12px",
                border: "1px solid #E5E7EB",
                bgcolor: "#F9FAFB",
              }}
            >
              <Typography
                component="summary"
                fontWeight="900"
                sx={{ cursor: "pointer" }}
              >
                Advanced JSON Edit
              </Typography>

              <Stack gap={2} sx={{ mt: 2 }}>
                <TextField
                  label="Generated Question JSON"
                  value={reviewVariantQuestionText}
                  onChange={(e) => setReviewVariantQuestionText(e.target.value)}
                  multiline
                  minRows={12}
                  fullWidth
                  sx={{
                    "& textarea": {
                      fontFamily: "Consolas, Monaco, 'Courier New', monospace",
                      fontSize: "13px",
                    },
                  }}
                />

                <TextField
                  label="Generated Marking Scheme JSON"
                  value={reviewVariantSchemeText}
                  onChange={(e) => setReviewVariantSchemeText(e.target.value)}
                  multiline
                  minRows={10}
                  fullWidth
                  sx={{
                    "& textarea": {
                      fontFamily: "Consolas, Monaco, 'Courier New', monospace",
                      fontSize: "13px",
                    },
                  }}
                />
              </Stack>
            </Box>
          </Stack>
        )}
      </DialogContent>

      <DialogActions sx={{ px: 3, py: 2 }}>
        <Button
          variant="contained"
          disabled={reviewVariantSaving || reviewVariantLoading || !selectedReviewVariant}
          onClick={handleSaveReviewVariantEdit}
          sx={{
            bgcolor: "#3855c0",
            borderRadius: "10px",
            textTransform: "none",
            fontWeight: "900",
            "&:hover": { bgcolor: "#2d4499" },
          }}
        >
          {reviewVariantSaving ? "Saving..." : "Save Changes"}
        </Button>

        <Button
          onClick={() => setReviewVariantDetailOpen(false)}
          sx={{ textTransform: "none", fontWeight: 800 }}
        >
          Close
        </Button>
      </DialogActions>
    </Dialog>
    <Dialog
      open={addAdminOpen}
      onClose={() => setAddAdminOpen(false)}
      maxWidth="sm"
      fullWidth
      PaperProps={{ sx: { borderRadius: "18px" } }}
    >
      <DialogTitle
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          fontWeight: 900,
        }}
      >
        Add Admin

        <IconButton onClick={() => setAddAdminOpen(false)}>
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      <DialogContent dividers>
        <Stack gap={2}>
          <Alert severity="info" sx={{ borderRadius: "12px" }}>
            Add an admin account for EasyLearn. EasyLearn admin account is only able to active and deactivate through admin page.
          </Alert>

          <TextField
            label="Admin Name"
            value={addAdminForm.name}
            onChange={(e) =>
              setAddAdminForm((prev) => ({
                ...prev,
                name: e.target.value,
              }))
            }
            fullWidth
          />

          <TextField
            label="Admin Email"
            type="email"
            value={addAdminForm.email}
            onChange={(e) =>
              setAddAdminForm((prev) => ({
                ...prev,
                email: e.target.value,
              }))
            }
            fullWidth
          />
          {addAdminResetLink && (
            <Alert severity="success" sx={{ borderRadius: "12px" }}>
              <Typography fontWeight="900" mb={1}>
                Admin created. Password setup link:
              </Typography>

              <TextField
                value={addAdminResetLink}
                fullWidth
                multiline
                minRows={2}
                InputProps={{ readOnly: true }}
              />
            </Alert>
          )}
        </Stack>
      </DialogContent>

      <DialogActions sx={{ px: 3, py: 2 }}>
        <Button
          variant="contained"
          disabled={addAdminSaving}
          onClick={handleCreateAdmin}
          sx={{
            bgcolor: "#3855c0",
            borderRadius: "10px",
            textTransform: "none",
            fontWeight: "900",
            "&:hover": { bgcolor: "#2d4499" },
          }}
        >
          {addAdminSaving ? "Adding..." : "Add Admin"}
        </Button>

        <Button
          onClick={() => setAddAdminOpen(false)}
          sx={{ textTransform: "none", fontWeight: 800 }}
        >
          Close
        </Button>
      </DialogActions>
    </Dialog>
    </Box>
  );
};

export default AdminDashboard;
