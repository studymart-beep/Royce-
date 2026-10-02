import type { ReactNode } from "react";
import { BottomNav } from "@/components/BottomNav";
import { Sidebar } from "@/components/Sidebar";
import { AuthGuard } from "@/components/AuthGuard";

export default function AppLayout({ children }: { children: ReactNode }) {
  return (
    <AuthGuard>
      <div className="flex min-h-screen bg-ivory-100">
        <Sidebar />
        <div className="flex-1 flex flex-col min-w-0">
          <main className="flex-1 pb-20 md:pb-6">{children}</main>
          <BottomNav />
        </div>
      </div>
    </AuthGuard>
  );
}