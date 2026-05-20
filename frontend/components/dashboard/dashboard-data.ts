import { ChatConversation, DashboardSection, PastScheduleEntry, ScheduleItem } from "./types";

export const navItems: { id: DashboardSection; label: string }[] = [
  { id: "chat", label: "Chat" },
  { id: "schedules", label: "Schedules" },
  { id: "profile", label: "Profile" },
];

export const liveSchedules: ScheduleItem[] = [
  {
    title: "AI Revision Sprint",
    time: "Today • 10:00 AM",
    duration: "60 min",
    topic: "Memory Techniques",
    progress: 62,
    status: "Live",
  },
  {
    title: "Exam Strategy Session",
    time: "Today • 1:30 PM",
    duration: "45 min",
    topic: "Question Prioritization",
    progress: 28,
    status: "Upcoming",
  },
];

export const pastSchedules: PastScheduleEntry[] = [
  {
    title: "Flashcard Review",
    time: "Yesterday • 7:00 PM",
    topic: "Biology Notes",
    outcome: "Completed",
  },
  {
    title: "Focus Burst",
    time: "Yesterday • 4:30 PM",
    topic: "Math Practice",
    outcome: "Completed",
  },
  {
    title: "Syllabus Scan",
    time: "Yesterday • 1:00 PM",
    topic: "History Framework",
    outcome: "Completed",
  },
];

export const chatConversations: ChatConversation[] = [
  {
    id: "today",
    title: "Today’s session plan",
    updated: "09:06",
    snippet: "Adjust the 10 AM sprint and add a break...",
    messages: [
      {
        from: "assistant",
        message: "Welcome back! I recommend focusing on your AI Revision Sprint first. Shall I adjust your schedule?",
        time: "09:02",
      },
      {
        from: "user",
        message: "Yes, prioritize the 10 AM session and add a short break after it.",
        time: "09:05",
      },
      {
        from: "assistant",
        message: "Got it. I saved the change and will remind you 10 minutes before your session.",
        time: "09:06",
      },
    ],
  },
  {
    id: "week",
    title: "Weekly review summary",
    updated: "Yesterday",
    snippet: "Your focus score is strong, but add more spaced recall...",
    messages: [
      {
        from: "assistant",
        message: "Your weekly review shows strong focus, but you should add more spaced recall for history and physics.",
        time: "18:20",
      },
      {
        from: "user",
        message: "Schedule more review for history tomorrow afternoon.",
        time: "18:22",
      },
      {
        from: "assistant",
        message: "Done. I created a new review block for history at 2:00 PM tomorrow.",
        time: "18:23",
      },
    ],
  },
];
