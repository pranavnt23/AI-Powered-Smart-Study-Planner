"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { ChatSidebar } from "../../components/dashboard/ChatSidebar";
import { ChatWindow } from "../../components/dashboard/ChatWindow";
import { ChatFooter } from "../../components/dashboard/ChatFooter";
import { ProfilePanel } from "../../components/dashboard/ProfilePanel";
import { SchedulePanel } from "../../components/dashboard/SchedulePanel";

import {
  chatConversations,
  liveSchedules,
  navItems,
  pastSchedules,
} from "../../components/dashboard/dashboard-data";

import {
  ChatConversation,
  DashboardSection,
} from "../../components/dashboard/types";

import { logoutUser } from "../../services/auth.service";

const initialNewChat = (): ChatConversation => ({
  id: "new-chat",
  title: "New conversation",
  updated: "Now",
  snippet: "Start your first chat with your AI study coach.",
  messages: [
    {
      from: "assistant",
      message:
        "Hi! I’m your AI study coach. Ask me anything about your schedule, revision plan, or exam prep.",
      time: "Now",
    },
  ],
});

const getCurrentTime = () => {
  const date = new Date();

  return date.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });
};

export default function DashboardPage() {
  const [activeSection, setActiveSection] =
    useState<DashboardSection>("chat");

  const [conversations, setConversations] = useState<
    ChatConversation[]
  >([initialNewChat(), ...chatConversations]);

  const [selectedChatId, setSelectedChatId] = useState(
    conversations[0].id
  );

  const [chatInput, setChatInput] = useState("");

  const [historyOpen, setHistoryOpen] = useState(false);

  const router = useRouter();

  const selectedChat =
    conversations.find(
      (item) => item.id === selectedChatId
    ) || conversations[0];

  const handleCreateNewChat = () => {
    const newConversation: ChatConversation = {
      id: `new-${Date.now()}`,
      title: "New conversation",
      updated: "Now",
      snippet: "Start a fresh AI-guided study session.",
      messages: [
        {
          from: "assistant",
          message:
            "Hi! I’m your AI study coach. Ask me anything about your schedule, revision plan, or exam prep.",
          time: "Now",
        },
      ],
    };

    setConversations((current) => [
      newConversation,
      ...current,
    ]);

    setSelectedChatId(newConversation.id);

    setChatInput("");
  };

  const handleSend = async (
    uploadedAttachments: {
      name: string;
      content: string | null;
    }[] = []
  ): Promise<void> => {

    const messageText = chatInput.trim();

    if (!messageText && uploadedAttachments.length === 0) return;

    const userMessage = {
      from: "user" as const,
      message: messageText || "Uploaded documents",
      attachments: uploadedAttachments.map((file) => file.name),
      time: getCurrentTime(),
    };

    setConversations((previous) =>
      previous.map((conversation) => {

        if (conversation.id !== selectedChatId) {
          return conversation;
        }

        return {
          ...conversation,
          updated: "Now",
          snippet: messageText || "Uploaded documents",
          messages: [
            ...conversation.messages,
            userMessage,
          ],
        };
      })
    );

    setChatInput("");

    // AI RESPONSE USING DOCUMENT CONTENT

    const extractedText = uploadedAttachments
      .map((file) => file.content)
      .filter(Boolean)
      .join("\n\n");

    if (extractedText) {

      setTimeout(() => {

        setConversations((previous) =>
          previous.map((conversation) => {

            if (conversation.id !== selectedChatId) {
              return conversation;
            }

            return {
              ...conversation,
              messages: [
                ...conversation.messages,
                {
                  from: "assistant",
                  message: extractedText,
                  time: getCurrentTime(),
                },
              ],
            };
          })
        );

      }, 1200);
    }
  };

  const handleLogout = async () => {
    try {
      const sessionId =
        window.localStorage.getItem("sessionId");

      if (sessionId) {
        await logoutUser({
          session_id: Number(sessionId),
        });
      }
    } catch {
    } finally {
      window.localStorage.removeItem("token");

      window.localStorage.removeItem("sessionId");

      window.localStorage.removeItem(
        "tokenExpiresAt"
      );

      router.push("/auth/login");
    }
  };

  return (
    <main className="h-dvh overflow-hidden bg-[#020617] text-slate-100">

      <div className="flex h-screen w-full overflow-hidden">

        {/* SIDEBAR */}

        {activeSection === "chat" && (
          <aside className="hidden lg:flex w-[320px] shrink-0 border-r border-white/10 bg-slate-950/95">
            <div className="flex h-full w-full flex-col overflow-hidden p-4">

              <div className="mb-4 flex items-center justify-between gap-3">

                <div>
                  <p className="text-[11px] uppercase tracking-[0.24em] text-cyan-300/80">
                    Chats
                  </p>

                  <h2 className="mt-1 text-xl font-bold text-white">
                    History
                  </h2>
                </div>

                <button
                  type="button"
                  onClick={handleCreateNewChat}
                  className="rounded-2xl bg-cyan-400/10 px-4 py-2 text-sm font-semibold text-cyan-200 transition hover:bg-cyan-400/20"
                >
                  + New
                </button>
              </div>

              <div className="flex-1 overflow-y-auto pr-1">
                <ChatSidebar
                  conversations={conversations}
                  selectedChatId={selectedChatId}
                  onSelectConversation={setSelectedChatId}
                />
              </div>
            </div>
          </aside>
        )}

        {/* MAIN CONTENT */}

        <div className="flex h-full min-w-0 flex-1 flex-col overflow-hidden">

          {/* TOPBAR */}

          <header className="flex shrink-0 items-center justify-between border-b border-white/10 bg-slate-950/80 px-4 py-3 backdrop-blur-xl lg:px-6">

            <div className="flex items-center gap-3">

              <button
                type="button"
                onClick={() => setHistoryOpen(true)}
                className="flex h-10 w-10 items-center justify-center rounded-2xl border border-white/10 bg-white/5 text-cyan-300 lg:hidden"
              >
                ☰
              </button>

              <div>
                <h1 className="text-lg font-bold text-white sm:text-xl">
                  Smart Study Planner
                </h1>

                <p className="text-xs text-slate-400">
                  AI powered learning assistant
                </p>
              </div>
            </div>

            <nav className="flex items-center gap-1 rounded-2xl border border-white/10 bg-slate-950/90 p-1 overflow-x-auto max-w-[58%] sm:max-w-none scrollbar-thin scrollbar-thumb-cyan-500/40">

              {navItems.map((item) => (
                <button
                  key={item.id}
                  onClick={() =>
                    setActiveSection(item.id)
                  }
                  className={`flex-shrink-0 whitespace-nowrap rounded-xl px-3 py-2 text-[11px] sm:px-4 sm:text-sm font-semibold transition-all duration-200 ${
                    activeSection === item.id
                      ? "bg-gradient-to-r from-indigo-500 to-cyan-400 text-slate-950"
                      : "text-slate-300 hover:bg-white/5"
                  }`}
                >
                  {item.label}
                </button>
              ))}
            </nav>
          </header>

          {/* CHAT SECTION */}

          {activeSection === "chat" && (
            <section className="flex min-h-0 flex-1 flex-col overflow-hidden">

              {/* CHAT HEADER */}

              <div className="flex shrink-0 flex-col gap-3 border-b border-white/10 bg-slate-950/70 px-4 py-3 sm:flex-row sm:items-center sm:justify-between lg:px-6">

                <div className="min-w-0">
                  <p className="text-[11px] uppercase tracking-[0.24em] text-cyan-300/80">
                    AI Study Chat
                  </p>

                  <h2 className="truncate text-xl font-bold text-white sm:text-2xl">
                    {selectedChat.title}
                  </h2>
                </div>

                <div className="flex flex-wrap items-center gap-2">

                  <span className="rounded-2xl bg-white/5 px-4 py-2 text-sm text-slate-300">
                    {conversations.length} chats
                  </span>

                  <button
                    type="button"
                    onClick={handleCreateNewChat}
                    className="rounded-2xl bg-cyan-400/10 px-4 py-2 text-sm font-semibold text-cyan-200 transition hover:bg-cyan-400/20"
                  >
                    + New Chat
                  </button>
                </div>
              </div>

              {/* CHAT WINDOW */}

              <div className="flex min-h-0 flex-1 flex-col overflow-hidden">

                <div className="flex-1 overflow-y-auto px-1 py-2 sm:px-4 lg:px-6">
                  <ChatWindow selectedChat={selectedChat} />
                </div>

                {/* STICKY FOOTER */}

                <div className="shrink-0 border-t border-white/10 bg-slate-950/95 px-2 py-2 pb-3 sm:px-4 lg:px-6">
                  <ChatFooter
                    chatInput={chatInput}
                    setChatInput={setChatInput}
                    onSend={handleSend}
                  />
                </div>
              </div>
            </section>
          )}

          {/* SCHEDULES */}

          {activeSection === "schedules" && (
            <div className="flex-1 overflow-y-auto p-4 lg:p-6">
              <SchedulePanel
                liveSchedules={liveSchedules}
                pastSchedules={pastSchedules}
              />
            </div>
          )}

          {/* PROFILE */}

          {activeSection === "profile" && (
            <div className="flex-1 overflow-y-auto p-4 lg:p-6">

              <div className="mx-auto max-w-5xl rounded-[32px] border border-white/10 bg-slate-950/90 p-6 shadow-2xl shadow-black/30">

                <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">

                  <div className="rounded-3xl border border-white/10 bg-slate-900/60 p-6">

                    <p className="text-sm uppercase tracking-[0.24em] text-cyan-300/80">
                      Profile
                    </p>

                    <h3 className="mt-4 text-3xl font-bold text-white">
                      Priya
                    </h3>

                    <p className="mt-4 text-slate-300 leading-relaxed">
                      You are using AI-assisted study planning
                      to improve consistency, retention, and
                      productivity.
                    </p>
                  </div>

                  <div className="rounded-3xl border border-white/10 bg-slate-900/60 p-6">

                    <div className="space-y-4">

                      <div className="rounded-3xl bg-slate-950/80 p-4">
                        <p className="text-sm text-slate-400">
                          Learning style
                        </p>

                        <p className="mt-2 text-lg font-semibold text-white">
                          Visual + Practice
                        </p>
                      </div>

                      <div className="rounded-3xl bg-slate-950/80 p-4">
                        <p className="text-sm text-slate-400">
                          Preferred subjects
                        </p>

                        <p className="mt-2 text-lg font-semibold text-white">
                          Physics, AI, History
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="mt-6 flex justify-end border-t border-white/10 pt-6">

                  <button
                    type="button"
                    onClick={handleLogout}
                    className="rounded-2xl border border-red-500/20 bg-red-500/10 px-5 py-3 text-sm font-semibold text-red-200 transition hover:bg-red-500/20"
                  >
                    Sign out
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* MOBILE CHAT HISTORY */}

        {historyOpen && activeSection === "chat" && (
          <>
            <div
              className="fixed inset-0 z-40 bg-black/60 lg:hidden"
              onClick={() => setHistoryOpen(false)}
            />

            <aside className="fixed inset-y-0 left-0 z-50 w-[85%] max-w-[300px] border-r border-white/10 bg-slate-950 p-4 shadow-2xl lg:hidden">

              <div className="mb-5 flex items-center justify-between">

                <div>
                  <p className="text-[11px] uppercase tracking-[0.24em] text-cyan-300/80">
                    Chats
                  </p>

                  <h2 className="mt-1 text-lg font-bold text-white">
                    History
                  </h2>
                </div>

                <button
                  type="button"
                  onClick={() =>
                    setHistoryOpen(false)
                  }
                  className="rounded-xl bg-white/5 px-3 py-2 text-sm text-slate-300"
                >
                  Close
                </button>
              </div>

              <div className="h-[calc(100%-80px)] overflow-y-auto">
                <ChatSidebar
                  conversations={conversations}
                  selectedChatId={selectedChatId}
                  onSelectConversation={(id) => {
                    setSelectedChatId(id);
                    setHistoryOpen(false);
                  }}
                />
              </div>
            </aside>
          </>
        )}
      </div>
    </main>
  );
}