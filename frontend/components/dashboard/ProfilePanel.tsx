export function ProfilePanel() {
  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-slate-800 bg-slate-900 p-6 shadow-sm">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">User</p>
            <h2 className="mt-1 text-2xl font-bold text-white">Priya</h2>
          </div>
        </div>

        <div className="mt-6 grid gap-4 sm:grid-cols-2">
          <div className="rounded-lg border border-slate-800 bg-slate-950 p-4">
            <p className="text-xs text-slate-400 uppercase tracking-wider font-bold">Completion streak</p>
            <p className="mt-2 text-2xl font-bold text-white">14 days</p>
          </div>
          <div className="rounded-lg border border-slate-800 bg-slate-950 p-4">
            <p className="text-xs text-slate-400 uppercase tracking-wider font-bold">Weekly goal</p>
            <p className="mt-2 text-2xl font-bold text-white font-mono">24 hours</p>
          </div>
        </div>
      </div>

      <div className="rounded-lg border border-slate-800 bg-slate-900 p-6 shadow-sm">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-xs text-slate-400 uppercase tracking-wider font-bold">Course focus</p>
            <h3 className="mt-1 text-lg font-bold text-white">Physics + AI</h3>
          </div>
          <span className="rounded bg-blue-600/10 border border-blue-900/40 px-2 py-1 text-xs font-semibold text-blue-400">High Priority</span>
        </div>

        <div className="mt-6 grid gap-3">
          <div className="rounded-lg border border-slate-800 bg-slate-950 p-4 flex justify-between items-center">
            <div>
              <p className="text-sm font-semibold text-slate-200">Model building</p>
              <p className="mt-1 text-xs text-slate-500">Relational Database Integration</p>
            </div>
            <p className="text-sm font-bold text-slate-400 font-mono">2h left</p>
          </div>
          
          <div className="rounded-lg border border-slate-800 bg-slate-950 p-4 flex justify-between items-center">
            <div>
              <p className="text-sm font-semibold text-slate-200">Concept review</p>
              <p className="mt-1 text-xs text-slate-500">Process scheduling & paging</p>
            </div>
            <p className="text-sm font-bold text-slate-400 font-mono">4 topics</p>
          </div>
        </div>
      </div>
    </div>
  );
}
