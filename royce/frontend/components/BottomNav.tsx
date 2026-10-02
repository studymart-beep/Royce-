"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home, MessageCircle, Brain, Wrench, User } from "lucide-react";
import { cn } from "@/lib/utils";

const items = [
  { href: "/app", label: "Home", icon: Home },
  { href: "/app/chat", label: "Chats", icon: MessageCircle },
  { href: "/app/memories", label: "Memory", icon: Brain },
  { href: "/app/tools", label: "Tools", icon: Wrench },
  { href: "/app/profile", label: "Profile", icon: User },
];

export function BottomNav() {
  const pathname = usePathname();
  return (
    <nav className="fixed bottom-0 inset-x-0 z-40 border-t border-ivory-300/80 bg-ivory-50/95 backdrop-blur-md md:hidden">
      <ul className="flex items-center justify-around px-2 py-2 safe-pb">
        {items.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || (href !== "/app" && pathname.startsWith(href));
          return (
            <li key={href}>
              <Link
                href={href}
                className={cn(
                  "flex flex-col items-center gap-0.5 px-3 py-1.5 rounded-xl text-[11px] transition",
                  active ? "text-gold-500" : "text-slate-muted hover:text-slate-soft"
                )}
              >
                <Icon className={cn("h-5 w-5", active && "stroke-[2.25]")} />
                <span>{label}</span>
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
