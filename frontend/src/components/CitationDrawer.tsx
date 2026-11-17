import React from "react";
import { Check, Copy, FileText, X } from "lucide-react";
import { Citation } from "../types";

interface CitationDrawerProps {
  citation: Citation | null;
  isOpen: boolean;
  onClose: () => void;
}

export const CitationDrawer: React.FC<CitationDrawerProps> = ({ citation, isOpen, onClose }) => {
  const [copied, setCopied] = React.useState(false);

  if (!isOpen || !citation) return null;

  const handleCopy = () => {
    if (citation.snippet) {
      navigator.clipboard.writeText(citation.snippet);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-slate-900/30 backdrop-blur-xs flex justify-end">
      <div className="w-full max-w-lg bg-white dark:bg-zinc-900 h-full shadow-2xl border-l border-slate-200 dark:border-zinc-800 flex flex-col animate-in slide-in-from-right duration-200">
        {/* Header */}
        <div className="p-6 border-b border-slate-100 dark:border-zinc-800 flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-indigo-50 dark:bg-indigo-950/40 text-indigo-600 dark:text-indigo-400">
              <FileText className="h-5 w-5" />
            </div>
            <div>
              <h3 className="font-semibold text-slate-900 dark:text-zinc-100 text-sm">
                Document Source
              </h3>
              <p className="text-xs text-slate-500 dark:text-zinc-400 truncate max-w-xs">
                {citation.document}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-zinc-200 hover:bg-slate-100 dark:hover:bg-zinc-800"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 flex-1 overflow-y-auto space-y-6">
          {/* Metadata badges */}
          <div className="grid grid-cols-2 gap-3">
            <div className="p-3 bg-slate-50 dark:bg-zinc-800/60 rounded-xl border border-slate-100 dark:border-zinc-700/50">
              <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider block">
                Section
              </span>
              <span className="text-xs font-semibold text-slate-800 dark:text-zinc-200 block truncate mt-0.5">
                {citation.section || "General"}
              </span>
            </div>
            <div className="p-3 bg-slate-50 dark:bg-zinc-800/60 rounded-xl border border-slate-100 dark:border-zinc-700/50">
              <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider block">
                Page Number
              </span>
              <span className="text-xs font-semibold text-slate-800 dark:text-zinc-200 block mt-0.5">
                Page {citation.page}
              </span>
            </div>
          </div>

          {/* Exact Text Chunk */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-semibold text-slate-700 dark:text-zinc-300">
                Verified Chunk Excerpt
              </label>
              <button
                onClick={handleCopy}
                className="flex items-center gap-1.5 text-xs text-indigo-600 dark:text-indigo-400 hover:underline"
              >
                {copied ? <Check className="h-3.5 w-3.5 text-emerald-500" /> : <Copy className="h-3.5 w-3.5" />}
                <span>{copied ? "Copied" : "Copy text"}</span>
              </button>
            </div>
            <div className="p-4 rounded-xl bg-slate-50 dark:bg-zinc-800/80 border border-slate-200/80 dark:border-zinc-700/70 text-xs text-slate-700 dark:text-zinc-300 leading-relaxed font-mono">
              {citation.snippet || "Full content chunk loaded directly from vector storage."}
            </div>
          </div>

          {/* Chunk ID */}
          <div className="pt-2">
            <span className="text-[11px] text-slate-400 block font-mono">
              Chunk ID: {citation.chunk_id}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
