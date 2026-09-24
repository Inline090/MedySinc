"use client";

import type { ReactNode } from "react";
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

import { api } from "./api";
import type { Credentials } from "./api";
import type { User } from "./types";

export type SessionStatus = "loading" | "authenticated" | "anonymous";

interface SessionValue {
  user: User | null;
  status: SessionStatus;
  refresh: () => Promise<void>;
  signIn: (credentials: Credentials) => Promise<User>;
  signOut: () => Promise<void>;
}

const SessionContext = createContext<SessionValue | null>(null);

export function SessionProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [status, setStatus] = useState<SessionStatus>("loading");

  const refresh = useCallback(async () => {
    try {
      const payload = await api.currentUser();
      setUser(payload.user);
      setStatus("authenticated");
    } catch {
      setUser(null);
      setStatus("anonymous");
    }
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const payload = await api.currentUser();

        if (cancelled) return;

        setUser(payload.user);
        setStatus("authenticated");
      } catch {
        if (cancelled) return;

        setUser(null);
        setStatus("anonymous");
      }
    }

    load();

    return () => {
      cancelled = true;
    };
  }, []);

  const value = useMemo<SessionValue>(
    () => ({
      user,
      status,
      refresh,
      signIn: async (credentials) => {
        const payload = await api.login(credentials);
        setUser(payload.user);
        setStatus("authenticated");
        return payload.user;
      },
      signOut: async () => {
        await api.logout();
        setUser(null);
        setStatus("anonymous");
      },
    }),
    [user, status, refresh],
  );

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

export function useSession(): SessionValue {
  const context = useContext(SessionContext);

  if (context === null) {
    throw new Error("useSession must be used within a SessionProvider");
  }

  return context;
}
