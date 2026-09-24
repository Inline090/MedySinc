import { SignInForm } from "./sign-in-form";

export default async function SignInPage({ searchParams }) {
  const { error } = await searchParams;

  return (
    <SignInForm
      initialError={error === "google" ? "Google sign-in did not complete. Please try again." : null}
    />
  );
}
