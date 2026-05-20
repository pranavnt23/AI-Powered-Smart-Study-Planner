"use client";

import { ChatConversation } from "./types";

type ChatSidebarProps = {
  conversations: ChatConversation[];
  selectedChatId: string;
  onSelectConversation: (id: string) => void;
};

export function ChatSidebar({ conversations, selectedChatId, onSelectConversation }: ChatSidebarProps) {
  return (
    <aside className="rounded-[32px] border border-white/10 bg-slate-950/80 p-6 shadow-2xl shadow-black/30 h-full">
      <div className="flex items-center justify-between gap-3 mb-5">
        <div>
          <p className="text-sm uppercase tracking-[0.24em] text-cyan-300/80">Chat history</p>
          <h2 className="mt-2 text-2xl font-semibold text-white">Saved conversations</h2>
        </div>
        <span className="rounded-2xl bg-white/5 px-3 py-2 text-xs uppercase tracking-[0.24em] text-slate-400">{conversations.length}</span>
      </div>

      <div className="space-y-4 max-h-[calc(100vh-260px)] overflow-y-auto pr-1">
        {conversations.map((conversation) => (
          <button
            key={conversation.id}
            onClick={() => onSelectConversation(conversation.id)}
            className={`w-full text-left rounded-3xl p-4 transition-all duration-200 ${
              selectedChatId === conversation.id
                ? "border border-cyan-400/30 bg-cyan-400/10"
                : "border border-white/10 bg-slate-950/70 hover:border-white/20 hover:bg-slate-900/80"
            }`}
          >
            <div className="flex items-center justify-between gap-3">
              <p className="text-sm font-semibold text-white">{conversation.title}</p>
              <span className="rounded-full bg-slate-950/80 px-3 py-1 text-xs text-slate-300">{conversation.updated}</span>
            </div>
            <p className="mt-3 text-sm leading-6 text-slate-400">{conversation.snippet}</p>
          </button>
        ))}
      </div>
    </aside>
  );
}
