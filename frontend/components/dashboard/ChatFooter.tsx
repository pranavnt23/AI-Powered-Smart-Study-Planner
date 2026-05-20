"use client";

import { useRef, ChangeEvent, Dispatch, SetStateAction, useState } from "react";

type ChatFooterProps = {
  chatInput: string;
  setChatInput: Dispatch<SetStateAction<string>>;
  onSend: () => void;
};

const getFileIcon = (name: string) => {
  const extension = name.split(".").pop()?.toLowerCase();
  switch (extension) {
    case "pdf":
      return "📄";
    case "doc":
    case "docx":
      return "📄";
    case "txt":
      return "📝";
    case "csv":
      return "📑";
    case "md":
      return "📝";
    default:
      return "📎";
  }
};

export function ChatFooter({ chatInput, setChatInput, onSend }: ChatFooterProps) {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const [fileType, setFileType] = useState<string | null>(null);
  const [fileContent, setFileContent] = useState<string | null>(null);

  const openFilePicker = () => {
    fileInputRef.current?.click();
  };

  const handleFileSelect = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const typeLabel = file.type ? file.type.split("/").pop()?.toUpperCase() : file.name.split(".").pop()?.toUpperCase();

    try {
      const text = await file.text();
      setFileName(file.name);
      setFileType(typeLabel ?? "File");
      setFileContent(text);
    } catch {
      setFileName(file.name);
      setFileType(typeLabel ?? "File");
      setFileContent(null);
    } finally {
      event.target.value = "";
    }
  };

  const clearFile = () => {
    setFileName(null);
    setFileType(null);
    setFileContent(null);
  };

  return (
    <div className="sticky bottom-0 z-10 rounded-[30px] border border-white/10 bg-slate-900/95 p-5 shadow-[0_-8px_30px_-20px_rgba(15,23,42,0.95)] backdrop-blur-xl">
      {fileName ? (
        <div className="mb-4 flex items-center justify-between gap-4 rounded-3xl border border-white/10 bg-slate-950/90 px-4 py-3">
          <div className="flex items-center gap-3 min-w-0">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-cyan-400/10 text-cyan-300 text-xl shadow-sm">
              {getFileIcon(fileName)}
            </div>
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold text-white">{fileName}</p>
              <p className="mt-1 text-xs text-slate-500">{fileType}</p>
            </div>
          </div>
          <button
            type="button"
            onClick={clearFile}
            className="inline-flex h-10 w-10 items-center justify-center rounded-full border border-white/10 bg-white/5 text-slate-300 transition hover:bg-white/10"
            aria-label="Remove uploaded document"
          >
            ×
          </button>
        </div>
      ) : null}

      <div className="relative">
        <textarea
          value={chatInput}
          onChange={(event) => setChatInput(event.target.value)}
          placeholder="Ask anything"
          className="min-h-[120px] w-full rounded-[28px] border border-white/10 bg-slate-950/80 px-4 py-4 pr-28 text-slate-100 placeholder:text-slate-500 focus:border-cyan-400 focus:outline-none focus:ring-2 focus:ring-cyan-400/20"
        />

        <div className="absolute bottom-4 right-4 flex items-center gap-3">
          <button
            type="button"
            onClick={openFilePicker}
            className="inline-flex h-11 items-center justify-center rounded-3xl border border-white/10 bg-white/5 px-4 text-sm font-semibold text-cyan-300 transition hover:bg-white/10"
          >
            +
          </button>
          <button
            type="button"
            onClick={onSend}
            className="inline-flex h-11 items-center justify-center rounded-3xl bg-gradient-to-r from-indigo-500 to-cyan-400 px-5 text-sm font-semibold text-slate-950 shadow-xl shadow-cyan-500/20 transition-all duration-200 hover:scale-[1.01]"
          >
            <span className="mr-2 hidden sm:inline">Send</span>
            ↵
          </button>
        </div>
      </div>

      <input
        ref={fileInputRef}
        type="file"
        accept=".txt,.md,.json,.csv,.docx,.doc,.pdf"
        className="hidden"
        onChange={handleFileSelect}
      />
    </div>
  );
}
