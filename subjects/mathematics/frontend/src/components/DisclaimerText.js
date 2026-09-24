import React from "react";
import { Box, Typography } from "@mui/material";
import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";
import { useLanguage } from "../context/LanguageContext";

const DisclaimerText = ({ sx = {} }) => {
  const { language } = useLanguage();

  return (
    <Box
      sx={{
        mt: 2.5,
        px: 1.6,
        py: 0.9,
        borderRadius: "999px",
        bgcolor: "#F8FAFC",
        border: "1px solid #E5E7EB",
        display: "inline-flex",
        width: "fit-content",
        maxWidth: "100%",
        alignItems: "center",
        gap: 0.8,
        color: "#6B7280",
        ...sx,
      }}
    >
      <InfoOutlinedIcon sx={{ fontSize: 16, color: "#9CA3AF", flexShrink: 0 }} />

      <Typography
        variant="caption"
        sx={{
          fontSize: "12px",
          lineHeight: 1.4,
          color: "#6B7280",
          fontWeight: 500,
          whiteSpace: "normal",
        }}
      >
        {language === "bm"
          ? "EasyLearn ialah AI dan mungkin membuat kesilapan."
          : "EasyLearn is AI and can make mistakes."}
      </Typography>
    </Box>
  );
};

export default DisclaimerText;