"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { api } from "@/lib/api";

export default function DocumentDetailPage() {
  const { id } = useParams();
  const [document, setDocument] = useState(null);
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState(null);
  const [pending, setPending] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function fetchDocument() {
      try {
        const payload = await api.getDocument(id);

        if (cancelled) return;

        setDocument(payload.document);
      } catch (failure) {
        if (cancelled) return;

        setError(failure.message);
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
      setError(failure.message);
    } finally {
      setPending(false);
    }
  }

  if (error && document === null) {
    return <p className="text-sm text-red-700">{error}</p>;
  }

  if (document === null) {
    return <p className="text-sm text-neutral-500">Loading...</p>;
  }

  return (
    <div>
      <Link href="/documents" className="text-sm text-neutral-500 underline">
        Back to documents
      </Link>

      <h1 className="mt-4 text-2xl font-semibold">{document.title}</h1>
      <p className="mt-1 text-sm text-neutral-600">
        {document.document_type.replace(/_/g, " ")} · {document.processing_status} ·{" "}
        {Math.round(document.size_bytes / 1024)} KB
      </p>

      {document.processing_status === "failed" ? (
        <p role="alert" className="mt-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
          This document could not be processed.
        </p>
      ) : null}

      <div className="mt-6 flex items-center gap-3">
        <button
          type="button"
          onClick={summarise}
          disabled={pending || document.processing_status !== "processed"}
          className="rounded-md bg-neutral-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          {pending ? "Summarising..." : "Summarise"}
        </button>
      </div>

      {error ? (
        <p role="alert" className="mt-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </p>
      ) : null}

      {summary ?? document.summary ? (
        <section className="mt-6 rounded-lg border border-neutral-200 bg-white p-6">
          <h2 className="text-sm font-semibold">Summary</h2>
          <p className="mt-2 whitespace-pre-wrap text-sm text-neutral-700">
            {summary ?? document.summary}
          </p>
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
    </div>
  );
}
