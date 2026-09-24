import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { loginFromPortal } from "../services/auth";
import type { AuthUser } from "../types/auth";

type AuthContextType = {
  user: AuthUser | null;
  logout: () => void;
  isLoading: boolean;
  login: (token: string) => Promise<void>;
  emailLogin: (email: string, password: string) => Promise<void>;
  emailRegister: (email: string, password: string) => Promise<void>;
};
const AuthContext = createContext<AuthContextType | undefined>(undefined);
const STORAGE_KEY = "easylearn_user";
const IS_LOCAL = ["localhost", "127.0.0.1"].includes(window.location.hostname);
const PORTAL_URL = import.meta.env.VITE_PORTAL_URL || (IS_LOCAL ? "http://localhost:4000" : "/");
const PLATFORM_URL = import.meta.env.VITE_SHARED_AUTH_URL || (IS_LOCAL ? "http://localhost:4500" : "/platform-api");


export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  useEffect(() => {
    let active = true;
    loginFromPortal().then((data) => {
      if (!active) return;
      setUser(data); localStorage.setItem(STORAGE_KEY, JSON.stringify(data)); setIsLoading(false);
    }).catch((error) => {
      console.error("Bahasa Melayu Portal login failed:", error);
      localStorage.removeItem(STORAGE_KEY); setIsLoading(false);
      window.location.replace(PORTAL_URL);
    });
    return () => { active = false; };
  }, []);
  function logout() {
    fetch(`${PLATFORM_URL}/auth/logout`, { method: "POST", credentials: "include" }).finally(() => {
      setUser(null); localStorage.removeItem(STORAGE_KEY); window.location.replace(PORTAL_URL);
    });
  }
  async function portalOnlyLogin() {
    window.location.replace(PORTAL_URL);
  }
  const value = useMemo(() => ({ user, logout, isLoading, login: portalOnlyLogin, emailLogin: portalOnlyLogin, emailRegister: portalOnlyLogin }), [user, isLoading]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider");
  return context;
}
