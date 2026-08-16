"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

import { ChatSidebar } from "../../components/dashboard/ChatSidebar";
import { ChatWindow } from "../../components/dashboard/ChatWindow";
import { ChatFooter } from "../../components/dashboard/ChatFooter";
import { ProfilePanel } from "../../components/dashboard/ProfilePanel";
import { SchedulePanel } from "../../components/dashboard/SchedulePanel";
import { LibraryPanel } from "../../components/dashboard/LibraryPanel";

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

  const [conversations, setConversations] = useState<ChatConversation[]>([]);
  const [selectedChatId, setSelectedChatId] = useState("");
  const [chatInput, setChatInput] = useState("");
  const [historyOpen, setHistoryOpen] = useState(false);
  const router = useRouter();

  // 1. Fetch conversations session list on mount
  useEffect(() => {
    const fetchSessions = async () => {
      try {
        const resp = await fetch("http://127.0.0.1:8000/chat/sessions?user_id=1");
        if (resp.ok) {
          const sessions = await resp.json();
          if (sessions.length > 0) {
            const mappedSessions = sessions.map((s: any) => ({
              id: s.id,
              title: s.title,
              updated: new Date(s.updated_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
              snippet: "Click to load chat history...",
              messages: []
            }));
            setConversations(mappedSessions);
            setSelectedChatId(mappedSessions[0].id);
          } else {
            setConversations([initialNewChat()]);
            setSelectedChatId("new-chat");
          }
        }
      } catch (err) {
        console.error("Failed to load chat sessions:", err);
        setConversations([initialNewChat()]);
        setSelectedChatId("new-chat");
      }
    };
    fetchSessions();
  }, []);

  // 2. Fetch chronological message list when selectedChatId changes
  useEffect(() => {
    if (!selectedChatId || selectedChatId === "new-chat") return;

    const activeChat = conversations.find(c => c.id === selectedChatId);
    if (activeChat && activeChat.messages.length > 0) return; // Cached in state

    const fetchMessages = async () => {
      try {
        const resp = await fetch(`http://127.0.0.1:8000/chat/session/${selectedChatId}/messages`);
        if (resp.ok) {
          const msgs = await resp.json();
          setConversations(current => current.map(c => {
            if (c.id === selectedChatId) {
              return {
                ...c,
                snippet: msgs[msgs.length - 1]?.message || c.snippet,
                messages: msgs.length > 0 ? msgs : [
                  { from: "assistant", message: "Empty chat log. Ask me anything!", time: "Now" }
                ]
              };
            }
            return c;
          }));
        }
      } catch (err) {
        console.error("Failed to load conversation history:", err);
      }
    };
    fetchMessages();
  }, [selectedChatId]);

  const handleSelectChat = (id: string) => {
    setSelectedChatId(id);
    if (typeof window !== "undefined") {
      window.localStorage.setItem("selectedChatId", id);
    }
  };

  const selectedChat =
    conversations.find(
      (item) => item.id === selectedChatId
    ) || conversations[0] || initialNewChat();

  const handleCreateNewChat = () => {
    const hasNewChat = conversations.some(c => c.id === "new-chat");
    if (!hasNewChat) {
      setConversations(current => [initialNewChat(), ...current]);
    }
    handleSelectChat("new-chat");
    setChatInput("");
  };

  const handleSend = async (
    uploadedAttachments: {
      name: string;
      content: string | null;
      fileId?: string | null;
    }[] = []
  ): Promise<void> => {
    const messageText = chatInput.trim();
    if (!messageText && uploadedAttachments.length === 0) return;

    let activeSessionId = selectedChatId;
    let isNewChat = false;

    // Use browser crypto API to pre-assign UUID to new sessions
    if (selectedChatId === "new-chat") {
      activeSessionId = crypto.randomUUID();
      isNewChat = true;
    }

    const userMessage = {
      from: "user" as const,
      message: messageText || "Uploaded documents",
      attachments: uploadedAttachments.map((file) => file.name),
      time: getCurrentTime(),
    };

    const assistantMessage = {
      from: "assistant" as const,
      message: "AI is thinking...",
      time: getCurrentTime(),
    };

    if (isNewChat) {
      const newConversation: ChatConversation = {
        id: activeSessionId,
        title: "New conversation",
        updated: "Now",
        snippet: messageText || "Uploaded documents",
        messages: [userMessage, assistantMessage],
      };
      setConversations((current) => [
        newConversation,
        ...current.filter((c) => c.id !== "new-chat"),
      ]);
      setSelectedChatId(activeSessionId);
    } else {
      setConversations((previous) =>
        previous.map((conversation) => {
          if (conversation.id !== activeSessionId) {
            return conversation;
          }

          return {
            ...conversation,
            updated: "Now",
            snippet: messageText || "Uploaded documents",
            messages: [
              ...conversation.messages,
              userMessage,
              assistantMessage,
            ],
          };
        })
      );
    }

    setChatInput("");

    try {
      const response = await fetch("http://127.0.0.1:8000/chat/query", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question: messageText || "Please summarize the uploaded files.",
          session_id: activeSessionId,
          user_id: 1,
          file_ids: uploadedAttachments.map((file) => file.fileId).filter(Boolean),
        }),
      });

      if (!response.ok || !response.body) {
        throw new Error("Failed to connect to local RAG server stream.");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let accumulatedText = "";
      
      let metadataObj: any = null;
      let citationsObj: any = null;

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const textChunk = decoder.decode(value, { stream: true });
        accumulatedText += textChunk;

        let displayText = accumulatedText;

        // 1. Delimiter stripping: Extract METADATA JSON block
        if (displayText.includes("---METADATA---")) {
          const parts = displayText.split("---METADATA---\n");
          if (parts.length > 1) {
            const metaSubparts = parts[1].split("\n\n");
            if (metaSubparts.length > 1) {
              try {
                metadataObj = JSON.parse(metaSubparts[0]);
                displayText = parts[0] + metaSubparts.slice(1).join("\n\n");
                
                // Cache the newly assigned active session ID
                if (typeof window !== "undefined" && metadataObj.session_id) {
                  window.localStorage.setItem("selectedChatId", metadataObj.session_id);
                }
              } catch (err) {
                // Incomplete JSON buffer chunk
              }
            }
          }
        }

        // 2. Delimiter stripping: Extract CITATIONS JSON block
        if (displayText.includes("\n\n---CITATIONS---")) {
          const parts = displayText.split("\n\n---CITATIONS---\n");
          if (parts.length > 1) {
            try {
              citationsObj = JSON.parse(parts[1]);
              displayText = parts[0];
            } catch (err) {
              // Incomplete citations JSON
            }
          }
        }

        setConversations((previous) =>
          previous.map((conversation) => {
            if (conversation.id !== activeSessionId) {
              return conversation;
            }

            const updatedMessages = [...conversation.messages];
            if (updatedMessages.length > 0) {
              updatedMessages[updatedMessages.length - 1] = {
                ...updatedMessages[updatedMessages.length - 1],
                message: displayText,
                citations: citationsObj || undefined
              };
            }

            return {
              ...conversation,
              title: metadataObj?.title || conversation.title,
              messages: updatedMessages,
            };
          })
        );
      }
    } catch (error) {
      console.error("Stream generation error:", error);
      setConversations((previous) =>
        previous.map((conversation) => {
          if (conversation.id !== activeSessionId) {
            return conversation;
          }

          const errorMessages = [...conversation.messages];
          if (errorMessages.length > 0) {
            errorMessages[errorMessages.length - 1] = {
              ...errorMessages[errorMessages.length - 1],
              message: "[Generation Error: Could not connect to local study planner RAG server. Ensure backend is running and Ollama is active.]",
            };
          }

          return {
            ...conversation,
            messages: errorMessages,
          };
        })
      );
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
    <main className="h-dvh overflow-hidden bg-slate-950 text-slate-100">

      <div className="flex h-screen w-full overflow-hidden">

        {/* SIDEBAR */}

        {activeSection === "chat" && (
          <aside className="hidden lg:flex w-[320px] shrink-0 border-r border-slate-800 bg-slate-950">
            <div className="flex h-full w-full flex-col overflow-hidden p-4">

              <div className="mb-4 flex items-center justify-between gap-3">

                <div>
                  <p className="text-xs uppercase tracking-wider text-slate-400">
                    Chats
                  </p>

                  <h2 className="mt-1 text-xl font-bold text-white">
                    History
                  </h2>
                </div>

                <button
                  type="button"
                  onClick={handleCreateNewChat}
                  className="rounded bg-slate-800 px-3 py-1.5 text-xs font-semibold text-slate-200 transition hover:bg-slate-700"
                >
                  + New
                </button>
              </div>

              <div className="flex-1 overflow-y-auto pr-1">
                <ChatSidebar
                  conversations={conversations}
                  selectedChatId={selectedChatId}
                  onSelectConversation={handleSelectChat}
                />
              </div>
            </div>
          </aside>
        )}

        {/* MAIN CONTENT */}

        <div className="flex h-full min-w-0 flex-1 flex-col overflow-hidden">

          {/* TOPBAR */}

          <header className="flex shrink-0 items-center justify-between border-b border-slate-800 bg-slate-900 px-4 py-3 lg:px-6">

            <div className="flex items-center gap-3">

              <button
                type="button"
                onClick={() => setHistoryOpen(true)}
                className="flex h-9 w-9 items-center justify-center rounded border border-slate-800 bg-slate-950 text-slate-300 lg:hidden"
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

            <nav className="flex items-center gap-1 rounded border border-slate-800 bg-slate-950 p-1 overflow-x-auto max-w-[58%] sm:max-w-none">

              {navItems.map((item) => (
                <button
                  key={item.id}
                  onClick={() =>
                    setActiveSection(item.id)
                  }
                  className={`flex-shrink-0 whitespace-nowrap rounded px-3 py-1.5 text-xs sm:px-4 font-semibold transition-colors ${
                    activeSection === item.id
                      ? "bg-blue-600 text-white"
                      : "text-slate-400 hover:bg-slate-900"
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

              <div className="flex shrink-0 flex-col gap-3 border-b border-slate-800 bg-slate-900 px-4 py-3 sm:flex-row sm:items-center sm:justify-between lg:px-6">

                <div className="min-w-0">
                  <p className="text-xs uppercase tracking-wider text-slate-400">
                    AI Study Chat
                  </p>

                  <h2 className="truncate text-xl font-bold text-white sm:text-2xl">
                    {selectedChat.title}
                  </h2>
                </div>

                <div className="flex flex-wrap items-center gap-2">

                  <span className="rounded bg-slate-800 px-3 py-1.5 text-xs text-slate-400 border border-slate-800">
                    {conversations.length} chats
                  </span>
                </div>
              </div>

              {/* CHAT WINDOW */}

              <div className="flex min-h-0 flex-1 flex-col overflow-hidden">

                <div className="flex-1 overflow-y-auto px-1 py-2 sm:px-4 lg:px-6">
                  <ChatWindow selectedChat={selectedChat} />
                </div>

                {/* STICKY FOOTER */}

                <div className="sticky bottom-0 z-20 shrink-0 border-t border-slate-800 bg-slate-950 px-2 py-2 pb-3 sm:px-4 lg:px-6">
                  <ChatFooter
                    chatInput={chatInput}
                    setChatInput={setChatInput}
                    onSend={handleSend}
                  />
                </div>
              </div>
            </section>
          )}

          {/* LIBRARY */}

          {activeSection === "library" && (
            <div className="flex-1 overflow-y-auto p-4 lg:p-6">
              <LibraryPanel />
            </div>
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

              <div className="mx-auto max-w-5xl rounded-lg border border-slate-800 bg-slate-900 p-6 shadow-sm">

                <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">

                  <div className="rounded-lg border border-slate-800 bg-slate-950 p-6">

                    <p className="text-xs uppercase tracking-wider text-slate-400">
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

                  <div className="rounded-lg border border-slate-800 bg-slate-950 p-6">

                    <div className="space-y-4">

                      <div className="rounded-lg bg-slate-900 p-4 border border-slate-800">
                        <p className="text-sm text-slate-400">
                          Learning style
                        </p>

                        <p className="mt-2 text-lg font-semibold text-white">
                          Visual + Practice
                        </p>
                      </div>

                      <div className="rounded-lg bg-slate-900 p-4 border border-slate-800">
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

                <div className="mt-6 flex justify-end border-t border-slate-800 pt-6">

                  <button
                    type="button"
                    onClick={handleLogout}
                    className="rounded border border-red-900/30 bg-red-900/10 px-4 py-2 text-xs font-semibold text-red-400 hover:bg-red-900/20 transition"
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

            <aside className="fixed inset-y-0 left-0 z-50 w-[85%] max-w-[300px] border-r border-slate-800 bg-slate-950 p-4 shadow-xl lg:hidden">

              <div className="mb-5 flex items-center justify-between">

                <div>
                  <p className="text-xs uppercase tracking-wider text-slate-400">
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
                  className="rounded bg-slate-800 px-3 py-1.5 text-xs text-slate-300"
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