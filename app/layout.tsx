import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ChronoVault",
  description:
    "ChronoVault is a GenLayer-powered redemption protocol for evidence-based Web3 sanction rehabilitation."
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
