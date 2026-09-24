import React, { useState } from "react";
import {
  Box,
  Typography,
  Paper,
  Avatar,
  Button,
  Chip,
  Stack,
  Divider,
  ToggleButton,
  ToggleButtonGroup,
  CircularProgress,
} from "@mui/material";
import PersonOutlineIcon from "@mui/icons-material/PersonOutline";
import MailOutlineIcon from "@mui/icons-material/MailOutline";
import LoginIcon from "@mui/icons-material/Login";
import TranslateIcon from "@mui/icons-material/Translate";
import { useLanguage } from "../../context/LanguageContext";

const ProfilePage = () => {
  const storedUser = JSON.parse(localStorage.getItem("user")) || {};
  const { t, setLanguage } = useLanguage();

  const [selectedLanguage, setSelectedLanguage] = useState(
    storedUser.language || "english"
  );
  const [isSaving, setIsSaving] = useState(false);

  const hasChanges = selectedLanguage !== (storedUser.language || "english");

  const handleLanguageChange = (_, newLanguage) => {
    if (newLanguage) {
      setSelectedLanguage(newLanguage);
    }
  };

  const handleSave = async () => {
    if (!hasChanges) return;

    try {
      setIsSaving(true);

      const response = await fetch(
        `${process.env.REACT_APP_API_BASE_URL}/api/users/${storedUser.id}/language`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            language: selectedLanguage,
          }),
        }
      );

      const data = await response.json();

      if (!data.success) {
        alert(data.message || "Failed to update language");
        return;
      }

      const updatedUser = {
        ...storedUser,
        language: selectedLanguage,
      };

      localStorage.setItem("user", JSON.stringify(updatedUser));
      setLanguage(selectedLanguage);
    } catch (error) {
      console.error("Failed to update language:", error);
      alert("Failed to update language");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <Box sx={{ maxWidth: "980px", mx: "auto", mt: 1 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" fontWeight="bold" sx={{ color: "#111827", mb: 1 }}>
          {t("profile_title")}
        </Typography>
        <Typography color="textSecondary" variant="subtitle1">
          {t("profile_subtitle")}
        </Typography>
      </Box>

      <Box
        sx={{
          display: "grid",
          gridTemplateColumns: { xs: "1fr", md: "1.1fr 1fr" },
          gap: 3,
        }}
      >
        {/* LEFT: ACCOUNT CARD */}
        <Paper
          elevation={0}
          sx={{
            p: 4,
            borderRadius: "24px",
            border: "1px solid #E5E7EB",
            background:
              "linear-gradient(180deg, #ffffff 0%, #f8fbff 100%)",
            boxShadow: "0 12px 32px rgba(15, 23, 42, 0.06)",
          }}
        >
          <Typography
            variant="overline"
            sx={{ color: "#3855c0", fontWeight: 700, letterSpacing: "0.08em" }}
          >
            {t("profile_account")}
          </Typography>

          <Box
            sx={{
              mt: 1.5,
              display: "flex",
              flexDirection: { xs: "column", sm: "row" },
              alignItems: { xs: "center", sm: "center" },
              gap: 2.5,
            }}
          >
            <Avatar
              src={storedUser.photo_url || ""}
              alt={storedUser.name || "User"}
              sx={{
                width: 86,
                height: 86,
                bgcolor: "#E0E7FF",
                color: "#3855c0",
                fontWeight: 700,
                fontSize: "28px",
                border: "3px solid #ffffff",
                boxShadow: "0 6px 18px rgba(0,0,0,0.08)",
              }}
            >
              {!storedUser.photo_url && (storedUser.name?.[0]?.toUpperCase() || "U")}
            </Avatar>

            <Box sx={{ textAlign: { xs: "center", sm: "left" } }}>
              <Typography variant="h5" fontWeight="bold" sx={{ color: "#111827" }}>
                {storedUser.name || t("profile_student_name")}
              </Typography>

              <Typography sx={{ color: "#6B7280", mt: 0.5 }}>
                {t("profile_signed_in_as")}
              </Typography>

              <Chip
                icon={<LoginIcon />}
                label={
                  storedUser.auth_provider === "google"
                    ? t("profile_provider_google")
                    : t("profile_provider_email")
                }
                sx={{
                  mt: 1.5,
                  borderRadius: "999px",
                  bgcolor: "#EEF2FF",
                  color: "#3855c0",
                  fontWeight: 600,
                }}
              />
            </Box>
          </Box>

          <Divider sx={{ my: 3 }} />

          <Stack spacing={2.5}>
            <Box
              sx={{
                display: "flex",
                alignItems: "center",
                gap: 1.5,
                p: 2,
                borderRadius: "16px",
                bgcolor: "#F9FAFB",
              }}
            >
              <PersonOutlineIcon sx={{ color: "#6B7280" }} />
              <Box>
                <Typography variant="caption" sx={{ color: "#9CA3AF", fontWeight: 700 }}>
                  {t("profile_full_name")}
                </Typography>
                <Typography sx={{ color: "#111827", fontWeight: 600 }}>
                  {storedUser.name || t("profile_student_name")}
                </Typography>
              </Box>
            </Box>

            <Box
              sx={{
                display: "flex",
                alignItems: "center",
                gap: 1.5,
                p: 2,
                borderRadius: "16px",
                bgcolor: "#F9FAFB",
              }}
            >
              <MailOutlineIcon sx={{ color: "#6B7280" }} />
              <Box>
                <Typography variant="caption" sx={{ color: "#9CA3AF", fontWeight: 700 }}>
                  {t("profile_email")}
                </Typography>
                <Typography sx={{ color: "#111827", fontWeight: 600 }}>
                  {storedUser.email || t("profile_student_email")}
                </Typography>
              </Box>
            </Box>
          </Stack>
        </Paper>

        {/* RIGHT: LANGUAGE CARD */}
        <Paper
          elevation={0}
          sx={{
            p: 4,
            borderRadius: "24px",
            border: "1px solid #E5E7EB",
            backgroundColor: "#ffffff",
            boxShadow: "0 12px 32px rgba(15, 23, 42, 0.06)",
          }}
        >
          <Typography
            variant="overline"
            sx={{ color: "#3855c0", fontWeight: 700, letterSpacing: "0.08em" }}
          >
            {t("profile_preferences")}
          </Typography>

          <Box sx={{ mt: 1.5, mb: 3 }}>
            <Typography variant="h6" fontWeight="bold" sx={{ color: "#111827", mb: 1 }}>
              {t("profile_language")}
            </Typography>
            <Typography sx={{ color: "#6B7280", fontSize: "14px", lineHeight: 1.7 }}>
              {t("profile_language_help")}
            </Typography>
          </Box>

          <Box
            sx={{
              p: 2,
              borderRadius: "18px",
              bgcolor: "#F8FAFC",
              border: "1px solid #E5E7EB",
            }}
          >
            <ToggleButtonGroup
              value={selectedLanguage}
              exclusive
              onChange={handleLanguageChange}
              fullWidth
              sx={{
                width: "100%",
                gap: 1,
                "& .MuiToggleButton-root": {
                  flex: 1,
                  border: "1px solid #D1D5DB !important",
                  borderRadius: "14px !important",
                  textTransform: "none",
                  fontWeight: 700,
                  py: 1.4,
                  color: "#374151",
                  backgroundColor: "#ffffff",
                },
                "& .Mui-selected": {
                  backgroundColor: "#3855c0 !important",
                  color: "#ffffff !important",
                  borderColor: "#3855c0 !important",
                },
              }}
            >
              <ToggleButton value="english">
                <TranslateIcon sx={{ mr: 1, fontSize: 18 }} />
                {t("profile_language_english")}
              </ToggleButton>

              <ToggleButton value="bm">
                <TranslateIcon sx={{ mr: 1, fontSize: 18 }} />
                {t("profile_language_bm")}
              </ToggleButton>
            </ToggleButtonGroup>
          </Box>

          <Box
            sx={{
              mt: 4,
              display: "flex",
              justifyContent: "flex-end",
            }}
          >
            <Button
              variant="contained"
              onClick={handleSave}
              disabled={!hasChanges || isSaving}
              sx={{
                minWidth: 170,
                borderRadius: "14px",
                textTransform: "none",
                fontWeight: 700,
                bgcolor: "#3855c0",
                py: 1.2,
                "&:hover": { bgcolor: "#2a4196" },
                "&.Mui-disabled": {
                  bgcolor: "#CBD5E1",
                  color: "#ffffff",
                },
              }}
              startIcon={
                isSaving ? <CircularProgress size={16} sx={{ color: "#ffffff" }} /> : null
              }
            >
              {isSaving ? t("profile_saving") : t("profile_save")}
            </Button>
          </Box>
        </Paper>
      </Box>
    </Box>
  );
};

export default ProfilePage;