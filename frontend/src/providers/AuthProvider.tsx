"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { AuthSession, SignInInput, SignUpInput } from "@/lib/types";
import { getAuthService } from "@/services";
import { apiConfig } from "@/services/config";

interface AuthState {
  session: AuthSession | null;
  /** True until the stored session has been checked on first mount. */
  initialising: boolean;
  pending: boolean;
  error: string | null;
  /** True when the active adapter cannot verify an identity. */
  isDemoAuth: boolean;
  /** True when unauthenticated visitors should be pushed to /login. */
  requireAuth: boolean;
  signIn: (input: SignInInput) => Promise<boolean>;
  signUp: (input: SignUpInput) => Promise<boolean>;
  signOut: () => Promise<void>;
  clearError: () => void;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const auth = useMemo(() => getAuthService(), []);
  const [session, setSession] = useState<AuthSession | null>(null);
  const [initialising, setInitialising] = useState(true);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    auth
      .restore()
      .then((restored) => {
        if (!cancelled) setSession(restored);
      })
      .catch(() => {
        if (!cancelled) setSession(null);
      })
      .finally(() => {
        if (!cancelled) setInitialising(false);
      });
    return () => {
      cancelled = true;
    };
  }, [auth]);

  const run = useCallback(
    async (action: () => Promise<AuthSession>): Promise<boolean> => {
      setPending(true);
      setError(null);
      try {
        setSession(await action());
        return true;
      } catch (err) {
        setError(err instanceof Error ? err.message : "Sign-in failed. Please try again.");
        return false;
      } finally {
        setPending(false);
      }
    },
    [],
  );

  const signIn = useCallback(
    (input: SignInInput) => run(() => auth.signIn(input)),
    [auth, run],
  );
  const signUp = useCallback(
    (input: SignUpInput) => run(() => auth.signUp(input)),
    [auth, run],
  );
  const signOut = useCallback(async () => {
    await auth.signOut();
    setSession(null);
  }, [auth]);

  const value = useMemo<AuthState>(
    () => ({
      session,
      initialising,
      pending,
      error,
      isDemoAuth: auth.isDemo,
      requireAuth: apiConfig.requireAuth,
      signIn,
      signUp,
      signOut,
      clearError: () => setError(null),
    }),
    [session, initialising, pending, error, auth.isDemo, signIn, signUp, signOut],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}
