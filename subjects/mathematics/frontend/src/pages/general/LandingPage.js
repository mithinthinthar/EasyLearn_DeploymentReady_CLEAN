import React from "react";
import {
  Box,
  Container,
  Typography,
  Button,
  Grid,
  Paper,
} from "@mui/material";
import { useNavigate } from "react-router-dom";
import logo from "../../assets/landingpage/logo.png";
import landingPageGIF from "../../assets/landingpage/landingpagegif.gif";
import practiceIcon from "../../assets/landingpage/practiceIcon.png";
import dashboardIcon from "../../assets/landingpage/dashboardIcon.png";
import chatbotIcon from "../../assets/landingpage/chatbotIconLanding.png";

const LandingPage = () => {
  const navigate = useNavigate();

  return (
    <Box sx={{ backgroundColor: "#ffffff", py: 4 }}>

      {/* HERO WRAPPER */}
      <Container>
        <Box
          sx={{
            backgroundColor: "#EEF2FF",
            borderRadius: "30px",
            p: { xs: 3, md: 6 },
          }}
        >

          {/* NAVBAR */}
          <Box
            sx={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              mb: 6,
            }}
          >
            <Box
              component="img"
              src={logo}
              alt="EasyLearn Logo"
              sx= {{height: 40 }}
            />
        </Box>

          {/* HERO CONTENT */}
          <Grid container spacing={10} alignItems="center">

            {/* TEXT */}
            <Grid item xs={12} md={6}>
              <Typography variant="h3" fontWeight="bold" mb={2}>
                Learn SPM Mathematics
                <br /> in a {" "}  <Box component="span" sx={{ color: "#4F46E5" }}>Smart</Box>{" "} Way.
              </Typography>

              <Typography mb={3} sx={{ color: "#8e939c"}}>
                Learn at your own pace with bilingual support questions, SPM-specific AI chatbot <br />explanations, personalized recommendation and performance tracking
              </Typography>

              <Button
                variant="contained"
                sx={{ backgroundColor: "#ffa526",
                      "&:hover": {backgroundColor: "#e97e03",},
                      borderRadius: "25px", 
                      px: 4 }}
                onClick={() => navigate("/register")}
              >
                Get started
              </Button>
            </Grid>


            {/* GIF PLACEHOLDER */}
            <Grid item xs={12} md={6}>
                <Box
                  component="img"
                  src={landingPageGIF}  
                  alt="Math animation"
                  sx={{
                    width: "100%",
                    height: 350,
                    objectFit: "contain",
                    animation: "float 3s ease-in-out infinite",

                    "@keyframes float": {
                      "0%": { transform: "translateY(0px)" },
                      "50%": { transform: "translateY(-15px)" },
                      "100%": { transform: "translateY(0px)" },
                    },
                  }}
                />
            </Grid>
          </Grid>
        </Box>
      </Container>

      {/* SERVICES */}
      <Container sx={{ mt: 10 }}>
        <Typography align="center" color="gray">
          SERVICES TO YOU
        </Typography>

        <Typography
          variant="h4"
          align="center"
          fontWeight="bold"
          mb={6}
        >
          What EasyLearn Provides
        </Typography>

        <Grid container spacing={4} justifyContent="center">
          {[
            {
              title: "Smart Practice",
              desc: "Practice SPM questions tailored to your level and improve step-by-step.",
              img: practiceIcon,
            },
            {
              title: "Performance Dashboard",
              desc: "Track your progress, identify weak topics, and study in your preferred way.",
              img: dashboardIcon,
            },
            {
              title: "AI Chatbot Tutor",
              desc: "Get instant explanations and guidance anytime using SPM-specific chatbot.",
              img: chatbotIcon,
            },
          ].map((item, index) => (
            <Grid item xs={12} sm={6} md={4} key={index}>
              <Paper
                sx={{
                  p: 2,
                  borderRadius: "20px",
                  textAlign: "center",
                  height: "100%", 
                  minHeight: 200,
                  display: "flex",
                  flexDirection: "column",
                  justifyContent: "center",

                  transition: "all 0.3s ease",

                  "&:hover": {
                    transform: "translateY(-5px)", 
                    boxShadow: 3,
                  },
                }}
              >
                {/* IMAGE */}
                <Box
                  component="img"
                  src={item.img}
                  alt={item.title}
                  sx={{
                    height: 120,
                    mb: 2,
                    mx: "auto",
                  }}
                />

                <Typography fontWeight="bold">{item.title}</Typography>

                <Typography 
                  color="#6B7280" 
                  mt={1}
                  sx={{
                    maxWidth: "300px",
                    mx: "auto",
                    lineHeight: 1.6,
                  }}
                >
                  {item.desc}
                </Typography>
              </Paper>
            </Grid>
          ))}
        </Grid>
      </Container>
      <br />
      <br />
    </Box>
  );
};

export default LandingPage;