"use client";

import Link from "next/link";
import type { ChangeEvent, FormEvent } from "react";
import { useCallback, useEffect, useRef, useState } from "react";

import { api } from "@/lib/api";
import type { DocumentSummary } from "@/lib/types";

type LoadStatus = "loading" | "ready" | "error";

function formatDate(value: string): string {
  return new Date(value).toLocaleDateString();
}

interface UploadFormProps {
  onUploaded: () => void;
}

export function UploadForm({ onUploaded }: UploadFormProps) {
  const formRef = useRef<HTMLFormElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const [dragging, setDragging] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    if (file === null) {
      setError("Choose a PDF or an image to upload.");
      return;
    }

    setPending(true);

    try {
      const form = new FormData();
      form.append("file", file);

      if (title.trim()) form.append("title", title.trim());

      await api.uploadDocument(form);

      setFile(null);
      setTitle("");
      // React drops the event target after the async wait, so we need to use a ref to clear the form.
      formRef.current?.reset();
      onUploaded();
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : "Upload failed.");
    } finally {
      setPending(false);
    }
  }

  return (
    <form
      ref={formRef}
      onSubmit={onSubmit}
      className="rounded-lg border border-neutral-200 bg-white p-6"
    >
      <h2 className="text-sm font-semibold">Upload a document</h2>

      <div className="mt-4">
        <span className="text-sm font-medium">File</span>

        <label
          className="file-drop mt-1"
          data-dragging={dragging}
          onDragOver={(event) => {
            event.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={(event) => {
            event.preventDefault();
            setDragging(false);
            setFile(event.dataTransfer.files?.[0] ?? null);
          }}
        >
          <input
            type="file"
            accept="application/pdf,image/png,image/jpeg"
            onChange={(event: ChangeEvent<HTMLInputElement>) =>
              setFile(event.target.files?.[0] ?? null)
            }
            className="sr-only"
          />

          <svg
            aria-hidden="true"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            className="h-8 w-8 text-neutral-400"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M12 16V4m0 0L8 8m4-4 4 4M4 16v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2"
            />
          </svg>

          <span className="text-sm font-medium">
            {file ? file.name : "Choose a file or drag it here"}
          </span>
          <span className="text-xs text-neutral-500">PDF, PNG or JPEG, up to 10 MB</span>
        </label>
      </div>

      <div className="mt-4">
        <label className="block text-sm">
          <span className="font-medium">Title</span>
          <input
            type="text"
            value={title}
            placeholder="Defaults to the file name"
            onChange={(event) => setTitle(event.target.value)}
            className="mt-1 w-full rounded-md border border-neutral-300 px-3 py-2 text-sm"
          />
        </label>

      </div>

      {error ? (
        <p role="alert" className="mt-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </p>
      ) : null}

      <button
        type="submit"
        disabled={pending}
        className="mt-4 rounded-md bg-neutral-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
      >
        {pending ? "Uploading..." : "Upload"}
      </button>
    </form>
  );
}

export function DocumentList() {
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [status, setStatus] = useState<LoadStatus>("loading");
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const payload = await api.listDocuments();
      setDocuments(payload.documents);
      setStatus("ready");
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : "Could not load documents.");
      setStatus("error");
    }
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function fetchDocuments() {
      try {
        const payload = await api.listDocuments();

        if (cancelled) return;

        setDocuments(payload.documents);
        setStatus("ready");
      } catch (failure) {
        if (cancelled) return;

        setError(failure instanceof Error ? failure.message : "Could not load documents.");
        setStatus("error");
      }
    }

    fetchDocuments();

    return () => {
      cancelled = true;
    };
  }, []);

  async function remove(id: string) {
    await api.deleteDocument(id);
    await load();
  }

  return (
    <section className="mt-8">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold">Your documents</h2>
        <button
          type="button"
          onClick={load}
          className="rounded-md border border-neutral-300 px-3 py-1.5 text-sm font-medium"
        >
          Refresh
        </button>
      </div>

      {status === "loading" ? <p className="mt-4 text-sm text-neutral-500">Loading...</p> : null}

      {status === "error" ? (
        <p role="alert" className="mt-4 text-sm text-red-700">
          {error}
        </p>
      ) : null}

      {status === "ready" && documents.length === 0 ? (
        <p className="mt-4 text-sm text-neutral-500">No documents yet.</p>
      ) : null}

      {documents.length > 0 ? (
        <ul className="mt-4 divide-y divide-neutral-200 rounded-lg border border-neutral-200 bg-white">
          {documents.map((document) => (
            <li key={document.id} className="flex items-center justify-between gap-4 px-4 py-3">
              <div className="min-w-0">
                <Link
                  href={`/documents/${document.id}`}
                  className="block truncate text-sm font-medium underline"
                >
                  {document.title}
                </Link>
                <p className="mt-0.5 text-xs text-neutral-500">
                  {formatDate(document.created_at)}. {document.processing_status}
                </p>
              </div>

              <button
                type="button"
                onClick={() => remove(document.id)}
                className="shrink-0 rounded-md border border-neutral-300 px-3 py-1.5 text-xs font-medium"
              >
                Delete
              </button>
            </li>
          ))}
        </ul>
      ) : null}
    </section>
  );
}
