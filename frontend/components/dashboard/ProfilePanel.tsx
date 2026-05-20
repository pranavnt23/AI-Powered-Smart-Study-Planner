export function ProfilePanel() {
  return (
    <div className="space-y-6">
      <div className="rounded-[32px] border border-white/10 bg-slate-950/80 p-6 shadow-2xl shadow-black/30">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-sm uppercase tracking-[0.24em] text-cyan-300/80">User</p>
            <h2 className="mt-3 text-3xl font-extrabold text-white">Priya</h2>
          </div>
        </div>

        <div className="mt-7 grid gap-4">
          <div className="rounded-3xl border border-white/10 bg-slate-900/70 p-4">
            <p className="text-sm text-slate-400">Completion streak</p>
            <p className="mt-3 text-3xl font-bold text-white">14 days</p>
          </div>
          <div className="rounded-3xl border border-white/10 bg-slate-900/70 p-4">
            <p className="text-sm text-slate-400">Weekly goal</p>
            <p className="mt-3 text-3xl font-bold text-white">24 hours</p>
          </div>
        </div>
      </div>

      <div className="rounded-[32px] border border-white/10 bg-slate-950/80 p-6 shadow-2xl shadow-black/30">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-sm text-slate-400">Course focus</p>
            <h3 className="mt-2 text-xl font-semibold text-white">Physics + AI</h3>
          </div>
          <span className="rounded-2xl bg-cyan-400/15 px-3 py-1 text-sm font-semibold text-cyan-300">High</span>
        </div>

        <div className="mt-6 grid gap-3">
          <div className="rounded-3xl border border-white/10 bg-slate-900/70 p-4">
            <p className="text-slate-300">Model building</p>
            <p className="mt-2 text-sm text-slate-400">2h left</p>
          </div>
          <div className="rounded-3xl border border-white/10 bg-slate-900/70 p-4">
            <p className="text-slate-300">Concept review</p>
            <p className="mt-2 text-sm text-slate-400">4 topics</p>
          </div>
        </div>
      </div>
    </div>
  );
}
