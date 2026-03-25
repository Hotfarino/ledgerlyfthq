import type { Metadata } from "next";
import { Manrope, IBM_Plex_Mono } from "next/font/google";
import "./globals.css";
import { Sidebar } from "@/components/sidebar";

const manrope = Manrope({
  subsets: ["latin"],
  variable: "--font-body"
});

const plexMono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400", "500"],
  variable: "--font-mono"
});

export const metadata: Metadata = {
  title: "LedgerLift",
  description: "Local-first bookkeeping cleanup support tool"
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${manrope.variable} ${plexMono.variable} font-[var(--font-body)]`}>
        <div className="flex min-h-screen">
          <Sidebar />
          <main className="flex-1 px-6 py-6 md:px-8">{children}</main>
        </div>
      </body>
    </html>
  );
}
