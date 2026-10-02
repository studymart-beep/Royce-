import Link from "next/link";

export default function LandingPage() {
  return (
    <main className="relative min-h-screen flex flex-col items-center justify-center px-6 overflow-hidden">
      {/* Soft abstract blob */}
      <div
        className="pointer-events-none absolute inset-0 opacity-70"
        style={{
          background:
            "radial-gradient(ellipse 80% 50% at 50% 40%, #F5E8C7 0%, transparent 60%), radial-gradient(ellipse 60% 40% at 70% 70%, #EDE2CF 0%, transparent 50%)",
        }}
      />
      <div className="relative z-10 flex flex-col items-center text-center max-w-md">
        <div className="mb-6 h-16 w-16 rounded-full bg-gradient-to-br from-gold-200 to-ivory-300 shadow-card flex items-center justify-center">
          <span className="text-2xl font-semibold text-gold-600">R</span>
        </div>
        <h1 className="text-4xl font-semibold tracking-tight text-slate-ink">Royce</h1>
        <p className="mt-2 text-slate-soft text-base">Your Personal AI Assistant</p>
        <p className="mt-8 text-sm text-slate-muted leading-relaxed">
          Think. Ask. Create.
          <br />
          Grow. Together.
        </p>
        <div className="mt-10 flex flex-col gap-3 w-full max-w-xs">
          <Link href="/app" className="royce-btn-primary w-full py-3">
            Get Started →
          </Link>
          <Link href="/login" className="royce-btn-secondary w-full py-3">
            Sign In
          </Link>
        </div>
      </div>
    </main>
  );
}
