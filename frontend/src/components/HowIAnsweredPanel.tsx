import React, { useState } from "react";
import { CheckCircle2, ChevronDown, ChevronUp, Database, ShieldCheck, Sparkles } from "lucide-react";
import { cn } from "../lib/utils";

interface HowIAnsweredPanelProps {
  agentPath?: "document_only" | "sql_only" | "hybrid";
  sqlQuery?: string | null;
  sqlRows?: Record<string, unknown>[];
  verificationPassed?: boolean;
  retried?: boolean;
  retryFixed?: boolean;
  executionSteps?: string[];
  latencyMs?: number;
}

export const HowIAnsweredPanel: React.FC<HowIAnsweredPanelProps> = ({
  agentPath,
  sqlQuery,
  sqlRows = [],
  verificationPassed = true,
  retried = false,
  retryFixed = false,
  executionSteps = [],
  latencyMs,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const getPathBadge = () => {
    switch (agentPath) {
      case "document_only":
        return { label: "Documents RAG", bg: "bg-blue-50 text-blue-700 dark:bg-blue-950/40 dark:text-blue-300" };
      case "sql_only":
        return { label: "SQL Analyst", bg: "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300" };
      case "hybrid":
      default:
        return { label: "Hybrid RAG + SQL", bg: "bg-purple-50 text-purple-700 dark:bg-purple-950/40 dark:text-purple-300" };
    }
  };

  const badge = getPathBadge();

  return (
    <div className="mt-3 rounded-xl border border-slate-200/80 dark:border-zinc-800 bg-slate-50/50 dark:bg-zinc-900/50 overflow-hidden text-xs">
      {/* Collapse Toggle Bar */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-2.5 flex items-center justify-between hover:bg-slate-100/60 dark:hover:bg-zinc-800/40 transition-colors"
      >
        <div className="flex items-center gap-2.5">
          <Sparkles className="h-3.5 w-3.5 text-indigo-500" />
          <span className="font-semibold text-slate-700 dark:text-zinc-200">How I answered</span>
          <span className={cn("px-2 py-0.5 rounded-full font-medium text-[11px]", badge.bg)}>
            {badge.label}
          </span>
          {verificationPassed && (
            <span className="flex items-center gap-1 text-[11px] font-medium text-emerald-600 dark:text-emerald-400">
              <CheckCircle2 className="h-3 w-3" />
              Verified
            </span>
          )}
          {latencyMs && (
            <span className="text-[11px] text-slate-400 dark:text-zinc-500">
              {latencyMs}ms
            </span>
          )}
        </div>
        <div className="text-slate-400 hover:text-slate-600 dark:hover:text-zinc-200">
          {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </div>
      </button>

      {/* Expanded Content Area */}
      {isExpanded && (
        <div className="p-4 border-t border-slate-200/80 dark:border-zinc-800 space-y-4 bg-white dark:bg-zinc-900/80">
          {/* Execution Steps */}
          {executionSteps.length > 0 && (
            <div>
              <span className="text-[11px] font-semibold uppercase text-slate-400 tracking-wider block mb-1.5">
                Execution Flow
              </span>
              <div className="flex flex-wrap gap-1.5">
                {executionSteps.map((step, idx) => (
                  <span
                    key={idx}
                    className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-100 dark:bg-zinc-800 text-slate-600 dark:text-zinc-300 text-[11px]"
                  >
                    <span className="text-slate-400">{idx + 1}.</span> {step}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* SQL Query Section */}
          {sqlQuery && (
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center gap-1.5">
                  <Database className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400" />
                  <span className="font-semibold text-slate-700 dark:text-zinc-200">
                    Generated PostgreSQL Query
                  </span>
                </div>
                <span className="px-2 py-0.5 rounded-full bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-400 font-semibold text-[10px] tracking-wider uppercase border border-amber-200/60 dark:border-amber-800/50">
                  Read-Only Role
                </span>
              </div>
              <pre className="p-3 rounded-xl bg-slate-900 text-slate-100 dark:bg-zinc-950 border border-slate-800 overflow-x-auto font-mono text-[11px] leading-relaxed">
                <code>{sqlQuery}</code>
              </pre>
            </div>
          )}

          {/* SQL Result Table Preview */}
          {sqlRows && sqlRows.length > 0 && (
            <div>
              <span className="text-[11px] font-semibold uppercase text-slate-400 tracking-wider block mb-1.5">
                Database Output ({sqlRows.length} rows returned)
              </span>
              <div className="max-h-48 overflow-auto rounded-xl border border-slate-200 dark:border-zinc-800">
                <table className="w-full text-left text-[11px]">
                  <thead className="bg-slate-50 dark:bg-zinc-800/80 sticky top-0 text-slate-700 dark:text-zinc-300 border-b border-slate-200 dark:border-zinc-700">
                    <tr>
                      {Object.keys(sqlRows[0]).map((col) => (
                        <th key={col} className="p-2 font-semibold">
                          {col}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-zinc-800 font-mono text-slate-600 dark:text-zinc-400">
                    {sqlRows.slice(0, 5).map((row, rIdx) => (
                      <tr key={rIdx} className="hover:bg-slate-50/60 dark:hover:bg-zinc-800/40">
                        {Object.values(row).map((val, cIdx) => (
                          <td key={cIdx} className="p-2 truncate max-w-xs">
                            {val !== null ? String(val) : "NULL"}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Verification Status */}
          <div className="p-3 rounded-xl bg-slate-50 dark:bg-zinc-800/50 border border-slate-200/60 dark:border-zinc-700/60 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <ShieldCheck className="h-4 w-4 text-emerald-500" />
              <div>
                <span className="font-semibold text-slate-800 dark:text-zinc-200 block">
                  Deterministic Verification Guard
                </span>
                <span className="text-[11px] text-slate-500 dark:text-zinc-400 block">
                  {retried
                    ? retryFixed
                      ? "Verification caught a mismatch and corrected it on automated retry."
                      : "Verification flagged a discrepancy; retry performed."
                    : "Verified: Cited chunk IDs match storage and quantitative figures match database records."}
                </span>
              </div>
            </div>
            <span
              className={cn(
                "px-2.5 py-1 rounded-full font-medium text-[11px]",
                verificationPassed
                  ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300"
                  : "bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300"
              )}
            >
              {verificationPassed ? "Passed" : "Flagged"}
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
