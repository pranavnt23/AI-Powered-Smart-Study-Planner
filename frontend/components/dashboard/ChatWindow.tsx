"use client";

import { ChatConversation, CitationInfo } from "./types";

type ChatWindowProps = {
  selectedChat: ChatConversation;
};

const parseMarkdown = (rawText: string): string => {
  let escaped = rawText
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  // 1. Temporarily extract code blocks to protect them from line-break modifications
  const codeBlocks: string[] = [];
  escaped = escaped.replace(/```([\s\S]*?)```/g, (match, code) => {
    const placeholder = `__CODE_BLOCK_${codeBlocks.length}__`;
    codeBlocks.push(
      `<pre class="bg-slate-950 border border-slate-800 rounded-md p-3 my-3 overflow-x-auto"><code class="font-mono text-xs text-slate-300">${code}</code></pre>`
    );
    return placeholder;
  });

  // 2. Setext headers (Header Text\n=== or Header Text\n---)
  escaped = escaped.replace(/^(.*?)\r?\n={3,}\s*$/gm, '<h2 class="text-lg font-bold text-white mt-4 mb-2">$1</h2>');
  escaped = escaped.replace(/^(.*?)\r?\n-{3,}\s*$/gm, '<h3 class="text-base font-bold text-slate-100 mt-3 mb-2">$1</h3>');

  // 3. ATX headers (# Header)
  escaped = escaped.replace(/^### (.*?)$/gm, '<h4 class="text-sm font-bold text-slate-200 mt-3 mb-1">$1</h4>');
  escaped = escaped.replace(/^## (.*?)$/gm, '<h3 class="text-base font-bold text-slate-100 mt-4 mb-2">$1</h3>');
  escaped = escaped.replace(/^# (.*?)$/gm, '<h2 class="text-lg font-bold text-white mt-5 mb-2">$1</h2>');

  // 4. Bold and Italic
  escaped = escaped.replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-blue-400">$1</strong>');
  escaped = escaped.replace(/\*(.*?)\*/g, '<em class="italic text-slate-400">$1</em>');

  // 5. Bullet items
  escaped = escaped.replace(/^\s*[-*]\s+(.*?)$/gm, '<li class="ml-4 list-disc text-sm text-slate-300 mb-1">$1</li>');

  // 6. Inline code
  escaped = escaped.replace(/`([^`]+)`/g, '<code class="font-mono text-xs bg-slate-950 border border-slate-800 px-1.5 py-0.5 rounded text-slate-300">$1</code>');

  // 7. Parse line breaks without breaking lists/headers/code block flow
  escaped = escaped.split(/\r?\n/).map((line) => {
    const trimmed = line.trim();
    if (!trimmed) {
      return '<div class="h-2"></div>';
    }
    // Avoid double breaking lists, block headers, or placeholders
    if (trimmed.endsWith("</li>") || trimmed.endsWith("</h2>") || trimmed.endsWith("</h3>") || trimmed.endsWith("</h4>") || trimmed.includes("__CODE_BLOCK_")) {
      return line;
    }
    return line + "<br />";
  }).join("");

  // 8. Restore protected code blocks
  codeBlocks.forEach((blockHTML, idx) => {
    escaped = escaped.replace(`__CODE_BLOCK_${idx}__`, blockHTML);
  });

  return escaped;
};

const formatMessageText = (text: string, citations: CitationInfo[] = []) => {
  const citationRegex = /(\[doc_\d+\])/g;
  const parts = text.split(citationRegex);

  return parts.map((part, idx) => {
    if (citationRegex.test(part)) {
      const match = citations.find(c => c.citation === part);
      if (match) {
        return (
          <span key={idx} className="group relative inline-block mx-0.5 align-middle">
            <button
              type="button"
              className="rounded bg-blue-600/25 px-2 py-0.5 text-xs font-mono font-bold text-blue-400 border border-blue-600/30 hover:bg-blue-600/35 transition cursor-pointer"
            >
              {part}
            </button>
            <span className="pointer-events-none absolute bottom-full left-1/2 z-50 mb-2 w-72 -translate-x-1/2 rounded border border-slate-800 bg-slate-950 p-3 shadow-md opacity-0 group-hover:opacity-100 transition-opacity duration-200 text-left">
              <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Source Grounding</p>
              <p className="mt-1 text-xs font-semibold text-blue-400 truncate">
                {match.document} {match.page ? `(Page ${match.page})` : ""}
              </p>
              {match.text && (
                <p className="mt-1 text-[11px] text-slate-300 italic line-clamp-3">"{match.text}"</p>
              )}
              <span className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-slate-950" />
            </span>
          </span>
        );
      }
      return <span key={idx} className="font-mono text-blue-400">{part}</span>;
    }

    return <span key={idx} dangerouslySetInnerHTML={{ __html: parseMarkdown(part) }} />;
  });
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
    case "json":
      return "JSON";
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

export function ChatWindow({ selectedChat }: ChatWindowProps) {
  return (
    <div className="flex h-full flex-col bg-slate-950">
      {/* SCROLLABLE CHAT AREA */}
      <div className="flex-1 overflow-y-auto px-3 py-4 sm:px-5 lg:px-8">
        <div className="mx-auto flex w-full max-w-5xl flex-col gap-4">
          {selectedChat.messages.map((message, index) => {
            const isUser = message.from === "user";

            return (
              <div
                key={index}
                className={`flex w-full ${isUser ? "justify-end" : "justify-start"}`}
              >
                {/* MESSAGE CARD */}
                <div
                  className={`
                    relative
                    w-fit
                    max-w-[92%]
                    sm:max-w-[82%]
                    lg:max-w-[72%]
                    rounded-lg
                    px-4
                    py-3
                    border
                    shadow-sm
                    transition-all
                    duration-150
                    ${
                      isUser
                        ? "border-blue-900/40 bg-blue-950/20 text-slate-100"
                        : "border-slate-800 bg-slate-900 text-slate-200"
                    }
                  `}
                >
                  {/* ATTACHMENTS */}
                  {message.attachments && message.attachments.length > 0 ? (
                    <div className="mb-3 flex flex-col gap-2">
                      {message.attachments.map((file, fileIndex) => (
                        <div
                          key={fileIndex}
                          className="flex items-center gap-3 rounded border p-2 border-slate-800 bg-slate-950"
                        >
                          {/* FILE ICON */}
                          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded border border-slate-700 bg-slate-800 text-[10px] font-mono font-bold text-slate-300">
                            {getFileIcon(file)}
                          </div>

                          {/* FILE DETAILS */}
                          <div className="min-w-0 flex-1">
                            <p className="truncate text-xs font-semibold text-slate-200">
                              {file}
                            </p>
                            <p className="mt-0.5 text-[10px] text-slate-500">
                              Uploaded document
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : null}

                  {/* MESSAGE CONTENT */}
                  {message.message && (
                    <div className="text-sm leading-relaxed space-y-1">
                      {formatMessageText(message.message, message.citations)}
                    </div>
                  )}

                  {/* TIME */}
                  <div className="mt-2.5 text-[10px] text-slate-500 font-mono">
                    {message.time}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}