import { apiConfig, isLiveMode } from "./config";

export type Unsubscribe = () => void;

export interface SubscribeOptions {
  /** Overrides the configured polling interval for this subscription. */
  intervalMs?: number;
  /** Channel name forwarded to the WebSocket server, e.g. "system.status". */
  channel?: string;
}

/**
 * Transport-agnostic realtime subscription.
 *
 * Today it polls, because the demo data source has no stream. When the backend
 * exposes a WebSocket or SSE endpoint, set `NEXT_PUBLIC_WS_URL` and the socket
 * branch below takes over — call sites do not change.
 */
export function subscribe(onTick: () => void, options: SubscribeOptions = {}): Unsubscribe {
  const interval = options.intervalMs ?? apiConfig.pollIntervalMs;

  if (isLiveMode && apiConfig.wsUrl) {
    let socket: WebSocket | null = null;
    let retry: ReturnType<typeof setTimeout> | null = null;
    let closed = false;

    const connect = () => {
      if (closed) return;
      const url = options.channel
        ? `${apiConfig.wsUrl}?channel=${encodeURIComponent(options.channel)}`
        : apiConfig.wsUrl;
      socket = new WebSocket(url);
      socket.onmessage = () => onTick();
      socket.onclose = () => {
        if (!closed) retry = setTimeout(connect, 3000);
      };
      socket.onerror = () => socket?.close();
    };

    connect();
    return () => {
      closed = true;
      if (retry) clearTimeout(retry);
      socket?.close();
    };
  }

  const id = setInterval(onTick, interval);
  return () => clearInterval(id);
}
