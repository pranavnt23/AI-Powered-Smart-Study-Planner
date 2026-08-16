import Link from "next/link";

export default function Home() {
  return (
    <main className="min-h-screen flex items-center justify-center px-6 lg:px-16 py-12 bg-slate-950">
      <section className="w-full max-w-7xl grid lg:grid-cols-[1.1fr_0.9fr] gap-12 xl:gap-20 items-center">
        
        {/* LEFT SECTION */}
        <div className="space-y-8">
          <div className="inline-flex items-center gap-2 bg-slate-900 border border-slate-800 rounded-md px-3.5 py-1.5 text-xs tracking-wider text-slate-300 uppercase">
            <span className="w-2.5 h-2.5 bg-blue-500 rounded-full" />
            AI Powered Learning Intelligence Platform
          </div>

          <div className="space-y-6">
            <h1 className="max-w-[700px] text-4xl sm:text-5xl lg:text-6xl font-extrabold leading-tight tracking-tight text-white">
              Build Your <br />
              <span className="text-blue-500">Smart Study</span> Future
            </h1>

            <p className="text-slate-400 text-base sm:text-lg leading-relaxed max-w-[620px]">
              Personalized AI schedules, syllabus analysis,
              adaptive planning, progress tracking,
              and intelligent study workflows.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-4 pt-2">
            <Link
              href="/auth/register"
              className="inline-flex items-center justify-center px-6 py-3 rounded-md bg-blue-600 hover:bg-blue-700 font-semibold text-white transition-colors"
            >
              Get Started
            </Link>

            <Link
              href="/auth/login"
              className="inline-flex items-center justify-center px-6 py-3 rounded-md border border-slate-800 bg-slate-900 hover:bg-slate-800 text-slate-200 transition-colors"
            >
              Login
            </Link>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-6">
            <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
              <h2 className="text-xl font-bold text-slate-100">
                AI
              </h2>
              <p className="text-xs text-slate-400 mt-2 leading-relaxed">
                Adaptive learning intelligence
              </p>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
              <h2 className="text-xl font-bold text-slate-100">
                RAG
              </h2>
              <p className="text-xs text-slate-400 mt-2 leading-relaxed">
                Context aware document analysis
              </p>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
              <h2 className="text-xl font-bold text-slate-100">
                ML
              </h2>
              <p className="text-xs text-slate-400 mt-2 leading-relaxed">
                AI driven performance predictions
              </p>
            </div>
          </div>
        </div>

        {/* RIGHT SECTION */}
        <div className="relative flex items-center justify-center lg:justify-end">
          <div className="relative w-full max-w-[500px] bg-slate-900 border border-slate-800 rounded-lg p-8 shadow-sm">
            <div className="space-y-6">
              <div>
                <p className="text-blue-500 text-xs font-bold uppercase tracking-wider mb-2">
                  AI Dashboard Preview
                </p>
                <h2 className="text-2xl font-bold text-white leading-tight">
                  Smart Study Insights
                </h2>
              </div>

              <div className="space-y-5">
                <div className="bg-slate-950 rounded-lg p-5 border border-slate-800">
                  <div className="flex items-center justify-between mb-3 text-sm">
                    <span className="text-slate-300">
                      Study Completion
                    </span>
                    <span className="text-white font-semibold">
                      82%
                    </span>
                  </div>
                  <div className="w-full h-3 bg-slate-800 rounded">
                    <div className="w-[82%] h-full bg-blue-600 rounded" />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-slate-950 rounded-lg p-5 border border-slate-800">
                    <h3 className="text-3xl font-extrabold text-blue-400">
                      12
                    </h3>
                    <p className="text-xs text-slate-400 mt-2">
                      Active Topics
                    </p>
                  </div>

                  <div className="bg-slate-950 rounded-lg p-5 border border-slate-800">
                    <h3 className="text-3xl font-extrabold text-slate-200">
                      6h
                    </h3>
                    <p className="text-xs text-slate-400 mt-2">
                      Planned Today
                    </p>
                  </div>
                </div>

                <div className="bg-slate-950 border border-slate-800 rounded-lg p-5">
                  <p className="text-xs text-slate-300 leading-relaxed">
                    Your productivity increased by
                    <span className="text-blue-400 font-semibold">
                      {" "}27%
                    </span>
                    {" "}this week based on AI scheduling optimization.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

      </section>
    </main>
  );
}