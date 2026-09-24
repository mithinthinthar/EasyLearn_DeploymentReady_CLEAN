import { useLocation } from "react-router-dom";
import Navbar from "./Navbar";
import AIChatBar from "./AIChatBar";
import { useAuth } from "../../context/AuthContext";

export default function Layout({ children }: any) {
  const location = useLocation();
  const localMode = import.meta.env.VITE_LOCAL_MODE === "true";
  const { user } = useAuth();

  const isQuizPage = location.pathname.endsWith("-quiz");

  return (
    <>
      <Navbar />
      <main className={`container${location.pathname === "/dashboard" ? " dashboard-container" : ""}`}>
        {localMode && (
          <div className="card-base" style={{ margin: "18px 0", padding: "12px", textAlign: "center", color: "#92400e", background: "#fff7ed" }}>
            Mod tetamu tempatan: latihan bertutur, mendengar dan AI Chat dinyahaktifkan.
          </div>
        )}
        {children}
      </main>
      {!isQuizPage && !localMode && user?.role === "student" && <AIChatBar />}
    </>
  );
}
