import React from "react";
import { Navigate, Outlet, useLocation } from "react-router-dom";
import { ensureLocalGuestUser } from "../utils/localGuest";

const getStoredUser = () => {
  try {
    const raw = localStorage.getItem("user");
    return raw ? JSON.parse(raw) : null;
  } catch (error) {
    console.error("Failed to parse stored user:", error);
    return null;
  }
};

const getDefaultRouteByRole = (role) => {
  if (role === "student") return "/studentDashboard";
  if (role === "parent") return "/parentDashboard";
  if (role === "teacher") return "/teacherDashboard";
  if (role === "admin") return "/adminDashboard";
  return "/login";
};

const RoleProtectedRoute = ({ allowedRoles = [], children }) => {
  const location = useLocation();
  const user = ensureLocalGuestUser() || getStoredUser();

  if (!user || !user.id || !user.role) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  if (!allowedRoles.includes(user.role)) {
    return <Navigate to={getDefaultRouteByRole(user.role)} replace />;
  }

  return children || <Outlet />;
};

export default RoleProtectedRoute;
