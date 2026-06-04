"use client";

import * as React from "react";
import Link from "next/link";
import { Lock, AlertCircle, CheckCircle2, KeyRound } from "lucide-react";
import { AuthLayoutWrapper } from "@/components/auth-layout-wrapper";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

export default function ResetPassword() {
  const [password, setPassword] = React.useState("");
  const [confirmPassword, setConfirmPassword] = React.useState("");
  
  // Field errors
  const [passwordError, setPasswordError] = React.useState("");
  const [confirmError, setConfirmError] = React.useState("");

  // UX states
  const [isLoading, setIsLoading] = React.useState(false);
  const [errorMessage, setErrorMessage] = React.useState("");
  const [successMessage, setSuccessMessage] = React.useState("");

  // Password strength metrics
  const [strengthScore, setStrengthScore] = React.useState(0);
  const [strengthLabel, setStrengthLabel] = React.useState("");

  React.useEffect(() => {
    if (!password) {
      setStrengthScore(0);
      setStrengthLabel("");
      return;
    }

    let score = 0;
    if (password.length >= 6) score += 1;
    if (password.length >= 8) score += 1;
    if (/[A-Z]/.test(password)) score += 1;
    if (/[0-9]/.test(password)) score += 1;
    if (/[^A-Za-z0-9]/.test(password)) score += 1;

    setStrengthScore(score);

    if (score <= 2) {
      setStrengthLabel("Weak");
    } else if (score <= 4) {
      setStrengthLabel("Medium");
    } else {
      setStrengthLabel("Strong");
    }
  }, [password]);

  const validate = () => {
    let isValid = true;
    setPasswordError("");
    setConfirmError("");

    if (!password) {
      setPasswordError("Password is required");
      isValid = false;
    } else if (password.length < 6) {
      setPasswordError("Password must be at least 6 characters");
      isValid = false;
    }

    if (password !== confirmPassword) {
      setConfirmError("Passwords do not match");
      isValid = false;
    }

    return isValid;
  };

  const handleResetPassword = (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage("");
    setSuccessMessage("");

    if (!validate()) return;

    setIsLoading(true);

    // Simulate reset
    setTimeout(() => {
      setIsLoading(false);
      setSuccessMessage("Password reset completed successfully! You can now log in with your new password.");
    }, 1800);
  };

  const getStrengthColor = () => {
    if (strengthScore <= 2) return "bg-red-500";
    if (strengthScore <= 4) return "bg-amber-400";
    return "bg-emerald-500";
  };

  return (
    <AuthLayoutWrapper
      title="Reset Password"
      subtitle="Establish your new password credentials for secure console session access."
    >
      <form onSubmit={handleResetPassword} className="flex flex-col gap-5">
        
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
            
            <Link href="/login" className="inline-flex">
              <Button type="button" variant="primary" className="w-full">
                Proceed to Login
              </Button>
            </Link>
          </div>
        ) : (
          <>
            {/* New Password */}
            <div>
              <Input
                label="New password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value);
                  if (passwordError) setPasswordError("");
                }}
                error={passwordError}
                icon={<Lock className="w-4 h-4" />}
                disabled={isLoading}
                required
              />

              {/* Password Strength Meter */}
              {password && (
                <div className="mt-2">
                  <div className="flex justify-between items-center mb-1 text-xs">
                    <span className="text-muted">Password Strength:</span>
                    <span className={`font-semibold ${
                      strengthScore <= 2 ? "text-red-400" : strengthScore <= 4 ? "text-amber-400" : "text-emerald-400"
                    }`}>
                      {strengthLabel}
                    </span>
                  </div>
                  <div className="h-1.5 w-full bg-slate-900 border border-white/5 rounded-full overflow-hidden">
                    <div
                      className={`h-full transition-all duration-300 ${getStrengthColor()}`}
                      style={{ width: `${(strengthScore / 5) * 100}%` }}
                    />
                  </div>
                </div>
              )}
            </div>

            {/* Confirm Password */}
            <Input
              label="Confirm new password"
              type="password"
              placeholder="••••••••"
              value={confirmPassword}
              onChange={(e) => {
                setConfirmPassword(e.target.value);
                if (confirmError) setConfirmError("");
              }}
              error={confirmError}
              icon={<Lock className="w-4 h-4" />}
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
                  Syncing new keys...
                </span>
              ) : (
                <span className="flex items-center gap-2">
                  <KeyRound className="w-4.5 h-4.5" />
                  Reset Password
                </span>
              )}
            </Button>
          </>
        )}

        {/* Footnote */}
        <p className="text-center text-xs text-muted mt-4">
          Need to go back?{" "}
          <Link href="/login" className="font-semibold text-primary hover:text-accent transition-colors">
            Sign In
          </Link>
        </p>

      </form>
    </AuthLayoutWrapper>
  );
}
