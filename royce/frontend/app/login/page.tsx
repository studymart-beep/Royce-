"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { signInWithEmail, signUpWithEmail } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"signin" | "signup">("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      if (mode === "signin") {
        await signInWithEmail(email, password);
      } else {
        await signUpWithEmail(email, password, name || undefined);
      }
      router.push("/app");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Authentication failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen flex items-center justify-center px-4 bg-ivory-100">
      <div className="w-full max-w-sm royce-card p-8">
        <div className="text-center mb-8">
          <div className="mx-auto mb-3 h-12 w-12 rounded-full bg-gradient-to-br from-gold-200 to-ivory-300 flex items-center justify-center">
            <span className="text-lg font-semibold text-gold-600">R</span>
          </div>
          <h1 className="text-xl font-semibold">Welcome to Royce</h1>
          <p className="text-sm text-slate-soft mt-1">
            {mode === "signin" ? "Sign in to continue" : "Create your account"}
          </p>
        </div>
        <form onSubmit={onSubmit} className="space-y-4">
          {mode === "signup" && (
            <input
              className="royce-input"
              placeholder="Display name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              autoComplete="name"
            />
          )}
          <input
            className="royce-input"
            type="email"
            placeholder="Email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="email"
          />
          <input
            className="royce-input"
            type="password"
            placeholder="Password"
            required
            minLength={6}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete={mode === "signin" ? "current-password" : "new-password"}
          />
          {error && (
            <p className="text-sm text-red-600 bg-red-50 rounded-xl px-3 py-2">{error}</p>
          )}
          <button type="submit" className="royce-btn-primary w-full py-3" disabled={loading}>
            {loading ? "Please wait…" : mode === "signin" ? "Sign In" : "Create Account"}
          </button>
        </form>
        <p className="mt-6 text-center text-sm text-slate-soft">
          {mode === "signin" ? (
            <>
              No account?{" "}
              <button type="button" className="text-gold-500 font-medium" onClick={() => setMode("signup")}>
                Sign up
              </button>
            </>
          ) : (
            <>
              Already have an account?{" "}
              <button type="button" className="text-gold-500 font-medium" onClick={() => setMode("signin")}>
                Sign in
              </button>
            </>
          )}
        </p>
        <p className="mt-4 text-center">
          <Link href="/" className="text-xs text-slate-muted hover:text-slate-soft">
            ← Back
          </Link>
        </p>
      </div>
    </main>
  );
}
