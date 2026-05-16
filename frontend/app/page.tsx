import Link from "next/link";

export default function Home() {
  return (
    <main className="min-h-screen flex items-center justify-center px-6 lg:px-16 py-12 overflow-hidden">

      <section className="w-full max-w-7xl grid lg:grid-cols-[1.1fr_0.9fr] gap-12 xl:gap-20 items-center">

        {/* LEFT SECTION */}
        <div className="space-y-10">

          <div className="inline-flex items-center gap-2 bg-white/10 border border-white/10 rounded-full px-4 py-2 text-sm backdrop-blur-lg w-fit">
            <span className="w-2 h-2 bg-cyan-400 rounded-full animate-pulse" />

            AI Powered Learning Intelligence Platform
          </div>

          <div className="space-y-8">

            <h1 className="max-w-[700px] text-5xl sm:text-6xl lg:text-7xl font-black leading-[1.05] tracking-tight">

              <span className="block text-white">
                Build Your
              </span>

              <span className="block bg-gradient-to-r from-indigo-400 via-purple-400 to-cyan-400 bg-clip-text text-transparent mt-2">
                Smart Study
              </span>

              <span className="block bg-gradient-to-r from-indigo-300 to-cyan-400 bg-clip-text text-transparent">
                Future
              </span>

            </h1>

            <p className="text-slate-300 text-lg lg:text-xl leading-relaxed max-w-[620px]">
              Personalized AI schedules, syllabus analysis,
              adaptive planning, progress tracking,
              and intelligent study workflows.
            </p>

          </div>

          <div className="flex flex-wrap items-center gap-5 pt-4">

            <Link
              href="/auth/register"
              className="inline-flex items-center justify-center px-8 py-4 rounded-2xl bg-gradient-to-r from-indigo-500 to-cyan-500 font-semibold text-white hover:scale-105 transition-all duration-300 shadow-2xl shadow-indigo-500/30"
            >
              Get Started
            </Link>

            <Link
              href="/auth/login"
              className="inline-flex items-center justify-center px-8 py-4 rounded-2xl border border-white/10 bg-white/5 backdrop-blur-xl hover:bg-white/10 transition-all duration-300 text-white"
            >
              Login
            </Link>

          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-5 pt-6">

            <div className="bg-white/5 border border-white/10 rounded-3xl p-5 backdrop-blur-xl">
              <h2 className="text-3xl font-bold text-white">
                AI
              </h2>

              <p className="text-sm text-slate-300 mt-3 leading-relaxed">
                Adaptive learning intelligence
              </p>
            </div>

            <div className="bg-white/5 border border-white/10 rounded-3xl p-5 backdrop-blur-xl">
              <h2 className="text-3xl font-bold text-white">
                RAG
              </h2>

              <p className="text-sm text-slate-300 mt-3 leading-relaxed">
                Context aware document analysis
              </p>
            </div>

            <div className="bg-white/5 border border-white/10 rounded-3xl p-5 backdrop-blur-xl">
              <h2 className="text-3xl font-bold text-white">
                ML
              </h2>

              <p className="text-sm text-slate-300 mt-3 leading-relaxed">
                AI driven performance predictions
              </p>
            </div>

          </div>

        </div>

        {/* RIGHT SECTION */}
        <div className="relative flex items-center justify-center lg:justify-end">

          <div className="absolute w-[350px] h-[350px] bg-indigo-500/20 blur-[120px] rounded-full" />

          <div className="relative w-full max-w-[520px] bg-white/5 border border-white/10 rounded-[36px] p-8 lg:p-10 backdrop-blur-2xl shadow-2xl shadow-black/50">

            <div className="space-y-8">

              <div>
                <p className="text-cyan-300 text-sm mb-3">
                  AI Dashboard Preview
                </p>

                <h2 className="text-4xl font-black text-white leading-tight">
                  Smart Study Insights
                </h2>
              </div>

              <div className="space-y-6">

                <div className="bg-slate-900/50 rounded-3xl p-5 border border-white/10">

                  <div className="flex items-center justify-between mb-4">
                    <span className="text-slate-200">
                      Study Completion
                    </span>

                    <span className="text-white font-semibold">
                      82%
                    </span>
                  </div>

                  <div className="w-full h-4 bg-slate-700 rounded-full overflow-hidden">
                    <div className="w-[82%] h-full bg-gradient-to-r from-indigo-400 to-cyan-400 rounded-full" />
                  </div>

                </div>

                <div className="grid grid-cols-2 gap-5">

                  <div className="bg-slate-900/50 rounded-3xl p-6 border border-white/10">
                    <h3 className="text-4xl font-black text-indigo-300">
                      12
                    </h3>

                    <p className="text-slate-300 mt-3">
                      Active Topics
                    </p>
                  </div>

                  <div className="bg-slate-900/50 rounded-3xl p-6 border border-white/10">
                    <h3 className="text-4xl font-black text-cyan-300">
                      6h
                    </h3>

                    <p className="text-slate-300 mt-3">
                      Planned Today
                    </p>
                  </div>

                </div>

                <div className="bg-gradient-to-r from-indigo-500/20 to-cyan-500/20 border border-cyan-400/20 rounded-3xl p-6">
                  <p className="text-slate-200 leading-relaxed">
                    Your productivity increased by
                    <span className="text-cyan-300 font-semibold">
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