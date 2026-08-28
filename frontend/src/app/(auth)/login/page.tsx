"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowRight } from "lucide-react";
import { useAuth } from "@/providers/AuthProvider";
import { AuthError, DemoAuthNotice, Field, SubmitButton } from "@/components/auth/AuthForm";

export default function LoginPage() {
  const router = useRouter();
  const { signIn, pending, error, clearError, isDemoAuth, session } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  // Someone already signed in has no business on this screen.
  useEffect(() => {
    if (session) router.replace("/");
  }, [session, router]);

  return (
    <>
      <header className="mb-6">
        <h1 className="text-xl font-semibold tracking-tight text-content">Sign in</h1>
        <p className="mt-1.5 text-xs leading-relaxed text-content-muted">
          Open the digital twin control centre for your site.
        </p>
      </header>

      <form
        className="space-y-4"
        onSubmit={async (e) => {
          e.preventDefault();
          const ok = await signIn({ email, password });
          if (ok) router.push("/");
        }}
      >
        {isDemoAuth ? <DemoAuthNotice /> : null}
        {error ? <AuthError message={error} /> : null}

        <Field
          label="Email"
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
          label="Password"
          type="password"
          value={password}
          onChange={(v) => {
            clearError();
            setPassword(v);
          }}
          placeholder="••••••••"
          autoComplete="current-password"
        />

        <SubmitButton pending={pending}>
          Sign in
          <ArrowRight className="h-3.5 w-3.5" aria-hidden />
        </SubmitButton>
      </form>

      <p className="mt-5 text-center text-xs text-content-muted">
        No account yet?{" "}
        <Link href="/signup" className="font-medium text-info hover:underline">
          Create one
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
