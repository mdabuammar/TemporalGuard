import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "TemporalGuard",
  description: "Verify, correct, and trust time-sensitive AI answers."
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
