import type { AuthSession, SignInInput, SignUpInput } from "@/lib/types";
import { apiConfig, isLiveMode } from "./config";
import { DataSourceError } from "./dataSource";

/**
 * Authentication contract.
 *
 * The UI depends only on this interface. Today the demo adapter satisfies it
 * without any identity provider; when the Python backend exposes `/auth`, the
 * HTTP adapter takes over and no screen changes.
 */
export interface AuthService {
  readonly name: string;
  /** True when this adapter cannot actually verify an identity. */
  readonly isDemo: boolean;

  signIn(input: SignInInput): Promise<AuthSession>;
  signUp(input: SignUpInput): Promise<AuthSession>;
  signOut(): Promise<void>;
  /** Restores a session from storage, or null when there is none. */
  restore(): Promise<AuthSession | null>;
}

const STORAGE_KEY = "enertwin.session";

function readStoredSession(): AuthSession | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as AuthSession;
    if (parsed.expiresAt && new Date(parsed.expiresAt).getTime() < Date.now()) return null;
    return parsed;
  } catch {
    return null;
  }
}

function writeStoredSession(session: AuthSession | null): void {
  if (typeof window === "undefined") return;
  try {
    if (session) window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(session));
    else window.sessionStorage.removeItem(STORAGE_KEY);
  } catch {
    // Storage can be unavailable (private windows, blocked site data). The app
    // still works; the session simply does not survive a reload.
  }
}

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function displayNameFromEmail(email: string): string {
  const local = email.split("@")[0] ?? "operator";
  return local
    .split(/[._-]+/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

/**
 * Demo adapter.
 *
 * It does NOT verify credentials and creates no account — it only records a
 * display name for the session so the shell has something to show. Every
 * session it issues is flagged `demo: true`, and the sign-in screens say so.
 */
export const mockAuthService: AuthService = {
  name: "Demo sign-in (no identity provider)",
  isDemo: true,

  async signIn(input) {
    await delay(apiConfig.mockLatencyMs);
    const session: AuthSession = {
      user: {
        id: "demo-user",
        name: displayNameFromEmail(input.email),
        email: input.email,
        role: "engineer",
        organisation: "Demo Plant",
      },
      token: "",
      issuedAt: new Date().toISOString(),
      expiresAt: null,
      demo: true,
    };
    writeStoredSession(session);
    return session;
  },

  async signUp(input) {
    await delay(apiConfig.mockLatencyMs);
    const session: AuthSession = {
      user: {
        id: "demo-user",
        name: input.name,
        email: input.email,
        role: "engineer",
        organisation: input.organisation || "Demo Plant",
      },
      token: "",
      issuedAt: new Date().toISOString(),
      expiresAt: null,
      demo: true,
    };
    writeStoredSession(session);
    return session;
  },

  async signOut() {
    writeStoredSession(null);
  },

  async restore() {
    return readStoredSession();
  },
};

/* ------------------------------------------------------------------ */
/* HTTP adapter                                                         */
/* ------------------------------------------------------------------ */

async function authRequest<T>(path: string, body: unknown): Promise<T> {
  if (!apiConfig.baseUrl) {
    throw new DataSourceError("No API base URL is configured.", path);
  }
  const url = `${apiConfig.baseUrl.replace(/\/$/, "")}${path}`;

  let response: Response;
  try {
    response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(body),
    });
  } catch {
    throw new DataSourceError("Could not reach the authentication service.", path);
  }

  if (response.status === 401) {
    throw new DataSourceError("Those credentials were not accepted.", path, 401);
  }
  if (response.status === 409) {
    throw new DataSourceError("An account already exists for that email address.", path, 409);
  }
  if (!response.ok) {
    throw new DataSourceError(
      `Authentication service responded with ${response.status} ${response.statusText}.`,
      path,
      response.status,
    );
  }
  return (await response.json()) as T;
}

/**
 * REST adapter for the backend's auth endpoints.
 *
 *   POST /auth/login     { email, password }        -> AuthSession
 *   POST /auth/register  { name, email, password, organisation } -> AuthSession
 *   POST /auth/logout    {}                         -> 204
 *
 * The backend must return `demo: false` on real sessions so the UI stops
 * labelling them as demo.
 */
export const httpAuthService: AuthService = {
  name: `Live auth (${apiConfig.baseUrl || "not configured"})`,
  isDemo: false,

  async signIn(input) {
    const session = await authRequest<AuthSession>("/auth/login", input);
    writeStoredSession(session);
    return session;
  },

  async signUp(input) {
    const session = await authRequest<AuthSession>("/auth/register", input);
    writeStoredSession(session);
    return session;
  },

  async signOut() {
    try {
      await authRequest<void>("/auth/logout", {});
    } finally {
      writeStoredSession(null);
    }
  },

  async restore() {
    return readStoredSession();
  },
};

export function getAuthService(): AuthService {
  return isLiveMode ? httpAuthService : mockAuthService;
}
