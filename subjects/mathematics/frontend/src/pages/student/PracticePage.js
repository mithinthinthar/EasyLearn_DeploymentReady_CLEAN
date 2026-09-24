import React, { useState, useEffect } from "react";
import {
  Box,
  Typography,
  Paper,
  Button,
  Tabs,
  Tab,
  Chip,
  Divider,
  CircularProgress,
} from "@mui/material";
import { useNavigate } from "react-router-dom";
import { useLanguage } from "../../context/LanguageContext";

// Icons
import MenuBookIcon from "@mui/icons-material/MenuBook";
import EditNoteIcon from "@mui/icons-material/EditNote";
import TranslateIcon from "@mui/icons-material/Translate";

const PracticePage = () => {
  const navigate = useNavigate();
  const { t, language } = useLanguage();

  const [form, setForm] = useState("Form 4");
  const [syllabus, setSyllabus] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  const isEnglish = language !== "bm";
  const languageDisplay = isEnglish
    ? t("header_language_english")
    : t("header_language_bm");

  useEffect(() => {
    const fetchSyllabus = async () => {
      try {
        const response = await fetch(
          `${process.env.REACT_APP_API_BASE_URL}/api/syllabus`
        );
        const data = await response.json();
        if (data.success) {
          setSyllabus(data.syllabus);
        }
      } catch (error) {
        console.error("Failed to fetch syllabus:", error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchSyllabus();
  }, []);

  const currentTopics = syllabus.filter((ch) => ch.form === form);

  const handleStart = (paper, chapterObj) => {
    const chapterString = `${chapterObj.chapter_no}: ${chapterObj.name_en}`;

    navigate(`/practice/${paper}`, {
      state: {
        form: form,
        chapter_id: chapterObj.id,

        // display name only
        topic: isEnglish ? chapterObj.name_en : chapterObj.name_bm,

        // backend matching
        chapter: chapterString,
        chapter_string: chapterString,
      },
    });
  };

  if (isLoading) {
    return (
      <Box
        sx={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          height: "80vh",
        }}
      >
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      {/* HEADER SECTION */}
      <Box mb={3} textAlign="center">
        <Box
          sx={{
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            gap: 1.5,
            mb: 1,
          }}
        >
          <Typography variant="h4" fontWeight="bold" sx={{ color: "#111827" }}>
            {t("practice_title")}
          </Typography>
        </Box>

        <Typography color="textSecondary" variant="subtitle1" mb={2}>
          {t("practice_subtitle")}
        </Typography>
      </Box>

      {/* TABS */}
      <Box sx={{ display: "flex", justifyContent: "center", mb: 5 }}>
        <Tabs
          value={form}
          onChange={(e, newValue) => setForm(newValue)}
          TabIndicatorProps={{
            style: {
              height: "100%",
              borderRadius: "25px",
              backgroundColor: "#3855c0",
              zIndex: 0,
            },
          }}
          sx={{
            minHeight: "44px",
            backgroundColor: "#F3F4F6",
            borderRadius: "25px",
            padding: "4px",
            "& .MuiTabs-indicator": {
              zIndex: 0,
            },
          }}
        >
          <Tab
            value="Form 4"
            label={t("practice_form4")}
            disableRipple
            sx={{
              textTransform: "none",
              fontWeight: "bold",
              fontSize: "14px",
              minHeight: "36px",
              borderRadius: "20px",
              zIndex: 1,
              px: { xs: 4, sm: 6 },
              color: form === "Form 4" ? "#ffffff" : "#6B7280",
              "&.Mui-selected": {
                color: "#ffffff",
              },
            }}
          />
          <Tab
            value="Form 5"
            label={t("practice_form5")}
            disableRipple
            sx={{
              textTransform: "none",
              fontWeight: "bold",
              fontSize: "14px",
              minHeight: "36px",
              borderRadius: "20px",
              zIndex: 1,
              px: { xs: 4, sm: 6 },
              color: form === "Form 5" ? "#ffffff" : "#6B7280",
              "&.Mui-selected": {
                color: "#ffffff",
              },
            }}
          />
        </Tabs>
      </Box>

      {/* TOPIC GRID */}
      <Box
        sx={{
          display: "grid",
          gridTemplateColumns: {
            xs: "1fr",
            sm: "repeat(2, 1fr)",
            md: "repeat(3, 1fr)",
          },
          gap: 3,
        }}
      >
        {currentTopics.map((topic) => (
          <Paper
            key={topic.id}
            elevation={0}
            sx={{
              p: 3,
              borderRadius: "16px",
              border: "1px solid #E5E7EB",
              display: "flex",
              flexDirection: "column",
              justifyContent: "space-between",
              transition: "all 0.2s ease-in-out",
              "&:hover": {
                transform: "translateY(-4px)",
                boxShadow: "0 12px 24px rgba(56, 85, 192, 0.08)",
                borderColor: "#3855c0",
              },
            }}
          >
            <Box>
              <Chip
                label={
                  isEnglish
                    ? topic.chapter_no
                    : topic.chapter_no.replace("Chapter", "Bab")
                }
                size="small"
                sx={{
                  bgcolor: "#EEF2FF",
                  color: "#3855c0",
                  fontWeight: "bold",
                  fontSize: "11px",
                  mb: 1.5,
                }}
              />

              <Typography
                variant="h6"
                fontWeight="bold"
                sx={{ color: "#111827", lineHeight: 1.3, mb: 1 }}
              >
                {isEnglish ? topic.name_en : topic.name_bm}
              </Typography>

              <Typography variant="body2" sx={{ color: "#6B7280", mb: 2 }}>
                {isEnglish ? topic.desc_en : topic.desc_bm}
              </Typography>
            </Box>

            <Box>
              <Divider sx={{ mb: 2, mt: 1 }} />

              <Box display="flex" gap={1.5}>
                <Button
                  startIcon={<MenuBookIcon fontSize="small" />}
                  fullWidth
                  disableElevation
                  onClick={() => handleStart("kertas1", topic)}
                  sx={{
                    borderRadius: "10px",
                    textTransform: "none",
                    fontWeight: "bold",
                    fontSize: "13px",
                    background: "#ECFDF5",
                    color: "#047857",
                    "&:hover": { background: "#D1FAE5" },
                  }}
                >
                  {t("practice_paper1")}
                </Button>

                <Button
                  startIcon={<EditNoteIcon fontSize="small" />}
                  fullWidth
                  disableElevation
                  onClick={() => handleStart("kertas2", topic)}
                  sx={{
                    borderRadius: "10px",
                    textTransform: "none",
                    fontWeight: "bold",
                    fontSize: "13px",
                    background: "#FFF7ED",
                    color: "#C2410C",
                    "&:hover": { background: "#FFEDD5" },
                  }}
                >
                  {t("practice_paper2")}
                </Button>
              </Box>
            </Box>
          </Paper>
        ))}
      </Box>
    </Box>
  );
};

export default PracticePage;