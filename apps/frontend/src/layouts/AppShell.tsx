import { Link } from "react-router-dom";
import { useNavigate } from "react-router-dom";
import { Outlet } from "react-router-dom";
import { useEffect } from "react";

import { useSession } from "@/lib/session";

export default function AppLayout() {
  const { status, user, signOut } = useSession();
  const navigate = useNavigate();

  useEffect(() => {
    if (status === "anonymous") {
      navigate("/sign-in");
    }
  }, [status, navigate]);

  if (status !== "authenticated") {
    return (
      <main className="flex min-h-screen items-center justify-center px-6">
        <div className="card w-full max-w-sm">
          <p className="text-sm text-neutral-500">Loading...</p>
        </div>
      </main>
    );
  }

  return (
    <div className="mx-auto max-w-4xl px-6 py-8">
      <div className="card">
        <header className="flex flex-wrap items-center justify-between gap-4 border-b border-neutral-200 pb-4">
          <div className="flex items-center gap-6">
            <Link to="/dashboard" className="text-sm font-semibold">
              MedSync
            </Link>
            <Link to="/documents" className="text-sm text-neutral-600">
              Documents
            </Link>
            <Link to="/medications" className="text-sm text-neutral-600">
              Medications
            </Link>
            <Link to="/ask" className="text-sm text-neutral-600">
              Ask
            </Link>
          </div>

          <div className="flex items-center gap-4 text-sm">
            <span className="text-neutral-500">{user?.email}</span>
            <button
              type="button"
              onClick={async () => {
                await signOut();
                navigate("/sign-in");
              }}
              className="rounded-md border border-neutral-300 px-3 py-1.5 font-medium"
            >
              Sign out
            </button>
          </div>
        </header>

        <main className="pt-6"><Outlet /></main>
      </div>
    </div>
  );
}
