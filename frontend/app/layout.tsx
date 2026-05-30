import "./globals.css";
import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "GigProof — Financial Identity for India's Invisible Workforce",
  description:
    "Multi-agent system on Coral that turns gig earnings across Zomato, Swiggy, Ola, Uber, Urban Company into ITR filings, bank-grade income certificates, and credit identity.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="glow min-h-screen antialiased">{children}</body>
    </html>
  );
}
