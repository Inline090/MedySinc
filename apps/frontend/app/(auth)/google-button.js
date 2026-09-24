const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export function GoogleButton() {
  return (
    <a
      href={`${API_URL}/api/v1/auth/google/start`}
      className="mt-4 flex w-full items-center justify-center rounded-md border border-neutral-300 px-4 py-2 text-sm font-medium"
    >
      Continue with Google
    </a>
  );
}
