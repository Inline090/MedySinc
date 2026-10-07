"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { AiDisclaimer } from "@/components/disclaimer";
import { api } from "@/lib/api";
import type { DocumentDetail } from "@/lib/types";

export default function DocumentDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [document, setDocument] = useState<DocumentDetail | null>(null);
  const [summary, setSummary] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [title, setTitle] = useState("");
  const [notes, setNotes] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function fetchDocument() {
      try {
        const payload = await api.getDocument(id);

        if (cancelled) return;

        setDocument(payload.document);
        setTitle(payload.document.title);
        setNotes(payload.document.notes ?? "");
      } catch (failure) {
        if (cancelled) return;

        setError(failure instanceof Error ? failure.message : "Could not load the document.");
      }
    }

    fetchDocument();

    return () => {
      cancelled = true;
    };
  }, [id]);

  async function summarise() {
    setError(null);
    setPending(true);

    try {
      const payload = await api.summarizeDocument(id);
      setSummary(payload.summary);
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : "Summarising failed.");
    } finally {
      setPending(false);
    }
  }

  async function save() {
    setError(null);
    setSaving(true);

    try {
      const payload = await api.updateDocument(id, { title, notes });
      setDocument(payload.document);
      setEditing(false);
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : "Saving failed.");
    } finally {
      setSaving(false);
    }
  }

  if (error && document === null) {
    return <p className="text-sm text-red-700">{error}</p>;
  }

  if (document === null) {
    return <p className="text-sm text-neutral-500">Loading...</p>;
  }

  const summaryText = summary ?? document.summary;

  return (
    <div>
      <Link href="/documents" className="text-sm text-neutral-500 underline">
        Back to documents
      </Link>

      <h1 className="mt-4 text-2xl font-semibold">{document.title}</h1>
      <p className="mt-1 text-sm text-neutral-600">
        {document.processing_status}. {Math.round(document.size_bytes / 1024)} KB
      </p>

      {document.processing_status === "failed" ? (
        <p role="alert" className="mt-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
          This document could not be processed.
        </p>
      ) : null}

      <div className="mt-6 flex flex-wrap items-center gap-3">
        <button
          type="button"
          onClick={summarise}
          disabled={pending || document.processing_status !== "processed"}
          className="rounded-md bg-neutral-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          {pending ? "Summarising..." : "Summarise"}
        </button>

        <a
          href={api.documentFileUrl(id)}
          className="rounded-md border border-neutral-300 px-4 py-2 text-sm font-medium"
        >
          Download
        </a>

        <button
          type="button"
          onClick={() => setEditing((value) => !value)}
          className="rounded-md border border-neutral-300 px-4 py-2 text-sm font-medium"
        >
          {editing ? "Close" : "Edit"}
        </button>
      </div>

      {editing ? (
        <div className="mt-4 grid gap-3 rounded-lg border border-neutral-200 bg-white p-4">
          <label className="block text-sm">
            <span className="font-medium">Title</span>
            <input
              type="text"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              className="mt-1 w-full rounded-md border border-neutral-300 px-3 py-2 text-sm"
            />
          </label>

          <label className="block text-sm">
            <span className="font-medium">Notes</span>
            <textarea
              value={notes}
              rows={3}
              onChange={(event) => setNotes(event.target.value)}
              className="mt-1 w-full rounded-md border border-neutral-300 px-3 py-2 text-sm"
            />
          </label>

          <div className="flex gap-2">
            <button
              type="button"
              onClick={save}
              disabled={saving}
              className="rounded-md bg-neutral-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
            >
              {saving ? "Saving..." : "Save"}
            </button>
            <button
              type="button"
              onClick={() => {
                setEditing(false);
                setTitle(document.title);
                setNotes(document.notes ?? "");
              }}
              className="rounded-md border border-neutral-300 px-4 py-2 text-sm font-medium"
            >
              Cancel
            </button>
          </div>
        </div>
      ) : null}

      {error ? (
        <p role="alert" className="mt-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </p>
      ) : null}

      {summaryText ? (
        <section className="mt-6 rounded-lg border border-neutral-200 bg-white p-6">
          <h2 className="flex items-center gap-2 text-sm font-semibold">
            <AttachmentIcon />
            Summary
          </h2>
          <p className="mt-2 whitespace-pre-wrap text-sm text-neutral-700">{summaryText}</p>
        </section>
      ) : null}

      {document.extracted_text ? (
        <section className="mt-6 rounded-lg border border-neutral-200 bg-white p-6">
          <h2 className="text-sm font-semibold">Extracted text</h2>
          <pre className="mt-2 max-h-96 overflow-auto whitespace-pre-wrap text-xs text-neutral-600">
            {document.extracted_text}
          </pre>
        </section>
      ) : null}

      <AiDisclaimer />
    </div>
  );
}

function AttachmentIcon() {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="h-4 w-4 shrink-0 text-neutral-400"
    >
      <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" />
    </svg>
  );
}
