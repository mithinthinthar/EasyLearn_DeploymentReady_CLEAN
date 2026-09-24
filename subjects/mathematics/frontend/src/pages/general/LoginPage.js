import React, { useState } from "react";
import {
  Box,
  Container,
  Typography,
  TextField,
  Paper,
  IconButton,
  InputAdornment,
  Button,
} from "@mui/material";
import { useLanguage } from "../../context/LanguageContext";

import CloseIcon from "@mui/icons-material/Close";
import MailOutlineIcon from "@mui/icons-material/MailOutline";
import LockOutlinedIcon from "@mui/icons-material/LockOutlined";
import VisibilityIcon from "@mui/icons-material/Visibility";
import VisibilityOffIcon from "@mui/icons-material/VisibilityOff";
import { useNavigate } from "react-router-dom";
import { signInWithEmailAndPassword, signInWithPopup } from "firebase/auth";
import { auth, googleProvider } from "../../firebase";
import { logUserActivity } from "../../utils/logger";
import CustomToast from "../../components/CustomToast";

import googleIcon from "../../assets/authpage/googleIcon.png";

const LoginPage = () => {
  const { setLanguage } = useLanguage();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(false);
  const [loadingText, setLoadingText] = useState("");
  const [formData, setFormData] = useState({
    email: "",
    password: "",
  });

  const [showPassword, setShowPassword] = useState(false);

  const [toast, setToast] = useState({
    open: false,
    type: "info",
    title: "",
    message: "",
  });

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
      case "auth/invalid-email":
        return "Please enter a valid email address.";
      case "auth/invalid-credential":
        return "Incorrect email or password.";
      case "auth/user-not-found":
        return "No account was found for this email.";
      case "auth/wrong-password":
        return "Incorrect email or password.";
      case "auth/email-already-in-use":
        return "This email is already being used by another account.";
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

  const handleChange = (e) => {
    setFormData((prev) => ({
      ...prev,
      [e.target.name]: e.target.value,
    }));
  };

  const handleEmailLogin = async () => {
    try {
      setLoading(true);
      setLoadingText("Signing in with email...");

      const userCredential = await signInWithEmailAndPassword(
        auth,
        formData.email,
        formData.password
      );

      const token = await userCredential.user.getIdToken();

      const res = await fetch(
        `${process.env.REACT_APP_API_BASE_URL}/api/auth/login`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ token }),
        }
      );

      const data = await res.json();

      if (data.success) {
        localStorage.setItem("user", JSON.stringify(data.user));
        setLanguage(data.user.language || "english");
        logUserActivity("login");
        showToast("success", "Login Successful", "Welcome back!");

        setTimeout(() => {
          if (data.user.role === "student") {
            navigate("/studentDashboard");
          } else if (data.user.role === "parent") {
            navigate("/parentDashboard");
          } else if (data.user.role === "admin") {
            navigate("/adminDashboard");
          }
        }, 700);
      } else {
        showToast("error", "Login Failed", data.message || "Login failed.");
      }
    } catch (error) {
      showToast("error", "Login Failed", getFirebaseErrorMessage(error));
    } finally {
      setLoading(false);
      setLoadingText("");
    }
  };

  const handleGoogleLogin = async () => {
    try {
      setLoading(true);
      setLoadingText("Waiting for Google sign-in session...");

      const result = await signInWithPopup(auth, googleProvider);
      const token = await result.user.getIdToken();

      const res = await fetch(
        `${process.env.REACT_APP_API_BASE_URL}/api/auth/login`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            token,
            photo_url: result.user.photoURL || null,
          }),
        }
      );

      const data = await res.json();

      if (data.success) {
        localStorage.setItem("user", JSON.stringify(data.user));
        setLanguage(data.user.language || "english");
        logUserActivity("login");
        showToast("success", "Login Successful", "Welcome back!");

        setTimeout(() => {
          if (data.user.role === "student") {
            navigate("/studentDashboard");
          } else if (data.user.role === "parent") {
            navigate("/parentDashboard");
          } else if (data.user.role === "admin") {
            navigate("/adminDashboard");
          }
        }, 700);
      } else {
        showToast("error", "Login Failed", data.message || "No account found. Please register first.");
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
              Welcome Back
            </Typography>
            <Typography sx={{ color: "#6B7280", fontSize: "15px" }}>
              Sign in to continue your EasyLearn learning journey
            </Typography>
          </Box>

          <TextField
            fullWidth
            label="Email"
            name="email"
            type="email"
            value={formData.email}
            onChange={handleChange}
            sx={{ mb: 2 }}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <MailOutlineIcon sx={{ color: "#9CA3AF" }} />
                </InputAdornment>
              ),
            }}
          />

          <TextField
            fullWidth
            label="Password"
            name="password"
            type={showPassword ? "text" : "password"}
            value={formData.password}
            onChange={handleChange}
            sx={{ mb: 3 }}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <LockOutlinedIcon sx={{ color: "#9CA3AF" }} />
                </InputAdornment>
              ),
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton
                    onClick={() => setShowPassword((prev) => !prev)}
                    edge="end"
                    sx={{ color: "#9CA3AF" }}
                  >
                    {showPassword ? <VisibilityOffIcon /> : <VisibilityIcon />}
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />

          <Button
            variant="contained"
            fullWidth
            onClick={handleEmailLogin}
            disabled={loading}
            sx={{
              py: 1.6,
              borderRadius: "16px",
              textTransform: "none",
              fontWeight: 700,
              fontSize: "15px",
              backgroundColor: "#2563EB",
              boxShadow: "0 12px 28px rgba(37, 99, 235, 0.18)",
              "&:hover": {
                backgroundColor: "#1D4ED8",
                boxShadow: "0 16px 32px rgba(37, 99, 235, 0.24)",
                transform: "translateY(-1px)",
              },
            }}
          >
            Login with Email
          </Button>

          <Box sx={{ display: "flex", alignItems: "center", my: 3 }}>
            <Box sx={{ flex: 1, height: "1px", backgroundColor: "#E5E7EB" }} />
            <Typography
              sx={{
                px: 2,
                color: "#9CA3AF",
                fontWeight: 700,
                fontSize: "12px",
                letterSpacing: "0.06em",
              }}
            >
              OR
            </Typography>
            <Box sx={{ flex: 1, height: "1px", backgroundColor: "#E5E7EB" }} />
          </Box>

          <Button
            variant="outlined"
            fullWidth
            onClick={handleGoogleLogin}
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
              Continue with{" "}
              <Box component="span" sx={{ color: "#4285F4" }}>G</Box>
              <Box component="span" sx={{ color: "#EA4335" }}>o</Box>
              <Box component="span" sx={{ color: "#FBBC05" }}>o</Box>
              <Box component="span" sx={{ color: "#4285F4" }}>g</Box>
              <Box component="span" sx={{ color: "#34A853" }}>l</Box>
              <Box component="span" sx={{ color: "#EA4335" }}>e</Box>
            </Box>
          </Button>

          <Typography align="center" sx={{ mt: 4, color: "#6B7280" }}>
            Don’t have an account?{" "}
            <Box
              component="span"
              onClick={() => navigate("/register")}
              sx={{
                color: "#4F46E5",
                cursor: "pointer",
                fontWeight: "bold",
                "&:hover": {
                  textDecoration: "underline",
                },
              }}
            >
              Register
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

export default LoginPage;