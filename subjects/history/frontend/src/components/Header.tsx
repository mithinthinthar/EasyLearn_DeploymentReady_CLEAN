import React, { useEffect, useRef, useState } from "react";
import MathUiIcon, { MathUiIconName } from "./MathUiIcon";
import { PageRoute } from "../types";
import { useAuth } from "../context/AuthContext";
import "./Header.css";
import "./HeaderPolish.css";

const PORTAL_URL = process.env.REACT_APP_PORTAL_URL || (["localhost", "127.0.0.1"].includes(window.location.hostname) ? "http://localhost:4000" : "/");
interface HeaderProps { currentPage: PageRoute; onNavigate: (page: PageRoute) => void; }

const Header: React.FC<HeaderProps> = ({ currentPage, onNavigate }) => {
  const { user, portalUser } = useAuth();
  const [accountOpen, setAccountOpen] = useState(false);
  const [language, setLanguage] = useState(() => localStorage.getItem("history-language") || "en");
  const accountRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const close = (event: MouseEvent) => { if (!accountRef.current?.contains(event.target as Node)) setAccountOpen(false); };
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, []);

  const changeLanguage = (next: string) => { localStorage.setItem("history-language", next); setLanguage(next); };
  const studentNavItems: { id: PageRoute; icon: MathUiIconName; label: string }[] = [
    { id: "dashboard", icon: "dashboard", label: "Home" },
    { id: "home", icon: "focus", label: "Practice" },
    { id: "game", icon: "arcade", label: "Arcade" },
  ];
  const navItems = portalUser?.role === "student" ? studentNavItems : studentNavItems.slice(0, 1);
  const initial = (portalUser?.name || user?.displayName || "E").charAt(0).toUpperCase();

  return <header className="header"><div className="header-container">
    <button className="logo-section" onClick={() => onNavigate("dashboard")} type="button"><img className="logo-icon" src="/easylearn-logo.svg" alt=""/><span className="logo-text">EasyLearn</span></button>
    <nav className="nav-menu" aria-label="History navigation">{navItems.map((item) => <button key={item.id} type="button" onClick={() => onNavigate(item.id)} className={`nav-item ${currentPage === item.id ? "active" : ""}`}><MathUiIcon name={item.icon} size={20}/><span className="nav-label">{item.label}</span></button>)}</nav>
    <div className="header-actions">{user && <>
      <a href={PORTAL_URL} className="header-icon-button" title="Open EasyLearn portal"><MathUiIcon name="grid"/></a>
      <div className="account-cluster" ref={accountRef}>
        <button type="button" onClick={() => setAccountOpen((value) => !value)} className="profile-trigger" title="Open profile">{user.photoURL ? <img src={user.photoURL} alt=""/> : <span>{initial}</span>}</button>
        {accountOpen && <section className="account-menu" aria-label="Account details">
          <div className="account-menu-head"><div className="menu-avatar">{initial}</div><div><strong>{portalUser?.name || user.displayName || "EasyLearn user"}</strong><span>{portalUser?.email || user.email}</span></div></div>
          {portalUser?.role === "student" && <div className="profile-detail"><MathUiIcon name="badge"/><div><span>Student ID</span><strong>{portalUser.student_code || "Not assigned"}</strong></div><span className="student-id-help" tabIndex={0} data-tooltip="Share this ID with a parent or teacher so they can connect to your EasyLearn progress." aria-label="About your Student ID"><MathUiIcon name="info" size={14} className="detail-info"/></span></div>}
          <div className="profile-detail language-detail"><MathUiIcon name="translate"/><strong>Language</strong><div className="language-toggle"><button className={language === "en" ? "selected" : ""} onClick={() => changeLanguage("en")}>EN</button><button className={language === "bm" ? "selected" : ""} onClick={() => changeLanguage("bm")}>BM</button></div></div>
        </section>}
      </div>
    </>}</div>
  </div></header>;
};

export default Header;
