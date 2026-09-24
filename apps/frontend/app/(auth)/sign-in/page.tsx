import { SignInForm } from "./sign-in-form";

interface SignInPageProps {
  searchParams: Promise<{ error?: string }>;
}

export default async function SignInPage({ searchParams }: SignInPageProps) {
  const { error } = await searchParams;

  return (
    <SignInForm
      initialError={error === "google" ? "Google sign-in did not complete. Please try again." : null}
    />
  );
}
