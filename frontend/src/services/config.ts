/**
 * Runtime data-source configuration.
 *
 * The UI never reads `process.env` directly — everything goes through here so
 * switching from the demo data set to the Python backend is a one-line change
 * in `.env.local`.
 */

export type ApiMode = "mock" | "live";

export interface ApiConfig {
  mode: ApiMode;
  /** e.g. "http://localhost:8000/api" — empty when no backend is configured. */
  baseUrl: string;
  /** e.g. "ws://localhost:8000/ws/stream" — empty when streaming is not set up. */
  wsUrl: string;
  /** Fallback polling interval when no stream is available, in milliseconds. */
  pollIntervalMs: number;
  /** Simulated latency for the mock adapter so loading states are exercised. */
  mockLatencyMs: number;
  /**
   * When true, unauthenticated visitors are redirected to /login.
   * Left false by default so the demo always opens straight into the app.
   */
  requireAuth: boolean;
}

function readMode(): ApiMode {
  const raw = process.env.NEXT_PUBLIC_API_MODE;
  return raw === "live" ? "live" : "mock";
}

export const apiConfig: ApiConfig = {
  mode: readMode(),
  baseUrl: process.env.NEXT_PUBLIC_API_BASE_URL ?? "",
  wsUrl: process.env.NEXT_PUBLIC_WS_URL ?? "",
  pollIntervalMs: Number(process.env.NEXT_PUBLIC_POLL_INTERVAL_MS ?? 5000),
  mockLatencyMs: Number(process.env.NEXT_PUBLIC_MOCK_LATENCY_MS ?? 260),
  requireAuth: process.env.NEXT_PUBLIC_REQUIRE_AUTH === "true",
};

export const isLiveMode = apiConfig.mode === "live" && apiConfig.baseUrl.length > 0;
