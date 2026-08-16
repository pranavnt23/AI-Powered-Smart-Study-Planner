import Link from "next/link";

import LoginForm from "@/components/forms/LoginForm";

export default function LoginPage() {
  return (
    <main className="min-h-screen flex items-center justify-center px-6 py-12">

      <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-lg p-8 shadow-sm">

        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold mb-3 text-white">
            Welcome Back
          </h1>

          <p className="text-slate-400 text-sm">
            Continue your AI powered learning journey
          </p>
        </div>

        <LoginForm />

        <p className="text-center text-slate-400 mt-6 text-sm">
          Don&apos;t have an account?{" "}

          <Link
            href="/auth/register"
            className="text-blue-400 hover:text-blue-300 font-semibold"
          >
            Register
          </Link>
        </p>
      </div>
    </main>
  );
}