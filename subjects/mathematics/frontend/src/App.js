import React, { useEffect, useState } from "react";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import CssBaseline from "@mui/material/CssBaseline";
import "katex/dist/katex.min.css";

import "@fontsource/lexend/500.css";
import "@fontsource/lexend/600.css";
import "@fontsource/lexend/700.css";

import "@fontsource/quicksand/400.css";
import "@fontsource/quicksand/500.css";
import "@fontsource/quicksand/600.css";
import "@fontsource/quicksand/700.css";

import AppRoutes from "./routes/AppRoutes";
import { ensureLocalGuestUser } from "./utils/localGuest";
import {
  getMathematicsHome,
  signInMathematicsFromPortal,
} from "./utils/sharedPortalAuth";
import { installMathematicsActivityTracker } from "./utils/platformActivity";

ensureLocalGuestUser();
installMathematicsActivityTracker();

const IS_LOCAL = ["localhost", "127.0.0.1"].includes(window.location.hostname);
const PORTAL_URL = process.env.REACT_APP_PORTAL_URL || (IS_LOCAL ? "http://localhost:4000" : "/");

function currentRoute() {
  return window.location.hash.replace(/^#/, "") || "/";
}

function replaceRoute(path) {
  window.location.replace(`${window.location.pathname}${window.location.search}#${path}`);
}

const headingStyle = {
  fontFamily: '"Lexend", sans-serif',
};

const headingVariants = [
  "h1",
  "h2",
  "h3",
  "h4",
  "h5",
  "h6",
].reduce((styles, variant) => {
  styles[variant] = headingStyle;
  return styles;
}, {});

const theme = createTheme({
  typography: {
    fontFamily:
      '"Quicksand", "Roboto", "Helvetica", "Arial", sans-serif',
    ...headingVariants,
  },

  palette: {
    primary: {
      main: "#3855c0",
    },

    background: {
      default: "#f9fbfd",
    },
  },
});

function LoadingAccount() {
  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "#f9fbfd",
        color: "#24324a",
        fontFamily: '"Quicksand", sans-serif',
        textAlign: "center",
        padding: "24px",
      }}
    >
      <div>
        <h2 style={{ marginBottom: "8px" }}>
          Opening Mathematics
        </h2>

        <p style={{ margin: 0 }}>
          Connecting to your EasyLearn account...
        </p>
      </div>
    </div>
  );
}

function App() {
  const [authenticationChecked, setAuthenticationChecked] =
    useState(false);

  useEffect(() => {
    let active = true;

    async function connectAccount() {
      try {
        const result = await signInMathematicsFromPortal();

        if (!active) {
          return;
        }

        if (result.status === "signed-in") {
          const destination = getMathematicsHome(
            result.user.role,
          );

          if (currentRoute() !== destination) {
            replaceRoute(destination);
            return;
          }
        }

        if (result.status === "no-portal-session") {
          window.location.replace(PORTAL_URL);
          return;
        }

        if (
          result.status === "math-account-not-found" &&
          currentRoute() !== "/auth"
        ) {
          replaceRoute("/auth");
          return;
        }

        setAuthenticationChecked(true);
      } catch (error) {
        console.error(
          "EasyLearn shared Mathematics login failed:",
          error,
        );

        window.location.replace(PORTAL_URL);
      }
    }

    connectAccount();

    return () => {
      active = false;
    };
  }, []);

  if (!authenticationChecked) {
    return <LoadingAccount />;
  }

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AppRoutes />
    </ThemeProvider>
  );
}

export default App;
