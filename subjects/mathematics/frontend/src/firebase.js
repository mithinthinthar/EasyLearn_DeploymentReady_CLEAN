import { initializeApp } from "firebase/app";
import {
  getAuth,
  GoogleAuthProvider,
} from "firebase/auth";
import { getAnalytics } from "firebase/analytics";

const firebaseConfig = {
  apiKey: process.env.REACT_APP_FIREBASE_API_KEY || "AIzaSyAPK9luTBa3w3DQXjxmCQxNZ8mJcURO_Eg",
  authDomain: process.env.REACT_APP_FIREBASE_AUTH_DOMAIN || "easylearn-fyp-2026.firebaseapp.com",
  projectId: process.env.REACT_APP_FIREBASE_PROJECT_ID || "easylearn-fyp-2026",
  storageBucket: process.env.REACT_APP_FIREBASE_STORAGE_BUCKET || "easylearn-fyp-2026.firebasestorage.app",
  messagingSenderId: process.env.REACT_APP_FIREBASE_MESSAGING_SENDER_ID || "739065040200",
  appId: process.env.REACT_APP_FIREBASE_APP_ID || "1:739065040200:web:a76f8cdf8e5214b453377d",
  measurementId: process.env.REACT_APP_FIREBASE_MEASUREMENT_ID,
};

const localMode = process.env.REACT_APP_LOCAL_MODE === "true";

let auth = null;
let googleProvider = null;

if (!localMode) {
  const app = initializeApp(firebaseConfig);
  auth = getAuth(app);
  googleProvider = new GoogleAuthProvider();
  googleProvider.setCustomParameters({ prompt: "select_account" });

  // Analytics is optional and should not stop the app if it is unavailable.
  if (firebaseConfig.measurementId) {
    try {
      getAnalytics(app);
    } catch (error) {
      console.warn("Firebase Analytics is unavailable:", error);
    }
  }
}

export { auth, googleProvider };
