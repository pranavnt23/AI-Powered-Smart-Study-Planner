export type DashboardSection = "chat" | "library" | "schedules" | "profile";

export type CitationInfo = {
  citation: string;
  document: string;
  page?: number;
  text?: string;
};

export type ChatMessage = {
  from: "assistant" | "user";
  message: string;
  time: string;
  attachments?: string[];
  citations?: CitationInfo[];
};

export type ChatConversation = {
  id: string;
  title: string;
  updated: string;
  snippet: string;
  messages: ChatMessage[];
};

export type ScheduleItem = {
  title: string;
  time: string;
  duration: string;
  topic: string;
  progress: number;
  status: string;
};

export type PastScheduleEntry = {
  title: string;
  time: string;
  topic: string;
  outcome: string;
};
