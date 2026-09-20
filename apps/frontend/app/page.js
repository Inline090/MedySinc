import Link from "next/link";

export default function HomePage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col justify-center px-6">
      <h1 className="text-3xl font-semibold">MedSync</h1>
      <p className="mt-3 text-neutral-600">
        Upload medical documents, keep them organised in one place, and ask questions answered from
        your own records.
      </p>

      <div className="mt-8 flex gap-3">
        <Link
          href="/sign-in"
          className="rounded-md bg-neutral-900 px-4 py-2 text-sm font-medium text-white"
        >
          Sign in
        </Link>
        <Link
          href="/sign-up"
          className="rounded-md border border-neutral-300 px-4 py-2 text-sm font-medium"
        >
          Create an account
        </Link>
      </div>
    </main>
  );
}
