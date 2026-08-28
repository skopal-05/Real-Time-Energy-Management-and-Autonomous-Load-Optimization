import Link from "next/link";
import { Compass } from "lucide-react";

export default function NotFound() {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-3 text-center">
      <span className="flex h-12 w-12 items-center justify-center rounded-xl border border-line bg-surface-inset">
        <Compass className="h-5 w-5 text-content-faint" aria-hidden />
      </span>
      <h2 className="text-lg font-semibold tracking-tight text-content">Page not found</h2>
      <p className="max-w-md text-xs leading-relaxed text-content-muted">
        This route is not part of the control centre. Use the sidebar to reach a module, or return to the
        command centre.
      </p>
      <Link
        href="/"
        className="mt-1 rounded-lg border border-info/30 bg-info/10 px-3 py-1.5 text-xs font-medium text-info transition-colors hover:bg-info/15"
      >
        Back to Overview
      </Link>
    </div>
  );
}
