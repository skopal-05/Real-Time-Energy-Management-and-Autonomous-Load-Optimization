import type { Metadata, Viewport } from "next";
import "./globals.css";
import { AppStateProvider } from "@/providers/AppStateProvider";
import { AuthProvider } from "@/providers/AuthProvider";

export const metadata: Metadata = {
  title: {
    default: "EnerTwin · Digital Twin Energy Control Centre",
    template: "%s · EnerTwin",
  },
  description:
    "Control centre for a generative digital twin performing real-time energy management and autonomous load optimisation across an industrial manufacturing site.",
};

export const viewport: Viewport = {
  themeColor: "#070A0F",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-base text-content">
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:absolute focus:left-3 focus:top-3 focus:z-[100] focus:rounded-md focus:bg-surface-overlay focus:px-3 focus:py-2 focus:text-xs focus:text-content"
        >
          Skip to content
        </a>
        <AuthProvider>
          <AppStateProvider>{children}</AppStateProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
