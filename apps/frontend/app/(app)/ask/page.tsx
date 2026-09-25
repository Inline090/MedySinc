"use client";

import Link from "next/link";
import type { FormEvent } from "react";
import { useState } from "react";

import { api } from "@/lib/api";
import type { Answer } from "@/lib/types";

export default function AskPage() {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<Answer | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setPending(true);

    try {
      setResult(await api.ask(question));
    } catch (failure) {
      setResult(null);
      setError(failure instanceof Error ? failure.message : "Could not answer that.");
    } finally {
      setPending(false);
    }
  }

  const refused = result !== null && result.model === null;

  return (
    <div>
      <h1 className="text-2xl font-semibold">Ask your documents</h1>
      <p className="mt-2 text-sm text-neutral-600">
        Answers come only from the documents you uploaded, and every answer names its sources.
      </p>

      <form onSubmit={onSubmit} className="mt-6">
        <textarea
          value={question}
          required
          minLength={3}
          maxLength={500}
          rows={3}
          placeholder="When was I prescribed Dolo 650, and how often?"
          onChange={(event) => setQuestion(event.target.value)}
          className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm outline-none focus:border-neutral-900"
        />

        <button
          type="submit"
          disabled={pending}
          className="mt-3 rounded-md bg-neutral-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          {pending ? "Searching your documents..." : "Ask"}
        </button>
      </form>

      {error ? (
        <p role="alert" className="mt-6 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </p>
      ) : null}

      {refused ? (
        <aside className="mt-6 rounded-lg border border-amber-300 bg-amber-50 p-6">
          <h2 className="text-sm font-semibold">Not found in your documents</h2>
          <p className="mt-2 text-sm text-neutral-700">{result.answer}</p>
          <p className="mt-2 text-xs text-neutral-500">
            Nothing retrieved cleared the similarity threshold, so no answer was generated.
          </p>
        </aside>
      ) : null}

      {result !== null && !refused ? (
        <>
          <section className="mt-6 rounded-lg border border-neutral-200 bg-white p-6">
            <h2 className="text-sm font-semibold">Answer</h2>
            <p className="mt-2 whitespace-pre-wrap text-sm text-neutral-800">{result.answer}</p>
            <p className="mt-3 text-xs text-neutral-500">
              {result.sources.length} source{result.sources.length === 1 ? "" : "s"} cited
              {result.model ? ` · ${result.model}` : ""}
            </p>
          </section>

          <section className="mt-6">
            <h2 className="text-sm font-semibold">Sources</h2>

            <ol className="mt-3 space-y-3">
              {result.sources.map((source, position) => (
                <li
                  key={`${source.document_id}-${source.chunk_index}`}
                  className="rounded-lg border border-neutral-200 bg-white p-4"
                >
                  <div className="flex items-baseline justify-between gap-4">
                    <Link
                      href={`/documents/${source.document_id}`}
                      className="text-sm font-medium underline"
                    >
                      [{position + 1}] {source.document_title}
                    </Link>
                    <span className="shrink-0 text-xs text-neutral-500">
                      similarity {source.similarity.toFixed(3)}
                    </span>
                  </div>

                  <blockquote className="mt-2 border-l-2 border-neutral-200 pl-3 text-xs text-neutral-600">
                    {source.excerpt}
                  </blockquote>
                </li>
              ))}
            </ol>
          </section>
        </>
      ) : null}
    </div>
  );
}
