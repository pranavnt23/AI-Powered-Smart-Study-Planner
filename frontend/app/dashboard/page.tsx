"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ChatSidebar } from "../../components/dashboard/ChatSidebar";
import { ChatWindow } from "../../components/dashboard/ChatWindow";
import { ChatFooter } from "../../components/dashboard/ChatFooter";
import { ProfilePanel } from "../../components/dashboard/ProfilePanel";
import { SchedulePanel } from "../../components/dashboard/SchedulePanel";
import { chatConversations, liveSchedules, navItems, pastSchedules } from "../../components/dashboard/dashboard-data";
import { ChatConversation, DashboardSection } from "../../components/dashboard/types";
import { logoutUser } from "../../services/auth.service";

const initialNewChat = (): ChatConversation => ({
  id: "new-chat",
  title: "New conversation",
  updated: "Now",
  snippet: "Start your first chat with your AI study coach.",
  messages: [
    {
      from: "assistant",
      message: "Hi! I’m your AI study coach. Ask me anything about your schedule, revision plan, or exam prep.",
      time: "Now",
    },
  ],
});

const getCurrentTime = () => {
  const date = new Date();
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
};

export default function DashboardPage() {
  const [activeSection, setActiveSection] = useState<DashboardSection>("chat");
  const [conversations, setConversations] = useState<ChatConversation[]>([initialNewChat(), ...chatConversations]);
  const [selectedChatId, setSelectedChatId] = useState(conversations[0].id);
  const [chatInput, setChatInput] = useState("");
  const [historyOpen, setHistoryOpen] = useState(false);

  const selectedChat = conversations.find((item) => item.id === selectedChatId) || conversations[0];

  const handleCreateNewChat = () => {
    const newConversation: ChatConversation = {
      id: `new-${Date.now()}`,
      title: "New conversation",
      updated: "Now",
      snippet: "Start a fresh AI-guided study session.",
      messages: [
        {
          from: "assistant",
          message: "Hi! I’m your AI study coach. Ask me anything about your schedule, revision plan, or exam prep.",
          time: "Now",
        },
      ],
    };

    setConversations((current) => [newConversation, ...current]);
    setSelectedChatId(newConversation.id);
    setChatInput("");
  };

  const router = useRouter();

  const handleSend = () => {
    if (!chatInput.trim()) return;

    setConversations((previous) =>
      previous.map((conversation) => {
        if (conversation.id !== selectedChatId) {
          return conversation;
        }

        return {
          ...conversation,
          updated: "Now",
          snippet: chatInput.trim().slice(0, 120),
          messages: [
            ...conversation.messages,
            {
              from: "user",
              message: chatInput.trim(),
              time: getCurrentTime(),
            },
          ],
        };
      })
    );

    setChatInput("");
  };

  const handleLogout = async () => {
    try {
      const sessionId = window.localStorage.getItem("sessionId");

      if (sessionId) {
        await logoutUser({ session_id: Number(sessionId) });
      }
    } catch (error) {
      console.error("Logout error:", error);
    } finally {
      window.localStorage.removeItem("token");
      window.localStorage.removeItem("sessionId");
      window.localStorage.removeItem("tokenExpiresAt");
      router.push("/auth/login");
    }
  };

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(99,102,241,0.18),transparent_20%),radial-gradient(circle_at_bottom_right,_rgba(6,182,212,0.14),transparent_20%)] text-slate-100">
      <div className="max-w-7xl mx-auto px-6 py-8 lg:py-10">
        <header className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6 mb-10">
          <div className="space-y-3">
            <div className="inline-flex items-center gap-2 bg-slate-900/70 border border-white/10 rounded-full px-4 py-2 text-sm text-cyan-300">
              <span className="w-2 h-2 rounded-full bg-cyan-300 animate-pulse" />
              Smart Study Planner
            </div>
            <div className="space-y-2">
              <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight text-white">
                Your learning cockpit
              </h1>
              <p className="max-w-2xl text-slate-300 leading-relaxed">
                Access your profile, live schedules, and AI chat in a clean modular workspace. The chat is open by default so you can get instant guidance.
              </p>
            </div>
          </div>

          <nav className="inline-flex flex-wrap gap-3 rounded-3xl border border-white/10 bg-slate-950/80 p-3 shadow-2xl shadow-slate-950/30">
            {navItems.map((item) => (
              <button
                key={item.id}
                onClick={() => setActiveSection(item.id)}
                className={`rounded-2xl px-5 py-3 text-sm font-semibold transition-all duration-200 ${
                  activeSection === item.id
                    ? "bg-gradient-to-r from-indigo-500 to-cyan-400 text-slate-950 shadow-xl shadow-cyan-500/20"
                    : "text-slate-300 hover:bg-white/5"
                }`}
              >
                {item.label}
              </button>
            ))}
          </nav>
          <div className="mt-3 flex items-center gap-3">
            <button
              type="button"
              onClick={handleLogout}
              className="inline-flex items-center justify-center rounded-2xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm font-semibold text-red-200 transition-all duration-200 hover:bg-red-500/15"
            >
              Sign out
            </button>
          </div>
          {activeSection === "chat" ? (
            <div className="mt-3 flex flex-col gap-3 sm:flex-row sm:items-center">
              <button
                type="button"
                onClick={handleCreateNewChat}
                className="inline-flex items-center justify-center rounded-2xl border border-cyan-300/20 bg-cyan-400/10 px-4 py-3 text-sm font-semibold text-cyan-200 transition-all duration-200 hover:bg-cyan-400/15"
              >
                + New chat
              </button>
              <button
                type="button"
                onClick={() => setHistoryOpen(true)}
                className="inline-flex items-center gap-2 rounded-2xl border border-white/10 bg-slate-950/80 px-4 py-3 text-sm font-semibold text-cyan-300 transition-all duration-200 hover:bg-white/10 lg:hidden"
              >
                <span className="inline-flex h-5 w-5 items-center justify-center rounded-full bg-cyan-300/10 text-cyan-300">≡</span>
                Chat history
              </button>
            </div>
          ) : null}
        </header>

        <div className="grid gap-6 lg:grid-cols-[360px_minmax(0,_1fr)]">
          <aside className="hidden lg:block space-y-6">
            {activeSection === "chat" ? (
              <ChatSidebar
                conversations={conversations}
                selectedChatId={selectedChatId}
                onSelectConversation={setSelectedChatId}
              />
            ) : (
              <ProfilePanel />
            )}
          </aside>

          <section className="space-y-6">
            <div className="rounded-[40px] border border-white/10 bg-slate-950/80 p-6 shadow-2xl shadow-black/30">
              <div className="flex items-center justify-between gap-4 mb-6">
                <div>
                  <p className="text-sm uppercase tracking-[0.24em] text-cyan-300/80">Dashboard</p>
                  <h2 className="mt-2 text-3xl font-extrabold text-white capitalize">{activeSection}</h2>
                </div>
                <div className="rounded-3xl border border-white/10 bg-white/5 px-4 py-2 text-sm text-slate-300">
                  Updated 2 min ago
                </div>
              </div>

                  {activeSection === "chat" && (
                <div className="space-y-6">
                  <div className="rounded-[32px] border border-white/10 bg-slate-950/90 p-5 shadow-2xl shadow-black/20">
                    <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                      <div>
                        <p className="text-sm uppercase tracking-[0.24em] text-cyan-300/80">AI study chat</p>
                        <h3 className="mt-2 text-3xl font-extrabold text-white">{selectedChat.title}</h3>
                        <p className="mt-2 text-sm text-slate-400 max-w-2xl">
                          Get instant guidance on study sessions, reminders, review plans, and document analysis.
                        </p>
                      </div>
                      <div className="flex flex-wrap gap-3">
                        <button
                          type="button"
                          onClick={handleCreateNewChat}
                          className="inline-flex items-center justify-center rounded-2xl border border-cyan-300/20 bg-cyan-400/10 px-4 py-3 text-sm font-semibold text-cyan-200 transition-all duration-200 hover:bg-cyan-400/15"
                        >
                          + New chat
                        </button>
                        <span className="inline-flex items-center rounded-2xl bg-white/5 px-4 py-3 text-sm text-slate-300">
                          {conversations.length} conversations
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="relative flex min-h-[calc(100vh-340px)] flex-col gap-6 rounded-[32px] border border-white/10 bg-slate-950/90 shadow-2xl shadow-black/20">
                    <ChatWindow selectedChat={selectedChat} />
                    <ChatFooter chatInput={chatInput} setChatInput={setChatInput} onSend={handleSend} />
                  </div>
                </div>
              )}

              {activeSection === "schedules" && <SchedulePanel liveSchedules={liveSchedules} pastSchedules={pastSchedules} />}

              {activeSection === "profile" && (
                <div className="rounded-3xl border border-white/10 bg-slate-900/70 p-6">
                  <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
                    <div className="rounded-3xl border border-white/10 bg-slate-950/80 p-6">
                      <p className="text-sm uppercase tracking-[0.24em] text-cyan-300/80">Profile overview</p>
                      <h3 className="mt-4 text-3xl font-bold text-white">Priya</h3>
                      <p className="mt-4 text-slate-300">
                        You are using AI-assisted study planning to keep your schedule aligned and improve retention with active recall and spaced learning.
                      </p>
                    </div>

                    <div className="rounded-3xl border border-white/10 bg-slate-950/80 p-6">
                      <div className="space-y-4">
                        <div className="rounded-3xl bg-slate-900/70 p-4">
                          <p className="text-sm text-slate-400">Learning style</p>
                          <p className="mt-2 text-lg font-semibold text-white">Visual + Practice</p>
                        </div>
                        <div className="rounded-3xl bg-slate-900/70 p-4">
                          <p className="text-sm text-slate-400">Preferred subjects</p>
                          <p className="mt-2 text-lg font-semibold text-white">Physics, AI, History</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </section>
        </div>
        {historyOpen && activeSection === "chat" ? (
          <>
            <div className="fixed inset-0 z-40 bg-slate-950/70 lg:hidden" onClick={() => setHistoryOpen(false)} />
            <aside className="fixed inset-y-0 left-0 z-50 w-72 overflow-hidden border-r border-white/10 bg-slate-950/95 p-6 shadow-2xl lg:hidden">
              <div className="mb-5 flex items-center justify-between gap-3">
                <div>
                  <p className="text-xs uppercase tracking-[0.24em] text-cyan-300/80">Chat history</p>
                  <h2 className="mt-2 text-xl font-semibold text-white">Saved conversations</h2>
                </div>
                <button
                  type="button"
                  onClick={() => setHistoryOpen(false)}
                  className="rounded-2xl bg-white/5 px-3 py-2 text-xs font-semibold text-slate-300 transition hover:bg-white/10"
                >
                  Close
                </button>
              </div>
              <ChatSidebar
                conversations={conversations}
                selectedChatId={selectedChatId}
                onSelectConversation={(id) => {
                  setSelectedChatId(id);
                  setHistoryOpen(false);
                }}
              />
            </aside>
          </>
        ) : null}
      </div>
    </main>
  );
}
