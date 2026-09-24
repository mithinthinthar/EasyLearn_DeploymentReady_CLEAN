import React from "react";
import { Box } from "@mui/material";
import { styled } from "@mui/material/styles";
import Header from "../components/Header";
import Footer from "../components/Footer";
import FloatingChatbot from "../components/FloatingChatbot";

const LayoutWrapper = styled(Box)({
  display: "flex",
  flexDirection: "column",
  minHeight: "100vh",
});

const ContentArea = styled(Box)(({ theme }) => ({
  flex: 1,
  display: "flex",
  justifyContent: "center",
  padding: theme.spacing(4, 2),
  [theme.breakpoints.up("md")]: {
    padding: theme.spacing(6, 4),
  },
}));

const MainLayout = ({
  children,
  showTabs = true,
  navItems = [],
  homePath = "/studentDashboard",
  showFloatingChatbot = true,
}) => {
  const localMode = process.env.REACT_APP_LOCAL_MODE === "true";

  return (
    <LayoutWrapper>
      <Header
        showTabs={showTabs}
        navItems={navItems}
        homePath={homePath}
      />

      <ContentArea>
        <Box sx={{ width: "100%", maxWidth: "1000px" }}>
          {localMode && (
            <Box
              sx={{
                mb: 3,
                p: 1.5,
                borderRadius: 2,
                bgcolor: "#fff7ed",
                color: "#9a3412",
                textAlign: "center",
                fontWeight: 700,
              }}
            >
              Local guest mode: Kertas 1 and the MySQL question bank are available. AI and cloud features are disabled.
            </Box>
          )}
          {children}
        </Box>
      </ContentArea>

      <Footer />

      {showFloatingChatbot && !localMode && <FloatingChatbot />}
    </LayoutWrapper>
  );
};

export default MainLayout;
