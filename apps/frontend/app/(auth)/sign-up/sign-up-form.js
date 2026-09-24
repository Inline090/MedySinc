"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { api } from "@/lib/api";
import { useSession } from "@/lib/session";

import { GoogleButton } from "../google-button";

export function SignUpForm() {
  const router = useRouter();
  const { refresh } = useSession();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [error, setError] = useState(null);
  const [pending, setPending] = useState(false);

  async function onSubmit(event) {
    event.preventDefault();
    setError(null);
    setPending(true);

    try {
      await api.register({ email, password, full_name: fullName || null });
      await api.login({ email, password });
      await refresh();
      router.replace("/dashboard");
    } catch (failure) {
      setError(failure.message);
    } finally {
      setPending(false);
    }
  }

  return (
    <form
      onSubmit={onSubmit}
      className="w-full max-w-sm rounded-lg border border-neutral-200 bg-white p-8 shadow-sm"
    >
      <h1 className="text-xl font-semibold">Create an account</h1>
      <p className="mt-1 text-sm text-neutral-500">Upload documents and ask questions about them.</p>

      <label className="mt-6 block text-sm font-medium" htmlFor="fullName">
        Full name
      </label>
      <input
        id="fullName"
        type="text"
        autoComplete="name"
        value={fullName}
        onChange={(event) => setFullName(event.target.value)}
        className="mt-1 w-full rounded-md border border-neutral-300 px-3 py-2 text-sm outline-none focus:border-neutral-900"
      />

      <label className="mt-4 block text-sm font-medium" htmlFor="email">
        Email
      </label>
      <input
        id="email"
        type="email"
        required
        autoComplete="email"
        value={email}
        onChange={(event) => setEmail(event.target.value)}
        className="mt-1 w-full rounded-md border border-neutral-300 px-3 py-2 text-sm outline-none focus:border-neutral-900"
      />

      <label className="mt-4 block text-sm font-medium" htmlFor="password">
        Password
      </label>
      <input
        id="password"
        type="password"
        required
        minLength={8}
        autoComplete="new-password"
        value={password}
        onChange={(event) => setPassword(event.target.value)}
        className="mt-1 w-full rounded-md border border-neutral-300 px-3 py-2 text-sm outline-none focus:border-neutral-900"
      />
      <p className="mt-1 text-xs text-neutral-500">At least 8 characters.</p>

      {error ? (
        <p role="alert" className="mt-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </p>
      ) : null}

      <button
        type="submit"
        disabled={pending}
        className="mt-6 w-full rounded-md bg-neutral-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
      >
        {pending ? "Creating account..." : "Create account"}
      </button>

      <div className="mt-6 flex items-center gap-3">
        <span className="h-px flex-1 bg-neutral-200" />
        <span className="text-xs text-neutral-400">or</span>
        <span className="h-px flex-1 bg-neutral-200" />
      </div>

      <GoogleButton />

      <p className="mt-4 text-center text-sm text-neutral-500">
        Already registered?{" "}
        <Link href="/sign-in" className="font-medium text-neutral-900 underline">
          Sign in
        </Link>
      </p>
    </form>
  );
}
