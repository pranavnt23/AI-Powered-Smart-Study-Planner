"use client";

import {
  useRef,
  ChangeEvent,
  Dispatch,
  SetStateAction,
  useState,
} from "react";

import { uploadDocument } from "@/lib/upload";

type ChatFooterProps = {
  chatInput: string;
  setChatInput: Dispatch<SetStateAction<string>>;
  onSend: (
    attachmentNames?: {
      name: string;
      content: string | null;
      fileId?: string | null;
    }[]
  ) => Promise<void>;
};

type Attachment = {
  id: string;
  name: string;
  type: string;
  content: string | null;
  fileId: string | null;
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
    case "ppt":
    case "pptx":
      return "PPT";
    case "png":
    case "jpg":
    case "jpeg":
      return "IMG";
    default:
      return "FILE";
  }
};

export function ChatFooter({
  chatInput,
  setChatInput,
  onSend,
}: ChatFooterProps) {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const stopGenerationRef = useRef(false);

  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [loadingMessage, setLoadingMessage] = useState("");
  const [menuOpen, setMenuOpen] = useState(false);
  const [existingFiles, setExistingFiles] = useState<any[]>([]);

  const fetchExistingFiles = async () => {
    try {
      const resp = await fetch("http://127.0.0.1:8000/upload/files?user_id=1");
      if (resp.ok) {
        const data = await resp.json();
        setExistingFiles(data.files || []);
      }
    } catch (err) {
      console.error("Failed to load existing files:", err);
    }
  };

  const attachExistingFile = (file: any) => {
    const isAlreadyAttached = attachments.some(a => a.fileId === file.id);
    if (!isAlreadyAttached) {
      setAttachments(current => [
        ...current,
        {
          id: `${file.file_name}-${crypto.randomUUID()}`,
          name: file.file_name,
          type: file.file_type.replace(".", "").toUpperCase(),
          content: null,
          fileId: file.id
        }
      ]);
    }
    setMenuOpen(false);
  };

  const resizeTextarea = () => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    textarea.style.height = "auto";
    textarea.style.height = `${Math.min(textarea.scrollHeight, 180)}px`;
  };

  const handleTextareaChange = (event: ChangeEvent<HTMLTextAreaElement>) => {
    setChatInput(event.target.value);
    resizeTextarea();
  };

  const openFilePicker = () => {
    if (isLoading) return;
    fileInputRef.current?.click();
  };

  const handleFileSelect = async (event: ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = Array.from(event.target.files ?? []);
    if (selectedFiles.length === 0) return;

    setIsLoading(true);
    setLoadingMessage("Uploading and extracting document content...");
    stopGenerationRef.current = false;

    try {
      const nextAttachments = await Promise.all(
        selectedFiles.map(async (file) => {
          const typeLabel = file.type
            ? file.type.split("/").pop()?.toUpperCase()
            : file.name.split(".").pop()?.toUpperCase();

          try {
            const response = await uploadDocument(file);
            return {
              id: `${file.name}-${crypto.randomUUID()}`,
              name: file.name,
              type: typeLabel ?? "FILE",
              content: response?.content ?? response?.text ?? response?.data?.content ?? null,
              fileId: response?.file_id ?? response?.data?.file_id ?? null,
            };
          } catch {
            return {
              id: `${file.name}-${crypto.randomUUID()}`,
              name: file.name,
              type: typeLabel ?? "FILE",
              content: "Unable to process file",
              fileId: null,
            };
          }
        })
      );

      if (!stopGenerationRef.current) {
        setAttachments((current) => [...current, ...nextAttachments]);
      }
    } finally {
      setIsLoading(false);
      setLoadingMessage("");
      event.target.value = "";
    }
  };

  const removeAttachment = (id: string) => {
    if (isLoading) return;
    setAttachments((current) => current.filter((attachment) => attachment.id !== id));
  };

  const handleSend = async () => {
    if (!chatInput.trim() && attachments.length === 0) return;

    stopGenerationRef.current = false;
    setIsLoading(true);
    setLoadingMessage("AI is generating your response...");

    try {
      await onSend(
        attachments.map((attachment) => ({
          name: attachment.name,
          content: attachment.content,
          fileId: attachment.fileId,
        }))
      );

      if (!stopGenerationRef.current) {
        setAttachments([]);
        setChatInput("");
        if (textareaRef.current) {
          textareaRef.current.style.height = "52px";
        }
      }
    } finally {
      setIsLoading(false);
      setLoadingMessage("");
    }
  };

  const handleStopGenerating = () => {
    stopGenerationRef.current = true;
    setIsLoading(false);
    setLoadingMessage("");
  };

  return (
    <div className="border-t border-slate-800 bg-slate-950">
      {/* ATTACHMENTS */}
      {attachments.length > 0 && (
        <div className="flex gap-2 overflow-x-auto px-3 pt-3 pb-1 scrollbar-none">
          {attachments.map((attachment) => (
            <div
              key={attachment.id}
              className="flex min-w-[200px] items-center gap-3 rounded border border-slate-800 bg-slate-900 p-2.5"
            >
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded bg-slate-950 text-[10px] font-mono font-bold text-slate-400 border border-slate-800">
                {getFileIcon(attachment.name)}
              </div>

              <div className="min-w-0 flex-1">
                <p className="truncate text-xs font-semibold text-white">
                  {attachment.name}
                </p>
                <p className="mt-0.5 text-[10px] text-slate-500">
                  {attachment.type}
                </p>
              </div>

              <button
                type="button"
                onClick={() => removeAttachment(attachment.id)}
                className="flex h-6 w-6 items-center justify-center rounded bg-slate-800 text-slate-400 transition hover:bg-slate-700 text-xs"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      )}

      {/* INPUT AREA */}
      <div className="p-3 sm:p-4">
        <div className="relative rounded-lg border border-slate-800 bg-slate-900 focus-within:border-slate-700 transition">
          <textarea
            ref={textareaRef}
            value={chatInput}
            onChange={handleTextareaChange}
            rows={1}
            disabled={isLoading}
            placeholder="Ask anything about your study plan..."
            className="max-h-[180px] min-h-[52px] w-full resize-none overflow-y-auto bg-transparent px-4 py-3.5 pr-32 text-sm text-white placeholder:text-slate-500 focus:outline-none"
          />

          {/* ACTIONS */}
          <div className="absolute bottom-3 right-3 flex items-center gap-2">
            <div className="relative">
              <button
                type="button"
                onClick={() => {
                  setMenuOpen(!menuOpen);
                  if (!menuOpen) fetchExistingFiles();
                }}
                disabled={isLoading}
                className="flex h-8 w-8 items-center justify-center rounded border border-slate-700 bg-slate-800 text-slate-300 transition hover:bg-slate-700 disabled:opacity-50 text-base"
              >
                +
              </button>

              {menuOpen && (
                <div className="absolute bottom-full right-0 z-50 mb-2 w-64 rounded border border-slate-800 bg-slate-950 p-2 shadow-md max-h-60 overflow-y-auto">
                  <div className="px-3 py-1.5 border-b border-slate-800/60">
                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">File Actions</p>
                  </div>
                  <button
                    type="button"
                    onClick={() => {
                      setMenuOpen(false);
                      openFilePicker();
                    }}
                    className="w-full text-left rounded px-3 py-2 text-xs font-semibold text-white hover:bg-slate-800 transition mb-1"
                  >
                    📎 Upload New File...
                  </button>
                  {existingFiles.length > 0 && (
                    <>
                      <div className="px-3 py-1 border-t border-slate-800/60">
                        <p className="text-[9px] font-bold text-slate-500 uppercase tracking-wider">Attach Existing</p>
                      </div>
                      {existingFiles.map((file) => (
                        <button
                          key={file.id}
                          type="button"
                          onClick={() => attachExistingFile(file)}
                          className="w-full text-left rounded px-3 py-1.5 text-xs text-slate-300 hover:bg-slate-800 truncate transition"
                        >
                          📄 {file.file_name}
                        </button>
                      ))}
                    </>
                  )}
                </div>
              )}
            </div>

            {isLoading ? (
              <button
                type="button"
                onClick={handleStopGenerating}
                className="flex h-8 items-center justify-center rounded border border-red-900/30 bg-red-900/10 px-4 text-xs font-semibold text-red-400 hover:bg-red-900/20 transition"
              >
                Stop
              </button>
            ) : (
              <button
                type="button"
                onClick={handleSend}
                className="flex h-8 items-center justify-center rounded bg-blue-600 hover:bg-blue-700 px-4 text-xs font-semibold text-white transition-colors"
              >
                Send
              </button>
            )}
          </div>
        </div>

        {/* LOADING */}
        {isLoading && (
          <div className="mt-3 flex items-center gap-3 px-2">
            <div className="flex items-center gap-1">
              <span className="h-2 w-2 animate-bounce rounded-full bg-blue-600"></span>
              <span className="h-2 w-2 animate-bounce rounded-full bg-blue-600 [animation-delay:0.15s]"></span>
              <span className="h-2 w-2 animate-bounce rounded-full bg-blue-600 [animation-delay:0.3s]"></span>
            </div>
            <p className="text-sm text-slate-400">
              {loadingMessage}
            </p>
          </div>
        )}
      </div>

      <input
        ref={fileInputRef}
        type="file"
        accept=".txt,.md,.json,.csv,.docx,.doc,.pdf,.ppt,.pptx,.png,.jpg,.jpeg"
        multiple
        className="hidden"
        onChange={handleFileSelect}
      />
    </div>
  );
}