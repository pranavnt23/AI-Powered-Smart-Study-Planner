"use client";

import { useRef, ChangeEvent, Dispatch, SetStateAction, useState } from "react";
import { ChatConversation } from "./types";

type ChatWindowProps = {
  selectedChat: ChatConversation;
};

export function ChatWindow({ selectedChat }: ChatWindowProps) {
  return (
    <div className="flex min-h-[calc(100vh-340px)] flex-col gap-6 rounded-[32px] bg-slate-950/90 p-6">
      <div className="flex items-center justify-between gap-4 rounded-3xl border border-white/10 bg-slate-900/80 p-5">
        <div>
          <p className="text-sm uppercase tracking-[0.24em] text-cyan-300/80">Conversation</p>
          <h3 className="mt-2 text-2xl font-bold text-white">{selectedChat.title}</h3>
        </div>
        <div className="inline-flex items-center gap-3 rounded-3xl bg-slate-950/80 px-4 py-2 text-sm text-slate-300">
          <span className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-cyan-300/10 text-cyan-300">💡</span>
          Updated {selectedChat.updated}
        </div>
      </div>

      <div className="flex-1 space-y-4 overflow-y-auto pr-2">
        {selectedChat.messages.map((message, index) => (
          <div
            key={index}
            className={`max-w-[90%] rounded-[28px] border px-5 py-4 shadow-sm ${
              message.from === "assistant"
                ? "border-white/10 bg-slate-900/80 text-slate-200"
                : "ml-auto border-cyan-400/10 bg-cyan-500/10 text-cyan-100"
            }`}
          >
            <div className="flex items-start gap-3">
              <span className={`mt-1 inline-flex h-8 w-8 items-center justify-center rounded-2xl text-sm ${
                message.from === "assistant" ? "bg-slate-900/90 text-cyan-300" : "bg-cyan-500/20 text-cyan-100"
              }`}>
                {message.from === "assistant" ? "A" : "Y"}
              </span>
              <div>
                <p className="leading-7">{message.message}</p>
                <p className="mt-3 text-xs text-slate-500">{message.from === "assistant" ? "StudyBot" : "You"} • {message.time}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
