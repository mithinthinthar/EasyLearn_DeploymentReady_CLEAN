import React from "react";
import {
  Snackbar,
  Paper,
  Box,
  Typography,
  IconButton,
} from "@mui/material";
import CheckCircleRoundedIcon from "@mui/icons-material/CheckCircleRounded";
import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";
import WarningAmberRoundedIcon from "@mui/icons-material/WarningAmberRounded";
import HighlightOffRoundedIcon from "@mui/icons-material/HighlightOffRounded";
import CloseIcon from "@mui/icons-material/Close";

const toastStyles = {
  success: {
    bg: "#DDF3D2",
    iconColor: "#2FB65D",
  },
  info: {
    bg: "#D7EEF9",
    iconColor: "#1D7DF2",
  },
  warning: {
    bg: "#F8E7C9",
    iconColor: "#F59E0B",
  },
  error: {
    bg: "#F8D7D9",
    iconColor: "#EF4444",
  },
};

const iconMap = {
  success: CheckCircleRoundedIcon,
  info: InfoOutlinedIcon,
  warning: WarningAmberRoundedIcon,
  error: HighlightOffRoundedIcon,
};

const CustomToast = ({ open, onClose, type = "info", title, message }) => {
  const Icon = iconMap[type];
  const styles = toastStyles[type];

  return (
    <Snackbar
      open={open}
      autoHideDuration={3500}
      onClose={onClose}
      anchorOrigin={{ vertical: "top", horizontal: "center" }}
    >
      <Paper
        elevation={0}
        sx={{
          minWidth: 340,
          maxWidth: 480,
          px: 2,
          py: 1.5,
          borderRadius: "16px",
          backgroundColor: styles.bg,
          display: "flex",
          alignItems: "flex-start",
          gap: 1.5,
          boxShadow: "0 10px 30px rgba(15,23,42,0.10)",
          border: "1px solid rgba(255,255,255,0.6)",
        }}
      >
        <Icon sx={{ color: styles.iconColor, mt: "2px" }} />

        <Box sx={{ flex: 1 }}>
          <Typography sx={{ fontWeight: 700, color: "#1F2937", mb: 0.3 }}>
            {title}
          </Typography>
          <Typography sx={{ fontSize: "14px", color: "#4B5563" }}>
            {message}
          </Typography>
        </Box>

        <IconButton size="small" onClick={onClose}>
          <CloseIcon sx={{ fontSize: 18, color: "#374151" }} />
        </IconButton>
      </Paper>
    </Snackbar>
  );
};

export default CustomToast;