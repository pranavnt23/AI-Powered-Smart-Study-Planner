import { PastScheduleEntry, ScheduleItem } from "./types";

type SchedulePanelProps = {
  liveSchedules: ScheduleItem[];
  pastSchedules: PastScheduleEntry[];
};

export function SchedulePanel({ liveSchedules, pastSchedules }: SchedulePanelProps) {
  return (
    <div className="space-y-6">
      <div className="grid gap-5 xl:grid-cols-[1.2fr_0.8fr]">
        <div className="rounded-3xl border border-white/10 bg-slate-900/70 p-6">
          <div className="flex items-center justify-between gap-4 mb-5">
            <div>
              <p className="text-sm uppercase tracking-[0.24em] text-cyan-300/80">Live schedules</p>
              <h3 className="mt-3 text-2xl font-bold text-white">Today’s agenda</h3>
            </div>
            <span className="rounded-2xl bg-cyan-400/15 px-3 py-2 text-sm font-semibold text-cyan-300">2 active</span>
          </div>

          <div className="space-y-4">
            {liveSchedules.map((item) => (
              <div key={item.title} className="rounded-3xl border border-white/10 bg-slate-950/80 p-5">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                  <div>
                    <p className="text-xs uppercase tracking-[0.24em] text-slate-400">{item.time}</p>
                    <h4 className="mt-2 text-xl font-semibold text-white">{item.title}</h4>
                  </div>
                  <div className="rounded-2xl bg-slate-900/80 px-4 py-2 text-sm font-semibold text-slate-300">{item.duration}</div>
                </div>
                <p className="mt-4 text-slate-300">Topic: <span className="text-white">{item.topic}</span></p>
                <div className="mt-4 h-3 rounded-full bg-slate-800 overflow-hidden">
                  <div className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-cyan-400" style={{ width: `${item.progress}%` }} />
                </div>
                <div className="mt-3 flex items-center gap-2 text-sm text-slate-300">
                  <span className={`inline-flex h-2.5 w-2.5 rounded-full ${item.status === "Live" ? "bg-emerald-400" : "bg-slate-500"}`} />
                  <span>{item.status}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-3xl border border-white/10 bg-slate-900/70 p-6">
          <p className="text-sm uppercase tracking-[0.24em] text-cyan-300/80">Schedule summary</p>
          <div className="mt-5 grid gap-4">
            <div className="rounded-3xl bg-slate-950/80 p-4">
              <p className="text-sm text-slate-400">Next break</p>
              <p className="mt-2 text-lg font-semibold text-white">11:10 AM</p>
            </div>
            <div className="rounded-3xl bg-slate-950/80 p-4">
              <p className="text-sm text-slate-400">Focus mode</p>
              <p className="mt-2 text-lg font-semibold text-white">Deep Work</p>
            </div>
          </div>
        </div>
      </div>

      <div className="rounded-3xl border border-white/10 bg-slate-900/70 p-6">
        <div className="flex items-center justify-between gap-4 mb-5">
          <div>
            <p className="text-sm uppercase tracking-[0.24em] text-cyan-300/80">Past schedules</p>
            <h3 className="mt-2 text-2xl font-bold text-white">Completed sessions</h3>
          </div>
          <span className="text-sm text-slate-400">Most recent first</span>
        </div>

        <div className="space-y-4">
          {pastSchedules.map((entry) => (
            <div key={entry.title} className="rounded-3xl border border-white/10 bg-slate-950/80 p-5">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                <div>
                  <h4 className="text-xl font-semibold text-white">{entry.title}</h4>
                  <p className="mt-2 text-sm text-slate-400">{entry.topic}</p>
                </div>
                <div className="text-sm text-slate-300">{entry.time}</div>
              </div>
              <p className="mt-4 text-slate-300">Outcome: <span className="font-semibold text-white">{entry.outcome}</span></p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
