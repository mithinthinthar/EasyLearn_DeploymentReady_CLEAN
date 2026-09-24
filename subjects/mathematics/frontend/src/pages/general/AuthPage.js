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
  Dialog,
  DialogContent,
  Tabs,
  Tab,
  MenuItem,
} from "@mui/material";
import { useLanguage } from "../../context/LanguageContext";

import CloseIcon from "@mui/icons-material/Close";
import MailOutlineIcon from "@mui/icons-material/MailOutline";
import LockOutlinedIcon from "@mui/icons-material/LockOutlined";
import VisibilityIcon from "@mui/icons-material/Visibility";
import VisibilityOffIcon from "@mui/icons-material/VisibilityOff";
import TranslateIcon from "@mui/icons-material/Translate";
import SchoolOutlinedIcon from "@mui/icons-material/SchoolOutlined";
import FamilyRestroomOutlinedIcon from "@mui/icons-material/FamilyRestroomOutlined";

import { useNavigate } from "react-router-dom";
import {
  signInWithEmailAndPassword,
  signInWithPopup,
  signOut,
  createUserWithEmailAndPassword,
  sendEmailVerification,
  sendPasswordResetEmail,
} from "firebase/auth";
import { auth, googleProvider } from "../../firebase";
import { logUserActivity } from "../../utils/logger";
import CustomToast from "../../components/CustomToast";

import googleIcon from "../../assets/authpage/googleIcon.png";

const AuthPage = () => {
  const { setLanguage } = useLanguage();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(false);
  const [loadingText, setLoadingText] = useState("");

  const [authStep, setAuthStep] = useState("identifier");
  // identifier | password_login | password_signup | verify_email | google_only

  const [formData, setFormData] = useState({
    email: "",
  });

  const [emailFlow, setEmailFlow] = useState({
    email: "",
    password: "",
    confirmPassword: "",
    dbUserExists: false,
  });

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const [lookupUserRole, setLookupUserRole] = useState(null);
  const [lookupContactMessage, setLookupContactMessage] = useState("");

  const [toast, setToast] = useState({
    open: false,
    type: "info",
    title: "",
    message: "",
  });

  const [onboardingOpen, setOnboardingOpen] = useState(false);
  const [onboardingTab, setOnboardingTab] = useState(0);
  const [onboardingData, setOnboardingData] = useState({
    language: "english",
  });

  const [pendingAuth, setPendingAuth] = useState(null);

  const role = onboardingTab === 0 ? "student" : "parent";

  const showToast = (type, title, message) => {
    setToast({
      open: true,
      type,
      title,
      message,
    });
  };

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
      case "auth/weak-password":
        return "Password is too weak.";
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

  const buildNameFromEmail = (email) => {
    const localPart = (email || "").split("@")[0] || "User";
    return localPart
      .replace(/[._-]+/g, " ")
      .replace(/\b\w/g, (char) => char.toUpperCase());
  };

  const getActionCodeSettings = () => ({
    url: `${window.location.origin}/auth`,
    handleCodeInApp: false,
  });

  const loginToBackendWithToken = async (token, photo_url = null) => {
    const res = await fetch(`${process.env.REACT_APP_API_BASE_URL}/api/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        token,
        photo_url,
      }),
    });

    return {
      status: res.status,
      data: await res.json(),
    };
  };

  const completeLogin = (user) => {
    localStorage.setItem("user", JSON.stringify(user));
    setLanguage(user.language || "english");
    logUserActivity("login");

    showToast("success", "Login Successful", "Welcome!");

    setTimeout(() => {
      if (user.role === "student") {
        navigate("/studentDashboard");
      } else if (user.role === "parent") {
        navigate("/parentDashboard");
      } else if (user.role === "admin") {
        navigate("/adminDashboard");
      }
    }, 700);
  };

  const resetToIdentifierStep = async () => {
    setAuthStep("identifier");
    setEmailFlow({
      email: "",
      password: "",
      confirmPassword: "",
      dbUserExists: false,
    });
    setPendingAuth(null);
    setShowPassword(false);
    setShowConfirmPassword(false);
    setFormData({ email: "" });
    setLookupUserRole(null);
    setLookupContactMessage("");

    try {
      await signOut(auth);
    } catch (error) {
      console.error("Sign out reset error:", error);
    }
  };

  const handleIdentifierEmailChange = (e) => {
    setFormData((prev) => ({
      ...prev,
      email: e.target.value,
    }));
  };

  const handleEmailFlowChange = (field, value) => {
    setEmailFlow((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleOnboardingLanguageChange = (e) => {
    setOnboardingData((prev) => ({
      ...prev,
      [e.target.name]: e.target.value,
    }));
  };

  const isStrongPassword = (password) => {
    if (!password || password.length < 8) return false;
    if (!/[A-Z]/.test(password)) return false;
    if (!/[a-z]/.test(password)) return false;
    if (!/[0-9]/.test(password)) return false;
    return true;
  };

  const handleEmailLookup = async () => {
    const email = formData.email.trim().toLowerCase();

    if (!email) {
      showToast("warning", "Missing Email", "Please enter your email address.");
      return;
    }

    try {
      setLoading(true);
      setLoadingText("Checking your email...");

      const res = await fetch(
        `${process.env.REACT_APP_API_BASE_URL}/api/auth/lookup-email`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ email }),
        }
      );

      const data = await res.json();
      setLookupUserRole(data.user_role || null);
      setLookupContactMessage(data.contact_message || "");

      if (!data.success) {
        showToast("error", "Unable to Continue", data.message || "Please try again.");
        return;
      }

      setEmailFlow({
        email,
        password: "",
        confirmPassword: "",
        dbUserExists: Boolean(data.db_user_exists),
      });

      if (data.next_step === "password_login") {
        setAuthStep("password_login");
        return;
      }

      if (data.next_step === "password_signup") {
        setAuthStep("password_signup");
        return;
      }

      if (data.next_step === "google_only") {
        setAuthStep("google_only");
        return;
      }

      showToast("error", "Unable to Continue", "Unknown next step.");
    } catch (error) {
      showToast("error", "Lookup Failed", "Something went wrong. Please try again.");
    } finally {
      setLoading(false);
      setLoadingText("");
    }
  };

  const handleGoogleAuth = async () => {
    try {
      setLoading(true);
      setLoadingText("Waiting for Google sign-in session...");

      const result = await signInWithPopup(auth, googleProvider);
      const token = await result.user.getIdToken();

      const { status, data } = await loginToBackendWithToken(
        token,
        result.user.photoURL || null
      );

      if (data.success) {
        completeLogin(data.user);
        return;
      }

      if (status === 404) {
        setPendingAuth({
          provider: "google",
          token,
          name: result.user.displayName || "User",
          photo_url: result.user.photoURL || null,
        });
        setOnboardingTab(0);
        setOnboardingData({ language: "english" });
        setOnboardingOpen(true);
        return;
      }

      showToast(
        "error",
        "Sign-in Failed",
        data.message || "Unable to continue with Google."
      );
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

  const handlePasswordLogin = async () => {
    if (!emailFlow.password) {
      showToast("warning", "Missing Password", "Please enter your password.");
      return;
    }

    try {
      setLoading(true);
      setLoadingText("Signing you in...");

      const userCredential = await signInWithEmailAndPassword(
        auth,
        emailFlow.email,
        emailFlow.password
      );

      const firebaseUser = userCredential.user;
      await firebaseUser.reload();

      if (!firebaseUser.emailVerified) {
        setPendingAuth({
          provider: "email",
          email: emailFlow.email,
          password: emailFlow.password,
        });
        setAuthStep("verify_email");
        showToast(
          "warning",
          "Verify Your Email",
          "Please verify your email before continuing."
        );
        return;
      }

      const token = await firebaseUser.getIdToken(true);
      const { status, data } = await loginToBackendWithToken(token);

      if (data.success) {
        completeLogin(data.user);
        return;
      }

      if (status === 404) {
        setPendingAuth({
          provider: "email",
          token,
          name: buildNameFromEmail(emailFlow.email),
          photo_url: null,
        });
        setOnboardingTab(0);
        setOnboardingData({ language: "english" });
        setOnboardingOpen(true);
        return;
      }

      if (data.requires_verification) {
        setPendingAuth({
          provider: "email",
          email: emailFlow.email,
          password: emailFlow.password,
        });
        setAuthStep("verify_email");
        return;
      }

      showToast("error", "Login Failed", data.message || "Unable to sign in.");
    } catch (error) {
      showToast("error", "Login Failed", getFirebaseErrorMessage(error));
    } finally {
      setLoading(false);
      setLoadingText("");
    }
  };

  const handleForgotPassword = async () => {
    const email = emailFlow.email?.trim().toLowerCase();

    if (!email) {
      showToast("warning", "Missing Email", "Please enter your email first.");
      return;
    }

    if (lookupUserRole === "admin") {
      showToast(
        "info",
        "Admin Password Assistance",
        lookupContactMessage || "Please contact system administrator for admin account assistance."
      );
      return;
    }

    try {
      setLoading(true);
      setLoadingText("Sending password reset email...");

      await sendPasswordResetEmail(auth, email, getActionCodeSettings());

      showToast(
        "success",
        "Reset Email Sent",
        "Please check your inbox for the password reset email."
      );
    } catch (error) {
      showToast("error", "Reset Failed", getFirebaseErrorMessage(error));
    } finally {
      setLoading(false);
      setLoadingText("");
    }
  };

  const handlePasswordSignup = async () => {
    if (!emailFlow.password || !emailFlow.confirmPassword) {
      showToast("warning", "Missing Information", "Please fill in all password fields.");
      return;
    }

    if (emailFlow.password !== emailFlow.confirmPassword) {
      showToast("error", "Password Mismatch", "Passwords do not match.");
      return;
    }

    if (!isStrongPassword(emailFlow.password)) {
      showToast(
        "error",
        "Weak Password",
        "Password must be at least 8 characters and include uppercase, lowercase, and a number."
      );
      return;
    }

    try {
      setLoading(true);
      setLoadingText("Creating your account...");

      const userCredential = await createUserWithEmailAndPassword(
        auth,
        emailFlow.email,
        emailFlow.password
      );

      console.log("Sending verification to:", userCredential.user.email);

      const actionCodeSettings = getActionCodeSettings();
      await sendEmailVerification(userCredential.user, actionCodeSettings);

      console.log("Verification email request sent successfully");

      setPendingAuth({
        provider: "email",
        email: emailFlow.email,
        password: emailFlow.password,
      });

      setAuthStep("verify_email");

      showToast(
        "success",
        "Verification Email Sent",
        "Please check your inbox and verify your email."
      );
    } catch (error) {
      showToast("error", "Signup Failed", getFirebaseErrorMessage(error));
    } finally {
      setLoading(false);
      setLoadingText("");
    }
  };

  const handleCheckEmailVerified = async () => {
    try {
      setLoading(true);
      setLoadingText("Checking verification status...");

      let userCredential = null;

      if (!auth.currentUser && pendingAuth?.email && pendingAuth?.password) {
        userCredential = await signInWithEmailAndPassword(
          auth,
          pendingAuth.email,
          pendingAuth.password
        );
      }

      const firebaseUser = auth.currentUser || userCredential?.user;

      if (!firebaseUser) {
        showToast("error", "Session Missing", "Please enter your email again.");
        await resetToIdentifierStep();
        return;
      }

      await firebaseUser.reload();

      if (!firebaseUser.emailVerified) {
        showToast(
          "warning",
          "Not Verified Yet",
          "Your email is still not verified. Please check your inbox."
        );
        return;
      }

      const token = await firebaseUser.getIdToken(true);
      const { status, data } = await loginToBackendWithToken(token);

      if (data.success) {
        completeLogin(data.user);
        return;
      }

      if (status === 404) {
        setPendingAuth({
          provider: "email",
          token,
          name: buildNameFromEmail(firebaseUser.email || emailFlow.email),
          photo_url: null,
        });
        setOnboardingTab(0);
        setOnboardingData({ language: "english" });
        setOnboardingOpen(true);
        return;
      }

      showToast("error", "Unable to Continue", data.message || "Please try again.");
    } catch (error) {
      showToast("error", "Verification Check Failed", getFirebaseErrorMessage(error));
    } finally {
      setLoading(false);
      setLoadingText("");
    }
  };

  const handleResendVerificationEmail = async () => {
    try {
      setLoading(true);
      setLoadingText("Resending verification email...");

      let userCredential = null;

      if (!auth.currentUser && pendingAuth?.email && pendingAuth?.password) {
        userCredential = await signInWithEmailAndPassword(
          auth,
          pendingAuth.email,
          pendingAuth.password
        );
      }

      const firebaseUser = auth.currentUser || userCredential?.user;

      if (!firebaseUser) {
        showToast("error", "Session Missing", "Please enter your email again.");
        await resetToIdentifierStep();
        return;
      }

      await sendEmailVerification(firebaseUser, getActionCodeSettings());

      showToast(
        "success",
        "Email Sent",
        "A new verification email has been sent."
      );
    } catch (error) {
      showToast("error", "Resend Failed", getFirebaseErrorMessage(error));
    } finally {
      setLoading(false);
      setLoadingText("");
    }
  };

  const handleCloseOnboarding = async () => {
    setOnboardingOpen(false);
    setPendingAuth(null);
    setOnboardingTab(0);
    setOnboardingData({ language: "english" });

    try {
      await signOut(auth);
    } catch (error) {
      console.error("Failed to sign out after closing onboarding:", error);
    }
  };

  const handleCompleteOnboarding = async () => {
    if (!pendingAuth?.token) {
      showToast("error", "Missing Session", "Please sign in again.");
      return;
    }

    try {
      setLoading(true);
      setLoadingText("Creating your account...");

      const registerPayload = {
        token: pendingAuth.token,
        name: pendingAuth.name,
        role,
        language: onboardingData.language,
        photo_url: pendingAuth.photo_url,
      };

      const registerRes = await fetch(
        `${process.env.REACT_APP_API_BASE_URL}/api/auth/register`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(registerPayload),
        }
      );

      const registerData = await registerRes.json();

      if (!registerData.success) {
        showToast(
          "error",
          "Registration Failed",
          registerData.message || "Something went wrong."
        );
        return;
      }

      setLoadingText("Signing you in...");

      const { data: loginData } = await loginToBackendWithToken(
        pendingAuth.token,
        pendingAuth.photo_url || null
      );

      if (loginData.success) {
        setOnboardingOpen(false);
        setPendingAuth(null);
        completeLogin(loginData.user);
      } else {
        showToast(
          "error",
          "Login Failed",
          loginData.message || "Account created, but login failed."
        );
      }
    } catch (error) {
      showToast("error", "Registration Failed", getFirebaseErrorMessage(error));
    } finally {
      setLoading(false);
      setLoadingText("");
    }
  };

  const passwordRequirementPassed = isStrongPassword(emailFlow.password);
  const confirmPasswordMatched =
    emailFlow.confirmPassword.length > 0 &&
    emailFlow.password === emailFlow.confirmPassword;

  const renderIdentifierStep = () => (
    <>
      <Box sx={{ textAlign: "center", mb: 3 }}>
        <Typography
          variant="h4"
          fontWeight="bold"
          sx={{
            color: "#111827",
            mb: 1,
            fontSize: { xs: "1.55rem", sm: "1.85rem" },
          }}
        >
          Welcome to EasyLearn
        </Typography>
        <Typography sx={{ color: "#6B7280", fontSize: "15px" }}>
          Log in or sign up to unlock your math potential with EasyLearn
        </Typography>
      </Box>

      <TextField
        fullWidth
        label="Email Address"
        name="email"
        type="email"
        value={formData.email}
        onChange={handleIdentifierEmailChange}
        sx={{ mb: 3 }}
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <MailOutlineIcon sx={{ color: "#9CA3AF" }} />
            </InputAdornment>
          ),
        }}
      />

      <Button
        variant="contained"
        fullWidth
        onClick={handleEmailLookup}
        disabled={loading}
        sx={{
          py: 1.6,
          borderRadius: "16px",
          textTransform: "none",
          fontWeight: 700,
          fontSize: "15px",
          backgroundColor: "#2563EB",
          boxShadow: "0 12px 28px rgba(37, 99, 235, 0.18)",
          mb: 3,
          "&:hover": {
            backgroundColor: "#1D4ED8",
            boxShadow: "0 16px 32px rgba(37, 99, 235, 0.24)",
            transform: "translateY(-1px)",
          },
        }}
      >
        Continue
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
        onClick={handleGoogleAuth}
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
    </>
  );

  const renderPasswordLoginStep = () => (
    <>
      <Box sx={{ textAlign: "center", mb: 3 }}>
        <Typography
          variant="h4"
          fontWeight="bold"
          sx={{
            color: "#111827",
            mb: 1,
            fontSize: { xs: "1.55rem", sm: "1.85rem" },
          }}
        >
          Enter Your Password
        </Typography>
        <Typography sx={{ color: "#6B7280", fontSize: "15px" }}>
          Continue with your email account
        </Typography>
      </Box>

      <TextField
        fullWidth
        label="Email Address"
        value={emailFlow.email}
        disabled
        sx={{ mb: 2 }}
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <MailOutlineIcon sx={{ color: "#9CA3AF" }} />
            </InputAdornment>
          ),
        }}
      />

      <Button
        onClick={resetToIdentifierStep}
        sx={{
          p: 0,
          mb: 2.5,
          textTransform: "none",
          color: "#4F46E5",
          fontWeight: 700,
          minWidth: "auto",
          alignSelf: "flex-start",
        }}
      >
        Use different email
      </Button>

      <TextField
        fullWidth
        label="Password"
        type={showPassword ? "text" : "password"}
        value={emailFlow.password}
        onChange={(e) => handleEmailFlowChange("password", e.target.value)}
        sx={{ mb: 2 }}
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
        onClick={handleForgotPassword}
        sx={{
          p: 0,
          mb: 2.5,
          textTransform: "none",
          color: "#4F46E5",
          fontWeight: 700,
          minWidth: "auto",
          alignSelf: "flex-start",
        }}
      >
        Forgot password?
      </Button>
      <Button
        variant="contained"
        fullWidth
        onClick={handlePasswordLogin}
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
        Continue
      </Button>
    </>
  );

  const renderPasswordSignupStep = () => (
    <>
      <Box sx={{ textAlign: "center", mb: 3 }}>
        <Typography
          variant="h4"
          fontWeight="bold"
          sx={{
            color: "#111827",
            mb: 1,
            fontSize: { xs: "1.55rem", sm: "1.85rem" },
          }}
        >
          Create Your Password
        </Typography>
        <Typography sx={{ color: "#6B7280", fontSize: "15px" }}>
          Set a strong password for your new email account
        </Typography>
      </Box>

      <TextField
        fullWidth
        label="Email Address"
        value={emailFlow.email}
        disabled
        sx={{ mb: 2 }}
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <MailOutlineIcon sx={{ color: "#9CA3AF" }} />
            </InputAdornment>
          ),
        }}
      />

      <Button
        onClick={resetToIdentifierStep}
        sx={{
          p: 0,
          mb: 2.5,
          textTransform: "none",
          color: "#4F46E5",
          fontWeight: 700,
          minWidth: "auto",
          alignSelf: "flex-start",
        }}
      >
        Use different email
      </Button>

      <TextField
        fullWidth
        label="Password"
        type={showPassword ? "text" : "password"}
        value={emailFlow.password}
        onChange={(e) => handleEmailFlowChange("password", e.target.value)}
        sx={{ mb: 2 }}
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

      <TextField
        fullWidth
        label="Confirm Password"
        type={showConfirmPassword ? "text" : "password"}
        value={emailFlow.confirmPassword}
        onChange={(e) => handleEmailFlowChange("confirmPassword", e.target.value)}
        sx={{ mb: 2 }}
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <LockOutlinedIcon sx={{ color: "#9CA3AF" }} />
            </InputAdornment>
          ),
          endAdornment: (
            <InputAdornment position="end">
              <IconButton
                onClick={() => setShowConfirmPassword((prev) => !prev)}
                edge="end"
                sx={{ color: "#9CA3AF" }}
              >
                {showConfirmPassword ? <VisibilityOffIcon /> : <VisibilityIcon />}
              </IconButton>
            </InputAdornment>
          ),
        }}
      />

      <Typography
        sx={{
          color: passwordRequirementPassed ? "#1bbb56" : "#111827",
          fontSize: "13px",
          mb: 1,
          fontWeight: passwordRequirementPassed ? 700 : 500,
          transition: "all 0.2s ease",
        }}
      >
        ✓ At least 8 characters, including uppercase, lowercase, and a number.
      </Typography>

      <Typography
        sx={{
          color: confirmPasswordMatched ? "#1bbb56" : "#111827",
          fontSize: "13px",
          mb: 3,
          fontWeight: confirmPasswordMatched ? 700 : 500,
          transition: "all 0.2s ease",
        }}
      >
        ✓ Confirm password matches password.
      </Typography>

      <Button
        variant="contained"
        fullWidth
        onClick={handlePasswordSignup}
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
        Continue
      </Button>
    </>
  );

  const renderVerifyEmailStep = () => (
    <>
      <Box sx={{ textAlign: "center", mb: 3 }}>
        <Typography
          variant="h4"
          fontWeight="bold"
          sx={{
            color: "#111827",
            mb: 1,
            fontSize: { xs: "1.55rem", sm: "1.85rem" },
          }}
        >
          Check Your Inbox
        </Typography>
        <Typography sx={{ color: "#6B7280", fontSize: "15px" }}>
          We sent a verification email to {pendingAuth?.email || emailFlow.email}.
        </Typography>
      </Box>

      <Button
        variant="contained"
        fullWidth
        onClick={handleCheckEmailVerified}
        disabled={loading}
        sx={{
          py: 1.6,
          borderRadius: "16px",
          textTransform: "none",
          fontWeight: 700,
          fontSize: "15px",
          mb: 2,
          backgroundColor: "#2563EB",
          boxShadow: "0 12px 28px rgba(37, 99, 235, 0.18)",
          "&:hover": {
            backgroundColor: "#1D4ED8",
            boxShadow: "0 16px 32px rgba(37, 99, 235, 0.24)",
            transform: "translateY(-1px)",
          },
        }}
      >
        I’ve Verified My Email
      </Button>

      <Button
        variant="text"
        fullWidth
        onClick={handleResendVerificationEmail}
        disabled={loading}
        sx={{
          py: 1.2,
          textTransform: "none",
          fontWeight: 700,
          color: "#4F46E5",
          mb: 1,
        }}
      >
        Resend Email
      </Button>

      <Button
        variant="text"
        fullWidth
        onClick={resetToIdentifierStep}
        disabled={loading}
        sx={{
          py: 1.2,
          textTransform: "none",
          fontWeight: 700,
          color: "#6B7280",
        }}
      >
        Use Different Email
      </Button>
    </>
  );

  const renderGoogleOnlyStep = () => (
    <>
      <Box sx={{ textAlign: "center", mb: 3 }}>
        <Typography
          variant="h4"
          fontWeight="bold"
          sx={{
            color: "#111827",
            mb: 1,
            fontSize: { xs: "1.55rem", sm: "1.85rem" },
          }}
        >
          Continue with Google
        </Typography>
        <Typography sx={{ color: "#6B7280", fontSize: "15px" }}>
          This email is already linked to a Google sign-in account.
        </Typography>
      </Box>

      <TextField
        fullWidth
        label="Email Address"
        value={emailFlow.email}
        disabled
        sx={{ mb: 3 }}
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <MailOutlineIcon sx={{ color: "#9CA3AF" }} />
            </InputAdornment>
          ),
        }}
      />

      <Button
        variant="outlined"
        fullWidth
        onClick={handleGoogleAuth}
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
          mb: 2,
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
        Continue with Google
      </Button>

      <Button
        variant="text"
        fullWidth
        onClick={resetToIdentifierStep}
        disabled={loading}
        sx={{
          py: 1.2,
          textTransform: "none",
          fontWeight: 700,
          color: "#6B7280",
        }}
      >
        Use Different Email
      </Button>
    </>
  );

  const renderStepContent = () => {
    switch (authStep) {
      case "password_login":
        return renderPasswordLoginStep();
      case "password_signup":
        return renderPasswordSignupStep();
      case "verify_email":
        return renderVerifyEmailStep();
      case "google_only":
        return renderGoogleOnlyStep();
      case "identifier":
      default:
        return renderIdentifierStep();
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

          {renderStepContent()}
        </Paper>
      </Container>

      <Dialog
        open={onboardingOpen}
        onClose={handleCloseOnboarding}
        maxWidth="sm"
        fullWidth
        PaperProps={{
          sx: {
            borderRadius: "28px",
            p: { xs: 1, sm: 2 },
            boxShadow: "0 20px 60px rgba(15, 23, 42, 0.12)",
          },
        }}
      >
        <DialogContent sx={{ pt: 2 }}>
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
              Complete your account setup before entering EasyLearn
            </Typography>
          </Box>

          <Tabs
            value={onboardingTab}
            onChange={(_, newValue) => setOnboardingTab(newValue)}
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
            value={onboardingData.language}
            onChange={handleOnboardingLanguageChange}
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

          <Box sx={{ display: "flex", gap: 2 }}>
            <Button
              variant="outlined"
              fullWidth
              onClick={handleCloseOnboarding}
              disabled={loading}
              sx={{
                py: 1.4,
                borderRadius: "16px",
                textTransform: "none",
                fontWeight: 700,
              }}
            >
              Cancel
            </Button>

            <Button
              variant="contained"
              fullWidth
              onClick={handleCompleteOnboarding}
              disabled={loading}
              sx={{
                py: 1.4,
                borderRadius: "16px",
                textTransform: "none",
                fontWeight: 700,
                backgroundColor: "#2563EB",
              }}
            >
              Save and Continue
            </Button>
          </Box>
        </DialogContent>
      </Dialog>

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

export default AuthPage;