"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { AppShell } from "@/components/layout/AppShell";
import { useAuth } from "@/providers/AuthProvider";
import { LoadingState } from "@/components/ui/States";

/**
 * Shell for every control-centre route.
 *
 * The auth gate is opt-in: with `NEXT_PUBLIC_REQUIRE_AUTH=false` (the default)
 * the app opens straight into the dashboard, which keeps demonstrations simple.
 * Set it to `true` once a real identity provider is wired up.
 */
export default function AppGroupLayout({ children }: { children: React.ReactNode }) {
  const { session, initialising, requireAuth } = useAuth();
  const router = useRouter();

  const blocked = requireAuth && !initialising && session === null;

  useEffect(() => {
    if (blocked) router.replace("/login");
  }, [blocked, router]);

  if (requireAuth && (initialising || blocked)) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <LoadingState label="Checking your session" />
      </div>
    );
  }

  return <AppShell>{children}</AppShell>;
}
