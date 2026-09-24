import React, { createContext, useContext, useEffect, useState } from "react";
import { User, signInWithCustomToken, signOut } from "firebase/auth";
import { auth } from "../lib/firebase";

const IS_LOCAL = ["localhost", "127.0.0.1"].includes(window.location.hostname);
const SHARED_AUTH_URL = process.env.REACT_APP_SHARED_AUTH_URL || (IS_LOCAL ? "http://localhost:4500" : "/platform-api");
const PORTAL_URL = process.env.REACT_APP_PORTAL_URL || (IS_LOCAL ? "http://localhost:4000" : "/");
export type EasyLearnRole = "student" | "teacher" | "parent";
export interface PortalUser { uid: string; email: string; name: string; picture?: string | null; role: EasyLearnRole; student_code?: string | null; }
interface AuthContextType { user: User | null; portalUser: PortalUser | null; loading: boolean; signInWithGoogle: () => Promise<void>; logout: () => Promise<void>; }

const AuthContext = createContext<AuthContextType>({ user: null, portalUser: null, loading: true, signInWithGoogle: async () => { window.location.href = PORTAL_URL; }, logout: async () => {} });
export const useAuth = () => useContext(AuthContext);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [portalUser, setPortalUser] = useState<PortalUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    async function connectPortalAccount() {
      try {
        const response = await fetch(`${SHARED_AUTH_URL}/auth/custom-token`, { method: "POST", credentials: "include" });
        if (response.status === 401) { await signOut(auth).catch(() => {}); window.location.replace(PORTAL_URL); return; }
        const data = await response.json();
        if (!response.ok || !data.custom_token || !data.user) throw new Error(data.detail || "Portal session unavailable");
        const result = await signInWithCustomToken(auth, data.custom_token);
        if (active) { setUser(result.user); setPortalUser(data.user); setLoading(false); }
      } catch (error) {
        console.error("History Portal login failed:", error);
        if (active) setLoading(false);
        window.location.replace(PORTAL_URL);
      }
    }
    connectPortalAccount();
    return () => { active = false; };
  }, []);

  const signInWithGoogle = async () => { window.location.href = PORTAL_URL; };
  const logout = async () => { await fetch(`${SHARED_AUTH_URL}/auth/logout`, { method: "POST", credentials: "include" }).catch(() => {}); await signOut(auth).catch(() => {}); window.location.replace(PORTAL_URL); };
  return <AuthContext.Provider value={{ user, portalUser, loading, signInWithGoogle, logout }}>{!loading && children}</AuthContext.Provider>;
};
