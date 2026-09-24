import { useEffect, useRef, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { useLanguage, type Language } from "../../language";
import MathUiIcon from "./MathUiIcon";
import "./NavbarStandard.css";
import "./NavbarPolish.css";

export default function Navbar() {
  const location = useLocation();
  const { user } = useAuth();
  const { language, setLanguage, t } = useLanguage();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const close = (event: MouseEvent) => {
      if (!ref.current?.contains(event.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, []);

  const initial = (user?.name || user?.email || "User").trim().charAt(0).toUpperCase();
  const setLang = (value: Language) => setLanguage(value);
  const practiceActive = location.pathname.startsWith("/practice");
  const quizActive = location.pathname.startsWith("/quiz") || location.pathname.includes("-quiz");

  return (
    <header className="el-navbar">
      <div className="el-navbar-inner">
        <Link to="/dashboard" className="el-navbar-brand" aria-label="EasyLearn Bahasa Melayu dashboard">
          <img src="/easylearn-logo.svg" alt="" />
          <strong>EasyLearn</strong>
        </Link>

        <nav className="el-navbar-tabs" aria-label="Bahasa Melayu navigation">
          <Link to="/dashboard" className={location.pathname === "/dashboard" || location.pathname === "/home" ? "active" : ""}>
            <MathUiIcon name="dashboard" />{t("home")}
          </Link>
          {user?.role === "student" && <>
            <Link to="/practice" className={practiceActive ? "active" : ""}><MathUiIcon name="focus" />{t("practice")}</Link>
            <Link to="/quiz" className={quizActive ? "active" : ""}><MathUiIcon name="library" />{t("quiz")}</Link>
          </>}
        </nav>

        <div className="el-navbar-actions">
          {user && <div className="el-profile">
            <a href={import.meta.env.VITE_PORTAL_URL || (["localhost", "127.0.0.1"].includes(window.location.hostname) ? "http://localhost:4000" : "/")} className="el-icon-button" title="All EasyLearn subjects" aria-label="Open main EasyLearn portal"><MathUiIcon name="grid" /></a>
            <div className="el-profile-anchor" ref={ref}>
              <button className="el-profile-trigger" aria-label="Open account menu" aria-expanded={open} onClick={() => setOpen(value => !value)}>
                {user.picture ? <img src={user.picture} alt="" referrerPolicy="no-referrer" /> : <span>{initial}</span>}
              </button>
              {open && <div className="el-profile-menu">
                <div className="el-profile-head">
                  <span className="el-profile-avatar">{user.picture ? <img src={user.picture} alt="" referrerPolicy="no-referrer" /> : initial}</span>
                  <span><strong>{user.name || "EasyLearn user"}</strong><small>{user.email}</small></span>
                </div>
                {user.role === "student" && <div className="el-profile-row">
                  <MathUiIcon name="badge" />
                  <span><small>Student ID</small><strong>{user.student_code || "Not assigned"}</strong></span>
                  <span className="el-student-id-help" tabIndex={0} data-tooltip="Share this ID with a parent or teacher so they can connect to your EasyLearn progress." aria-label="About your Student ID"><MathUiIcon name="info" className="el-detail-info" /></span>
                </div>}
                <div className="el-profile-row language">
                  <MathUiIcon name="translate" /><strong>{t("languageLabel")}</strong>
                  <div className="el-language-switch">
                    <button className={language === "en" ? "active" : ""} onClick={() => setLang("en")}>EN</button>
                    <button className={language === "bm" ? "active" : ""} onClick={() => setLang("bm")}>BM</button>
                  </div>
                </div>
              </div>}
            </div>
          </div>}
        </div>
      </div>
    </header>
  );
}
