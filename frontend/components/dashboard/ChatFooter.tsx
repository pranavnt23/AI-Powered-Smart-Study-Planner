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
    }[]
  ) => Promise<void>;
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

  const resizeTextarea = () => {
    const textarea = textareaRef.current;

    if (!textarea) return;

    textarea.style.height = "auto";

    textarea.style.height = `${Math.min(
      textarea.scrollHeight,
      180
    )}px`;
  };

  const handleTextareaChange = (
    event: ChangeEvent<HTMLTextAreaElement>
  ) => {
    setChatInput(event.target.value);

    resizeTextarea();
  };

  const openFilePicker = () => {
    if (isLoading) return;

    fileInputRef.current?.click();
  };

  const handleFileSelect = async (
    event: ChangeEvent<HTMLInputElement>
  ) => {
    const selectedFiles = Array.from(event.target.files ?? []);

    if (selectedFiles.length === 0) return;

    setIsLoading(true);

    setLoadingMessage(
      "Uploading and extracting document content..."
    );

    stopGenerationRef.current = false;

    try {
      const nextAttachments = await Promise.all(
        selectedFiles.map(async (file) => {
          const typeLabel = file.type
            ? file.type.split("/").pop()?.toUpperCase()
            : file.name
                .split(".")
                .pop()
                ?.toUpperCase();

          try {
            const response = await uploadDocument(file);

            return {
              id: `${file.name}-${crypto.randomUUID()}`,
              name: file.name,
              type: typeLabel ?? "FILE",
              content:
                response?.content ??
                response?.text ??
                response?.data?.content ??
                null,
            };
          } catch {
            return {
              id: `${file.name}-${crypto.randomUUID()}`,
              name: file.name,
              type: typeLabel ?? "FILE",
              content: "Unable to process file",
            };
          }
        })
      );

      if (!stopGenerationRef.current) {
        setAttachments((current) => [
          ...current,
          ...nextAttachments,
        ]);
      }
    } finally {
      setIsLoading(false);

      setLoadingMessage("");

      event.target.value = "";
    }
  };

  const removeAttachment = (id: string) => {
    if (isLoading) return;

    setAttachments((current) =>
      current.filter(
        (attachment) => attachment.id !== id
      )
    );
  };

  const handleSend = async () => {
    if (
      !chatInput.trim() &&
      attachments.length === 0
    )
      return;

    stopGenerationRef.current = false;

    setIsLoading(true);

    setLoadingMessage(
      "AI is generating your response..."
    );

    try {
      await onSend(
        attachments.map((attachment) => ({
          name: attachment.name,
          content: attachment.content,
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
    <div className="border-t border-white/10 bg-slate-950/95 backdrop-blur-xl">

      {/* ATTACHMENTS */}

      {attachments.length > 0 && (
        <div className="flex gap-3 overflow-x-auto px-3 pt-3 pb-1 scrollbar-thin scrollbar-thumb-cyan-400/40">

          {attachments.map((attachment) => (
            <div
              key={attachment.id}
              className="flex min-w-[220px] items-center gap-3 rounded-2xl border border-white/10 bg-slate-900/90 p-3"
            >
              <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-cyan-400/10 text-xs font-bold text-cyan-300">
                {getFileIcon(attachment.name)}
              </div>

              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-semibold text-white">
                  {attachment.name}
                </p>

                <p className="mt-1 text-xs text-slate-500">
                  {attachment.type}
                </p>
              </div>

              <button
                type="button"
                onClick={() =>
                  removeAttachment(attachment.id)
                }
                className="flex h-8 w-8 items-center justify-center rounded-full bg-white/5 text-slate-400 transition hover:bg-white/10"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      )}

      {/* INPUT AREA */}

      <div className="p-3 sm:p-4">

        <div className="relative rounded-3xl border border-white/10 bg-slate-900/90 shadow-2xl">

          <textarea
            ref={textareaRef}
            value={chatInput}
            onChange={handleTextareaChange}
            rows={1}
            disabled={isLoading}
            placeholder="Ask anything about your study plan..."
            className="max-h-[180px] min-h-[52px] w-full resize-none overflow-y-auto bg-transparent px-4 py-4 pr-32 text-sm text-white placeholder:text-slate-500 focus:outline-none"
          />

          {/* ACTIONS */}

          <div className="absolute bottom-3 right-3 flex items-center gap-2">

            <button
              type="button"
              onClick={openFilePicker}
              disabled={isLoading}
              className="flex h-10 w-10 items-center justify-center rounded-full border border-white/10 bg-white/5 text-cyan-300 transition hover:bg-white/10 disabled:opacity-50"
            >
              +
            </button>

            {isLoading ? (
              <button
                type="button"
                onClick={handleStopGenerating}
                className="flex h-10 items-center justify-center rounded-full border border-red-400/20 bg-red-500/10 px-4 text-sm font-semibold text-red-300 transition hover:bg-red-500/20"
              >
                Stop
              </button>
            ) : (
              <button
                type="button"
                onClick={handleSend}
                className="flex h-10 items-center justify-center rounded-full bg-gradient-to-r from-indigo-500 to-cyan-400 px-5 text-sm font-semibold text-slate-950 transition hover:scale-[1.02]"
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

              <span className="h-2 w-2 animate-bounce rounded-full bg-cyan-300"></span>

              <span className="h-2 w-2 animate-bounce rounded-full bg-cyan-300 [animation-delay:0.15s]"></span>

              <span className="h-2 w-2 animate-bounce rounded-full bg-cyan-300 [animation-delay:0.3s]"></span>

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