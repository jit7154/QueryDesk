import React from "react";
import { Link, useLocation } from "react-router-dom";
import { BarChart3, Bot, FileText, History, MessageSquare } from "lucide-react";
import { cn } from "../lib/utils";

const NAV_ITEMS = [
  { name: "Chat", path: "/", icon: MessageSquare },
  { name: "Documents", path: "/documents", icon: FileText },
  { name: "Analytics", path: "/analytics", icon: BarChart3 },
  { name: "History", path: "/history", icon: History },
];

export const Sidebar: React.FC = () => {
  const location = useLocation();

  return (
    <aside className="w-64 border-r border-slate-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 flex flex-col justify-between select-none">
      <div>
        {/* Brand Header */}
        <div className="h-16 flex items-center px-6 gap-3 border-b border-slate-100 dark:border-zinc-800/80">
          <div className="h-9 w-9 rounded-xl bg-indigo-600 flex items-center justify-center text-white shadow-sm shadow-indigo-500/20">
            <Bot className="h-5 w-5" />
          </div>
          <div>
            <span className="font-semibold text-slate-900 dark:text-zinc-100 tracking-tight text-base block">
              QueryDesk
            </span>
            <span className="text-[11px] text-slate-500 dark:text-zinc-400 font-medium">
              Enterprise Assistant
            </span>
          </div>
        </div>

        {/* Navigation Links */}
        <nav className="p-3 space-y-1">
          {NAV_ITEMS.map((item) => {
            const isActive = location.pathname === item.path;
            const Icon = item.icon;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={cn(
                  "flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-medium transition-colors",
                  isActive
                    ? "bg-indigo-50 text-indigo-700 dark:bg-indigo-950/40 dark:text-indigo-400 font-semibold"
                    : "text-slate-600 hover:text-slate-900 hover:bg-slate-50 dark:text-zinc-400 dark:hover:text-zinc-100 dark:hover:bg-zinc-800/60"
                )}
              >
                <Icon className={cn("h-4 w-4", isActive ? "text-indigo-600 dark:text-indigo-400" : "text-slate-400 dark:text-zinc-500")} />
                {item.name}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Footer Branding */}
      <div className="p-4 border-t border-slate-100 dark:border-zinc-800">
        <div className="bg-slate-50 dark:bg-zinc-800/60 rounded-xl p-3 border border-slate-200/60 dark:border-zinc-700/50">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[11px] font-semibold text-slate-500 dark:text-zinc-400 uppercase tracking-wider">
              Workspace
            </span>
            <span className="inline-block w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          </div>
          <p className="text-xs font-semibold text-slate-900 dark:text-zinc-200">
            RetailFlow Inc.
          </p>
          <p className="text-[11px] text-slate-500 dark:text-zinc-400">
            E-Commerce Intelligence
          </p>
        </div>
      </div>
    </aside>
  );
};
