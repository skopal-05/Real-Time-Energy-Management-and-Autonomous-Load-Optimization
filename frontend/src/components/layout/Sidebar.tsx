"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { PanelLeftClose, PanelLeftOpen, Zap } from "lucide-react";
import { cn } from "@/lib/utils";
import { NAV_GROUPS } from "./navigation";

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
  /** Mobile drawer: closes the sheet after navigation. */
  onNavigate?: () => void;
}

export function Sidebar({ collapsed, onToggle, onNavigate }: SidebarProps) {
  const pathname = usePathname();

  const isActive = (href: string) =>
    href === "/" ? pathname === "/" : pathname === href || pathname.startsWith(`${href}/`);

  return (
    <nav
      aria-label="Primary"
      className={cn(
        "flex h-full flex-col border-r border-line bg-surface-inset transition-[width] duration-200",
        collapsed ? "w-[68px]" : "w-[248px]",
      )}
    >
      {/* Brand — returns to the introduction page */}
      <Link
        href="/"
        onClick={onNavigate}
        title="EnerTwin · system introduction"
        aria-label="EnerTwin — go to the system introduction"
        className="group flex h-14 items-center gap-2.5 border-b border-line px-4 transition-colors hover:bg-surface-raised"
      >
        <span className="relative flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-info/12 ring-1 ring-info/25 transition-colors group-hover:bg-info/20">
          <Zap className="h-3.5 w-3.5 text-info" aria-hidden />
        </span>
        {!collapsed ? (
          <div className="min-w-0">
            <p className="truncate text-[13px] font-semibold leading-tight tracking-tight text-content">
              EnerTwin
            </p>
            <p className="truncate text-2xs text-content-faint">Digital Twin Control</p>
          </div>
        ) : null}
      </Link>

      {/* Groups */}
      <div className="flex-1 overflow-y-auto px-2.5 py-3">
        {NAV_GROUPS.map((group) => (
          <div key={group.id} className="mb-4 last:mb-0">
            {!collapsed ? (
              <p className="mb-1.5 px-2 text-2xs font-medium uppercase tracking-wider text-content-faint">
                {group.label}
              </p>
            ) : (
              <div className="mx-2 mb-2 h-px bg-line" aria-hidden />
            )}
            <ul className="space-y-0.5">
              {group.items.map((item) => {
                const active = isActive(item.href);
                const Icon = item.icon;
                return (
                  <li key={item.href}>
                    <Link
                      href={item.href}
                      onClick={onNavigate}
                      title={collapsed ? item.label : undefined}
                      aria-current={active ? "page" : undefined}
                      className={cn(
                        "group relative flex items-center gap-2.5 rounded-lg px-2 py-2 transition-colors",
                        active
                          ? "bg-info/10 text-content"
                          : "text-content-muted hover:bg-surface-raised hover:text-content",
                      )}
                    >
                      {active ? (
                        <span
                          className="absolute inset-y-1.5 left-0 w-0.5 rounded-full bg-info"
                          aria-hidden
                        />
                      ) : null}
                      <Icon
                        className={cn("h-4 w-4 shrink-0", active ? "text-info" : "text-content-faint")}
                        aria-hidden
                      />
                      {!collapsed ? (
                        <span className="min-w-0 flex-1">
                          <span className="block truncate text-[13px] font-medium leading-tight">
                            {item.label}
                          </span>
                          <span className="block truncate text-2xs text-content-faint">
                            {item.module ?? item.description}
                          </span>
                        </span>
                      ) : null}
                    </Link>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </div>

      {/* Collapse control */}
      <div className="border-t border-line p-2.5">
        <button
          type="button"
          onClick={onToggle}
          className="flex w-full items-center gap-2.5 rounded-lg px-2 py-2 text-content-faint transition-colors hover:bg-surface-raised hover:text-content"
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? (
            <PanelLeftOpen className="h-4 w-4" aria-hidden />
          ) : (
            <PanelLeftClose className="h-4 w-4" aria-hidden />
          )}
          {!collapsed ? <span className="text-xs font-medium">Collapse</span> : null}
        </button>
      </div>
    </nav>
  );
}
