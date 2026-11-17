import React, { useState, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  FileText,
  Upload,
  Search,
  Trash2,
  Eye,
  FileCode,
  Layers,
  Calendar,
  AlertCircle,
  X,
  CheckCircle2,
  Loader2,
} from "lucide-react";
import { apiClient } from "../api/client";
import { DocumentSummary, ChunkInfo } from "../types";
import { cn } from "../lib/utils";

export const DocumentsPage: React.FC = () => {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [searchFilter, setSearchFilter] = useState("");
  const [selectedDoc, setSelectedDoc] = useState<string | null>(null);
  const [deleteConfirmDoc, setDeleteConfirmDoc] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  // Fetch document summaries
  const {
    data: documents = [],
    isLoading,
    error,
  } = useQuery<DocumentSummary[]>({
    queryKey: ["documents"],
    queryFn: () => apiClient.getDocuments(),
  });

  // Fetch chunks for preview drawer
  const {
    data: previewChunks = [],
    isLoading: isLoadingChunks,
  } = useQuery<ChunkInfo[]>({
    queryKey: ["documentChunks", selectedDoc],
    queryFn: () => (selectedDoc ? apiClient.getDocumentChunks(selectedDoc) : Promise.resolve([])),
    enabled: Boolean(selectedDoc),
  });

  // Upload mutation
  const uploadMutation = useMutation({
    mutationFn: (file: File) => apiClient.uploadDocument(file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents"] });
      setUploadError(null);
    },
    onError: (err: Error) => {
      setUploadError(err.message || "Failed to upload document");
    },
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (docName: string) => apiClient.deleteDocument(docName),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents"] });
      setDeleteConfirmDoc(null);
      if (selectedDoc === deleteConfirmDoc) {
        setSelectedDoc(null);
      }
    },
  });

  const handleFileDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    setUploadError(null);

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      const file = files[0];
      validateAndUpload(file);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      validateAndUpload(files[0]);
    }
  };

  const validateAndUpload = (file: File) => {
    const validExtensions = [".pdf", ".docx"];
    const ext = "." + file.name.split(".").pop()?.toLowerCase();
    if (!validExtensions.includes(ext)) {
      setUploadError("Only PDF and DOCX files are supported.");
      return;
    }
    uploadMutation.mutate(file);
  };

  // Filtered documents
  const filteredDocs = documents.filter((doc) =>
    doc.document_name.toLowerCase().includes(searchFilter.toLowerCase())
  );

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden bg-slate-50/50 dark:bg-zinc-950 p-8">
      <div className="max-w-6xl w-full mx-auto flex flex-col h-full space-y-6">
        {/* Header & Overview */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-2xl font-bold text-slate-900 dark:text-zinc-100 tracking-tight">
              Document Knowledge Base
            </h2>
            <p className="text-sm text-slate-500 dark:text-zinc-400 mt-1">
              Synthetic RetailFlow company policies, supplier contracts, and operational reports parsed into 768-dim embeddings.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <span className="text-xs font-semibold px-3 py-1.5 rounded-full bg-indigo-50 text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-400 border border-indigo-200 dark:border-indigo-800">
              {documents.length} Documents Indexed
            </span>
          </div>
        </div>

        {/* Upload Zone */}
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setIsDragging(true);
          }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleFileDrop}
          onClick={() => fileInputRef.current?.click()}
          className={cn(
            "border-2 border-dashed rounded-2xl p-6 text-center cursor-pointer transition-all flex flex-col items-center justify-center",
            isDragging
              ? "border-indigo-500 bg-indigo-50/50 dark:bg-indigo-950/20 shadow-md"
              : "border-slate-300 dark:border-zinc-800 hover:border-indigo-400 dark:hover:border-indigo-600 bg-white dark:bg-zinc-900/60"
          )}
        >
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileSelect}
            accept=".pdf,.docx"
            className="hidden"
          />

          <div className="w-12 h-12 rounded-xl bg-indigo-100 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400 flex items-center justify-center mb-3">
            {uploadMutation.isPending ? (
              <Loader2 className="w-6 h-6 animate-spin" />
            ) : (
              <Upload className="w-6 h-6" />
            )}
          </div>

          <p className="text-sm font-semibold text-slate-800 dark:text-zinc-200">
            {uploadMutation.isPending
              ? "Parsing, chunking and embedding document..."
              : "Click to upload or drag and drop"}
          </p>
          <p className="text-xs text-slate-500 dark:text-zinc-400 mt-1">
            Supported formats: PDF, DOCX (Max 10MB)
          </p>

          {uploadError && (
            <div className="mt-3 flex items-center gap-2 text-xs font-medium text-rose-600 dark:text-rose-400 bg-rose-50 dark:bg-rose-950/40 px-3 py-1.5 rounded-lg border border-rose-200 dark:border-rose-900">
              <AlertCircle className="w-4 h-4" />
              <span>{uploadError}</span>
            </div>
          )}

          {uploadMutation.isSuccess && (
            <div className="mt-3 flex items-center gap-2 text-xs font-medium text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/40 px-3 py-1.5 rounded-lg border border-emerald-200 dark:border-emerald-900">
              <CheckCircle2 className="w-4 h-4" />
              <span>Document indexed successfully!</span>
            </div>
          )}
        </div>

        {/* Filter and Search Bar */}
        <div className="flex items-center justify-between gap-4">
          <div className="relative flex-1 max-w-md">
            <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search documents by name..."
              value={searchFilter}
              onChange={(e) => setSearchFilter(e.target.value)}
              className="w-full pl-10 pr-4 py-2 text-sm rounded-xl border border-slate-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 text-slate-900 dark:text-zinc-100 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all"
            />
          </div>
          <span className="text-xs text-slate-500 dark:text-zinc-400 font-medium">
            Showing {filteredDocs.length} of {documents.length}
          </span>
        </div>

        {/* Documents Table */}
        <div className="flex-1 overflow-auto bg-white dark:bg-zinc-900 rounded-2xl border border-slate-200 dark:border-zinc-800 shadow-sm">
          {isLoading ? (
            <div className="p-12 flex flex-col items-center justify-center text-slate-400">
              <Loader2 className="w-8 h-8 animate-spin mb-3 text-indigo-500" />
              <p className="text-sm">Loading document catalog...</p>
            </div>
          ) : error ? (
            <div className="p-8 text-center text-rose-500 text-sm">
              Failed to load documents. Please check backend connectivity.
            </div>
          ) : filteredDocs.length === 0 ? (
            <div className="p-12 text-center text-slate-400">
              <FileText className="w-12 h-12 mx-auto stroke-[1.2] mb-3 text-slate-300 dark:text-zinc-700" />
              <p className="text-sm font-medium text-slate-600 dark:text-zinc-400">
                No documents found matching your filter
              </p>
            </div>
          ) : (
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-100 dark:border-zinc-800 text-[12px] font-semibold text-slate-500 dark:text-zinc-400 uppercase tracking-wider bg-slate-50/50 dark:bg-zinc-800/40">
                  <th className="py-3 px-5">Document Name</th>
                  <th className="py-3 px-5">Type</th>
                  <th className="py-3 px-5">Pages</th>
                  <th className="py-3 px-5">Chunks</th>
                  <th className="py-3 px-5">Indexed At</th>
                  <th className="py-3 px-5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-zinc-800 text-sm">
                {filteredDocs.map((doc) => {
                  const isPdf = doc.file_type.toLowerCase() === "pdf";
                  return (
                    <tr
                      key={doc.document_name}
                      className="hover:bg-slate-50/80 dark:hover:bg-zinc-800/40 transition-colors group"
                    >
                      <td className="py-3.5 px-5 font-medium text-slate-900 dark:text-zinc-100 flex items-center gap-3">
                        <div
                          className={cn(
                            "w-8 h-8 rounded-lg flex items-center justify-center shrink-0",
                            isPdf
                              ? "bg-rose-50 dark:bg-rose-950/40 text-rose-600 dark:text-rose-400"
                              : "bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400"
                          )}
                        >
                          {isPdf ? (
                            <FileText className="w-4 h-4" />
                          ) : (
                            <FileCode className="w-4 h-4" />
                          )}
                        </div>
                        <span className="truncate max-w-md">{doc.document_name}</span>
                      </td>

                      <td className="py-3.5 px-5">
                        <span
                          className={cn(
                            "inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold uppercase tracking-wider",
                            isPdf
                              ? "bg-rose-100/70 text-rose-700 dark:bg-rose-900/40 dark:text-rose-300"
                              : "bg-blue-100/70 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300"
                          )}
                        >
                          {doc.file_type}
                        </span>
                      </td>

                      <td className="py-3.5 px-5 text-slate-600 dark:text-zinc-400 font-mono text-xs">
                        {doc.total_pages} {doc.total_pages === 1 ? "page" : "pages"}
                      </td>

                      <td className="py-3.5 px-5">
                        <div className="flex items-center gap-1.5 text-slate-600 dark:text-zinc-400 text-xs">
                          <Layers className="w-3.5 h-3.5 text-indigo-500" />
                          <span className="font-mono font-medium">{doc.total_chunks}</span>
                        </div>
                      </td>

                      <td className="py-3.5 px-5 text-slate-500 dark:text-zinc-400 text-xs">
                        <div className="flex items-center gap-1.5">
                          <Calendar className="w-3.5 h-3.5 text-slate-400" />
                          <span>
                            {doc.created_at
                              ? new Date(doc.created_at).toLocaleDateString()
                              : "Initial Batch"}
                          </span>
                        </div>
                      </td>

                      <td className="py-3.5 px-5 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={() => setSelectedDoc(doc.document_name)}
                            className="p-1.5 rounded-lg text-slate-500 hover:text-indigo-600 hover:bg-indigo-50 dark:text-zinc-400 dark:hover:text-indigo-400 dark:hover:bg-zinc-800 transition-colors"
                            title="Preview chunks"
                          >
                            <Eye className="w-4 h-4" />
                          </button>

                          <button
                            onClick={() => setDeleteConfirmDoc(doc.document_name)}
                            className="p-1.5 rounded-lg text-slate-500 hover:text-rose-600 hover:bg-rose-50 dark:text-zinc-400 dark:hover:text-rose-400 dark:hover:bg-zinc-800 transition-colors"
                            title="Delete document"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      {deleteConfirmDoc && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white dark:bg-zinc-900 rounded-2xl max-w-md w-full p-6 border border-slate-200 dark:border-zinc-800 shadow-xl space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-rose-100 dark:bg-rose-950/60 text-rose-600 flex items-center justify-center">
                <AlertCircle className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-semibold text-slate-900 dark:text-zinc-100">
                  Delete Document?
                </h3>
                <p className="text-xs text-slate-500 dark:text-zinc-400">
                  This will remove all associated chunk embeddings from pgvector.
                </p>
              </div>
            </div>

            <p className="text-sm text-slate-700 dark:text-zinc-300 font-mono bg-slate-50 dark:bg-zinc-800/60 p-2.5 rounded-lg break-all">
              {deleteConfirmDoc}
            </p>

            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                onClick={() => setDeleteConfirmDoc(null)}
                className="px-4 py-2 rounded-xl text-sm font-medium text-slate-600 dark:text-zinc-400 hover:bg-slate-100 dark:hover:bg-zinc-800 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => deleteMutation.mutate(deleteConfirmDoc)}
                disabled={deleteMutation.isPending}
                className="px-4 py-2 rounded-xl text-sm font-medium bg-rose-600 hover:bg-rose-700 text-white shadow-sm transition-colors flex items-center gap-2"
              >
                {deleteMutation.isPending && <Loader2 className="w-4 h-4 animate-spin" />}
                Delete
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Preview Chunks Drawer */}
      {selectedDoc && (
        <div className="fixed inset-0 z-50 overflow-hidden bg-black/40 backdrop-blur-xs flex justify-end">
          <div className="w-full max-w-xl bg-white dark:bg-zinc-900 h-full shadow-2xl flex flex-col border-l border-slate-200 dark:border-zinc-800">
            {/* Drawer Header */}
            <div className="p-6 border-b border-slate-100 dark:border-zinc-800 flex items-center justify-between">
              <div>
                <span className="text-xs font-semibold text-indigo-600 dark:text-indigo-400 uppercase tracking-wider">
                  Document Preview
                </span>
                <h3 className="text-lg font-bold text-slate-900 dark:text-zinc-100 truncate max-w-md">
                  {selectedDoc}
                </h3>
              </div>
              <button
                onClick={() => setSelectedDoc(null)}
                className="p-2 rounded-xl text-slate-400 hover:text-slate-600 dark:hover:text-zinc-200 hover:bg-slate-100 dark:hover:bg-zinc-800 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Chunks List */}
            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              {isLoadingChunks ? (
                <div className="p-12 flex flex-col items-center justify-center text-slate-400">
                  <Loader2 className="w-7 h-7 animate-spin text-indigo-500 mb-2" />
                  <p className="text-xs">Fetching chunk segments...</p>
                </div>
              ) : previewChunks.length === 0 ? (
                <div className="p-8 text-center text-slate-400 text-sm">
                  No chunk details available.
                </div>
              ) : (
                previewChunks.map((chunk, index) => (
                  <div
                    key={chunk.chunk_id || index}
                    className="p-4 rounded-xl border border-slate-200 dark:border-zinc-800 bg-slate-50/50 dark:bg-zinc-800/40 space-y-2"
                  >
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-semibold text-indigo-600 dark:text-indigo-400">
                        {chunk.section_title || "Section"}
                      </span>
                      <span className="font-mono text-slate-400 dark:text-zinc-500">
                        Page {chunk.page_number} • Chunk {chunk.chunk_index}
                      </span>
                    </div>
                    <p className="text-xs text-slate-700 dark:text-zinc-300 leading-relaxed font-sans whitespace-pre-wrap">
                      {chunk.content}
                    </p>
                    <div className="pt-1 text-[10px] text-slate-400 dark:text-zinc-500 font-mono">
                      ID: {chunk.chunk_id}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};