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



async function syncMathematicsSnapshot(mathUser, idToken) {
  try {
    if (!mathUser?.id || !idToken) return;

    const summaryResponse = await fetch(
      `${MATHEMATICS_API_URL}/api/student/platform-summary/${mathUser.id}`,
      {
        headers: {
          Authorization: `Bearer ${idToken}`,
        },
      },
    );

    const summary = await readResponse(summaryResponse);
    if (!summaryResponse.ok || !summary.success) {
      console.warn("Mathematics portal snapshot source was unavailable.", summary);
      return;
    }

    const snapshotResponse = await fetch(
      `${SHARED_AUTH_URL}/subjects/mathematics/snapshot`,
      {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          subject: "mathematics",
          average_score: summary.average_score,
          activities: summary.activities || 0,
          questions_answered: summary.questions_answered || 0,
          minutes_spent: summary.minutes_spent || 0,
          last_active: summary.last_active || null,
          metadata: summary.metadata || {},
        }),
      },
    );

    if (!snapshotResponse.ok) {
      console.warn("Mathematics portal snapshot could not be saved.");
    }
  } catch (error) {
    // Snapshot sync is deliberately non-blocking: Math should still open even
    // if the shared dashboard is temporarily unavailable.
    console.warn("Mathematics portal snapshot sync warning:", error);
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

  // Do not make the Math loading screen wait for dashboard synchronization.
  // The UI opens immediately; Aiven -> Firestore aggregate sync runs quietly.
  syncMathematicsSnapshot(mathData.user, idToken);

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
