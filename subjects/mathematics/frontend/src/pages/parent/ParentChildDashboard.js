import React, { useState, useEffect } from "react";
import {
  Box,
  Typography,
  Paper,
  Divider,
  Button,
  Chip,
  Tooltip,
  Avatar,
  IconButton,
  CircularProgress,
} from "@mui/material";
import { logUserActivity } from "../../utils/logger";
import { useNavigate, useParams } from "react-router-dom";

import { useLanguage } from "../../context/LanguageContext";
import { apiFetch } from "../../utils/apiFetch";
// Chart.js
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip as ChartTooltip,
  Legend,
  LineElement,
  PointElement,
  CategoryScale,
  LinearScale,
  Filler,
} from "chart.js";
import { Line } from "react-chartjs-2";

// Icons
import TrendingUpRoundedIcon from "@mui/icons-material/TrendingUpRounded";
import TrackChangesRoundedIcon from "@mui/icons-material/TrackChangesRounded";
import QuizRoundedIcon from "@mui/icons-material/QuizRounded";
import AccessTimeFilledRoundedIcon from "@mui/icons-material/AccessTimeFilledRounded";
import PlayCircleRoundedIcon from "@mui/icons-material/PlayCircleRounded";
import ScheduleRoundedIcon from "@mui/icons-material/ScheduleRounded";
import CalendarMonthRoundedIcon from "@mui/icons-material/CalendarMonthRounded";
import InsightsRoundedIcon from "@mui/icons-material/InsightsRounded";
import AutoGraphRoundedIcon from "@mui/icons-material/AutoGraphRounded";
import CheckCircleRoundedIcon from "@mui/icons-material/CheckCircleRounded";
import ReportProblemRoundedIcon from "@mui/icons-material/ReportProblemRounded";
import SummarizeRoundedIcon from "@mui/icons-material/SummarizeRounded";
import BarChartRoundedIcon from "@mui/icons-material/BarChartRounded";
import TipsAndUpdatesRoundedIcon from "@mui/icons-material/TipsAndUpdatesRounded";
import EventRepeatRoundedIcon from "@mui/icons-material/EventRepeatRounded";
import BoltRoundedIcon from "@mui/icons-material/BoltRounded";
import RefreshRoundedIcon from "@mui/icons-material/RefreshRounded";

ChartJS.register(
  ArcElement,
  ChartTooltip,
  Legend,
  LineElement,
  PointElement,
  CategoryScale,
  LinearScale,
  Filler
);

const ParentChildDashboard = () => {
  const { studentId } = useParams();
  const [child, setChild] = useState(null);
  const { t, language } = useLanguage();
  const navigate = useNavigate();

  const currentYear = new Date().getFullYear();

  const [selectedHeatmapYear, setSelectedHeatmapYear] = useState(currentYear);
  const [gradeMessage, setGradeMessage] = useState("Analyzing recent performance...");
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [dashboardKpis, setDashboardKpis] = useState({
    predicted_grade: {
      grade: "--",
      estimated_grade: "--",
      score: null,
      estimated_score: null,
      performance_band: "--",
      performance_band_label: "Performance Band",
      confidence: 0,
    },
    practice_accuracy: { accuracy: 0 },
    total_questions_attempted: { total: 0, paper1: 0, paper2: 0 },
    total_study_time: { total: "0h 0m", this_week_delta: "No change this week" },
    last_updated_at: null,
  });

  const [aiOverview, setAiOverview] = useState({
    strength: "Analyzing strengths...",
    concern: "Analyzing weak areas...",
    prediction_reason: "Analyzing recent performance...",
  });

  const [topicMastery, setTopicMastery] = useState({
    mastered_count: 0,
    average_count: 0,
    review_count: 0,
    topics: [],
  });

  const [recommendedTopics, setRecommendedTopics] = useState([]);

  const [performanceTrend, setPerformanceTrend] = useState({
    points: [],
    trend_direction: "stable",
  });

  const [studyPattern, setStudyPattern] = useState({
    persona: "Analyzing...",
    proof: "Gathering study data...",
    suggestion: "More completed sessions are needed for AI insights.",
    total_time: "0h 0m",
  });

  const [studySchedule, setStudySchedule] = useState({
    pattern_type: "Analyzing...",
    best_time_window: "--",
    recommended_session_length_label: "--",
    weekly_target_sessions: 0,
    weekly_progress: {
      completed: 0,
      target: 0,
      label: "--",
    },
    next_suggested_session: {
      label: "--",
      time_window: "--",
      focus_topic: "--",
      chapter_id: null,
    },
  });

  const [studyHeatmap, setStudyHeatmap] = useState({
    cells: [],
    active_days: 0,
    best_minutes: 0,
  });

  const [consistency, setConsistency] = useState({
    weekly_target_sessions: 0,
    weekly_completed_sessions: 0,
    weekly_progress_label: "--",
  });

  const fetchDashboardData = async () => {
    try {
      const response = await apiFetch(
        `${process.env.REACT_APP_API_BASE_URL}/api/parent/children/${studentId}/dashboard?lang=${language}&year=${selectedHeatmapYear}`
      );

      const data = await response.json();

      if (data.success) {
        setChild(data.child || null);

        if (data.kpis) setDashboardKpis(data.kpis);

        if (data.ai_overview) {
          const predictionReason =
            data.ai_overview.prediction_reason ||
            data.kpis?.predicted_grade?.reason ||
            "Analyzing recent performance...";

          setAiOverview({
            strength: data.ai_overview.strength || "Analyzing...",
            concern: data.ai_overview.concern || "Analyzing...",
            prediction_reason: predictionReason,
          });

          setGradeMessage(predictionReason);
        }

        if (data.topic_recommendations) {
          setRecommendedTopics(data.topic_recommendations);
        }

        if (data.topic_mastery) {
          setTopicMastery(data.topic_mastery);
        }

        if (data.performance_trend) {
          setPerformanceTrend(data.performance_trend);
        }

        if (data.study_schedule) {
          setStudySchedule(data.study_schedule);
        }

        if (data.study_pattern) {
          setStudyPattern(data.study_pattern);
        }

        if (data.consistency) {
          setConsistency(data.consistency);
        }

        if (data.study_heatmap) {
          setStudyHeatmap(data.study_heatmap);
        }
      } else {
        console.error("Parent child dashboard failed:", data.message);
        navigate("/parentDashboard");
      }
    } catch (error) {
      console.error("Failed to fetch child dashboard data:", error);
    }
  };

  const handleRefreshDashboard = async () => {
    if (!studentId) return;

    try {
      setIsRefreshing(true);
      await fetchDashboardData();
    } catch (error) {
      console.error("Failed to refresh child dashboard:", error);
    } finally {
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    logUserActivity("viewed_parent_child_dashboard");

    if (studentId) {
      handleRefreshDashboard();
    }
  }, [studentId, language, selectedHeatmapYear]);

  const gradePrediction = dashboardKpis?.predicted_grade || {};

  const kpiGrade = gradePrediction?.grade || "--";
  const kpiConfidence = gradePrediction?.confidence || 0;
  const kpiAccuracy = dashboardKpis?.practice_accuracy?.accuracy || 0;
  const kpiAttemptsTotal = dashboardKpis?.total_questions_attempted?.total || 0;
  const kpiPaper1 = dashboardKpis?.total_questions_attempted?.paper1 || 0;
  const kpiPaper2 = dashboardKpis?.total_questions_attempted?.paper2 || 0;
  const kpiStudyTime = dashboardKpis?.total_study_time?.total || "0h 0m";
  const kpiStudyDelta =
    dashboardKpis?.total_study_time?.this_week_delta || "No change this week";
  const isPositiveStudyDelta = !String(kpiStudyDelta).trim().startsWith("-");

  const trendPoints = performanceTrend?.points || [];
  const trendLabels = trendPoints.map((point) => point.label);
  const trendValues = trendPoints.map((point) => Number(point.accuracy || 0));

  const hasEnoughTrendData = trendValues.length >= 2;

  const trendDirectionLabel =
    trendValues.length === 0
      ? t("dashboard_trend_no_data")
      : trendValues.length === 1
      ? t("dashboard_trend_need_more_days")
      : performanceTrend?.trend_direction === "up"
      ? t("dashboard_trend_improving")
      : performanceTrend?.trend_direction === "down"
      ? t("dashboard_trend_declining")
      : t("dashboard_trend_stable");

  const trendChartData = {
    labels: trendLabels,
    datasets: [
      {
        data: trendValues,
        borderColor: "#7C9CFF",
        backgroundColor: "rgba(124, 156, 255, 0.12)",
        fill: true,
        tension: 0.35,
        pointRadius: trendValues.length > 1 ? 2.5 : 0,
        pointHoverRadius: 4,
        pointBackgroundColor: "#7C9CFF",
        pointBorderWidth: 0,
        borderWidth: 2.2,
      },
    ],
  };

  const trendChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: "#111827",
        padding: 10,
        cornerRadius: 8,
        displayColors: false,
        callbacks: {
          label: (context) => `${context.parsed.y}%`,
        },
      },
    },
    scales: {
      x: {
        display: false,
        grid: { display: false },
        border: { display: false },
      },
      y: {
        display: false,
        min: 0,
        max: 100,
        grid: { display: false },
        border: { display: false },
      },
    },
  };

  const isMalayLanguage = () =>
    language === "bm" || language === "ms" || language === "malay";

  const masteryTopics = topicMastery?.topics || [];
  const masteryMasteredCount = topicMastery?.mastered_count || 0;
  const masteryAverageCount = topicMastery?.average_count || 0;
  const masteryReviewCount = topicMastery?.review_count || 0;

  const masteryUnpracticedCount = masteryTopics.filter(
    (topic) =>
      String(topic?.status || "").toLowerCase() === "unpracticed" ||
      Number(topic?.attempts || topic?.total_attempts || 0) === 0
  ).length;

  const masteryTotalSegments =
    masteryMasteredCount +
    masteryAverageCount +
    masteryReviewCount +
    masteryUnpracticedCount;

  const masterySegments = [
    {
      key: "mastered",
      label: t("dashboard_mastered"),
      count: masteryMasteredCount,
      color: "#10B981",
    },
    {
      key: "average",
      label: t("dashboard_average"),
      count: masteryAverageCount,
      color: "#F59E0B",
    },
    {
      key: "review",
      label: t("dashboard_review"),
      count: masteryReviewCount,
      color: "#EF4444",
    },
    {
      key: "unpracticed",
      label: isMalayLanguage() ? "Belum Dicuba" : "Unattempted",
      count: masteryUnpracticedCount,
      color: "#6366F1",
    },
  ];

  const scheduleBestTime = studySchedule?.best_time_window || "--";
  const scheduleSessionLength =
    studySchedule?.recommended_session_length_label || "--";
  const scheduleWeeklyTarget =
    studySchedule?.weekly_target_sessions || 0;

  const nextSessionLabel =
    studySchedule?.next_suggested_session?.label || "--";
  const nextSessionTime =
    studySchedule?.next_suggested_session?.time_window || "--";
  const nextSessionFocus =
    studySchedule?.next_suggested_session?.focus_topic || "--";

  const consistencyWeeklyTarget =
    consistency?.weekly_target_sessions || scheduleWeeklyTarget || 0;
  const consistencyWeeklyCompleted =
    consistency?.weekly_completed_sessions ||
    studySchedule?.weekly_progress?.completed ||
    0;

  const consistencyProgressPercent =
    consistencyWeeklyTarget > 0
      ? Math.min((consistencyWeeklyCompleted / consistencyWeeklyTarget) * 100, 100)
      : 0;

  const patternTitle =
    studyPattern?.persona || studySchedule?.pattern_type || t("dashboard_analyzing");
  const patternSummary =
    studyPattern?.proof || studyPattern?.suggestion || t("dashboard_analyzing");

  const heatmapCells =
    studyHeatmap?.cells?.length > 0
      ? studyHeatmap.cells
      : Array.from({ length: 371 }, (_, index) => ({
          date: `placeholder-${index}`,
          minutes: 0,
          intensity: 0,
        }));

  const getAlignedHeatmapCells = (cells, year) => {
    const realCells = (cells || []).filter(
      (cell) => cell?.date && !String(cell.date).startsWith("placeholder")
    );

    if (realCells.length === 0) {
      return Array.from({ length: 371 }, (_, index) => ({
        date: `placeholder-${index}`,
        minutes: 0,
        intensity: 0,
        isPlaceholder: true,
      }));
    }

    // JS getDay(): Sunday = 0, Monday = 1, ..., Saturday = 6
    // Convert to Monday-first offset: Monday = 0, Sunday = 6
    const janFirst = new Date(year, 0, 1);
    const leadingEmptyCells = (janFirst.getDay() + 6) % 7;

    const totalCellsAfterLeading = leadingEmptyCells + realCells.length;
    const trailingEmptyCells = (7 - (totalCellsAfterLeading % 7)) % 7;

    const leading = Array.from({ length: leadingEmptyCells }, (_, index) => ({
      date: `leading-${index}`,
      minutes: 0,
      intensity: 0,
      isPlaceholder: true,
    }));

    const trailing = Array.from({ length: trailingEmptyCells }, (_, index) => ({
      date: `trailing-${index}`,
      minutes: 0,
      intensity: 0,
      isPlaceholder: true,
    }));

    return [...leading, ...realCells, ...trailing];
  };

  const alignedHeatmapCells = getAlignedHeatmapCells(
    heatmapCells,
    selectedHeatmapYear
  );
        
  const heatmapActiveDays = studyHeatmap?.active_days || 0;
  const heatmapBestMinutes = studyHeatmap?.best_minutes || 0;

  const getHeatmapColor = (intensity) => {
    switch (intensity) {
      case 1:
        return "#BBF7D0";
      case 2:
        return "#86EFAC";
      case 3:
        return "#4ADE80";
      case 4:
        return "#15803D";
      default:
        return "#E5E7EB";
    }
  };

  const getTopicTitle = (topic) =>
    topic?.topic_name ||
    topic?.topic ||
    topic?.name ||
    "Recommended Topic";

  const getTopicAttempts = (topic) =>
    topic?.total_attempts ??
    topic?.attempts ??
    0;

  const getTopicChapterLabel = (topic) => {
    const form = topic?.form;
    const chapterNo = topic?.chapter_no;

    const formNumber = String(form || "")
      .replace(/form/i, "")
      .replace(/tingkatan/i, "")
      .trim();

    const chapterNumber = String(chapterNo || "")
      .replace(/chapter/i, "")
      .replace(/bab/i, "")
      .trim();

    if (formNumber && chapterNumber) {
      return isMalayLanguage()
        ? `Tingkatan ${formNumber} • Bab ${chapterNumber}`
        : `Form ${formNumber} • Chapter ${chapterNumber}`;
    }

    if (chapterNumber) {
      return isMalayLanguage()
        ? `Bab ${chapterNumber}`
        : `Chapter ${chapterNumber}`;
    }

    if (topic?.chapter_id) {
      return isMalayLanguage()
        ? `Bab ${topic.chapter_id}`
        : `Chapter ${topic.chapter_id}`;
    }

    return isMalayLanguage() ? "Bab" : "Chapter";
  };

  const getTopicStatusStyle = (topic) => {
    const status = String(topic?.status || "").toLowerCase();

    if (status === "mastered") {
      return {
        bg: "#ECFDF5",
        border: "#A7F3D0",
        chipBg: "#D1FAE5",
        text: "#059669",
      };
    }

    if (status === "average") {
      return {
        bg: "#FFFBEB",
        border: "#FDE68A",
        chipBg: "#FEF3C7",
        text: "#D97706",
      };
    }

    if (status === "review" || status === "weak" || topic?.is_weak_highlight) {
      return {
        bg: "#FEF2F2",
        border: "#FECACA",
        chipBg: "#FEE2E2",
        text: "#DC2626",
      };
    }

    if (status === "unpracticed") {
      return {
        bg: "#F8FAFF",
        border: "#DBEAFE",
        chipBg: "#EEF2FF",
        text: "#4F46E5",
      };
    }

    return {
      bg: "#F9FAFB",
      border: "#EEF2F7",
      chipBg: "#EEF2FF",
      text: "#4F46E5",
    };
  };

  const getPriorityLabel = (topic, index) => {
    if (index === 0) {
      return t("dashboard_high_priority");
    }

    return t("dashboard_secondary_review");
  };

  const childDisplayName = child?.nickname
    ? `${child.nickname} (${child.name})`
    : child?.name || "Child Dashboard";

  const childAvatarLetter =
    child?.nickname?.[0]?.toUpperCase() ||
    child?.name?.[0]?.toUpperCase() ||
    "S";

  return (
    <Box>
      <Box
        mb={{ xs: 1.6, md: 2 }}
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: { xs: "flex-start", md: "center" },
          gap: 1.2,
          flexWrap: "wrap",
        }}
      >
        <Box>
          <Button
            onClick={() => navigate("/parentDashboard")}
            sx={{
              textTransform: "none",
              fontWeight: 800,
              color: "#3855c0",
              px: 0,
              mb: 0.6,
            }}
          >
            ← {t("parent_child_dashboard_back_to_children")}
          </Button>

          <Box sx={{ display: "flex", alignItems: "center", gap: 1.4 }}>
            <Avatar
              src={child?.photo_url || ""}
              alt={childDisplayName}
              sx={{
                width: { xs: 48, md: 56 },
                height: { xs: 48, md: 56 },
                bgcolor: "#EEF2FF",
                color: "#3855c0",
                fontWeight: 900,
                fontSize: { xs: "1rem", md: "1.15rem" },
                border: "2px solid #FFFFFF",
                boxShadow: "0 8px 18px rgba(15, 23, 42, 0.08)",
                flexShrink: 0,
              }}
            >
              {!child?.photo_url && childAvatarLetter}
            </Avatar>

            <Box>
              <Typography
                variant="h4"
                fontWeight="bold"
                sx={{
                  color: "#111827",
                  fontSize: { xs: "1.35rem", md: "1.7rem" },
                  lineHeight: 1.08,
                  pb: "2px",
                }}
              >
                {childDisplayName}
              </Typography>

              <Typography
                sx={{
                  color: "#6B7280",
                  fontSize: { xs: "0.88rem", md: "0.92rem" },
                  lineHeight: 1.4,
                  maxWidth: "760px",
                }}
              >
                {t("parent_child_dashboard_subtitle")}
              </Typography>
            </Box>
          </Box>
        </Box>

        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            gap: 1,
            flexWrap: "wrap",
            justifyContent: { xs: "flex-start", md: "flex-end" },
          }}
        >
          {child?.student_code && (
            <Chip
              label={`${t("parent_student_id")}: ${child.student_code}`}
              sx={{
                bgcolor: "#FFFFFF",
                border: "1px solid #E5E7EB",
                fontWeight: 800,
                height: 38,
                borderRadius: "999px",
              }}
            />
          )}

          <Tooltip
            title={
              isRefreshing
                ? t("parent_child_dashboard_refreshing")
                : t("parent_child_dashboard_refresh_tooltip")
            }
            arrow
          >
            <span>
              <IconButton
                onClick={handleRefreshDashboard}
                disabled={isRefreshing}
                sx={{
                  width: 40,
                  height: 40,
                  borderRadius: "14px",
                  border: "1px solid #B9C7F5",
                  color: "#3855c0",
                  bgcolor: "#FFFFFF",
                  transition: "all 0.18s ease",
                  "&:hover": {
                    bgcolor: "#EEF2FF",
                    borderColor: "#3855c0",
                    transform: "translateY(-1px)",
                    boxShadow: "0 8px 18px rgba(56, 85, 192, 0.12)",
                  },
                  "&.Mui-disabled": {
                    bgcolor: "#F3F4F6",
                    color: "#9CA3AF",
                  },
                }}
              >
                {isRefreshing ? (
                  <CircularProgress size={18} color="inherit" />
                ) : (
                  <RefreshRoundedIcon fontSize="small" />
                )}
              </IconButton>
            </span>
          </Tooltip>
        </Box>
      </Box>

      {/* ROW 1: QUICK KPI CARDS */}
      <Box
        sx={{
          display: "grid",
          gridTemplateColumns: {
            xs: "repeat(2, minmax(0, 1fr))",
            md: "repeat(4, minmax(0, 1fr))",
          },
          gap: { xs: 1, sm: 1.25, md: 1.5 },
          mb: 2.0,
        }}
      >
        {/* Card 1 */}
        <Paper
          elevation={0}
          sx={{
            p: { xs: 1.15, sm: 1.35 },
            borderRadius: "16px",
            minHeight: { xs: 105, md: 115 },
            position: "relative",
            overflow: "hidden",
            border: "1px solid rgba(124, 154, 255, 0.22)",
            background: "linear-gradient(135deg, #6E97FF 0%, #8EB2FF 100%)",
            boxShadow: "0 10px 24px rgba(94, 132, 255, 0.16)",
          }}
        >
          <Box
            sx={{
              position: "absolute",
              left: "-8%",
              right: "-8%",
              bottom: "-28%",
              height: "68%",
              borderRadius: "50%",
              bgcolor: "rgba(255,255,255,0.18)",
              transform: "rotate(-5deg)",
              pointerEvents: "none",
            }}
          />
          <Box
            sx={{
              position: "absolute",
              left: "-15%",
              right: "-5%",
              bottom: "-40%",
              height: "62%",
              borderRadius: "50%",
              bgcolor: "rgba(255,255,255,0.10)",
              transform: "rotate(6deg)",
              pointerEvents: "none",
            }}
          />

          <Box
            sx={{
              position: "relative",
              zIndex: 1,
              height: "100%",
              display: "flex",
              flexDirection: "column",
            }}
          >
            <Box
              sx={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                gap: 1,
                minHeight: 30,
              }}
            >
              <Typography
                variant="body2"
                fontWeight="700"
                sx={{
                  color: "rgba(255,255,255,0.95)",
                  fontSize: { xs: "0.7rem", sm: "0.78rem" },
                  lineHeight: 1.2,
                  display: "flex",
                  alignItems: "center",
                  minHeight: 20,
                }}
              >
                {t("dashboard_predicted_grade")}
              </Typography>

              <Box
                sx={{
                  width: 30,
                  height: 30,
                  borderRadius: "10px",
                  bgcolor: "rgba(255,255,255,0.20)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  flexShrink: 0,
                  backdropFilter: "blur(4px)",
                }}
              >
                <TrendingUpRoundedIcon sx={{ fontSize: 16, color: "#FFFFFF" }} />
              </Box>
            </Box>

            <Box
              sx={{
                mt: 0.35,
                display: "flex",
                flexDirection: "column",
                justifyContent: "flex-start",
                height: { xs: 70, md: 76 },
              }}
            >
              <Typography
                sx={{
                  fontSize: { xs: "2.15rem", sm: "2.25rem", md: "2.35rem" },
                  lineHeight: 1,
                  fontWeight: 900,
                  color: "#FFFFFF",
                  letterSpacing: "-0.04em",
                  height: { xs: 40, md: 43 },
                  display: "flex",
                  alignItems: "center",
                }}
              >
                {kpiGrade}
              </Typography>
              <Box
                sx={{
                  mt: 0.25,
                  display: "inline-flex",
                  alignItems: "center",
                  gap: 0.45,
                  bgcolor: "rgba(255,255,255,0.92)",
                  color: "#4F46E5",
                  px: 1,
                  py: 0.4,
                  borderRadius: "999px",
                  border: "1px solid rgba(255,255,255,0.85)",
                  boxShadow: "0 4px 12px rgba(47, 84, 170, 0.16)",
                  width: "fit-content",
                }}
              >
                <TrendingUpRoundedIcon sx={{ fontSize: 12, color: "#4F46E5" }} />
                <Typography
                  sx={{
                    fontSize: { xs: "0.68rem", sm: "0.74rem" },
                    fontWeight: 800,
                    lineHeight: 1,
                    whiteSpace: "nowrap",
                    color: "#5182fd",
                  }}
                >
                  {kpiConfidence}% {t("dashboard_confidence_short")}
                </Typography>
              </Box>
            </Box>
          </Box>
        </Paper>

        {/* Card 2 */}
        <Paper
          elevation={0}
          sx={{
            p: { xs: 1.15, sm: 1.35 },
            borderRadius: "16px",
            border: "1px solid #E5E7EB",
            minHeight: { xs: 108, md: 118 },
            bgcolor: "#FFFFFF",
            display: "flex",
            flexDirection: "column",
          }}
        >
          <Box
            sx={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              gap: 1,
              minHeight: 30,
            }}
          >
            <Typography
              variant="body2"
              fontWeight="600"
              color="text.secondary"
              sx={{
                fontSize: { xs: "0.7rem", sm: "0.78rem" },
                lineHeight: 1.2,
                display: "flex",
                alignItems: "center",
                minHeight: 20,
              }}
            >
              {t("dashboard_total_questions_attempted")}
            </Typography>

            <Box
              sx={{
                width: 30,
                height: 30,
                borderRadius: "10px",
                bgcolor: "#EFF6FF",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                flexShrink: 0,
              }}
            >
              <QuizRoundedIcon sx={{ fontSize: 16, color: "#3B82F6" }} />
            </Box>
          </Box>

          <Box sx={{ mt: 0.35 }}>
            <Typography
              sx={{
                fontSize: { xs: "1.65rem", sm: "1.75rem", md: "1.85rem" },
                lineHeight: 1,
                fontWeight: 800,
                color: "#111827",
                letterSpacing: "-0.03em",
                minHeight: { xs: 36, md: 40 },
                display: "flex",
                alignItems: "center",
              }}
            >
              {kpiAttemptsTotal}
            </Typography>

            <Typography
              sx={{
                mt: 0.35,
                fontSize: { xs: "0.66rem", sm: "0.74rem" },
                color: "#4B5563",
                fontWeight: 600,
                lineHeight: 1.35,
              }}
            >
              {t("dashboard_paper1_short")}: {kpiPaper1}
              <Box component="span" sx={{ color: "#D1D5DB", px: 0.5 }}>
                |
              </Box>
              {t("dashboard_paper2_short")}: {kpiPaper2}
            </Typography>
          </Box>
        </Paper>

        {/* Card 3 */}
        <Paper
          elevation={0}
          sx={{
            p: { xs: 1.15, sm: 1.35 },
            borderRadius: "16px",
            border: "1px solid #E5E7EB",
            minHeight: { xs: 108, md: 118 },
            bgcolor: "#FFFFFF",
            display: "flex",
            flexDirection: "column",
          }}
        >
          <Box
            sx={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              gap: 1,
              minHeight: 30,
            }}
          >
            <Typography
              variant="body2"
              fontWeight="600"
              color="text.secondary"
              sx={{
                fontSize: { xs: "0.7rem", sm: "0.78rem" },
                lineHeight: 1.2,
                display: "flex",
                alignItems: "center",
                minHeight: 20,
              }}
            >
              {t("dashboard_practice_accuracy")}
            </Typography>

            <Box
              sx={{
                width: 30,
                height: 30,
                borderRadius: "10px",
                bgcolor: "#ECFDF5",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                flexShrink: 0,
              }}
            >
              <TrackChangesRoundedIcon sx={{ fontSize: 16, color: "#10B981" }} />
            </Box>
          </Box>

          <Box sx={{ mt: 0.35 }}>
            <Typography
              sx={{
                fontSize: { xs: "1.65rem", sm: "1.75rem", md: "1.85rem" },
                lineHeight: 1,
                fontWeight: 800,
                color: "#111827",
                letterSpacing: "-0.03em",
                minHeight: { xs: 36, md: 40 },
                display: "flex",
                alignItems: "center",
              }}
            >
              {kpiAccuracy}%
            </Typography>

            <Box
              sx={{
                mt: 0.35,
                display: "inline-flex",
                alignItems: "center",
                gap: 0.45,
                bgcolor: "#ECFDF5",
                color: "#059669",
                px: 0.95,
                py: 0.35,
                borderRadius: "999px",
              }}
            >
              <TrackChangesRoundedIcon sx={{ fontSize: 12 }} />
              <Typography sx={{ fontSize: "0.68rem", fontWeight: 700, lineHeight: 1 }}>
                {t("dashboard_live_accuracy")}
              </Typography>
            </Box>
          </Box>
        </Paper>

        {/* Card 4 */}
        <Paper
          elevation={0}
          sx={{
            p: { xs: 1.15, sm: 1.35 },
            borderRadius: "16px",
            border: "1px solid #E5E7EB",
            minHeight: { xs: 108, md: 118 },
            bgcolor: "#FFFFFF",
            display: "flex",
            flexDirection: "column",
          }}
        >
          <Box
            sx={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              gap: 1,
              minHeight: 30,
            }}
          >
            <Typography
              variant="body2"
              fontWeight="600"
              color="text.secondary"
              sx={{
                fontSize: { xs: "0.7rem", sm: "0.78rem" },
                lineHeight: 1.2,
                display: "flex",
                alignItems: "center",
                minHeight: 20,
              }}
            >
              {t("dashboard_total_study_time")}
            </Typography>

            <Box
              sx={{
                width: 30,
                height: 30,
                borderRadius: "10px",
                bgcolor: "#FFF7ED",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                flexShrink: 0,
              }}
            >
              <AccessTimeFilledRoundedIcon sx={{ fontSize: 16, color: "#F59E0B" }} />
            </Box>
          </Box>

          <Box sx={{ mt: 0.35 }}>
            <Typography
              sx={{
                fontSize: { xs: "1.65rem", sm: "1.75rem", md: "1.85rem" },
                lineHeight: 1,
                fontWeight: 800,
                color: "#111827",
                letterSpacing: "-0.03em",
                minHeight: { xs: 36, md: 40 },
                display: "flex",
                alignItems: "center",
              }}
            >
              {kpiStudyTime}
            </Typography>

            <Typography
              sx={{
                mt: 0.35,
                fontSize: { xs: "0.66rem", sm: "0.74rem" },
                fontWeight: 700,
                color: isPositiveStudyDelta ? "#10B981" : "#EF4444",
                lineHeight: 1.2,
              }}
            >
              {kpiStudyDelta}
            </Typography>
          </Box>
        </Paper>
      </Box>

      {/* ROW 2 */}
      <Box
        sx={{
          display: "grid",
          gridTemplateColumns: { xs: "1fr", lg: "1.05fr 0.95fr" },
          gap: 3,
          mb: 2.2,
          width: "100%",
          minWidth: 0,
        }}
      >
        {/* Left: AI Performance Overview */}
        <Paper
          elevation={0}
          sx={{
            p: { xs: 1.6, sm: 2, md: 2.1 },
            borderRadius: "20px",
            border: "1px solid #E5E7EB",
            bgcolor: "#FFFFFF",
            height: "100%",
            minWidth: 0,
            overflow: "hidden",
          }}
        >
          <Box
            sx={{
              display: "flex",
              alignItems: "center",
              gap: 1,
              mb: 1.1,
            }}
          >
            <InsightsRoundedIcon sx={{ fontSize: 18, color: "#3855c0" }} />
            <Typography
              sx={{
                fontSize: { xs: "0.92rem", sm: "0.96rem" },
                fontWeight: 700,
                color: "#3855c0",
              }}
            >
              {t("dashboard_ai_performance_overview")}
            </Typography>
          </Box>

          <Divider sx={{ borderColor: "#E5E7EB", mb: 1.45 }} />

          <Box
            sx={{
              p: { xs: 1.15, sm: 1.35 },
              borderRadius: "16px",
              bgcolor: "#F8FAFF",
              border: "1px solid #E8EEFF",
              mb: 1.35,
            }}
          >
            <Box
              sx={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                gap: 1,
                mb: 0.85,
                flexWrap: "wrap",
              }}
            >
              <Box>
                <Typography
                  sx={{
                    fontSize: "0.76rem",
                    fontWeight: 700,
                    color: "#6B7280",
                    mb: 0.15,
                  }}
                >
                  {t("dashboard_recent_performance_trend")}
                </Typography>
                <Typography
                  sx={{
                    fontSize: "0.84rem",
                    fontWeight: 700,
                    color: "#111827",
                  }}
                >
                  {trendDirectionLabel}
                </Typography>
              </Box>

              <Chip
                icon={<AutoGraphRoundedIcon sx={{ fontSize: "15px !important" }} />}
                label={t("dashboard_live_trend")}
                sx={{
                  height: 26,
                  borderRadius: "999px",
                  bgcolor: "#EEF2FF",
                  color: "#5F8FFF",
                  fontWeight: 700,
                  "& .MuiChip-label": {
                    px: 1,
                    fontSize: "0.72rem",
                  },
                }}
              />
            </Box>

            <Box sx={{ height: 150, mt: 2 }}>
              {hasEnoughTrendData ? (
                <Line data={trendChartData} options={trendChartOptions} />
              ) : (
                <Box
                  sx={{
                    height: "100%",
                    borderRadius: "14px",
                    border: "1px dashed #CBD5E1",
                    bgcolor: "#F8FAFC",
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    justifyContent: "center",
                    textAlign: "center",
                    px: 2,
                  }}
                >
                  <AutoGraphRoundedIcon
                    sx={{
                      fontSize: 32,
                      color: "#94A3B8",
                      mb: 1,
                    }}
                  />

                  <Typography
                    sx={{
                      fontSize: "0.9rem",
                      fontWeight: 800,
                      color: "#475569",
                      mb: 0.4,
                    }}
                  >
                    {trendValues.length === 0
                      ? t("dashboard_trend_placeholder_no_data_title")
                      : t("dashboard_trend_placeholder_one_day_title")}
                  </Typography>

                  <Typography
                    sx={{
                      fontSize: "0.78rem",
                      fontWeight: 500,
                      color: "#64748B",
                      maxWidth: 420,
                      lineHeight: 1.45,
                    }}
                  >
                    {trendValues.length === 0
                      ? t("dashboard_trend_placeholder_no_data_desc")
                      : t("dashboard_trend_placeholder_one_day_desc")}
                  </Typography>
                </Box>
              )}
            </Box>
          </Box>

          <Box sx={{ display: "flex", flexDirection: "column", gap: 0.85 }}>
            <Box
              sx={{
                display: "flex",
                gap: 1,
                alignItems: "flex-start",
                p: 1.05,
                borderRadius: "12px",
                border: "1px solid #EEF2F7",
                bgcolor: "#FFFFFF",
              }}
            >
              <CheckCircleRoundedIcon
                sx={{ fontSize: 17, color: "#10B981", mt: "2px", flexShrink: 0 }}
              />
              <Box sx={{ minWidth: 0, flex: 1 }}>
                <Typography
                  sx={{
                    fontSize: "0.78rem",
                    fontWeight: 700,
                    color: "#111827",
                    mb: 0.15,
                  }}
                >
                  {t("dashboard_strength")}
                </Typography>
                <Typography
                  sx={{
                    fontSize: "0.86rem",
                    color: "#4B5563",
                    lineHeight: 1.4,
                    wordBreak: "break-word",
                    overflowWrap: "anywhere",
                  }}
                >
                  {aiOverview?.strength || t("dashboard_analyzing")}
                </Typography>
              </Box>
            </Box>

            <Box
              sx={{
                display: "flex",
                gap: 1,
                alignItems: "flex-start",
                p: 1.05,
                borderRadius: "12px",
                border: "1px solid #EEF2F7",
                bgcolor: "#FFFFFF",
              }}
            >
              <ReportProblemRoundedIcon
                sx={{ fontSize: 17, color: "#F59E0B", mt: "2px", flexShrink: 0 }}
              />
              <Box sx={{ minWidth: 0, flex: 1 }}>
                <Typography
                  sx={{
                    fontSize: "0.78rem",
                    fontWeight: 700,
                    color: "#111827",
                    mb: 0.15,
                  }}
                >
                  {t("dashboard_concern")}
                </Typography>
                <Typography
                  sx={{
                    fontSize: "0.86rem",
                    color: "#4B5563",
                    lineHeight: 1.4,
                    wordBreak: "break-word",
                    overflowWrap: "anywhere",
                  }}
                >
                  {aiOverview?.concern || t("dashboard_analyzing")}
                </Typography>
              </Box>
            </Box>

            <Box
              sx={{
                display: "flex",
                gap: 1,
                alignItems: "flex-start",
                p: 1.05,
                borderRadius: "12px",
                border: "1px solid #E9EEF8",
                bgcolor: "#F8FAFF",
              }}
            >
              <SummarizeRoundedIcon
                sx={{ fontSize: 17, color: "#5F8FFF", mt: "2px", flexShrink: 0 }}
              />
              <Box sx={{ minWidth: 0, flex: 1 }}>
                <Typography
                  sx={{
                    fontSize: "0.78rem",
                    fontWeight: 700,
                    color: "#111827",
                    mb: 0.15,
                  }}
                >
                  {t("dashboard_ai_feedback_summary")}
                </Typography>
                <Box sx={{ display: "flex", flexDirection: "column", gap: 0.35 }}>
                  <Typography
                    sx={{
                      fontSize: "0.86rem",
                      color: "#4B5563",
                      lineHeight: 1.45,
                      wordBreak: "break-word",
                      overflowWrap: "anywhere",
                    }}
                  >
                    {gradeMessage || aiOverview?.prediction_reason || t("dashboard_analyzing")}
                  </Typography>
                </Box>
              </Box>
            </Box>
          </Box>
        </Paper>

        {/* Right: Topic Mastery + Recommendations */}
        <Box
          sx={{
            display: "flex",
            flexDirection: "column",
            gap: { xs: 1.4, md: 1.8 },
            minWidth: 0,
          }}
        >
          {/* Topic Mastery */}
          <Paper
            elevation={0}
            sx={{
              p: { xs: 1.6, sm: 2, md: 2 },
              borderRadius: "20px",
              border: "1px solid #E5E7EB",
              bgcolor: "#FFFFFF",
              minWidth: 0,
              overflow: "hidden",
            }}
          >
            <Box
              sx={{
                display: "flex",
                alignItems: "center",
                gap: 1,
                mb: 1.1,
              }}
            >
              <BarChartRoundedIcon sx={{ fontSize: 18, color: "#F59E0B" }} />
              <Typography
                sx={{
                  fontSize: { xs: "0.92rem", sm: "0.96rem" },
                  fontWeight: 700,
                  color: "#F59E0B",
                }}
              >
                {t("dashboard_topic_mastery")}
              </Typography>
            </Box>

            <Divider sx={{ borderColor: "#E5E7EB", mb: 1.3 }} />

            <Box sx={{ mb: 1.2 }}>
              <Box
                sx={{
                  display: "flex",
                  alignItems: "center",
                  gap: 1,
                  flexWrap: "wrap",
                  mb: 0.75,
                }}
              >
                {masterySegments.map((segment) => (
                  <Box
                    key={segment.key}
                    sx={{
                      display: "flex",
                      alignItems: "center",
                      gap: 0.45,
                    }}
                  >
                    <Box
                      sx={{
                        width: 9,
                        height: 9,
                        borderRadius: "999px",
                        bgcolor: segment.color,
                      }}
                    />
                    <Typography
                      sx={{
                        fontSize: "0.72rem",
                        color: "#4B5563",
                        fontWeight: 700,
                      }}
                    >
                      {segment.count} {segment.label}
                    </Typography>
                  </Box>
                ))}
              </Box>

              <Box
                sx={{
                  width: "100%",
                  height: 10,
                  borderRadius: "999px",
                  bgcolor: "#EEF2F7",
                  overflow: "hidden",
                  display: "flex",
                }}
              >
                {masteryTotalSegments > 0 ? (
                  masterySegments.map(
                    (segment) =>
                      segment.count > 0 && (
                        <Tooltip
                          key={segment.key}
                          title={`${segment.label}: ${segment.count}`}
                          arrow
                        >
                          <Box
                            sx={{
                              flex: segment.count,
                              bgcolor: segment.color,
                              cursor: "pointer",
                            }}
                          />
                        </Tooltip>
                      )
                  )
                ) : (
                  <Box sx={{ width: "100%", bgcolor: "#E5E7EB" }} />
                )}
              </Box>
            </Box>

            <Box
              sx={{
                maxHeight: { xs: 120, md: 140 },
                overflowY: "auto",
                pr: 0.5,
                display: "flex",
                flexDirection: "column",
                gap: 0.85,
              }}
            >
              {masteryTopics.length > 0 ? (
                masteryTopics.map((topic, index) => {
                  const statusStyle = getTopicStatusStyle(topic);

                  return (
                    <Box
                      key={index}
                      sx={{
                        p: 0.95,
                        borderRadius: "12px",
                        bgcolor: statusStyle.bg,
                        border: `1px solid ${statusStyle.border}`,
                      }}
                    >
                    <Box
                      sx={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "flex-start",
                        gap: 1,
                        mb: 0.4,
                      }}
                    >
                      <Box sx={{ minWidth: 0, flex: 1, maxWidth: "100%" }}>
                        <Box
                          sx={{
                            display: "flex",
                            alignItems: "center",
                            gap: 0.6,
                            mb: 0.35,
                            flexWrap: "wrap",
                          }}
                        >
                        <Chip
                          label={getTopicChapterLabel(topic)}
                          size="small"
                          sx={{
                            height: 20,
                            borderRadius: "999px",
                            bgcolor: "#EEF2FF",
                            color: "#4F46E5",
                            fontWeight: 700,
                            "& .MuiChip-label": {
                              px: 1,
                              fontSize: "0.66rem",
                            },
                          }}
                        />
                        </Box>

                        <Typography
                          sx={{
                            fontSize: "0.8rem",
                            fontWeight: 700,
                            color: "#111827",
                            lineHeight: 1.25,
                            wordBreak: "break-word",
                            overflowWrap: "anywhere",
                          }}
                        >
                          {getTopicTitle(topic)}
                        </Typography>
                      </Box>

                      <Box
                        sx={{
                          px: 0.7,
                          py: 0.3,
                          borderRadius: "999px",
                          bgcolor: statusStyle.chipBg,
                          color: statusStyle.text,
                          fontSize: "0.68rem",
                          fontWeight: 800,
                          whiteSpace: "nowrap",
                        }}
                      >
                        {topic.accuracy}%
                      </Box>
                    </Box>

                    <Box
                      sx={{
                        display: "flex",
                        justifyContent: "space-between",
                        gap: 1,
                        flexWrap: "wrap",
                      }}
                    >
                      <Typography sx={{ fontSize: "0.7rem", color: "#6B7280" }}>
                        {t("dashboard_total_questions_attempted")}: {getTopicAttempts(topic)}
                      </Typography>

                      <Typography sx={{ fontSize: "0.7rem", color: "#6B7280", fontWeight: 600 }}>
                        {t("dashboard_practice_accuracy")}: {topic.accuracy}%
                      </Typography>
                    </Box>
                  </Box>
                );
              })
              ) : (
                <Typography sx={{ fontSize: "0.82rem", color: "#6B7280" }}>
                  {t("dashboard_analyzing")}
                </Typography>
              )}
            </Box>
          </Paper>

          {/* Recommendations */}
          <Paper
            elevation={0}
            sx={{
              p: { xs: 1.6, sm: 2, md: 2 },
              borderRadius: "20px",
              border: "1px solid #E5E7EB",
              bgcolor: "#FFFFFF",
              minWidth: 0,
              overflow: "hidden",
            }}
          >
            <Box
              sx={{
                display: "flex",
                alignItems: "center",
                gap: 1,
                mb: 1.1,
              }}
            >
              <TipsAndUpdatesRoundedIcon sx={{ fontSize: 18, color: "#F59E0B" }} />
              <Typography
                sx={{
                  fontSize: { xs: "0.92rem", sm: "0.96rem" },
                  fontWeight: 700,
                  color: "#F59E0B",
                }}
              >
                {t("dashboard_topic_recommendations")}
              </Typography>
            </Box>

            <Divider sx={{ borderColor: "#E5E7EB", mb: 1.3 }} />

            <Box sx={{ display: "flex", flexDirection: "column", gap: 0.95 }}>
              {recommendedTopics.length > 0 ? (
                recommendedTopics.slice(0, 2).map((topic, index) => (
                  <Box
                    key={index}
                    sx={{
                      p: 1,
                      borderRadius: "12px",
                      bgcolor: index === 0 ? "#FFF8ED" : "#F9FAFB",
                      border: `1px solid ${index === 0 ? "#FDE7C2" : "#EEF2F7"}`,
                    }}
                  >
                    <Box
                      sx={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "flex-start",
                        gap: 1,
                        mb: 0.35,
                        flexWrap: "wrap",
                        minWidth: 0,
                      }}
                    >
                      <Typography
                        sx={{
                          fontSize: "0.82rem",
                          fontWeight: 800,
                          color: "#111827",
                          minWidth: 0,
                          flex: 1,
                          wordBreak: "break-word",
                          overflowWrap: "anywhere",
                        }}
                      >
                        {getTopicTitle(topic)}
                      </Typography>

                      <Chip
                        label={getPriorityLabel(topic, index)}
                        sx={{
                          height: 22,
                          borderRadius: "999px",
                          bgcolor: index === 0 ? "#FEF3C7" : "#EEF2F7",
                          color: index === 0 ? "#B45309" : "#807c6b",
                          fontWeight: 700,
                          "& .MuiChip-label": {
                            px: 1,
                            fontSize: "0.68rem",
                          },
                        }}
                      />
                    </Box>

                    <Typography
                      sx={{
                        fontSize: "0.76rem",
                        color: "#4B5563",
                        lineHeight: 1.4,
                        mb: index === 0 ? 0.7 : 0,
                      }}
                    >
                      {topic.reason}
                    </Typography>
                  </Box>
                ))
              ) : (
                <Typography sx={{ fontSize: "0.82rem", color: "#6B7280" }}>
                  {t("dashboard_analyzing")}
                </Typography>
              )}
            </Box>
          </Paper>
        </Box>
      </Box>

      {/* ROW 3 */}
      <Paper
        elevation={0}
        sx={{
          p: { xs: 1.45, sm: 1.8, md: 2 },
          borderRadius: "20px",
          border: "1px solid #E5E7EB",
          bgcolor: "#FFFFFF",
          mb: 2.2,
          overflow: "hidden",
        }}
      >
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            gap: 1,
            mb: 1.1,
          }}
        >
          <CalendarMonthRoundedIcon sx={{ fontSize: 18, color: "#10B981" }} />
          <Typography
            sx={{
              fontSize: { xs: "0.92rem", sm: "0.96rem" },
              fontWeight: 700,
              color: "#009b67",
            }}
          >
            {t("parent_dashboard_study_insights_schedule")}
          </Typography>
        </Box>

        <Divider sx={{ borderColor: "#E5E7EB", mb: 1.45 }} />

        <Box
          sx={{
            display: "grid",
            gridTemplateColumns: { xs: "1fr", lg: "0.58fr 1.42fr" },
            gap: 1.2,
            mb: 1.2,
            minWidth: 0,
            alignItems: "stretch",
          }}
        >
          <Box
            sx={{
              p: { xs: 1.15, sm: 1.3 },
              borderRadius: "16px",
              bgcolor: "#ECFDF5",
              border: "1px solid #BBF7D0",
              boxShadow: "inset 0 1px 0 rgba(255,255,255,0.45)",
              minWidth: 0,
            }}
          >
            <Typography
              sx={{
                fontSize: "0.74rem",
                fontWeight: 700,
                color: "#047857",
                mb: 0.7,
              }}
            >
              {t("dashboard_study_pattern")}
            </Typography>

            <Typography
              sx={{
                fontSize: { xs: "1.35rem", sm: "1.55rem" },
                fontWeight: 800,
                color: "#111827",
                lineHeight: 1.1,
                mb: 0.85,
                wordBreak: "break-word",
                overflowWrap: "anywhere",
              }}
            >
              {patternTitle}
            </Typography>

            <Typography
              sx={{
                fontSize: "0.84rem",
                color: "#4B5563",
                lineHeight: 1.45,
                wordBreak: "break-word",
                overflowWrap: "anywhere",
              }}
            >
              {patternSummary}
            </Typography>
            {studyPattern?.suggestion && (
              <Box
                sx={{
                  mt: 1.1,
                  p: 1,
                  borderRadius: "12px",
                  bgcolor: "#FFFFFF",
                  border: "1px solid #BBF7D0",
                }}
              >
                <Typography
                  sx={{
                    fontSize: "0.72rem",
                    fontWeight: 800,
                    color: "#047857",
                    mb: 0.35,
                  }}
                >
                  {language === "bm" ? "Cadangan" : "Suggestion"}
                </Typography>

                <Typography
                  sx={{
                    fontSize: "0.8rem",
                    color: "#4B5563",
                    lineHeight: 1.4,
                    wordBreak: "break-word",
                    overflowWrap: "anywhere",
                  }}
                >
                  {studyPattern.suggestion}
                </Typography>
              </Box>
            )}
          </Box>

          <Box
            sx={{
              p: { xs: 1.15, sm: 1.3 },
              borderRadius: "16px",
              bgcolor: "#F8FAFC",
              border: "1px solid #EEF2F7",
              minWidth: 0,
              height: "100%",
              display: "flex",
              flexDirection: "column",
            }}
          >
            <Box
              sx={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                gap: 1,
                flexWrap: "wrap",
                mb: 0.85,
              }}
            >
              <Box sx={{ minWidth: 0 }}>
                <Typography
                  sx={{
                    fontSize: "0.74rem",
                    fontWeight: 700,
                    color: "#6B7280",
                    mb: 0.15,
                  }}
                >
                  {t("dashboard_consistency_across_year")}
                </Typography>

                <Typography
                  sx={{
                    fontSize: "0.82rem",
                    fontWeight: 700,
                    color: "#111827",
                    lineHeight: 1.3,
                  }}
                >
                  {t("parent_dashboard_consistency_subtitle")}
                </Typography>
              </Box>

              <Box sx={{ display: "flex", alignItems: "center", gap: 0.7, flexWrap: "wrap" }}>
                <Chip
                  label={`${heatmapActiveDays} ${t("dashboard_active_days")}`}
                  sx={{
                    height: 24,
                    borderRadius: "999px",
                    bgcolor: "#ECFDF5",
                    color: "#059669",
                    fontWeight: 700,
                    "& .MuiChip-label": {
                      px: 1,
                      fontSize: "0.7rem",
                    },
                  }}
                />

                <select
                  value={selectedHeatmapYear}
                  onChange={(e) => setSelectedHeatmapYear(Number(e.target.value))}
                  style={{
                    height: "28px",
                    borderRadius: "10px",
                    border: "1px solid #D1D5DB",
                    padding: "0 10px",
                    fontWeight: 700,
                    color: "#374151",
                    background: "#FFFFFF",
                  }}
                >
                  <option value={currentYear}>{currentYear}</option>
                  <option value={currentYear - 1}>{currentYear - 1}</option>
                </select>
              </Box>
            </Box>

            <Box
              sx={{
                flex: 1,
                minHeight: { xs: 90, md: 105 },
                display: "flex",
                alignItems: "center",
                justifyContent: "flex-start",
                width: "100%",
                overflowX: "auto",
                pb: 0.35,
              }}
            >
              <Box
                sx={{
                  display: "grid",
                  gridAutoFlow: "column",
                  gridTemplateRows: {
                    xs: "repeat(7, 8px)",
                    sm: "repeat(7, 10px)",
                    md: "repeat(7, 11px)",
                  },
                  gridAutoColumns: {
                    xs: "8px",
                    sm: "10px",
                    md: "11px",
                  },
                  gap: { xs: "2px", sm: "3px", md: "4px" },
                  minWidth: "fit-content",
                }}
              >
                {alignedHeatmapCells.map((cell, index) => (
                  <Tooltip
                    key={index}
                    title={
                      cell.isPlaceholder
                        ? ""
                        : `${cell.date} • ${cell.minutes} min`
                    }
                    arrow
                  >
                    <Box
                      sx={{
                        width: { xs: 8, sm: 10, md: 11 },
                        height: { xs: 8, sm: 10, md: 11 },
                        borderRadius: "2px",
                        bgcolor: cell.isPlaceholder
                          ? "transparent"
                          : getHeatmapColor(cell.intensity),
                        cursor: cell.isPlaceholder ? "default" : "pointer",
                      }}
                    />
                  </Tooltip>
                ))}
              </Box>
            </Box>

            <Box
              sx={{
                display: "flex",
                alignItems: "center",
                gap: 0.85,
                flexWrap: "wrap",
                mt: "auto",
                pt: 0.9,
              }}
            >
              <Typography sx={{ fontSize: "0.72rem", color: "#6B7280", fontWeight: 700 }}>
                {t("dashboard_best_day")}: {heatmapBestMinutes} min
              </Typography>

              <Box sx={{ display: "flex", alignItems: "center", gap: 0.35 }}>
                {[0, 1, 2, 3, 4].map((level) => (
                  <Box
                    key={level}
                    sx={{
                      width: 8,
                      height: 8,
                      borderRadius: "2px",
                      bgcolor: getHeatmapColor(level),
                    }}
                  />
                ))}
              </Box>
            </Box>
          </Box>
        </Box>

        <Box
          sx={{
            p: { xs: 1.15, sm: 1.35, md: 1.45 },
            borderRadius: "18px",
            bgcolor: "#F8FAFC",
            border: "1px solid #E5E7EB",
            minWidth: 0,
          }}
        >
          <Box
            sx={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              gap: 1,
              flexWrap: "wrap",
              mb: 1,
            }}
          >
            <Box sx={{ display: "flex", alignItems: "center", gap: 0.8 }}>
              <EventRepeatRoundedIcon sx={{ fontSize: 18, color: "#10B981" }} />
              <Typography
                sx={{
                  fontSize: { xs: "0.9rem", sm: "0.95rem" },
                  fontWeight: 800,
                  color: "#065F46",
                }}
              >
                {t("parent_dashboard_personalized_study_schedule")}
              </Typography>
            </Box>

            <Chip
              label={`${consistencyWeeklyCompleted}/${consistencyWeeklyTarget} ${t(
                "dashboard_sessions_done"
              )}`}
              sx={{
                height: 26,
                borderRadius: "999px",
                bgcolor: "#ECFDF5",
                color: "#059669",
                fontWeight: 700,
                "& .MuiChip-label": {
                  px: 1,
                  fontSize: "0.74rem",
                },
              }}
            />
          </Box>

          <Box
            sx={{
              display: "grid",
              gridTemplateColumns: {
                xs: "1fr",
                sm: "repeat(2, minmax(0, 1fr))",
                lg: "repeat(3, minmax(0, 1fr))",
              },
              gap: 1,
              mb: 1,
            }}
          >
            <Box
              sx={{
                p: 1.05,
                borderRadius: "14px",
                bgcolor: "#FFFFFF",
                border: "1px solid #D1FAE5",
                boxShadow: "0 4px 14px rgba(16, 185, 129, 0.05)",
              }}
            >
              <Box sx={{ display: "flex", alignItems: "center", gap: 0.7, mb: 0.45 }}>
                <ScheduleRoundedIcon sx={{ fontSize: 16, color: "#10B981" }} />
                <Typography sx={{ fontSize: "0.72rem", fontWeight: 700, color: "#6B7280" }}>
                  {t("dashboard_best_study_time_window")}
                </Typography>
              </Box>

              <Typography sx={{ fontSize: "0.92rem", fontWeight: 800, color: "#111827" }}>
                {scheduleBestTime}
              </Typography>
            </Box>

            <Box
              sx={{
                p: 1.05,
                borderRadius: "14px",
                bgcolor: "#FFFFFF",
                border: "1px solid #DBEAFE",
                boxShadow: "0 4px 14px rgba(59, 130, 246, 0.05)",
              }}
            >
              <Box sx={{ display: "flex", alignItems: "center", gap: 0.7, mb: 0.45 }}>
                <AccessTimeFilledRoundedIcon sx={{ fontSize: 16, color: "#3B82F6" }} />
                <Typography sx={{ fontSize: "0.72rem", fontWeight: 700, color: "#6B7280" }}>
                  {t("dashboard_recommended_session_length")}
                </Typography>
              </Box>

              <Typography sx={{ fontSize: "0.92rem", fontWeight: 800, color: "#111827" }}>
                {scheduleSessionLength}
              </Typography>
            </Box>

            <Box
              sx={{
                p: 1.05,
                borderRadius: "14px",
                bgcolor: "#FFFFFF",
                border: "1px solid #FDE68A",
                boxShadow: "0 4px 14px rgba(245, 158, 11, 0.05)",
              }}
            >
              <Box sx={{ display: "flex", alignItems: "center", gap: 0.7, mb: 0.45 }}>
                <BoltRoundedIcon sx={{ fontSize: 16, color: "#F59E0B" }} />
                <Typography sx={{ fontSize: "0.72rem", fontWeight: 700, color: "#6B7280" }}>
                  {t("dashboard_weekly_target")}
                </Typography>
              </Box>

              <Typography sx={{ fontSize: "0.92rem", fontWeight: 800, color: "#111827" }}>
                {scheduleWeeklyTarget} {t("dashboard_sessions")}
              </Typography>
            </Box>
          </Box>

          <Box
            sx={{
              p: 1.05,
              borderRadius: "14px",
              bgcolor: "#FFFFFF",
              border: "1px solid #E5E7EB",
              mb: 1,
            }}
          >
            <Box
              sx={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                gap: 1,
                mb: 0.55,
                flexWrap: "wrap",
              }}
            >
              <Typography sx={{ fontSize: "0.72rem", fontWeight: 700, color: "#6B7280" }}>
                {t("dashboard_weekly_target_progress")}
              </Typography>

              <Typography sx={{ fontSize: "0.76rem", fontWeight: 800, color: "#111827" }}>
                {consistencyWeeklyCompleted}/{consistencyWeeklyTarget} {t("dashboard_sessions_done")}
              </Typography>
            </Box>

            <Box
              sx={{
                width: "100%",
                height: 8,
                borderRadius: "999px",
                bgcolor: "#E5E7EB",
                overflow: "hidden",
              }}
            >
              <Box
                sx={{
                  width: `${consistencyProgressPercent}%`,
                  height: "100%",
                  borderRadius: "999px",
                  background: "linear-gradient(90deg, #10B981 0%, #3B82F6 100%)",
                }}
              />
            </Box>
          </Box>

          <Box
            sx={{
              p: 1.05,
              borderRadius: "16px",
              bgcolor: "#FFFFFF",
              border: "1px solid #E5E7EB",
              minWidth: 0,
            }}
          >
            <Box sx={{ display: "flex", alignItems: "center", gap: 0.7, mb: 0.75 }}>
              <PlayCircleRoundedIcon sx={{ fontSize: 17, color: "#5F8FFF" }} />
              <Typography
                sx={{
                  fontSize: "0.73rem",
                  fontWeight: 700,
                  color: "#6B7280",
                }}
              >
                {t("dashboard_next_suggested_session")}
              </Typography>
            </Box>

            <Box
              sx={{
                display: "grid",
                gridTemplateColumns: { xs: "1fr", md: "auto 34px minmax(0, 1fr) auto" },
                alignItems: "center",
                gap: { xs: 0.85, md: 1 },
                minWidth: 0,
              }}
            >
              {/* chips */}
              <Box
                sx={{
                  display: "flex",
                  alignItems: "center",
                  gap: 0.6,
                  flexWrap: "wrap",
                  minWidth: 0,
                }}
              >
                <Chip
                  label={nextSessionLabel}
                  sx={{
                    height: 27,
                    borderRadius: "999px",
                    bgcolor: "#FEF3C7",
                    color: "#B45309",
                    fontWeight: 700,
                    "& .MuiChip-label": {
                      px: 1,
                      fontSize: "0.74rem",
                    },
                  }}
                />
                <Chip
                  label={nextSessionTime}
                  sx={{
                    height: 27,
                    borderRadius: "999px",
                    bgcolor: "#EEF2FF",
                    color: "#4F46E5",
                    fontWeight: 700,
                    "& .MuiChip-label": {
                      px: 1,
                      fontSize: "0.74rem",
                    },
                  }}
                />
              </Box>

              {/* separator */}
              <Box
                sx={{
                  display: { xs: "none", md: "block" },
                  width: 34,
                  height: "1px",
                  bgcolor: "#D1D5DB",
                  flexShrink: 0,
                }}
              />

              {/* topic */}
              <Box
                sx={{
                  minWidth: 0,
                  display: "flex",
                  alignItems: "flex-start",
                  gap: 0.65,
                  gridColumn: { xs: "1 / -1", md: "auto" },
                }}
              >
                <BoltRoundedIcon sx={{ fontSize: 15, color: "#10B981", flexShrink: 0, mt: "2px" }} />
                <Typography
                  sx={{
                    fontSize: "0.84rem",
                    color: "#111827",
                    fontWeight: 700,
                    lineHeight: 1.35,
                    wordBreak: "break-word",
                    overflowWrap: "anywhere",
                  }}
                >
                  {nextSessionFocus}
                </Typography>
              </Box>
            </Box>
          </Box>
        </Box>
      </Paper>
    </Box>
  );
};

export default ParentChildDashboard;