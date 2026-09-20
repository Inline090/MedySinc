"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

import { api } from "./api";

const SessionContext = createContext(null);

export function SessionProvider({ children }) {
  const [user, setUser] = useState(null);
  const [status, setStatus] = useState("loading");

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

  const value = useMemo(
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

export function useSession() {
  const context = useContext(SessionContext);

  if (context === null) {
    throw new Error("useSession must be used within a SessionProvider");
  }

  return context;
}
