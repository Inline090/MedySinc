"use client";

import Link from "next/link";
import type { FormEvent, KeyboardEvent } from "react";
import { useEffect, useRef, useState } from "react";

import { AiDisclaimer } from "@/components/disclaimer";
import { api } from "@/lib/api";
import type { Answer } from "@/lib/types";

interface Turn {
  id: number;
  question: string;
  answer: Answer | null;
  error: string | null;
}

export default function AskPage() {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [question, setQuestion] = useState("");
  const [pending, setPending] = useState(false);
  const nextId = useRef(0);
  const endOfThread = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endOfThread.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [turns]);

  async function ask(text: string) {
    const asked = text.trim();

    if (asked.length < 3 || pending) return;

    const id = nextId.current;
    nextId.current += 1;

    setTurns((current) => [...current, { id, question: asked, answer: null, error: null }]);
    setQuestion("");
    setPending(true);

    try {
      const answer = await api.ask(asked);
      setTurns((current) => current.map((turn) => (turn.id === id ? { ...turn, answer } : turn)));
    } catch (failure) {
      const message = failure instanceof Error ? failure.message : "Could not answer that.";
      setTurns((current) => current.map((turn) => (turn.id === id ? { ...turn, error: message } : turn)));
    } finally {
      setPending(false);
    }
  }

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void ask(question);
  }

  function onKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    // Pressing Enter sends the message. Holding Shift + Enter adds a new line.
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void ask(question);
    }
  }

  return (
    <div>
      <h1 className="text-2xl font-semibold">Ask your documents</h1>
      <p className="mt-2 text-sm text-neutral-600">
        Answers come only from the documents you uploaded, and every answer names its sources.
      </p>

      <div className="mt-6">
        {turns.map((turn, position) => (
          <div
            key={turn.id}
            className={`space-y-2 ${position > 0 ? "mt-6 border-t border-neutral-200 pt-6" : ""}`}
          >
            <p className="text-xs text-neutral-400">You asked</p>

            <div className="flex justify-end">
              <p className="max-w-[75%] rounded-2xl bg-neutral-900 px-4 py-2 text-sm text-white">
                {turn.question}
              </p>
            </div>

            {turn.answer === null && turn.error === null ? (
              <p className="text-sm text-neutral-500">Searching your documents...</p>
            ) : null}

            {turn.error !== null ? (
              <p role="alert" className="max-w-[85%] rounded-2xl bg-red-50 px-4 py-3 text-sm text-red-700">
                {turn.error}
              </p>
            ) : null}

            {turn.answer !== null ? <AnswerBubble answer={turn.answer} /> : null}
          </div>
        ))}

        <div ref={endOfThread} />
      </div>

      <form onSubmit={onSubmit} className="mt-6 border-t border-neutral-200 pt-6">
        <p className="text-xs text-neutral-400">
          Each question is searched on its own, so ask it in full rather than as a follow-up.
        </p>

        <textarea
          value={question}
          required
          minLength={3}
          maxLength={500}
          rows={2}
          placeholder="When was I prescribed Dolo 650, and how often?"
          onChange={(event) => setQuestion(event.target.value)}
          onKeyDown={onKeyDown}
          className="w-full rounded-2xl border border-neutral-300 px-4 py-3 text-sm outline-none focus:border-neutral-900"
        />

        <button
          type="submit"
          disabled={pending}
          className="mt-3 rounded-full bg-neutral-900 px-5 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          {pending ? "Searching..." : "Ask"}
        </button>
      </form>

      {turns.length > 0 ? <AiDisclaimer /> : null}
    </div>
  );
}

function AnswerBubble({ answer }: { answer: Answer }) {
  const [showSources, setShowSources] = useState(false);

  if (answer.status === "not_found") {
    return (
      <div className="max-w-[85%] rounded-2xl border border-amber-300 bg-amber-50 px-4 py-3">
        <p className="text-sm text-neutral-700">{answer.answer}</p>
      </div>
    );
  }

  return (
    <div className="max-w-[85%] rounded-2xl border border-neutral-200 bg-white px-4 py-3">
      <p className="whitespace-pre-wrap text-sm text-neutral-800">{answer.answer}</p>

      <div className="mt-3 flex items-center gap-3 text-xs">
        <ConfidenceWord confidence={answer.confidence} />

        {answer.sources.length > 0 ? (
          <button
            type="button"
            onClick={() => setShowSources((open) => !open)}
            title={showSources ? "Hide sources" : "Show sources"}
            aria-label={showSources ? "Hide sources" : "Show sources"}
            aria-expanded={showSources}
            className="flex items-center gap-1 rounded-full border border-neutral-300 px-2 py-0.5 text-neutral-600 hover:border-neutral-900 hover:text-neutral-900"
          >
            <ClipIcon />
            {answer.sources.length}
          </button>
        ) : null}

        {answer.cached ? <span className="text-neutral-400">cached</span> : null}
      </div>

      {showSources ? (
        <ol className="mt-3 space-y-2 border-t border-neutral-200 pt-3">
          {answer.sources.map((source, position) => (
            <li key={`${source.document_id}-${source.chunk_index}`}>
              <div className="flex items-baseline justify-between gap-4">
                <Link
                  href={`/documents/${source.document_id}`}
                  className="truncate text-xs font-medium underline"
                >
                  [{position + 1}] {source.document_title}
                </Link>
                <span className="shrink-0 text-xs text-neutral-400">
                  {source.similarity.toFixed(2)}
                </span>
              </div>

              <blockquote className="mt-1 border-l-2 border-neutral-200 pl-3 text-xs text-neutral-600">
                {source.excerpt}
              </blockquote>
            </li>
          ))}
        </ol>
      ) : null}
    </div>
  );
}

function ConfidenceWord({ confidence }: { confidence: "Low" | "High" | null }) {
  if (confidence === null) return null;

  const tone =
    confidence === "High"
      ? "bg-emerald-50 text-emerald-700"
      : "bg-amber-50 text-amber-700";

  return (
    <span className={`rounded-full px-2 py-0.5 font-medium ${tone}`} title={`${confidence} confidence`}>
      {confidence}
    </span>
  );
}

function ClipIcon() {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="h-3.5 w-3.5 shrink-0"
    >
      <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" />
    </svg>
  );
}
