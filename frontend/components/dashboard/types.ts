export type DashboardSection = "chat" | "schedules" | "profile";

export type ChatMessage = {
  from: "assistant" | "user";
  message: string;
  time: string;
  attachments?: string[];
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
