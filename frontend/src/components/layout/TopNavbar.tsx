"use client";

import { useCallback, useMemo, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Bell, LogIn, LogOut, Menu, Pause, Play, RefreshCw, Target } from "lucide-react";
import { getDataSource } from "@/services";
import { useResource } from "@/hooks/useResource";
import { useAppState } from "@/providers/AppStateProvider";
import { useAuth } from "@/providers/AuthProvider";
import { formatKw, formatRelative, formatTime } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { SystemEvent, SystemStatus } from "@/lib/types";
import { StatusBadge, Chip } from "@/components/ui/StatusBadge";
import { DataOriginBadge } from "@/components/ui/DataOriginBadge";
import { Skeleton } from "@/components/ui/States";
import { SEVERITY_STYLES } from "@/lib/constants";
import { findNavItem } from "./navigation";

interface TopNavbarProps {
  onOpenMenu: () => void;
}

export function TopNavbar({ onOpenMenu }: TopNavbarProps) {
  const pathname = usePathname();
  const { streaming, setStreaming, refreshNow, lastRefreshedAt } = useAppState();
  const [notificationsOpen, setNotificationsOpen] = useState(false);

  const ds = getDataSource();
  const statusLoader = useCallback(() => ds.getSystemStatus(), [ds]);
  const eventsLoader = useCallback(() => ds.getEvents(), [ds]);
  const status = useResource<SystemStatus>(statusLoader);
  const events = useResource<SystemEvent[]>(eventsLoader);

  const current = findNavItem(pathname);
  const unread = useMemo(
    () => (events.data ?? []).filter((e) => e.severity !== "info").length,
    [events.data],
  );

  return (
    <header className="sticky top-0 z-40 border-b border-line bg-base/85 backdrop-blur-md">
      <div className="flex h-14 items-center gap-3 px-3 sm:px-5">
        <button
          type="button"
          onClick={onOpenMenu}
          className="rounded-md p-1.5 text-content-muted transition-colors hover:bg-surface-raised hover:text-content lg:hidden"
          aria-label="Open navigation"
        >
          <Menu className="h-4 w-4" aria-hidden />
        </button>

        {/* System identity — also a route back to the introduction */}
        <Link href="/" className="min-w-0 rounded-md transition-opacity hover:opacity-80">
          <h1 className="truncate text-[13px] font-semibold leading-tight tracking-tight text-content">
            Generative Digital Twin · Energy Management
          </h1>
          <p className="truncate text-2xs text-content-faint">
            {current ? current.label : "Control Centre"}
            {current?.module ? ` · ${current.module}` : ""}
          </p>
        </Link>

        <div className="ml-auto flex items-center gap-2 sm:gap-3">
          {/* Operating mode + health */}
          <div className="hidden items-center gap-2 md:flex">
            {status.data ? (
              <>
                <span className="inline-flex items-center gap-1.5 rounded-md border border-line bg-surface-inset px-2 py-1 text-2xs font-medium text-content-muted">
                  <Target className="h-3 w-3 text-info" aria-hidden />
                  {status.data.operatingModeLabel}
                </span>
                <StatusBadge status={status.data.overall} size="md" />
                <span className="hidden items-center gap-1.5 rounded-md border border-line bg-surface-inset px-2 py-1 text-2xs tabular text-content-muted xl:inline-flex">
                  Load {formatKw(status.data.consumptionKw, 0)}
                </span>
              </>
            ) : (
              <Skeleton className="h-6 w-40" />
            )}
          </div>

          <DataOriginBadge origin={status.origin} className="hidden sm:inline-flex" />

          {/* Last updated */}
          <div className="hidden flex-col items-end leading-tight sm:flex">
            <span className="text-2xs text-content-faint">Last updated</span>
            <span className="text-2xs font-medium tabular text-content-muted">
              {lastRefreshedAt ? formatTime(new Date(lastRefreshedAt).toISOString()) : "—"}
            </span>
          </div>

          {/* Stream controls */}
          <div className="flex items-center gap-1 rounded-lg border border-line bg-surface-inset p-0.5">
            <button
              type="button"
              onClick={() => setStreaming(!streaming)}
              className={cn(
                "rounded-md p-1.5 transition-colors",
                streaming ? "text-ok hover:bg-surface-raised" : "text-content-faint hover:bg-surface-raised",
              )}
              aria-label={streaming ? "Pause live updates" : "Resume live updates"}
              title={streaming ? "Pause live updates" : "Resume live updates"}
            >
              {streaming ? <Pause className="h-3.5 w-3.5" /> : <Play className="h-3.5 w-3.5" />}
            </button>
            <button
              type="button"
              onClick={refreshNow}
              className="rounded-md p-1.5 text-content-muted transition-colors hover:bg-surface-raised hover:text-content"
              aria-label="Refresh now"
              title="Refresh now"
            >
              <RefreshCw className="h-3.5 w-3.5" />
            </button>
          </div>

          {/* Notifications */}
          <div className="relative">
            <button
              type="button"
              onClick={() => setNotificationsOpen((v) => !v)}
              className="relative rounded-md border border-line bg-surface-inset p-1.5 text-content-muted transition-colors hover:text-content"
              aria-label={`Notifications (${unread})`}
              aria-expanded={notificationsOpen}
            >
              <Bell className="h-3.5 w-3.5" aria-hidden />
              {unread > 0 ? (
                <span className="absolute -right-1 -top-1 flex h-3.5 min-w-3.5 items-center justify-center rounded-full bg-crit px-1 text-[9px] font-semibold text-white">
                  {unread}
                </span>
              ) : null}
            </button>

            {notificationsOpen ? (
              <div className="absolute right-0 top-10 z-50 w-80 animate-fade-up overflow-hidden rounded-xl border border-line-strong bg-surface-overlay shadow-lift">
                <div className="flex items-center justify-between border-b border-line px-3 py-2">
                  <span className="text-xs font-semibold text-content">Recent events</span>
                  <Link
                    href="/anomalies"
                    onClick={() => setNotificationsOpen(false)}
                    className="text-2xs text-info hover:underline"
                  >
                    View all
                  </Link>
                </div>
                <ul className="max-h-80 overflow-y-auto">
                  {(events.data ?? []).slice(0, 6).map((e) => (
                    <li key={e.id} className="border-b border-line-soft px-3 py-2.5 last:border-0">
                      <div className="flex items-start gap-2">
                        <span
                          className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full"
                          style={{
                            backgroundColor:
                              e.severity === "info" ? "#64748B" : SEVERITY_STYLES[e.severity].hex,
                          }}
                          aria-hidden
                        />
                        <div className="min-w-0">
                          <p className="text-xs font-medium leading-snug text-content">{e.title}</p>
                          <p className="mt-0.5 line-clamp-2 text-2xs text-content-muted">{e.detail}</p>
                          <p className="mt-1 text-2xs text-content-faint">
                            {formatRelative(e.timestamp, lastRefreshedAt ?? Date.now())}
                          </p>
                        </div>
                      </div>
                    </li>
                  ))}
                  {(events.data ?? []).length === 0 ? (
                    <li className="px-3 py-6 text-center text-xs text-content-faint">No events recorded.</li>
                  ) : null}
                </ul>
              </div>
            ) : null}
          </div>

          <UserMenu />
        </div>
      </div>
    </header>
  );
}

/** Session chip: who is signed in, or a route to the sign-in screen. */
function UserMenu() {
  const { session, signOut, isDemoAuth } = useAuth();
  const [open, setOpen] = useState(false);

  if (!session) {
    return (
      <Link
        href="/login"
        className="inline-flex items-center gap-1.5 rounded-lg border border-line bg-surface-inset px-2.5 py-1.5 text-2xs font-medium text-content-muted transition-colors hover:border-line-strong hover:text-content"
      >
        <LogIn className="h-3 w-3" aria-hidden />
        Sign in
      </Link>
    );
  }

  const initials = session.user.name
    .split(" ")
    .slice(0, 2)
    .map((p) => p.charAt(0).toUpperCase())
    .join("");

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        aria-label="Account menu"
        className="flex items-center gap-2 rounded-lg border border-line bg-surface-inset py-1 pl-1 pr-2 transition-colors hover:border-line-strong"
      >
        <span className="flex h-6 w-6 items-center justify-center rounded-md bg-info/12 text-2xs font-semibold text-info">
          {initials || "?"}
        </span>
        <span className="hidden max-w-[8rem] truncate text-2xs font-medium text-content-muted sm:block">
          {session.user.name}
        </span>
      </button>

      {open ? (
        <div className="absolute right-0 top-10 z-50 w-60 animate-fade-up overflow-hidden rounded-xl border border-line-strong bg-surface-overlay shadow-lift">
          <div className="border-b border-line px-3 py-2.5">
            <p className="truncate text-xs font-semibold text-content">{session.user.name}</p>
            <p className="truncate text-2xs text-content-faint">{session.user.email}</p>
            <div className="mt-1.5 flex flex-wrap items-center gap-1">
              <Chip>{session.user.role}</Chip>
              <Chip>{session.user.organisation}</Chip>
            </div>
          </div>
          {isDemoAuth || session.demo ? (
            <p className="border-b border-line bg-warn/[0.06] px-3 py-2 text-2xs leading-relaxed text-warn/90">
              Demo session — no identity provider verified these details and no account exists.
            </p>
          ) : null}
          <button
            type="button"
            onClick={() => {
              setOpen(false);
              void signOut();
            }}
            className="flex w-full items-center gap-2 px-3 py-2.5 text-xs text-content-muted transition-colors hover:bg-surface-raised hover:text-content"
          >
            <LogOut className="h-3 w-3" aria-hidden />
            Sign out
          </button>
        </div>
      ) : null}
    </div>
  );
}
