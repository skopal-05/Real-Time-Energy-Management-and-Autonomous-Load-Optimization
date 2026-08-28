"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowRight } from "lucide-react";
import { useAuth } from "@/providers/AuthProvider";
import { AuthError, DemoAuthNotice, Field, SubmitButton } from "@/components/auth/AuthForm";

const MIN_PASSWORD_LENGTH = 8;

export default function SignUpPage() {
  const router = useRouter();
  const { signUp, pending, error, clearError, isDemoAuth, session } = useAuth();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [organisation, setOrganisation] = useState("");
  const [password, setPassword] = useState("");
  const [localError, setLocalError] = useState<string | null>(null);

  useEffect(() => {
    if (session) router.replace("/");
  }, [session, router]);

  const shown = localError ?? error;

  return (
    <>
      <header className="mb-6">
        <h1 className="text-xl font-semibold tracking-tight text-content">Create an account</h1>
        <p className="mt-1.5 text-xs leading-relaxed text-content-muted">
          Set up access to the control centre for your plant.
        </p>
      </header>

      <form
        className="space-y-4"
        onSubmit={async (e) => {
          e.preventDefault();
          setLocalError(null);
          if (password.length < MIN_PASSWORD_LENGTH) {
            setLocalError(`Use at least ${MIN_PASSWORD_LENGTH} characters for the password.`);
            return;
          }
          const ok = await signUp({ name, email, organisation, password });
          if (ok) router.push("/");
        }}
      >
        {isDemoAuth ? <DemoAuthNotice /> : null}
        {shown ? <AuthError message={shown} /> : null}

        <Field
          label="Full name"
          value={name}
          onChange={(v) => {
            clearError();
            setName(v);
          }}
          placeholder="Udit Mittal"
          autoComplete="name"
        />
        <Field
          label="Work email"
          type="email"
          value={email}
          onChange={(v) => {
            clearError();
            setEmail(v);
          }}
          placeholder="you@plant.example"
          autoComplete="email"
        />
        <Field
          label="Organisation"
          value={organisation}
          onChange={(v) => {
            clearError();
            setOrganisation(v);
          }}
          placeholder="Plant or company name"
          autoComplete="organization"
          required={false}
        />
        <Field
          label="Password"
          type="password"
          value={password}
          onChange={(v) => {
            setLocalError(null);
            clearError();
            setPassword(v);
          }}
          placeholder="••••••••"
          autoComplete="new-password"
          hint={`At least ${MIN_PASSWORD_LENGTH} characters.`}
        />

        <SubmitButton pending={pending}>
          Create account
          <ArrowRight className="h-3.5 w-3.5" aria-hidden />
        </SubmitButton>
      </form>

      <p className="mt-5 text-center text-xs text-content-muted">
        Already have an account?{" "}
        <Link href="/login" className="font-medium text-info hover:underline">
          Sign in
        </Link>
      </p>

      <div className="mt-6 border-t border-line pt-4 text-center">
        <Link href="/" className="text-2xs text-content-faint transition-colors hover:text-content-muted">
          Skip and explore the demo →
        </Link>
      </div>
    </>
  );
}
