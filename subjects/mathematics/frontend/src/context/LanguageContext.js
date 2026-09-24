import React, { createContext, useContext, useMemo, useState } from "react";
import { translations } from "../i18n/translations";

const LanguageContext = createContext();

// LanguageProvider component to wrap the app and provide language context
export const LanguageProvider = ({ children }) => {
  const storedUser = JSON.parse(localStorage.getItem("user")) || {};
  // Initialize language state from localStorage or default to "english"
  const [language, setLanguageState] = useState(storedUser.language || "english");

  const setLanguage = (lang) => {
    setLanguageState(lang);

    // Update the user's language in localStorage so it persists across sessions
    const user = JSON.parse(localStorage.getItem("user")) || {};
    user.language = lang;
    localStorage.setItem("user", JSON.stringify(user));
  };

  const t = (key) => {
    return translations[language]?.[key] || key;
  };

  const value = useMemo(() => {
    return { language, setLanguage, t };
  }, [language]);

  return (
    <LanguageContext.Provider value={value}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = () => useContext(LanguageContext);