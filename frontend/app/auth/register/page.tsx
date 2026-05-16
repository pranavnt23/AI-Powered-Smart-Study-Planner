import Link from "next/link";

import RegisterForm from "@/components/forms/RegisterForm";

export default function RegisterPage() {
  return (
    <main className="min-h-screen flex items-center justify-center px-6 py-12">

      <div className="w-full max-w-md bg-white/5 border border-white/10 backdrop-blur-2xl rounded-[32px] p-8 shadow-2xl">

        <div className="mb-8 text-center">
          <h1 className="text-4xl font-black mb-3">
            Create Account
          </h1>

          <p className="text-slate-300">
            Start building your smart learning workflow
          </p>
        </div>

        <RegisterForm />

        <p className="text-center text-slate-300 mt-6">
          Already have an account?{" "}

          <Link
            href="/auth/login"
            className="text-cyan-300 hover:text-cyan-200"
          >
            Login
          </Link>
        </p>
      </div>
    </main>
  );
}