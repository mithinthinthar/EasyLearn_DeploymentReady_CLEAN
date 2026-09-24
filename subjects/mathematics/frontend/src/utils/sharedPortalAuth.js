import {
  signInWithCustomToken,
  signOut,
} from "firebase/auth";

import { auth } from "../firebase";

const IS_LOCAL = ["localhost", "127.0.0.1"].includes(window.location.hostname);
const SHARED_AUTH_URL = process.env.REACT_APP_SHARED_AUTH_URL || (IS_LOCAL ? "http://localhost:4500" : "/platform-api");

const MATHEMATICS_API_URL =
  process.env.REACT_APP_API_BASE_URL || "http://127.0.0.1:5001";

let signInPromise = null;

async function readResponse(response) {
  try {
    return await response.json();
  } catch {
    return {};
  }
}

async function performPortalSignIn() {
  // Local guest mode does not initialize Firebase.
  if (!auth) {
    return {
      status: "local-mode",
    };
  }

  const sharedResponse = await fetch(
    `${SHARED_AUTH_URL}/auth/custom-token`,
    {
      method: "POST",
      credentials: "include",
    },
  );

  if (sharedResponse.status === 401) {
    localStorage.removeItem("user");

    try {
      await signOut(auth);
    } catch (error) {
      console.warn("Firebase sign-out warning:", error);
    }

    return {
      status: "no-portal-session",
    };
  }

  const sharedData = await readResponse(sharedResponse);

  if (!sharedResponse.ok || !sharedData.custom_token) {
    throw new Error(
      sharedData.detail ||
        "The EasyLearn shared login service could not create a Mathematics token.",
    );
  }

  const firebaseCredential = await signInWithCustomToken(
    auth,
    sharedData.custom_token,
  );

  const firebaseUser = firebaseCredential.user;
  const idToken = await firebaseUser.getIdToken(true);

  const mathResponse = await fetch(
    `${MATHEMATICS_API_URL}/api/auth/portal-login`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        token: idToken,
        photo_url: firebaseUser.photoURL || null,
      }),
    },
  );

  const mathData = await readResponse(mathResponse);

  if (mathResponse.status === 404) {
    return {
      status: "math-account-not-found",
    };
  }

  if (!mathResponse.ok || !mathData.success || !mathData.user) {
    throw new Error(
      mathData.message ||
        "The Mathematics backend could not complete the login.",
    );
  }

  localStorage.setItem(
    "user",
    JSON.stringify(mathData.user),
  );

  return {
    status: "signed-in",
    user: mathData.user,
  };
}

export function signInMathematicsFromPortal() {
  if (!signInPromise) {
    signInPromise = performPortalSignIn().catch((error) => {
      signInPromise = null;
      throw error;
    });
  }

  return signInPromise;
}

export function getMathematicsHome(role) {
  if (role === "student") {
    return "/studentDashboard";
  }

  if (role === "parent") {
    return "/parentDashboard";
  }

  if (role === "teacher") {
    return "/teacherDashboard";
  }

  if (role === "admin") {
    return "/adminDashboard";
  }

  return "/auth";
}
