import React from "react";
import { Navigate, Outlet, useLocation } from "react-router-dom";
import { ensureLocalGuestUser } from "../utils/localGuest";

// Helper function to safely retrieve and parse the user from localStorage
const getStoredUser = () => {
  try {
    const raw = localStorage.getItem("user");
    return raw ? JSON.parse(raw) : null;
  } catch (error) {
    console.error("Failed to parse stored user:", error); // Log error for debugging purposes
    return null;
  }
};

// Component that protects routes based on user authentication and role
const ProtectedRoute = ({ children }) => {
  const location = useLocation();
  const user = ensureLocalGuestUser() || getStoredUser();

  // Check if the user is authenticated and has the necessary properties
  if (!user || !user.id || !user.role) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return children || <Outlet />;
};

export default ProtectedRoute;
