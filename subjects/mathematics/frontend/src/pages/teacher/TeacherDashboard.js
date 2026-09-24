import React from "react";
import { Box, Button, Card, CardContent, Chip, Typography } from "@mui/material";

export default function TeacherDashboard() {
  return <Box sx={{ py: 3 }}>
    <Chip label="TEACHER VIEW" color="primary" size="small" sx={{ fontWeight: 800, mb: 2 }} />
    <Typography variant="h3" sx={{ fontWeight: 700, mb: 1 }}>Mathematics performance</Typography>
    <Typography color="text.secondary" sx={{ mb: 4 }}>Student learning tools are read-only for teacher accounts.</Typography>
    <Card variant="outlined" sx={{ borderRadius: 4 }}><CardContent sx={{ p: 4, textAlign: "center" }}>
      <Typography variant="h5" sx={{ fontWeight: 700, mb: 1 }}>Open the unified EasyLearn dashboard</Typography>
      <Typography color="text.secondary" sx={{ mb: 3 }}>Review the class overview, compare all three subjects, and open individual student dashboards from the main portal.</Typography>
      <Button href={process.env.REACT_APP_PORTAL_URL || (["localhost", "127.0.0.1"].includes(window.location.hostname) ? "http://localhost:4000" : "/")} variant="contained" size="large">Open EasyLearn Dashboard</Button>
    </CardContent></Card>
  </Box>;
}
