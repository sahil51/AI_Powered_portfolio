"use client";

import * as React from "react";
import Link from "next/link";
import { Mail, AlertCircle, CheckCircle2, ArrowRight } from "lucide-react";
import { AuthLayoutWrapper } from "@/components/auth-layout-wrapper";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

export default function ForgotPassword() {
  const [email, setEmail] = React.useState("");
  const [emailError, setEmailError] = React.useState("");
  
  // UX states
  const [isLoading, setIsLoading] = React.useState(false);
  const [errorMessage, setErrorMessage] = React.useState("");
  const [successMessage, setSuccessMessage] = React.useState("");

  const handleResetRequest = (e: React.FormEvent) => {
    e.preventDefault();
    setEmailError("");
    setErrorMessage("");
    setSuccessMessage("");

    if (!email.trim()) {
      setEmailError("Email address is required");
      return;
    } else if (!/\S+@\S+\.\S+/.test(email)) {
      setEmailError("Please enter a valid email format");
      return;
    }

    setIsLoading(true);

    // Simulate sending reset link
    setTimeout(() => {
      setIsLoading(false);
      setSuccessMessage(`A password reset link has been dispatched to ${email}. Please check your inbox and spam folder.`);
    }, 1500);
  };

  return (
    <AuthLayoutWrapper
      title="Forgot Password"
      subtitle="Enter your email address and we'll dispatch password reset guidelines."
    >
      <form onSubmit={handleResetRequest} className="flex flex-col gap-5">
        
        {/* Error Alert Box */}
        {errorMessage && (
          <div className="flex items-start gap-2.5 p-3.5 rounded-xl bg-red-500/10 border border-red-500/30 text-red-200 text-xs">
            <AlertCircle className="w-4.5 h-4.5 flex-shrink-0 text-red-400" />
            <span>{errorMessage}</span>
          </div>
        )}

        {/* Success Alert Box */}
        {successMessage ? (
          <div className="flex flex-col gap-4">
            <div className="flex items-start gap-2.5 p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-200 text-xs">
              <CheckCircle2 className="w-4.5 h-4.5 flex-shrink-0 text-emerald-400" />
              <span>{successMessage}</span>
            </div>
            
            {/* Quick Demo Redirect to Reset Link */}
            <div className="p-3.5 rounded-xl bg-slate-900 border border-border flex flex-col gap-2">
              <span className="text-[11px] font-bold text-accent uppercase tracking-wider">
                Dev Environment Simulation Link:
              </span>
              <p className="text-xs text-muted">
                To test the reset flow, use the tokenized redirection link below:
              </p>
              <Link href="/reset-password" className="inline-flex">
                <Button type="button" variant="outline" size="sm" className="w-full gap-2 border-accent/30 text-accent hover:bg-accent/10">
                  Simulate Email Reset Link
                  <ArrowRight className="w-3.5 h-3.5" />
                </Button>
              </Link>
            </div>
          </div>
        ) : (
          <>
            {/* Email Field */}
            <Input
              label="Email address"
              type="email"
              placeholder="name@company.com"
              value={email}
              onChange={(e) => {
                setEmail(e.target.value);
                if (emailError) setEmailError("");
              }}
              error={emailError}
              icon={<Mail className="w-4 h-4" />}
              disabled={isLoading}
              required
            />

            {/* Submit */}
            <Button type="submit" variant="primary" className="w-full py-2.5 mt-2" disabled={isLoading}>
              {isLoading ? (
                <span className="flex items-center gap-2">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Dispatching guidelines...
                </span>
              ) : (
                "Send Reset Link"
              )}
            </Button>
          </>
        )}

        {/* Back redirect */}
        <p className="text-center text-xs text-muted mt-4">
          Remember your password?{" "}
          <Link href="/login" className="font-semibold text-primary hover:text-accent transition-colors">
            Sign In
          </Link>
        </p>

      </form>
    </AuthLayoutWrapper>
  );
}
