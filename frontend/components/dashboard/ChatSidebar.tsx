"use client";

import { ChatConversation } from "./types";

type ChatSidebarProps = {
  conversations: ChatConversation[];
  selectedChatId: string;
  onSelectConversation: (id: string) => void;
};

export function ChatSidebar({ conversations, selectedChatId, onSelectConversation }: ChatSidebarProps) {
  return (
    <aside className="rounded-lg border border-slate-800 bg-slate-900 p-4 h-full">
      <div className="flex items-center justify-between gap-3 mb-4">
        <div>
          <p className="text-xs uppercase tracking-wider text-slate-400">Chat history</p>
          <h2 className="mt-1 text-lg font-bold text-white">Saved conversations</h2>
        </div>
        <span className="rounded bg-slate-800 px-2 py-1 text-xs text-slate-400 font-mono">{conversations.length}</span>
      </div>

      <div className="space-y-2 max-h-[calc(100vh-260px)] overflow-y-auto pr-1">
        {conversations.map((conversation) => (
          <button
            key={conversation.id}
            onClick={() => onSelectConversation(conversation.id)}
            className={`w-full text-left rounded-md p-3.5 border transition-colors ${
              selectedChatId === conversation.id
                ? "border-blue-600 bg-blue-600/10 text-blue-400"
                : "border-slate-800 bg-slate-900 hover:border-slate-700 hover:bg-slate-800"
            }`}
          >
            <div className="flex items-center justify-between gap-3">
              <p className="text-sm font-semibold text-white truncate max-w-[70%]">{conversation.title}</p>
              <span className="rounded bg-slate-950 px-2 py-0.5 text-[10px] text-slate-400 font-mono">{conversation.updated}</span>
            </div>
            <p className="mt-2 text-xs leading-relaxed text-slate-400 truncate">{conversation.snippet}</p>
          </button>
        ))}
      </div>
    </aside>
  );
}
