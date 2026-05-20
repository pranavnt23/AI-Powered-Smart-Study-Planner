"use client";

import { useRef, ChangeEvent, Dispatch, SetStateAction, useState } from "react";

type ChatFooterProps = {
  chatInput: string;
  setChatInput: Dispatch<SetStateAction<string>>;
  onSend: (attachmentNames?: string[]) => void;
};

type Attachment = {
  id: string;
  name: string;
  type: string;
  content: string | null;
};

const getFileIcon = (name: string) => {
  const extension = name.split(".").pop()?.toLowerCase();

  switch (extension) {
    case "pdf":
      return "PDF";
    case "doc":
    case "docx":
      return "DOC";
    case "txt":
      return "TXT";
    case "csv":
      return "CSV";
    case "md":
      return "MD";
    default:
      return "FILE";
  }
};

export function ChatFooter({ chatInput, setChatInput, onSend }: ChatFooterProps) {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [attachments, setAttachments] = useState<Attachment[]>([]);

  const openFilePicker = () => {
    fileInputRef.current?.click();
  };

  const handleFileSelect = async (event: ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = Array.from(event.target.files ?? []);
    if (selectedFiles.length === 0) return;

    const nextAttachments = await Promise.all(
      selectedFiles.map(async (file) => {
        const typeLabel = file.type
          ? file.type.split("/").pop()?.toUpperCase()
          : file.name.split(".").pop()?.toUpperCase();

        try {
          const text = await file.text();

          return {
            id: `${file.name}-${file.lastModified}-${crypto.randomUUID()}`,
            name: file.name,
            type: typeLabel ?? "File",
            content: text,
          };
        } catch {
          return {
            id: `${file.name}-${file.lastModified}-${crypto.randomUUID()}`,
            name: file.name,
            type: typeLabel ?? "File",
            content: null,
          };
        }
      })
    );

    setAttachments((current) => [...current, ...nextAttachments]);
    event.target.value = "";
  };

  const removeAttachment = (id: string) => {
    setAttachments((current) => current.filter((attachment) => attachment.id !== id));
  };

  const handleSend = () => {
    if (!chatInput.trim() && attachments.length === 0) return;

    onSend(attachments.map((attachment) => attachment.name));
    setAttachments([]);
  };

  return (
    <div className="sticky bottom-0 z-10 rounded-[30px] border border-white/10 bg-slate-900/95 p-5 shadow-[0_-8px_30px_-20px_rgba(15,23,42,0.95)] backdrop-blur-xl">
      {attachments.length > 0 ? (
        <div className="mb-4 grid gap-3 sm:grid-cols-2">
          {attachments.map((attachment) => (
            <div
              key={attachment.id}
              className="flex items-center justify-between gap-4 rounded-3xl border border-white/10 bg-slate-950/90 px-4 py-3"
            >
              <div className="flex min-w-0 items-center gap-3">
                <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-cyan-400/10 text-xs font-bold text-cyan-300 shadow-sm">
                  {getFileIcon(attachment.name)}
                </div>
                <div className="min-w-0">
                  <p className="truncate text-sm font-semibold text-white">{attachment.name}</p>
                  <p className="mt-1 text-xs text-slate-500">
                    {attachment.type}
                    {attachment.content === null ? " preview unavailable" : ""}
                  </p>
                </div>
              </div>

              <button
                type="button"
                onClick={() => removeAttachment(attachment.id)}
                className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-white/10 bg-white/5 text-slate-300 transition hover:bg-white/10"
                aria-label={`Remove ${attachment.name}`}
              >
                x
              </button>
            </div>
          ))}
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
            aria-label="Upload documents"
          >
            +
          </button>

          <button
            type="button"
            onClick={handleSend}
            className="inline-flex h-11 items-center justify-center rounded-3xl bg-gradient-to-r from-indigo-500 to-cyan-400 px-5 text-sm font-semibold text-slate-950 shadow-xl shadow-cyan-500/20 transition-all duration-200 hover:scale-[1.01]"
          >
            Send
          </button>
        </div>
      </div>

      <input
        ref={fileInputRef}
        type="file"
        accept=".txt,.md,.json,.csv,.docx,.doc,.pdf"
        multiple
        className="hidden"
        onChange={handleFileSelect}
      />
    </div>
  );
}
