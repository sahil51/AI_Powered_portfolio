"use client";

import * as React from "react";
import Link from "next/link";
import { Menu, X, Bot } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";

const navLinks = [
  { name: "Home", href: "/" },
  { name: "About", href: "/about" },
  { name: "Projects", href: "/projects" },
  { name: "AI Assistant", href: "/assistant" },
  { name: "Contact", href: "/contact" },
];

export function Navbar({ onTalkToAI }: { onTalkToAI?: () => void }) {
  const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false);
  const [scrolled, setScrolled] = React.useState(false);

  React.useEffect(() => {
    const handleScroll = () => {
      if (window.scrollY > 20) {
        setScrolled(true);
      } else {
        setScrolled(false);
      }
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <>
      <header
        className={`fixed top-0 left-0 right-0 z-40 transition-all duration-300 ${
          scrolled ? "glass-navbar py-3 shadow-lg shadow-black/20" : "bg-transparent py-5"
        }`}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            {/* Logo */}
            <Link href="#home" className="flex items-center gap-2 group">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-primary to-accent flex items-center justify-center text-slate-900 font-bold shadow-md shadow-primary/20 group-hover:scale-105 transition-transform duration-300">
                <Bot className="w-4 h-4 text-slate-950" />
              </div>
              <span className="text-xl font-black tracking-tight text-foreground group-hover:text-primary transition-colors">
                Lucy <span className="text-accent">AI</span>
              </span>
            </Link>

            {/* Desktop Nav Links */}
            <nav className="hidden md:flex items-center gap-8">
              {navLinks.map((link) => (
                <Link
                  key={link.name}
                  href={link.href}
                  className="text-sm font-medium text-muted hover:text-foreground transition-colors relative group py-1"
                >
                  {link.name}
                  <span className="absolute bottom-0 left-0 w-0 h-0.5 bg-accent transition-all duration-300 group-hover:w-full" />
                </Link>
              ))}
            </nav>

            {/* Desktop Action Buttons */}
            <div className="hidden md:flex items-center gap-4">
              {onTalkToAI && (
                <Button variant="outline" size="sm" onClick={onTalkToAI} className="border-primary/40 text-primary hover:bg-primary/10">
                  <Bot className="w-4 h-4" />
                  Talk With AI
                </Button>
              )}
              <Link href="/login">
                <Button variant="ghost" size="sm">
                  Login
                </Button>
              </Link>
              <Link href="/register">
                <Button variant="primary" size="sm">
                  Get Started
                </Button>
              </Link>
            </div>

            {/* Mobile Hamburger Trigger */}
            <div className="flex md:hidden items-center gap-3">
              {onTalkToAI && (
                <Button variant="outline" size="sm" onClick={onTalkToAI} className="px-2.5 border-primary/40">
                  <Bot className="w-4 h-4" />
                </Button>
              )}
              <button
                type="button"
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="text-muted hover:text-foreground p-1.5 rounded-lg hover:bg-white/5 transition-colors"
              >
                {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Mobile Drawer Menu */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setMobileMenuOpen(false)}
              className="fixed inset-0 z-30 bg-black/60 backdrop-blur-sm md:hidden"
            />

            {/* Sliding Panel */}
            <motion.div
              initial={{ x: "100%" }}
              animate={{ x: 0 }}
              exit={{ x: "100%" }}
              transition={{ type: "spring", damping: 25, stiffness: 200 }}
              className="fixed right-0 top-0 bottom-0 w-3/4 max-w-sm z-35 bg-card border-l border-white/5 p-6 flex flex-col justify-between shadow-2xl md:hidden pt-24"
            >
              <div className="flex flex-col gap-6">
                <span className="text-xs font-semibold tracking-wider text-muted uppercase border-b border-border pb-2">
                  Navigation
                </span>
                <nav className="flex flex-col gap-4">
                  {navLinks.map((link) => (
                    <Link
                      key={link.name}
                      href={link.href}
                      onClick={() => setMobileMenuOpen(false)}
                      className="text-lg font-medium text-muted hover:text-foreground transition-colors py-1"
                    >
                      {link.name}
                    </Link>
                  ))}
                </nav>
              </div>

              <div className="flex flex-col gap-4 border-t border-border pt-6">
                <Link href="/login" onClick={() => setMobileMenuOpen(false)} className="w-full">
                  <Button
                    variant="ghost"
                    className="w-full justify-center"
                  >
                    Login
                  </Button>
                </Link>
                <Link href="/register" onClick={() => setMobileMenuOpen(false)} className="w-full">
                  <Button
                    variant="primary"
                    className="w-full justify-center shadow-lg"
                  >
                    Get Started
                  </Button>
                </Link>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
