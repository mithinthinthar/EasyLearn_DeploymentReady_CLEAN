import React from "react";
import { Box, Typography } from "@mui/material";
import { styled } from "@mui/material/styles";
import { useLocation } from "react-router-dom";

const FooterContainer = styled(Box, {
  shouldForwardProp: (prop) => prop !== "isChatbotPage",
})(({ isChatbotPage }) => ({
  backgroundColor: "#d7dffa",
  padding: "8px",
  textAlign: "center",
  borderTop: "1px solid #ffffff",
  marginTop: isChatbotPage ? 0 : "auto",

  ...(isChatbotPage && {
    position: "fixed",
    left: 0,
    right: 0,
    bottom: 0,
    zIndex: 1200,
  }),
}));

const Footer = () => {
  const location = useLocation();
  const isChatbotPage = location.pathname === "/chatbot";

  return (
    <FooterContainer isChatbotPage={isChatbotPage}>
      <Typography variant="body2" color="textSecondary">
        © Copyright MATHSY. All right reserved.
      </Typography>
    </FooterContainer>
  );
};

export default Footer;