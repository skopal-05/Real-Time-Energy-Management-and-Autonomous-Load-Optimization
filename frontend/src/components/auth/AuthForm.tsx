"use client";

import { useId, useState, type ReactNode } from "react";
import { AlertTriangle, Eye, EyeOff, FlaskConical, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface FieldProps {
  label: string;
  type?: "text" | "email" | "password";
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  autoComplete?: string;
  required?: boolean;
  hint?: string;
}

/** Labelled input matching the control-centre design tokens. */
export function Field({
  label,
  type = "text",
  value,
  onChange,
  placeholder,
  autoComplete,
  required = true,
  hint,
}: FieldProps) {
  const id = useId();
  const [reveal, setReveal] = useState(false);
  const isPassword = type === "password";
  const inputType = isPassword && reveal ? "text" : type;

  return (
    <div>
      <label htmlFor={id} className="mb-1.5 block text-2xs font-medium uppercase tracking-wider text-content-faint">
        {label}
      </label>
      <div className="relative">
        <input
          id={id}
          type={inputType}
          value={value}
          required={required}
          autoComplete={autoComplete}
          placeholder={placeholder}
          onChange={(e) => onChange(e.target.value)}
          className={cn(
            "w-full rounded-lg border border-line bg-surface-inset px-3 py-2 text-sm text-content",
            "placeholder:text-content-faint/70 transition-colors",
            "hover:border-line-strong focus:border-info/60",
            isPassword && "pr-10",
          )}
        />
        {isPassword ? (
          <button
            type="button"
            onClick={() => setReveal((v) => !v)}
            aria-label={reveal ? "Hide password" : "Show password"}
            className="absolute right-2 top-1/2 -translate-y-1/2 rounded p-1 text-content-faint transition-colors hover:text-content-muted"
          >
            {reveal ? <EyeOff className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5" />}
          </button>
        ) : null}
      </div>
      {hint ? <p className="mt-1 text-2xs text-content-faint">{hint}</p> : null}
    </div>
  );
}

/** Amber notice shown whenever the active adapter cannot verify an identity. */
export function DemoAuthNotice() {
  return (
    <div className="flex items-start gap-2 rounded-lg border border-warn/25 bg-warn/[0.06] px-3 py-2.5">
      <FlaskConical className="mt-0.5 h-3.5 w-3.5 shrink-0 text-warn" aria-hidden />
      <p className="text-2xs leading-relaxed text-warn/90">
        <span className="font-semibold">Demo sign-in.</span> No identity provider is connected, so
        nothing is verified, no account is created and no password is stored or transmitted. Any
        details are kept in this browser tab only, to give the shell a name to display. Set{" "}
        <code className="rounded bg-warn/10 px-1 font-mono">NEXT_PUBLIC_API_MODE=live</code> to
        authenticate against the backend instead.
      </p>
    </div>
  );
}

export function AuthError({ message }: { message: string }) {
  return (
    <div className="flex items-start gap-2 rounded-lg border border-crit/30 bg-crit/[0.07] px-3 py-2.5" role="alert">
      <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-crit" aria-hidden />
      <p className="text-2xs leading-relaxed text-crit">{message}</p>
    </div>
  );
}

export function SubmitButton({ pending, children }: { pending: boolean; children: ReactNode }) {
  return (
    <button
      type="submit"
      disabled={pending}
      className={cn(
        "inline-flex w-full items-center justify-center gap-2 rounded-lg border border-info/40 bg-info/15 px-3 py-2.5",
        "text-sm font-medium text-info transition-colors hover:bg-info/20 disabled:opacity-60",
      )}
    >
      {pending ? <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden /> : null}
      {children}
    </button>
  );
}
