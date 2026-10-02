"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getUser, signOut } from "@/lib/auth";
import { api } from "@/lib/api";
import { getAccessToken } from "@/lib/auth";

export default function ProfilePage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [profile, setProfile] = useState<Record<string, unknown> | null>(null);

  useEffect(() => {
    (async () => {
      const u = await getUser();
      setEmail(u?.email || "");
      const meta = u?.user_metadata as { full_name?: string } | undefined;
      setName(meta?.full_name || "");
      const token = await getAccessToken();
      if (token) {
        try {
          setProfile(await api.me(token));
        } catch {
          /* ignore */
        }
      }
    })();
  }, []);

  async function logout() {
    await signOut();
    router.replace("/login");
  }

  return (
    <div className="mx-auto max-w-lg px-4 pt-8 pb-12">
      <h1 className="text-xl font-semibold mb-6">Profile</h1>
      <div className="royce-card p-6 space-y-4">
        <div className="flex items-center gap-4">
          <div className="h-14 w-14 rounded-full bg-gradient-to-br from-gold-200 to-ivory-300 flex items-center justify-center text-xl font-semibold text-gold-600">
            {(name || email || "R")[0].toUpperCase()}
          </div>
          <div>
            <p className="font-medium">{name || (profile?.display_name as string) || "Royce user"}</p>
            <p className="text-sm text-slate-muted">{email}</p>
          </div>
        </div>
        <button type="button" onClick={() => void logout()} className="royce-btn-secondary w-full mt-4">
          Sign out
        </button>
      </div>
    </div>
  );
}
