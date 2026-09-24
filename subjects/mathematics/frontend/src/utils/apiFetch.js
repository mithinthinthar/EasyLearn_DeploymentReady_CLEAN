import { onAuthStateChanged } from "firebase/auth";
import { auth } from "../firebase";

const getFirebaseToken = () =>
  new Promise((resolve, reject) => {
    const unsubscribe = onAuthStateChanged(auth, async (user) => {
      unsubscribe();

      if (!user) {
        reject(new Error("No authenticated Firebase user found."));
        return;
      }

      try {
        const token = await user.getIdToken();
        resolve(token);
      } catch (error) {
        reject(error);
      }
    });
  });

export const apiFetch = async (url, options = {}) => {
  const localMode = process.env.REACT_APP_LOCAL_MODE === "true";
  const token = localMode ? null : await getFirebaseToken();

  const headers = {
    ...(options.headers || {}),
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const isFormData = options.body instanceof FormData;
  if (!isFormData && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  return fetch(url, {
    ...options,
    headers,
  });
};
