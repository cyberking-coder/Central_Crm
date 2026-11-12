import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Central CRM",
  description: "Central Company CRM — internal platform.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
