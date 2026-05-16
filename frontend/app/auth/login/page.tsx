import Link from "next/link";

import LoginForm from "@/components/forms/LoginForm";

export default function LoginPage() {
  return (
    <main className="min-h-screen flex items-center justify-center px-6 py-12">

      <div className="w-full max-w-md bg-white/5 border border-white/10 backdrop-blur-2xl rounded-[32px] p-8 shadow-2xl">

        <div className="mb-8 text-center">
          <h1 className="text-4xl font-black mb-3">
            Welcome Back
          </h1>

          <p className="text-slate-300">
            Continue your AI powered learning journey
          </p>
        </div>

        <LoginForm />

        <p className="text-center text-slate-300 mt-6">
          Don&apos;t have an account?{" "}

          <Link
            href="/auth/register"
            className="text-cyan-300 hover:text-cyan-200 underline underline-offset-2 font-semibold"
          >
            Register
          </Link>
        </p>
      </div>
    </main>
  );
}