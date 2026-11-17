import React, { useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { ArrowUp, Bot, FileText, Loader2, Sparkles, User } from "lucide-react";
import { apiClient } from "../api/client";
import { CitationDrawer } from "../components/CitationDrawer";
import { HowIAnsweredPanel } from "../components/HowIAnsweredPanel";
import { ChatMessage, Citation } from "../types";

const SUGGESTED_QUESTIONS = [
  "What are the late delivery penalties for supplier Apex (6560211a19b4)?",
  "What are the top 5 product categories by revenue in the database?",
  "What photographic evidence is required for damaged goods refunds?",
  "Calculate the late delivery penalties for seller Apex (6560211a19b4) across delayed orders.",
  "Which 3 cities have the highest concentration of customers?",
];

export const ChatPage: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>(() => {
    const saved = localStorage.getItem("querydesk_chat_history");
    return saved ? JSON.parse(saved) : [];
  });
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null);
  const [currentSteps, setCurrentSteps] = useState<string[]>([]);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  React.useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  React.useEffect(() => {
    localStorage.setItem("querydesk_chat_history", JSON.stringify(messages));
  }, [messages]);

  const handleSend = async (queryText?: string) => {
    const textToSend = queryText || input;
    if (!textToSend.trim() || isLoading) return;

    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: textToSend.trim(),
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsLoading(true);
    setCurrentSteps(["Decomposing query", "Routing to specialized agent"]);

    try {
      const response = await apiClient.sendChat(textToSend.trim());
      setMessages((prev) => [...prev, response]);
    } catch (err) {
      const errorMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: `Error: ${err instanceof Error ? err.message : "Failed to generate answer"}`,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
      setCurrentSteps([]);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex-1 flex flex-col h-[calc(100vh-4rem)] max-w-4xl mx-auto w-full px-4 py-6">
      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto space-y-6 pb-6">
        {messages.length === 0 ? (
          /* Empty State */
          <div className="h-full flex flex-col items-center justify-center text-center p-8 max-w-xl mx-auto my-auto">
            <div className="h-12 w-12 rounded-2xl bg-indigo-50 dark:bg-indigo-950/50 flex items-center justify-center text-indigo-600 dark:text-indigo-400 mb-4 shadow-sm border border-indigo-100 dark:border-indigo-900/50">
              <Sparkles className="h-6 w-6" />
            </div>
            <h2 className="text-xl font-semibold text-slate-900 dark:text-zinc-100 tracking-tight">
              Ask RetailFlow Intelligence
            </h2>
            <p className="text-sm text-slate-500 dark:text-zinc-400 mt-1 mb-8">
              Seamlessly query across relational database metrics and unstructured company policies with auditable citations.
            </p>

            <div className="w-full space-y-2">
              <span className="text-xs font-semibold uppercase text-slate-400 dark:text-zinc-500 tracking-wider block text-left mb-2">
                Suggested business inquiries
              </span>
              {SUGGESTED_QUESTIONS.map((q, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSend(q)}
                  className="w-full text-left p-3 rounded-xl border border-slate-200/80 dark:border-zinc-800 bg-white dark:bg-zinc-900/70 hover:border-indigo-500/50 hover:bg-slate-50/80 dark:hover:bg-zinc-800/60 text-xs text-slate-700 dark:text-zinc-300 font-medium transition-all shadow-xs"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        ) : (
          /* Message List */
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex gap-3.5 ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              {msg.role === "assistant" && (
                <div className="h-8 w-8 rounded-xl bg-indigo-600 flex items-center justify-center text-white shrink-0 mt-0.5 shadow-sm">
                  <Bot className="h-4 w-4" />
                </div>
              )}

              <div
                className={`max-w-[85%] rounded-2xl p-4.5 ${
                  msg.role === "user"
                    ? "bg-indigo-600 text-white shadow-sm"
                    : "bg-white dark:bg-zinc-900 border border-slate-200/80 dark:border-zinc-800 text-slate-900 dark:text-zinc-100 shadow-xs"
                }`}
              >
                {/* Message Body */}
                <div className="prose prose-sm dark:prose-invert max-w-none text-xs leading-relaxed">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {msg.content}
                  </ReactMarkdown>
                </div>

                {/* Sources Row (Assistant only) */}
                {msg.role === "assistant" && msg.citations && msg.citations.length > 0 && (
                  <div className="mt-3.5 pt-3 border-t border-slate-100 dark:border-zinc-800/80">
                    <span className="text-[11px] font-semibold text-slate-400 dark:text-zinc-500 uppercase tracking-wider block mb-2">
                      Sources & Citations
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {msg.citations.map((c, cIdx) => (
                        <button
                          key={cIdx}
                          onClick={() => setSelectedCitation(c)}
                          className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-indigo-50/80 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-400 border border-indigo-200/60 dark:border-indigo-800/50 text-[11px] font-medium hover:bg-indigo-100 dark:hover:bg-indigo-900/50 transition-colors"
                        >
                          <FileText className="h-3 w-3 shrink-0" />
                          <span className="truncate max-w-[180px]">{c.document}</span>
                          <span className="text-indigo-400 dark:text-indigo-500 font-mono text-[10px]">
                            p.{c.page}
                          </span>
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* How I Answered Panel (Assistant only) */}
                {msg.role === "assistant" && msg.agentPath && (
                  <HowIAnsweredPanel
                    agentPath={msg.agentPath}
                    sqlQuery={msg.sqlQuery}
                    sqlRows={msg.sqlRows}
                    verificationPassed={msg.verificationPassed}
                    retried={msg.retried}
                    retryFixed={msg.retryFixed}
                    executionSteps={msg.executionSteps}
                    latencyMs={msg.latencyMs}
                  />
                )}
              </div>

              {msg.role === "user" && (
                <div className="h-8 w-8 rounded-xl bg-slate-200 dark:bg-zinc-800 flex items-center justify-center text-slate-600 dark:text-zinc-300 shrink-0 mt-0.5">
                  <User className="h-4 w-4" />
                </div>
              )}
            </div>
          ))
        )}

        {/* Loading Indicator */}
        {isLoading && (
          <div className="flex gap-3.5">
            <div className="h-8 w-8 rounded-xl bg-indigo-600 flex items-center justify-center text-white shrink-0 mt-0.5">
              <Bot className="h-4 w-4" />
            </div>
            <div className="bg-white dark:bg-zinc-900 border border-slate-200/80 dark:border-zinc-800 rounded-2xl p-4 shadow-xs space-y-2">
              <div className="flex items-center gap-2 text-xs font-medium text-slate-600 dark:text-zinc-300">
                <Loader2 className="h-3.5 w-3.5 animate-spin text-indigo-600 dark:text-indigo-400" />
                <span>Thinking and analyzing...</span>
              </div>
              {currentSteps.length > 0 && (
                <div className="flex gap-1.5 flex-wrap">
                  {currentSteps.map((s, i) => (
                    <span
                      key={i}
                      className="px-2 py-0.5 rounded-md bg-slate-100 dark:bg-zinc-800 text-[10px] text-slate-500 font-mono"
                    >
                      {s}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Box */}
      <div className="pt-2">
        <div className="relative rounded-2xl border border-slate-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-sm focus-within:border-indigo-500 focus-within:ring-2 focus-within:ring-indigo-500/20 transition-all p-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question across RetailFlow documents or SQL database..."
            className="w-full resize-none border-0 bg-transparent p-2 text-xs text-slate-900 dark:text-zinc-100 placeholder:text-slate-400 focus:outline-none min-h-[48px] max-h-32"
            rows={2}
          />
          <div className="flex items-center justify-between pt-1 px-1">
            <span className="text-[10px] text-slate-400">
              Shift + Enter for new line • Enter to submit
            </span>
            <button
              onClick={() => handleSend()}
              disabled={!input.trim() || isLoading}
              className="h-8 w-8 rounded-xl bg-indigo-600 hover:bg-indigo-700 disabled:opacity-40 text-white flex items-center justify-center transition-colors shadow-xs"
              aria-label="Send message"
            >
              <ArrowUp className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Citation Slide-over Drawer */}
      <CitationDrawer
        citation={selectedCitation}
        isOpen={selectedCitation !== null}
        onClose={() => setSelectedCitation(null)}
      />
    </div>
  );
};
