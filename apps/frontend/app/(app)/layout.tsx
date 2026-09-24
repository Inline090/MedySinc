"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import type { ReactNode } from "react";
import { useEffect } from "react";

import { useSession } from "@/lib/session";

export default function AppLayout({ children }: { children: ReactNode }) {
  const { status, user, signOut } = useSession();
  const router = useRouter();

  useEffect(() => {
    if (status === "anonymous") {
      router.replace("/sign-in");
    }
  }, [status, router]);

  if (status !== "authenticated") {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <p className="text-sm text-neutral-500">Loading...</p>
      </main>
    );
  }

  return (
    <div className="min-h-screen">
      <header className="border-b border-neutral-200 bg-white">
        <div className="mx-auto flex max-w-4xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-6">
            <Link href="/dashboard" className="text-sm font-semibold">
              MedSync
            </Link>
            <Link href="/documents" className="text-sm text-neutral-600">
              Documents
            </Link>
          </div>

          <div className="flex items-center gap-4 text-sm">
            <span className="text-neutral-500">{user?.email}</span>
            <button
              type="button"
              onClick={async () => {
                await signOut();
                router.replace("/sign-in");
              }}
              className="rounded-md border border-neutral-300 px-3 py-1.5 font-medium"
            >
              Sign out
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-4xl px-6 py-8">{children}</main>
    </div>
  );
}
