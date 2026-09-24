import { apiFetch } from "./apiFetch";

// Logs user activity to the backend for analytics purposes.
export const logUserActivity = async (actionString) => {
  try {
    await apiFetch(`${process.env.REACT_APP_API_BASE_URL}/api/log-activity`, {
      method: "POST",
      body: JSON.stringify({
        action_type: actionString,
        timestamp: new Date().toISOString(),
      }),
    });
  } catch (error) {
    console.error("Failed to log activity:", error);
  }
};