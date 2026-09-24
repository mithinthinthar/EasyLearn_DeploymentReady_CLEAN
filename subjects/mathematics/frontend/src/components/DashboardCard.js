import React from "react";
import { Paper, Typography, Box } from "@mui/material";

const DashboardCard = ({ title, color, icon, children }) => {
  return (
    <Paper
      elevation={3}
        sx={{
        p: 3,
        borderRadius: "20px",
        position: "relative",
        overflow: "hidden",
        background: "rgba(255,255,255,0.8)",
        backdropFilter: "blur(10px)",
        boxShadow: "0 8px 30px rgba(0,0,0,0.08)",
        transition: "0.3s",

        "&:hover": {
            transform: "translateY(-5px)",
            boxShadow: "0 12px 40px rgba(0,0,0,0.12)",
        },
        }}
    >
      {/* Bottom Color Line */}
      <Box
        sx={{
          position: "absolute",
          bottom: 0,
          left: 0,
          width: "100%",
          height: "6px",
          background: color,
        }}
      />
    <Box
    sx={{
        width: 40,
        height: 3,
        background: color,
        borderRadius: "10px",
        mb: 2,
    }}
    />
    <Box
    sx={{
        display: "flex",
        alignItems: "center",
        gap: 1.5,
        mb: 2,
    }}
    >
    {icon}

    <Typography
        variant="h6"
        fontWeight="bold"
        sx={{
        color: color,
        letterSpacing: "0.5px",
        }}
    >
        {title}
    </Typography>
    </Box>
      {children}
    </Paper>
  );
};

export default DashboardCard;