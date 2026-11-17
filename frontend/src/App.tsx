import React, { useState, useEffect } from "react";
import { BrowserRouter, Routes, Route, useLocation } from "react-router-dom";
import { Sidebar } from "./components/Sidebar";
import { Header } from "./components/Header";
import { ChatPage } from "./pages/ChatPage";
import { DocumentsPage } from "./pages/DocumentsPage";
import { AnalyticsPage } from "./pages/AnalyticsPage";
import { HistoryPage } from "./pages/HistoryPage";

const getPageTitle = (pathname: string): string => {
  switch (pathname) {
    case "/documents":
      return "Knowledge Base & Documents";
    case "/analytics":
      return "System Analytics & Telemetry";
    case "/history":
      return "Audit & Query History";
    case "/":
    default:
      return "QueryDesk AI Assistant";
  }
};

const Layout: React.FC<{ isDark: boolean; onToggleDark: () => void }> = ({
  isDark,
  onToggleDark,
}) => {
  const location = useLocation();
  const title = getPageTitle(location.pathname);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-50 dark:bg-zinc-950 font-sans text-slate-900 dark:text-zinc-100 antialiased">
      {/* Left fixed Sidebar */}
      <Sidebar />

      {/* Main App Canvas */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <Header title={title} isDark={isDark} onToggleDark={onToggleDark} />
        <main className="flex-1 overflow-hidden flex flex-col">
          <Routes>
            <Route path="/" element={<ChatPage />} />
            <Route path="/documents" element={<DocumentsPage />} />
            <Route path="/analytics" element={<AnalyticsPage />} />
            <Route path="/history" element={<HistoryPage />} />
          </Routes>
        </main>
      </div>
    </div>
  );
};

export const App: React.FC = () => {
  const [isDark, setIsDark] = useState<boolean>(() => {
    const saved = localStorage.getItem("querydesk_theme");
    if (saved) return saved === "dark";
    return window.matchMedia("(prefers-color-scheme: dark)").matches;
  });

  useEffect(() => {
    if (isDark) {
      document.documentElement.classList.add("dark");
      localStorage.setItem("querydesk_theme", "dark");
    } else {
      document.documentElement.classList.remove("dark");
      localStorage.setItem("querydesk_theme", "light");
    }
  }, [isDark]);

  const toggleDark = () => setIsDark((prev) => !prev);

  return (
    <BrowserRouter>
      <Layout isDark={isDark} onToggleDark={toggleDark} />
    </BrowserRouter>
  );
};