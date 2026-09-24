import React from "react";
import { HashRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import { LanguageProvider } from "../context/LanguageContext";

// Import Layout
import MainLayout from "../layouts/MainLayout";

// Import General Pages
import LandingPage from "../pages/general/LandingPage";
import AuthPage from "../pages/general/AuthPage";

// Import Student Pages
import StudentDashboard from "../pages/student/StudentDashboard";
import PracticePage from "../pages/student/PracticePage";
import QuickSnapPage from "../pages/student/QuickSnapPage";
import PracticePageKertas1 from "../pages/student/PracticePageKertas1";
import PracticePageKertas2 from "../pages/student/PracticePageKertas2";
import ChatbotPage from "../pages/student/ChatbotPage";

// Import Parent Pages
import ParentDashboard from "../pages/parent/ParentDashboard";
import ParentChildDashboard from "../pages/parent/ParentChildDashboard";

// Import Admin Pages
import AdminDashboard from "../pages/admin/AdminDashboard";
import TeacherDashboard from "../pages/teacher/TeacherDashboard";

// Route guards
import ProtectedRoute from "./ProtectedRoute";
import RoleProtectedRoute from "./RoleProtectedRoute";



const AppRoutes = () => {
  const localMode = process.env.REACT_APP_LOCAL_MODE === "true";

  return (
    <LanguageProvider>
      <Router>
        <Routes>
          
          {/* PUBLIC ROUTES - w/o header/footer layout */}
          <Route path="/" element={localMode ? <Navigate to="/practice" replace /> : <LandingPage />} />
          <Route path="/auth" element={localMode ? <Navigate to="/practice" replace /> : <AuthPage />} />
          <Route path="/login" element={<Navigate to={localMode ? "/practice" : "/auth"} replace />} />
          <Route path="/register" element={<Navigate to={localMode ? "/practice" : "/auth"} replace />} />

          {/* STUDENT ROUTES - wrapped in MainLayout */}
          <Route
            path="/studentDashboard"
            element={
              localMode ? <Navigate to="/practice" replace /> : <RoleProtectedRoute allowedRoles={["student"]}>
                <MainLayout>
                  <StudentDashboard />
                </MainLayout>
              </RoleProtectedRoute>
            }
          />
          
          <Route
            path="/chatbot"
            element={
              localMode ? <Navigate to="/practice" replace /> : <RoleProtectedRoute allowedRoles={["student"]}>
                <MainLayout showFloatingChatbot={false}>
                  <ChatbotPage />
                </MainLayout>
              </RoleProtectedRoute>
            }
          />

          <Route
            path="/practice"
            element={
              <RoleProtectedRoute allowedRoles={["student"]}>
                <MainLayout>
                  <PracticePage />
                </MainLayout>
              </RoleProtectedRoute>
            }
          />

          <Route
            path="/quick-snap"
            element={
              localMode ? <Navigate to="/practice" replace /> : <RoleProtectedRoute allowedRoles={["student"]}>
                <MainLayout>
                  <QuickSnapPage />
                </MainLayout>
              </RoleProtectedRoute>
            }
          />

         <Route
            path="/practice/kertas1"
            element={
              <RoleProtectedRoute allowedRoles={["student"]}>
                <PracticePageKertas1 />
              </RoleProtectedRoute>
            }
          />
          
          <Route
            path="/practice/kertas2"
            element={
              <RoleProtectedRoute allowedRoles={["student"]}>
                <PracticePageKertas2 />
              </RoleProtectedRoute>
            }
          />

          {/* PARENT ROUTES - wrapped in MainLayout */}
          <Route
            path="/parentDashboard"
            element={
              <RoleProtectedRoute allowedRoles={["parent"]}>
                <MainLayout
                  showTabs={false}
                  homePath="/parentDashboard"
                  showFloatingChatbot={false}
                >
                  <ParentDashboard />
                </MainLayout>
              </RoleProtectedRoute>
            }
          />
          
          <Route
            path="/parentDashboard/child/:studentId"
            element={
              <RoleProtectedRoute allowedRoles={["parent"]}>
                <MainLayout
                  showTabs={false}
                  homePath="/parentDashboard"
                  showFloatingChatbot={false}
                >
                  <ParentChildDashboard />
                </MainLayout>
              </RoleProtectedRoute>
            }
          />
          {/* ADMIN ROUTES - wrapped in MainLayout */}
          <Route
            path="/teacherDashboard"
            element={
              <RoleProtectedRoute allowedRoles={["teacher"]}>
                <MainLayout showTabs={false} homePath="/teacherDashboard" showFloatingChatbot={false}>
                  <TeacherDashboard />
                </MainLayout>
              </RoleProtectedRoute>
            }
          />
          <Route
            path="/adminDashboard"
            element={
              <RoleProtectedRoute allowedRoles={["admin"]}>
                <AdminDashboard />
              </RoleProtectedRoute>
            }
          />

          <Route path="*" element={<Navigate to="/" replace />} />
          {/*can add other pages **must wrap in <MainLayout>, except inner pages like student kertas1 */}
        </Routes>
      </Router>
    </LanguageProvider>
  );
};

export default AppRoutes;
