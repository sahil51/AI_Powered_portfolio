import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { ToastProvider } from "@/components/ui/ToastProvider";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "Lucy AI | Portfolio Platform & Multi-Agent Assistant",
  description: "Showcase Projects. Automate Research. Impress Recruiters. Explore Lucy's projects and interact with the custom AI Agent recruiter assistant.",
  keywords: ["AI Portfolio", "Multi-Agent System", "AI Backend Engineer", "Django", "Redis", "Celery", "PostgreSQL", "Next.js", "Tailwind CSS"],
  authors: [{ name: "Lucy AI" }],
  openGraph: {
    title: "Lucy AI | Portfolio Platform & Multi-Agent Assistant",
    description: "Showcase Projects. Automate Research. Impress Recruiters. Interact with the custom AI Agent recruiter assistant.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${inter.variable} h-full antialiased scroll-smooth`}
    >
      <body className="min-h-full bg-background text-foreground antialiased flex flex-col selection:bg-primary/35 selection:text-accent">
        <ToastProvider>
          {children}
        </ToastProvider>
      </body>
    </html>
  );
}
