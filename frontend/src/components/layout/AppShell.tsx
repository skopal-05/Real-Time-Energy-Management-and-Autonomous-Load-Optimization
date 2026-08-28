"use client";

import { useState } from "react";
import { X } from "lucide-react";
import { Sidebar } from "./Sidebar";
import { TopNavbar } from "./TopNavbar";
import { DemoBanner } from "./DemoBanner";

export function AppShell({ children }: { children: React.ReactNode }) {
  const [collapsed, setCollapsed] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);

  return (
    <div className="flex min-h-screen bg-base">
      {/* Desktop sidebar */}
      <aside className="sticky top-0 hidden h-screen shrink-0 lg:block">
        <Sidebar collapsed={collapsed} onToggle={() => setCollapsed((v) => !v)} />
      </aside>

      {/* Mobile drawer */}
      {drawerOpen ? (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={() => setDrawerOpen(false)}
            role="presentation"
          />
          <div className="absolute inset-y-0 left-0 animate-fade-up">
            <Sidebar collapsed={false} onToggle={() => setDrawerOpen(false)} onNavigate={() => setDrawerOpen(false)} />
          </div>
          <button
            type="button"
            onClick={() => setDrawerOpen(false)}
            className="absolute right-4 top-4 rounded-md border border-line bg-surface p-2 text-content-muted"
            aria-label="Close navigation"
          >
            <X className="h-4 w-4" aria-hidden />
          </button>
        </div>
      ) : null}

      <div className="flex min-w-0 flex-1 flex-col">
        <TopNavbar onOpenMenu={() => setDrawerOpen(true)} />
        <DemoBanner />
        <main id="main-content" className="min-w-0 flex-1 px-3 py-4 sm:px-5 sm:py-5 xl:px-7">
          {children}
        </main>
        <footer className="border-t border-line px-5 py-3 text-2xs text-content-faint">
          Generative Digital Twin for Real-Time Energy Management and Autonomous Load Optimization ·
          Frontend control centre · Data layer is swappable between the built-in demo scenario and the
          project&apos;s Python API.
        </footer>
      </div>
    </div>
  );
}
