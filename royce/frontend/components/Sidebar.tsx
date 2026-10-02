"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Home,
  MessageCircle,
  Brain,
  Wrench,
  User,
  Settings,
  FileText,
  CheckSquare,
} from "lucide-react";
import { cn } from "@/lib/utils";

const items = [
  { href: "/app", label: "Home", icon: Home },
  { href: "/app/chat", label: "Chats", icon: MessageCircle },
  { href: "/app/memories", label: "Memory", icon: Brain },
  { href: "/app/tasks", label: "Tasks", icon: CheckSquare },
  { href: "/app/files", label: "Files", icon: FileText },
  { href: "/app/tools", label: "Tools", icon: Wrench },
  { href: "/app/settings", label: "Settings", icon: Settings },
  { href: "/app/profile", label: "Profile", icon: User },
];

export function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="hidden md:flex md:w-60 lg:w-64 flex-col border-r border-ivory-300/80 bg-ivory-50/80 min-h-screen sticky top-0">
      <div className="flex items-center gap-3 px-5 py-6">
        <div className="h-9 w-9 rounded-full bg-gradient-to-br from-gold-200 to-ivory-300 flex items-center justify-center shadow-soft">
          <span className="text-sm font-semibold text-gold-600">R</span>
        </div>
        <div>
          <p className="font-semibold text-sm tracking-tight">Royce</p>
          <p className="text-[11px] text-slate-muted">Personal AI</p>
        </div>
      </div>
      <nav className="flex-1 px-3 space-y-0.5">
        {items.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || (href !== "/app" && pathname.startsWith(href));
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition",
                active
                  ? "bg-gold-50 text-gold-600 font-medium"
                  : "text-slate-soft hover:bg-ivory-200/60"
              )}
            >
              <Icon className="h-4.5 w-4.5 shrink-0" size={18} />
              {label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
