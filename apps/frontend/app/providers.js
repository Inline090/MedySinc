"use client";

import { SessionProvider } from "@/lib/session";

export function Providers({ children }) {
  return <SessionProvider>{children}</SessionProvider>;
}
