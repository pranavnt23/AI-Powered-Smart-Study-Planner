import { PastScheduleEntry, ScheduleItem } from "./types";

type SchedulePanelProps = {
  liveSchedules: ScheduleItem[];
  pastSchedules: PastScheduleEntry[];
};

export function SchedulePanel({ liveSchedules, pastSchedules }: SchedulePanelProps) {
  return (
    <div className="space-y-6">
      <div className="grid gap-5 md:grid-cols-[1fr_0.8fr] lg:grid-cols-[1.2fr_0.8fr]">
        <div className="rounded-lg border border-slate-800 bg-slate-900 p-4 sm:p-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 sm:gap-4 mb-5">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Live schedules</p>
              <h3 className="mt-1.5 text-xl font-bold text-white">Today's agenda</h3>
            </div>
            <span className="rounded bg-blue-600/10 border border-blue-900/40 px-2 py-1 text-xs font-semibold text-blue-400 w-fit">2 active</span>
          </div>

          <div className="space-y-4">
            {liveSchedules.map((item) => (
              <div key={item.title} className="rounded-lg border border-slate-800 bg-slate-950 p-4 sm:p-5">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                  <div>
                    <p className="text-[10px] font-mono uppercase tracking-wider text-slate-500">{item.time}</p>
                    <h4 className="mt-1 text-lg font-bold text-white">{item.title}</h4>
                  </div>
                  <div className="rounded bg-slate-900 border border-slate-800 px-3 py-1 text-xs font-semibold text-slate-300 w-fit">{item.duration}</div>
                </div>
                <p className="mt-3 text-sm text-slate-300">Topic: <span className="text-white font-medium">{item.topic}</span></p>
                <div className="mt-3.5 h-2 rounded bg-slate-800 overflow-hidden">
                  <div className="h-full rounded bg-blue-600" style={{ width: `${item.progress}%` }} />
                </div>
                <div className="mt-3 flex items-center gap-2 text-xs text-slate-400">
                  <span className={`inline-flex h-2 w-2 rounded-full ${item.status === "Live" ? "bg-emerald-500" : "bg-slate-500"}`} />
                  <span>{item.status}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-lg border border-slate-800 bg-slate-900 p-4 sm:p-6">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Schedule summary</p>
          <div className="mt-5 grid gap-4">
            <div className="rounded-lg bg-slate-950 p-4 border border-slate-800">
              <p className="text-xs text-slate-500 uppercase tracking-wider font-bold">Next break</p>
              <p className="mt-1 text-lg font-bold text-white font-mono">11:10 AM</p>
            </div>
            <div className="rounded-lg bg-slate-950 p-4 border border-slate-800">
              <p className="text-xs text-slate-500 uppercase tracking-wider font-bold">Focus mode</p>
              <p className="mt-1 text-lg font-bold text-white">Deep Work</p>
            </div>
          </div>
        </div>
      </div>

      <div className="rounded-lg border border-slate-800 bg-slate-900 p-4 sm:p-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 sm:gap-4 mb-5">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Past schedules</p>
            <h3 className="mt-1.5 text-xl font-bold text-white">Completed sessions</h3>
          </div>
          <span className="text-xs text-slate-500 w-fit font-medium">Most recent first</span>
        </div>

        <div className="space-y-4">
          {pastSchedules.map((entry) => (
            <div key={entry.title} className="rounded-lg border border-slate-800 bg-slate-950 p-4 sm:p-5">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                <div>
                  <h4 className="text-lg font-bold text-white">{entry.title}</h4>
                  <p className="mt-1 text-xs text-slate-400">{entry.topic}</p>
                </div>
                <div className="text-xs text-slate-400 font-mono w-fit">{entry.time}</div>
              </div>
              <p className="mt-3 text-sm text-slate-300">Outcome: <span className="font-semibold text-white">{entry.outcome}</span></p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
