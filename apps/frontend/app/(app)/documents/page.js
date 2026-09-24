"use client";

import { useState } from "react";

import { DocumentList, UploadForm } from "./document-views";

export default function DocumentsPage() {
  const [refreshToken, setRefreshToken] = useState(0);

  return (
    <div>
      <h1 className="text-2xl font-semibold">Documents</h1>
      <p className="mt-2 text-sm text-neutral-600">
        Upload a report or prescription, then ask questions about it.
      </p>

      <div className="mt-6">
        <UploadForm onUploaded={() => setRefreshToken((value) => value + 1)} />
      </div>

      <DocumentList key={refreshToken} />
    </div>
  );
}
