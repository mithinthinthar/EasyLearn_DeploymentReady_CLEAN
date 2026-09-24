import React, { useState } from "react";
import {
  Box,
  Container,
  Typography,
  TextField,
  Tabs,
  Tab,
  MenuItem,
  Paper,
  IconButton,
  InputAdornment,
  Button,
} from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";
import TranslateIcon from "@mui/icons-material/Translate";
import SchoolOutlinedIcon from "@mui/icons-material/SchoolOutlined";
import FamilyRestroomOutlinedIcon from "@mui/icons-material/FamilyRestroomOutlined";
import { useNavigate } from "react-router-dom";
import { signInWithPopup } from "firebase/auth";
import { auth, googleProvider } from "../../firebase";
import CustomToast from "../../components/CustomToast";

import googleIcon from "../../assets/authpage/googleIcon.png";

const RegisterPage = () => {
  const [tab, setTab] = useState(0);
  const [loading, setLoading] = useState(false);
  const [loadingText, setLoadingText] = useState("");

  const [toast, setToast] = useState({
    open: false,
    type: "info",
    title: "",
    message: "",
  });

  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    language: "english",
  });

  const role = tab === 0 ? "student" : "parent";

  const showToast = (type, title, message) => {
    setToast({
      open: true,
      type,
      title,
      message,
    });
  };

  // Helper function to map Firebase error codes to user-friendly messages
  const getFirebaseErrorMessage = (error) => {
    switch (error.code) {
      case "auth/popup-closed-by-user":
        return "The Google sign-in popup was closed before completing.";
      case "auth/account-exists-with-different-credential":
        return "An account already exists with a different sign-in method.";
      case "auth/too-many-requests":
        return "Too many attempts. Please try again a little later.";
      case "auth/network-request-failed":
        return "Network error. Please check your internet connection.";
      default:
        return "Something went wrong. Please try again.";
    }
  };

  const handleTabChange = (event, newValue) => {
    setTab(newValue);
  };

  const handleChange = (e) => {
    setFormData((prev) => ({
      ...prev,
      [e.target.name]: e.target.value,
    }));
  };

  const handleGoogleRegister = async () => {
    try {
      setLoading(true);
      setLoadingText("Waiting for Google sign-in session...");

      const result = await signInWithPopup(auth, googleProvider);
      const token = await result.user.getIdToken();

      const payload = {
        token,
        name: result.user.displayName || "User",
        role,
        language: formData.language,
        photo_url: result.user.photoURL || null,
      };

      const res = await fetch(
        `${process.env.REACT_APP_API_BASE_URL}/api/auth/register`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(payload),
        }
      );

      const data = await res.json();

      if (data.success) {
        showToast("success", "Registration Successful", "Your account has been created successfully! Please login.");
        setTimeout(() => navigate("/login"), 900);
      } else {
        showToast("error", "Registration Failed", data.message || "Something went wrong.");
      }
    } catch (error) {
      if (error.code === "auth/popup-closed-by-user") {
        showToast("warning", "Sign-in Cancelled", getFirebaseErrorMessage(error));
      } else {
        showToast("error", "Google Sign-in Failed", getFirebaseErrorMessage(error));
      }
    } finally {
      setLoading(false);
      setLoadingText("");
    }
  };

  return (
    <Box
      sx={{
        minHeight: "100vh",
        background: "linear-gradient(180deg, #f8fbff 0%, #eef4ff 100%)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        px: 2,
        py: 4,
      }}
    >
      <Container maxWidth="sm">
        <Paper
          elevation={0}
          sx={{
            width: "100%",
            p: { xs: 3, sm: 4 },
            borderRadius: "28px",
            position: "relative",
            boxShadow: "0 20px 60px rgba(15, 23, 42, 0.08)",
            border: "1px solid #E5E7EB",
            backgroundColor: "#ffffff",
            overflow: "hidden",
          }}
        >
          <IconButton
            onClick={() => navigate("/")}
            sx={{
              position: "absolute",
              top: 14,
              right: 14,
              color: "#6B7280",
              "&:hover": {
                backgroundColor: "#F3F4F6",
              },
            }}
          >
            <CloseIcon />
          </IconButton>

          <Box sx={{ textAlign: "center", mb: 3 }}>
            <Typography
              variant="h4"
              fontWeight="bold"
              sx={{
                color: "#111827",
                mb: 1,
                fontSize: { xs: "1.9rem", sm: "2.2rem" },
              }}
            >
              Create Account
            </Typography>
            <Typography sx={{ color: "#6B7280", fontSize: "15px" }}>
              Join EasyLearn and unlock your math potential
            </Typography>
          </Box>

          <Tabs
            value={tab}
            onChange={handleTabChange}
            centered
            sx={{
              mb: 3,
              minHeight: "48px",
              "& .MuiTabs-flexContainer": {
                gap: 2,
              },
              "& .MuiTab-root": {
                textTransform: "none",
                fontWeight: "bold",
                fontSize: "15px",
                color: "#6B7280",
                minHeight: "48px",
                px: 2,
                borderRadius: "14px",
                transition: "all 0.2s ease",
              },
              "& .Mui-selected": {
                color: "#2563EB !important",
                backgroundColor: "#EFF6FF",
              },
              "& .MuiTabs-indicator": {
                height: 4,
                borderRadius: 999,
                backgroundColor: "#4F46E5",
              },
            }}
          >
            <Tab
              label={
                <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                  <SchoolOutlinedIcon sx={{ fontSize: 20 }} />
                  <span>Student</span>
                </Box>
              }
            />
            <Tab
              label={
                <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                  <FamilyRestroomOutlinedIcon sx={{ fontSize: 20 }} />
                  <span>Parent</span>
                </Box>
              }
            />
          </Tabs>

          <TextField
            select
            fullWidth
            label="Preferred Language"
            name="language"
            value={formData.language}
            onChange={handleChange}
            sx={{ mb: 3 }}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <TranslateIcon sx={{ color: "#9CA3AF" }} />
                </InputAdornment>
              ),
            }}
          >
            {role === "student"
              ? [
                  <MenuItem key="english" value="english">
                    English (DLP)
                  </MenuItem>,
                  <MenuItem key="bm" value="bm">
                    Bahasa Melayu (Non-DLP)
                  </MenuItem>,
                ]
              : [
                  <MenuItem key="english" value="english">
                    English
                  </MenuItem>,
                  <MenuItem key="bm" value="bm">
                    Bahasa Melayu
                  </MenuItem>,
                ]}
          </TextField>

          <Button
            variant="outlined"
            fullWidth
            onClick={handleGoogleRegister}
            disabled={loading}
            startIcon={
              <Box
                component="img"
                src={googleIcon}
                alt="Google"
                sx={{ width: 22, height: 22 }}
              />
            }
            sx={{
              py: 1.6,
              borderRadius: "16px",
              textTransform: "none",
              fontWeight: 700,
              fontSize: "15px",
              borderColor: "#E5E7EB",
              color: "#111827",
              backgroundColor: "#ffffff",
              boxShadow: "0 8px 20px rgba(15, 23, 42, 0.06)",
              transition: "all 0.2s ease",
              "&:hover": {
                backgroundColor: "#F8FAFC",
                borderColor: "#CBD5E1",
                boxShadow: "0 12px 28px rgba(15, 23, 42, 0.10)",
                transform: "translateY(-1px)",
              },
            }}
          >
            <Box component="span" sx={{ ml: 0.5 }}>
              Sign Up with{" "}
              <Box component="span" sx={{ color: "#4285F4" }}>G</Box>
              <Box component="span" sx={{ color: "#EA4335" }}>o</Box>
              <Box component="span" sx={{ color: "#FBBC05" }}>o</Box>
              <Box component="span" sx={{ color: "#4285F4" }}>g</Box>
              <Box component="span" sx={{ color: "#34A853" }}>l</Box>
              <Box component="span" sx={{ color: "#EA4335" }}>e</Box>
            </Box>
          </Button>

          <Typography align="center" sx={{ mt: 4, color: "#6B7280" }}>
            Already have an account?{" "}
            <Box
              component="span"
              onClick={() => navigate("/login")}
              sx={{
                color: "#4F46E5",
                cursor: "pointer",
                fontWeight: "bold",
                "&:hover": {
                  textDecoration: "underline",
                },
              }}
            >
              Login
            </Box>
          </Typography>
        </Paper>
      </Container>

      {loading && (
        <Box
          sx={{
            position: "fixed",
            inset: 0,
            bgcolor: "rgba(255,255,255,0.65)",
            backdropFilter: "blur(2px)",
            zIndex: 2000,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexDirection: "column",
            gap: 2,
          }}
        >
          <Box
            sx={{
              width: 42,
              height: 42,
              border: "4px solid #DBEAFE",
              borderTop: "4px solid #2563EB",
              borderRadius: "50%",
              animation: "spin 0.9s linear infinite",
            }}
          />
          <Typography sx={{ color: "#1F2937", fontWeight: 600 }}>
            {loadingText || "Please wait..."}
          </Typography>

          <style>
            {`@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`}
          </style>
        </Box>
      )}

      <CustomToast
        open={toast.open}
        type={toast.type}
        title={toast.title}
        message={toast.message}
        onClose={() => setToast((prev) => ({ ...prev, open: false }))}
      />
    </Box>
  );
};

export default RegisterPage;