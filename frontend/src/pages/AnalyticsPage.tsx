import React from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Activity,
  CheckCircle2,
  Clock,
  DollarSign,
  Layers,
  PieChart as PieIcon,
  RefreshCw,
  ShieldAlert,
  Loader2,
} from "lucide-react";
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  AreaChart,
  Area,
  CartesianGrid,
} from "recharts";
import { apiClient } from "../api/client";
import { AnalyticsData } from "../types";

const COLORS = ["#6366f1", "#10b981", "#f59e0b", "#ec4899", "#8b5cf6"];

export const AnalyticsPage: React.FC = () => {
  const { data: analytics, isLoading, error } = useQuery<AnalyticsData>({
    queryKey: ["analytics"],
    queryFn: () => apiClient.getAnalytics(),
    refetchInterval: 15000,
  });

  if (isLoading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center h-full bg-slate-50/50 dark:bg-zinc-950">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-500 mb-3" />
        <p className="text-sm font-medium text-slate-500 dark:text-zinc-400">
          Gathering system telemetry...
        </p>
      </div>
    );
  }

  if (error || !analytics) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center h-full bg-slate-50/50 dark:bg-zinc-950 p-8">
        <div className="max-w-md text-center p-6 bg-white dark:bg-zinc-900 rounded-2xl border border-slate-200 dark:border-zinc-800 shadow-sm">
          <ShieldAlert className="w-10 h-10 text-rose-500 mx-auto mb-3" />
          <h3 className="text-base font-semibold text-slate-900 dark:text-zinc-100 mb-1">
            Telemetry Unavailable
          </h3>
          <p className="text-sm text-slate-500 dark:text-zinc-400">
            Could not fetch usage analytics. Verify that the backend service and PostgreSQL are active.
          </p>
        </div>
      </div>
    );
  }

  // Route split data for Pie Chart
  const routeSplitData = Object.entries(analytics.route_split || {}).map(([key, value]) => {
    let name = "Hybrid";
    if (key === "document_only") name = "Docs RAG";
    if (key === "sql_only") name = "Text-to-SQL";
    return { name, value };
  });

  // Recent latency timeline data
  const latencyTimeline = (analytics.recent_queries || [])
    .slice()
    .reverse()
    .map((q, idx) => ({
      index: idx + 1,
      latency: q.latency_ms,
      time: new Date(q.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      path: q.agent_path,
    }));

  // Top documents data
  const topDocsData = (analytics.top_documents || []).map((doc) => ({
    name: doc.document.length > 25 ? doc.document.substring(0, 22) + "..." : doc.document,
    citations: doc.citations,
  }));

  return (
    <div className="flex-1 flex flex-col h-full overflow-y-auto bg-slate-50/50 dark:bg-zinc-950 p-8 space-y-8">
      <div className="max-w-6xl w-full mx-auto space-y-8">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-2xl font-bold text-slate-900 dark:text-zinc-100 tracking-tight">
              Observability & Analytics
            </h2>
            <p className="text-sm text-slate-500 dark:text-zinc-400 mt-1">
              Real-time query metrics, agent routing breakdown, latency percentiles, and cost attribution.
            </p>
          </div>
          <div className="flex items-center gap-2 text-xs font-semibold px-3 py-1.5 rounded-full bg-slate-100 dark:bg-zinc-800 text-slate-700 dark:text-zinc-300 border border-slate-200 dark:border-zinc-700">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            Live Ingestion Logs
          </div>
        </div>

        {/* 4 Stat Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Total Queries */}
          <div className="bg-white dark:bg-zinc-900 p-5 rounded-2xl border border-slate-200 dark:border-zinc-800 shadow-sm">
            <div className="flex items-center justify-between text-slate-500 dark:text-zinc-400 mb-3">
              <span className="text-xs font-semibold uppercase tracking-wider">Total Queries</span>
              <Activity className="w-4 h-4 text-indigo-500" />
            </div>
            <div className="text-2xl font-bold text-slate-900 dark:text-zinc-100 font-mono">
              {analytics.total_queries}
            </div>
            <div className="text-[11px] text-slate-400 dark:text-zinc-500 mt-1">
              Supervisor orchestrated
            </div>
          </div>

          {/* Average Latency */}
          <div className="bg-white dark:bg-zinc-900 p-5 rounded-2xl border border-slate-200 dark:border-zinc-800 shadow-sm">
            <div className="flex items-center justify-between text-slate-500 dark:text-zinc-400 mb-3">
              <span className="text-xs font-semibold uppercase tracking-wider">Avg Latency</span>
              <Clock className="w-4 h-4 text-emerald-500" />
            </div>
            <div className="text-2xl font-bold text-slate-900 dark:text-zinc-100 font-mono">
              {analytics.avg_latency_ms.toFixed(0)} <span className="text-sm font-normal text-slate-400">ms</span>
            </div>
            <div className="text-[11px] text-slate-400 dark:text-zinc-500 mt-1">
              p95: {analytics.p95_latency_ms.toFixed(0)} ms
            </div>
          </div>

          {/* Average Cost per Query */}
          <div className="bg-white dark:bg-zinc-900 p-5 rounded-2xl border border-slate-200 dark:border-zinc-800 shadow-sm">
            <div className="flex items-center justify-between text-slate-500 dark:text-zinc-400 mb-3">
              <span className="text-xs font-semibold uppercase tracking-wider">Avg Cost / Query</span>
              <DollarSign className="w-4 h-4 text-amber-500" />
            </div>
            <div className="text-2xl font-bold text-slate-900 dark:text-zinc-100 font-mono">
              ${analytics.avg_cost_usd.toFixed(4)}
            </div>
            <div className="text-[11px] text-slate-400 dark:text-zinc-500 mt-1">
              Total spend: ${analytics.total_cost_usd.toFixed(4)}
            </div>
          </div>

          {/* Verification Pass Rate */}
          <div className="bg-white dark:bg-zinc-900 p-5 rounded-2xl border border-slate-200 dark:border-zinc-800 shadow-sm">
            <div className="flex items-center justify-between text-slate-500 dark:text-zinc-400 mb-3">
              <span className="text-xs font-semibold uppercase tracking-wider">Verification Rate</span>
              <CheckCircle2 className="w-4 h-4 text-indigo-500" />
            </div>
            <div className="text-2xl font-bold text-slate-900 dark:text-zinc-100 font-mono">
              {(analytics.verification_pass_rate * 100).toFixed(0)}%
            </div>
            <div className="text-[11px] text-slate-400 dark:text-zinc-500 mt-1 flex items-center gap-1.5">
              <RefreshCw className="w-3 h-3 text-emerald-500" />
              <span>{analytics.total_retry_fixed} of {analytics.total_retried} fixed by retry</span>
            </div>
          </div>
        </div>

        {/* Charts Row 1: Route Split & Latency Curve */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Route Split Pie */}
          <div className="bg-white dark:bg-zinc-900 p-6 rounded-2xl border border-slate-200 dark:border-zinc-800 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-semibold text-slate-900 dark:text-zinc-100 flex items-center gap-2">
                <PieIcon className="w-4 h-4 text-indigo-500" />
                Agent Routing Breakdown
              </h3>
              <span className="text-xs text-slate-400">Classification distribution</span>
            </div>

            <div className="h-64 w-full flex items-center justify-center">
              {routeSplitData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={routeSplitData}
                      cx="50%"
                      cy="50%"
                      innerRadius={65}
                      outerRadius={95}
                      paddingAngle={4}
                      dataKey="value"
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    >
                      {routeSplitData.map((_, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#18181b",
                        borderColor: "#27272a",
                        borderRadius: "12px",
                        color: "#f4f4f5",
                        fontSize: "12px",
                      }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <p className="text-xs text-slate-400">No route logs recorded yet</p>
              )}
            </div>
          </div>

          {/* Latency History */}
          <div className="bg-white dark:bg-zinc-900 p-6 rounded-2xl border border-slate-200 dark:border-zinc-800 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-semibold text-slate-900 dark:text-zinc-100 flex items-center gap-2">
                <Clock className="w-4 h-4 text-emerald-500" />
                Recent Query Latency (ms)
              </h3>
              <span className="text-xs text-slate-400">Chronological timeline</span>
            </div>

            <div className="h-64 w-full">
              {latencyTimeline.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={latencyTimeline} margin={{ top: 10, right: 20, left: -20, bottom: 0 }}>
                    <defs>
                      <linearGradient id="latencyGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4} />
                        <stop offset="95%" stopColor="#6366f1" stopOpacity={0.0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" opacity={0.15} />
                    <XAxis dataKey="index" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 11 }} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#18181b",
                        borderColor: "#27272a",
                        borderRadius: "12px",
                        color: "#f4f4f5",
                        fontSize: "12px",
                      }}
                    />
                    <Area
                      type="monotone"
                      dataKey="latency"
                      stroke="#6366f1"
                      strokeWidth={2}
                      fillOpacity={1}
                      fill="url(#latencyGrad)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full flex items-center justify-center text-xs text-slate-400">
                  No latency measurements yet
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Charts Row 2: Top Retrieved Documents */}
        <div className="bg-white dark:bg-zinc-900 p-6 rounded-2xl border border-slate-200 dark:border-zinc-800 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-semibold text-slate-900 dark:text-zinc-100 flex items-center gap-2">
              <Layers className="w-4 h-4 text-indigo-500" />
              Most Cited Documents
            </h3>
            <span className="text-xs text-slate-400">Frequency in RAG answers</span>
          </div>

          <div className="h-64 w-full">
            {topDocsData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={topDocsData} layout="vertical" margin={{ top: 5, right: 30, left: 40, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.15} horizontal={false} />
                  <XAxis type="number" tick={{ fontSize: 11 }} />
                  <YAxis type="category" dataKey="name" tick={{ fontSize: 11 }} width={140} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#18181b",
                      borderColor: "#27272a",
                      borderRadius: "12px",
                      color: "#f4f4f5",
                      fontSize: "12px",
                    }}
                  />
                  <Bar dataKey="citations" fill="#6366f1" radius={[0, 6, 6, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-xs text-slate-400">
                No citations registered yet
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};