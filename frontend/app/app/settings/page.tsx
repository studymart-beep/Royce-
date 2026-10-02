"use client";

import Link from "next/link";
import { ChevronRight, KeyRound, Palette, Bell, Shield, Globe, Info } from "lucide-react";

const sections = [
  { href: "/app/settings/providers", label: "AI Providers", desc: "API keys, models, priority", icon: KeyRound },
  { href: "/app/settings/appearance", label: "Appearance", desc: "Theme, colors", icon: Palette },
  { href: "/app/settings/notifications", label: "Notifications", desc: "Chat, email, reminders", icon: Bell },
  { href: "/app/settings/privacy", label: "Privacy & Data", desc: "Manage your data", icon: Shield },
  { href: "/app/settings/language", label: "Language", desc: "English (US)", icon: Globe },
  { href: "/app/settings/about", label: "About Royce", desc: "Version 0.1.0", icon: Info },
];

export default function SettingsPage() {
  return (
    <div className="mx-auto max-w-lg px-4 pt-8">
      <h1 className="text-xl font-semibold mb-6">Settings</h1>
      <ul className="royce-card divide-y divide-ivory-200 overflow-hidden">
        {sections.map((s) => (
          <li key={s.href}>
            <Link
              href={s.href}
              className="flex items-center gap-3 px-4 py-3.5 hover:bg-ivory-100/80 transition"
            >
              <span className="h-9 w-9 rounded-xl bg-gold-50 text-gold-500 flex items-center justify-center shrink-0">
                <s.icon size={18} />
              </span>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium">{s.label}</p>
                <p className="text-xs text-slate-muted truncate">{s.desc}</p>
              </div>
              <ChevronRight size={16} className="text-slate-muted" />
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
