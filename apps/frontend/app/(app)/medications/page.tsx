"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { AiDisclaimer } from "@/components/disclaimer";
import { api } from "@/lib/api";
import type { Medicine } from "@/lib/types";

export default function MedicationsPage() {
  const [medicines, setMedicines] = useState<Medicine[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let live = true;

    api
      .listMedications()
      .then((body) => {
        if (live) setMedicines(body.medicines);
      })
      .catch((failure) => {
        if (live) {
          setError(
            failure instanceof Error ? failure.message : "Could not load your medications.",
          );
        }
      });

    return () => {
      live = false;
    };
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-semibold">Medications</h1>
      <p className="mt-2 text-sm text-neutral-600">
        Every medicine read out of your prescriptions, newest document first.
      </p>

      {error !== null ? (
        <p role="alert" className="mt-6 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </p>
      ) : null}

      {error === null && medicines === null ? (
        <p className="mt-6 text-sm text-neutral-500">Loading...</p>
      ) : null}

      {medicines !== null && medicines.length === 0 ? (
        <aside className="mt-6 rounded-lg border border-neutral-200 bg-white p-6">
          <p className="text-sm text-neutral-700">No medicines have been found yet.</p>
          <p className="mt-2 text-sm text-neutral-500">
            Upload a prescription and its medicines will be listed here once the document has
            finished processing.
          </p>
        </aside>
      ) : null}

      {medicines !== null && medicines.length > 0 ? (
        <div className="mt-6 overflow-x-auto rounded-lg border border-neutral-200 bg-white">
          <table className="w-full border-collapse text-left text-sm">
            <thead>
              <tr className="border-b border-neutral-200 text-xs uppercase tracking-wide text-neutral-500">
                <th className="px-4 py-3 font-medium">Medicine</th>
                <th className="px-4 py-3 font-medium">Dose</th>
                <th className="px-4 py-3 font-medium">Frequency</th>
                <th className="px-4 py-3 font-medium">Prescribed</th>
                <th className="px-4 py-3 font-medium">Hospital</th>
                <th className="px-4 py-3 font-medium">Notes</th>
                <th className="px-4 py-3 font-medium">Document</th>
              </tr>
            </thead>

            <tbody>
              {medicines.map((medicine) => (
                <tr key={medicine.id} className="border-b border-neutral-100 last:border-0">
                  <td className="px-4 py-3 font-medium text-neutral-900">{medicine.medicine}</td>
                  <Cell value={medicine.dose} />
                  <Cell value={medicine.frequency} />
                  <Cell value={medicine.prescribed_on} />
                  <Cell value={medicine.hospital} />
                  <Cell value={medicine.notes} />
                  <td className="px-4 py-3">
                    <Link
                      href={`/documents/${medicine.document_id}`}
                      className="text-xs text-neutral-600 underline"
                    >
                      {medicine.document_title}
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}

      {medicines !== null && medicines.length > 0 ? <AiDisclaimer /> : null}
    </div>
  );
}

function Cell({ value }: { value: string | null }) {
  return (
    <td className="px-4 py-3">
      {value ?? <span className="text-neutral-400">not stated</span>}
    </td>
  );
}
