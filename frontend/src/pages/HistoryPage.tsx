import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  History,
  Search,
  CheckCircle2,
  AlertCircle,
  Database,
  FileText,
  GitMerge,
  Clock,
  DollarSign,
  ChevronRight,
  Loader2,
  X,
} from "lucide-react";
import { apiClient } from "../api/client";
import { AnalyticsData } from "../types";
import { cn } from "../lib/utils";

type QueryLog = AnalyticsData["recent_queries"][number];

export const HistoryPage: React.FC = () => {
  const [searchFilter, setSearchFilter] = useState("");
  const [selectedItem, setSelectedItem] = useState<QueryLog | null>(null);

  const { data: analytics, isLoading, error } = useQuery<AnalyticsData>({
    queryKey: ["analytics"],
    queryFn: () => apiClient.getAnalytics(),
  });

  const queryLogs = analytics?.recent_queries || [];

  const filteredLogs = queryLogs.filter(
    (log) =>
      log.query_text.toLowerCase().includes(searchFilter.toLowerCase()) ||
      log.agent_path.toLowerCase().includes(searchFilter.toLowerCase()) ||
      (log.sql_query && log.sql_query.toLowerCase().includes(searchFilter.toLowerCase()))
  );

  const getPathBadge = (path: string) => {
    switch (path) {
      case "document_only":
        return {
          label: "Docs RAG",
          icon: FileText,
          cls: "bg-blue-50 text-blue-700 dark:bg-blue-950/60 dark:text-blue-300 border-blue-200 dark:border-blue-900",
        };
      case "sql_only":
        return {
          label: "Text-to-SQL",
          icon: Database,
          cls: "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300 border-emerald-200 dark:border-emerald-900",
        };
      case "hybrid":
      default:
        return {
          label: "Hybrid",
          icon: GitMerge,
          cls: "bg-purple-50 text-purple-700 dark:bg-purple-950/60 dark:text-purple-300 border-purple-200 dark:border-purple-900",
        };
    }
  };

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden bg-slate-50/50 dark:bg-zinc-950 p-8">
      <div className="max-w-6xl w-full mx-auto flex flex-col h-full space-y-6">
        {/* Page Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-2xl font-bold text-slate-900 dark:text-zinc-100 tracking-tight">
              Audit & Query History
            </h2>
            <p className="text-sm text-slate-500 dark:text-zinc-400 mt-1">
              Immutable ledger of business questions, routing determinations, executed SQL, and verification outcomes.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold px-3 py-1.5 rounded-full bg-slate-100 dark:bg-zinc-800 text-slate-700 dark:text-zinc-300 border border-slate-200 dark:border-zinc-700">
              {queryLogs.length} Queries Recorded
            </span>
          </div>
        </div>

        {/* Search Bar */}
        <div className="flex items-center justify-between gap-4">
          <div className="relative flex-1 max-w-md">
            <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search historical queries, routes, or SQL..."
              value={searchFilter}
              onChange={(e) => setSearchFilter(e.target.value)}
              className="w-full pl-10 pr-4 py-2 text-sm rounded-xl border border-slate-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 text-slate-900 dark:text-zinc-100 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all"
            />
          </div>
          <span className="text-xs text-slate-500 dark:text-zinc-400 font-medium">
            Showing {filteredLogs.length} of {queryLogs.length}
          </span>
        </div>

        {/* Query Log Table / List */}
        <div className="flex-1 overflow-auto bg-white dark:bg-zinc-900 rounded-2xl border border-slate-200 dark:border-zinc-800 shadow-sm">
          {isLoading ? (
            <div className="p-12 flex flex-col items-center justify-center text-slate-400">
              <Loader2 className="w-8 h-8 animate-spin mb-3 text-indigo-500" />
              <p className="text-sm">Loading historical query logs...</p>
            </div>
          ) : error ? (
            <div className="p-8 text-center text-rose-500 text-sm">
              Failed to load history. Verify backend connectivity.
            </div>
          ) : filteredLogs.length === 0 ? (
            <div className="p-12 text-center text-slate-400">
              <History className="w-12 h-12 mx-auto stroke-[1.2] mb-3 text-slate-300 dark:text-zinc-700" />
              <p className="text-sm font-medium text-slate-600 dark:text-zinc-400">
                No past queries found
              </p>
              <p className="text-xs text-slate-400 dark:text-zinc-500 mt-1">
                Ask a question in the Chat view to generate audit logs.
              </p>
            </div>
          ) : (
            <div className="divide-y divide-slate-100 dark:divide-zinc-800">
              {filteredLogs.map((log) => {
                const badge = getPathBadge(log.agent_path);
                const BadgeIcon = badge.icon;
                return (
                  <div
                    key={log.query_id}
                    onClick={() => setSelectedItem(log)}
                    className="p-4 sm:px-6 hover:bg-slate-50/80 dark:hover:bg-zinc-800/40 cursor-pointer transition-colors flex items-center justify-between gap-4 group"
                  >
                    <div className="flex-1 min-w-0 space-y-1.5">
                      <div className="flex items-center gap-2.5 flex-wrap">
                        <span
                          className={cn(
                            "inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold border",
                            badge.cls
                          )}
                        >
                          <BadgeIcon className="w-3 h-3" />
                          {badge.label}
                        </span>

                        {log.verification_passed ? (
                          <span className="inline-flex items-center gap-1 text-[11px] text-emerald-600 dark:text-emerald-400 font-medium">
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            Verified
                          </span>
                        ) : log.retry_fixed ? (
                          <span className="inline-flex items-center gap-1 text-[11px] text-amber-600 dark:text-amber-400 font-medium">
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            Fixed by Retry
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-[11px] text-rose-500 font-medium">
                            <AlertCircle className="w-3.5 h-3.5" />
                            Unverified
                          </span>
                        )}

                        <span className="text-[11px] text-slate-400 dark:text-zinc-500 font-mono">
                          {new Date(log.created_at).toLocaleString([], {
                            month: "short",
                            day: "numeric",
                            hour: "2-digit",
                            minute: "2-digit",
                          })}
                        </span>
                      </div>

                      <p className="text-sm font-medium text-slate-900 dark:text-zinc-100 truncate">
                        {log.query_text}
                      </p>

                      {log.sql_query && (
                        <p className="text-xs font-mono text-slate-500 dark:text-zinc-400 truncate max-w-xl">
                          {log.sql_query}
                        </p>
                      )}
                    </div>

                    <div className="flex items-center gap-4 text-xs text-slate-500 dark:text-zinc-400 shrink-0 font-mono">
                      <div className="hidden sm:flex items-center gap-1">
                        <Clock className="w-3.5 h-3.5 text-slate-400" />
                        <span>{log.latency_ms}ms</span>
                      </div>

                      <div className="hidden sm:flex items-center gap-1">
                        <DollarSign className="w-3.5 h-3.5 text-slate-400" />
                        <span>${log.estimated_cost_usd.toFixed(4)}</span>
                      </div>

                      <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-transform group-hover:translate-x-0.5" />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Detail Slide-out Drawer */}
      {selectedItem && (
        <div className="fixed inset-0 z-50 overflow-hidden bg-black/40 backdrop-blur-xs flex justify-end">
          <div className="w-full max-w-xl bg-white dark:bg-zinc-900 h-full shadow-2xl flex flex-col border-l border-slate-200 dark:border-zinc-800">
            {/* Header */}
            <div className="p-6 border-b border-slate-100 dark:border-zinc-800 flex items-center justify-between">
              <div>
                <span className="text-xs font-semibold text-indigo-600 dark:text-indigo-400 uppercase tracking-wider">
                  Query Audit Record
                </span>
                <h3 className="text-base font-mono text-slate-500 dark:text-zinc-400 text-xs mt-0.5">
                  ID: {selectedItem.query_id}
                </h3>
              </div>
              <button
                onClick={() => setSelectedItem(null)}
                className="p-2 rounded-xl text-slate-400 hover:text-slate-600 dark:hover:text-zinc-200 hover:bg-slate-100 dark:hover:bg-zinc-800 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Content Details */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              {/* Question */}
              <div className="space-y-1.5">
                <label className="text-xs font-semibold uppercase tracking-wider text-slate-400 dark:text-zinc-500">
                  Question
                </label>
                <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-zinc-800/60 border border-slate-200/80 dark:border-zinc-700/60 text-sm font-medium text-slate-900 dark:text-zinc-100">
                  {selectedItem.query_text}
                </div>
              </div>

              {/* Metrics Grid */}
              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 rounded-xl bg-slate-50 dark:bg-zinc-800/40 border border-slate-200/60 dark:border-zinc-800">
                  <div className="text-[11px] text-slate-400 uppercase font-semibold">Agent Path</div>
                  <div className="text-xs font-semibold text-slate-800 dark:text-zinc-200 mt-1 capitalize">
                    {selectedItem.agent_path.replace("_", " ")}
                  </div>
                </div>

                <div className="p-3 rounded-xl bg-slate-50 dark:bg-zinc-800/40 border border-slate-200/60 dark:border-zinc-800">
                  <div className="text-[11px] text-slate-400 uppercase font-semibold">Latency</div>
                  <div className="text-xs font-mono font-semibold text-slate-800 dark:text-zinc-200 mt-1">
                    {selectedItem.latency_ms} ms
                  </div>
                </div>

                <div className="p-3 rounded-xl bg-slate-50 dark:bg-zinc-800/40 border border-slate-200/60 dark:border-zinc-800">
                  <div className="text-[11px] text-slate-400 uppercase font-semibold">Cost</div>
                  <div className="text-xs font-mono font-semibold text-slate-800 dark:text-zinc-200 mt-1">
                    ${selectedItem.estimated_cost_usd.toFixed(4)}
                  </div>
                </div>

                <div className="p-3 rounded-xl bg-slate-50 dark:bg-zinc-800/40 border border-slate-200/60 dark:border-zinc-800">
                  <div className="text-[11px] text-slate-400 uppercase font-semibold">Verification</div>
                  <div className="text-xs font-semibold mt-1">
                    {selectedItem.verification_passed ? (
                      <span className="text-emerald-600 dark:text-emerald-400">Passed</span>
                    ) : selectedItem.retry_fixed ? (
                      <span className="text-amber-600 dark:text-amber-400">Fixed by Retry</span>
                    ) : (
                      <span className="text-rose-500">Failed</span>
                    )}
                  </div>
                </div>
              </div>

              {/* SQL Query */}
              {selectedItem.sql_query && (
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <label className="text-xs font-semibold uppercase tracking-wider text-slate-400 dark:text-zinc-500">
                      Executed SQL (Guarded Read-Only)
                    </label>
                  </div>
                  <pre className="p-4 rounded-xl bg-zinc-950 text-indigo-300 font-mono text-xs overflow-x-auto border border-zinc-800 leading-relaxed whitespace-pre-wrap">
                    {selectedItem.sql_query}
                  </pre>
                </div>
              )}

              {/* Timestamp */}
              <div className="pt-4 border-t border-slate-100 dark:border-zinc-800 text-xs text-slate-400 dark:text-zinc-500">
                Executed on {new Date(selectedItem.created_at).toUTCString()}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};