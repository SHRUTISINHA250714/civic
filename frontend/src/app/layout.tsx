import type { Metadata } from "next";
// import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Toaster } from "sonner";

const geistSans = { variable: "--font-geist-sans" };
const geistMono = { variable: "--font-geist-mono" };

export const metadata: Metadata = {
  title: "CivicAI Karnataka – Smart Civic Grievance Management",
  description: "AI-Powered Civic Grievance Management System for Karnataka - Automatically classify complaints, verify images, detect duplicates, and route issues to BBMP, BWSSB, BESCOM, and Traffic Police.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100">
        {children}
        <Toaster position="top-right" richColors />
      </body>
    </html>
  );
}
