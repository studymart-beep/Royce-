import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./globals.css";

export const metadata: Metadata = {
  title: "Royce — Your Personal AI Assistant",
  description: "Conversational AI with memory, tools, and multi-provider routing",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-ivory-100 text-slate-ink antialiased">
        {children}
      </body>
    </html>
  );
}
