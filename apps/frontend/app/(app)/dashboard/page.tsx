"use client";

import { useSession } from "@/lib/session";

export default function DashboardPage() {
  const { user } = useSession();

  return (
    <div>
      <h1 className="text-2xl font-semibold">
        Welcome{user?.full_name ? `, ${user.full_name}` : ""}
      </h1>
      <p className="mt-2 text-sm text-neutral-600">
        Signed in as {user?.email}. Your documents will appear here.
      </p>
    </div>
  );
}
