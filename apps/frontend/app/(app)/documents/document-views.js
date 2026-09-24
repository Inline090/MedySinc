"use client";

import { useCallback, useEffect, useState } from "react";

import { api } from "@/lib/api";

const DOCUMENT_TYPES = ["lab_report", "prescription", "discharge_summary", "imaging", "other"];

function formatDate(value) {
  return new Date(value).toLocaleDateString();
}

export function UploadForm({ onUploaded }) {
  const [file, setFile] = useState(null);
  const [title, setTitle] = useState("");
  const [documentType, setDocumentType] = useState("other");
  const [tags, setTags] = useState("");
  const [error, setError] = useState(null);
  const [pending, setPending] = useState(false);

  async function onSubmit(event) {
    event.preventDefault();
    setError(null);

    if (file === null) {
      setError("Choose a PDF to upload.");
      return;
    }

    setPending(true);

    try {
      const form = new FormData();
      form.append("file", file);
      form.append("document_type", documentType);

      if (title.trim()) form.append("title", title.trim());
      if (tags.trim()) form.append("tags", tags.trim());

      await api.uploadDocument(form);

      setFile(null);
      setTitle("");
      setTags("");
      event.target.reset();
      onUploaded();
    } catch (failure) {
      setError(failure.message);
    } finally {
      setPending(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="rounded-lg border border-neutral-200 bg-white p-6">
      <h2 className="text-sm font-semibold">Upload a document</h2>

      <div className="mt-4 grid gap-4 sm:grid-cols-2">
        <label className="block text-sm">
          <span className="font-medium">File</span>
          <input
            type="file"
            accept="application/pdf"
            onChange={(event) => setFile(event.target.files?.[0] ?? null)}
            className="mt-1 w-full text-sm"
          />
        </label>

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

        <label className="block text-sm">
          <span className="font-medium">Type</span>
          <select
            value={documentType}
            onChange={(event) => setDocumentType(event.target.value)}
            className="mt-1 w-full rounded-md border border-neutral-300 px-3 py-2 text-sm"
          >
            {DOCUMENT_TYPES.map((value) => (
              <option key={value} value={value}>
                {value.replace(/_/g, " ")}
              </option>
            ))}
          </select>
        </label>

        <label className="block text-sm">
          <span className="font-medium">Tags</span>
          <input
            type="text"
            value={tags}
            placeholder="comma, separated"
            onChange={(event) => setTags(event.target.value)}
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
  const [documents, setDocuments] = useState([]);
  const [status, setStatus] = useState("loading");
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    try {
      const payload = await api.listDocuments();
      setDocuments(payload.documents);
      setStatus("ready");
    } catch (failure) {
      setError(failure.message);
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

        setError(failure.message);
        setStatus("error");
      }
    }

    fetchDocuments();

    return () => {
      cancelled = true;
    };
  }, []);

  async function remove(id) {
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
                <a
                  href={`/documents/${document.id}`}
                  className="block truncate text-sm font-medium underline"
                >
                  {document.title}
                </a>
                <p className="mt-0.5 text-xs text-neutral-500">
                  {document.document_type.replace(/_/g, " ")} · {formatDate(document.created_at)} ·{" "}
                  {document.processing_status}
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
