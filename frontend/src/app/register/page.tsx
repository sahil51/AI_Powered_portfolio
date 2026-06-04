"use client";

import * as React from "react";
import Link from "next/link";
import { User, Mail, Lock, AlertCircle, CheckCircle2, ShieldCheck } from "lucide-react";
import { AuthLayoutWrapper } from "@/components/auth-layout-wrapper";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

export default function Register() {
  const [fullName, setFullName] = React.useState("");
  const [email, setEmail] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [confirmPassword, setConfirmPassword] = React.useState("");
  const [agreeTerms, setAgreeTerms] = React.useState(false);

  // Field errors
  const [nameError, setNameError] = React.useState("");
  const [emailError, setEmailError] = React.useState("");
  const [passwordError, setPasswordError] = React.useState("");
  const [confirmError, setConfirmError] = React.useState("");
  const [termsError, setTermsError] = React.useState("");

  // UX states
  const [isLoading, setIsLoading] = React.useState(false);
  const [successMessage, setSuccessMessage] = React.useState("");
  const [errorMessage, setErrorMessage] = React.useState("");

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
    setNameError("");
    setEmailError("");
    setPasswordError("");
    setConfirmError("");
    setTermsError("");

    if (!fullName.trim()) {
      setNameError("Full name is required");
      isValid = false;
    }

    if (!email.trim()) {
      setEmailError("Email address is required");
      isValid = false;
    } else if (!/\S+@\S+\.\S+/.test(email)) {
      setEmailError("Please enter a valid email format");
      isValid = false;
    }

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

    if (!agreeTerms) {
      setTermsError("You must agree to the Terms and Conditions");
      isValid = false;
    }

    return isValid;
  };

  const handleRegister = (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage("");
    setSuccessMessage("");

    if (!validate()) return;

    setIsLoading(true);

    // Simulate registration
    setTimeout(() => {
      setIsLoading(false);
      setSuccessMessage("Account created successfully! Redirecting to login...");
    }, 1800);
  };

  const getStrengthColor = () => {
    if (strengthScore <= 2) return "bg-red-500";
    if (strengthScore <= 4) return "bg-amber-400";
    return "bg-emerald-500";
  };

  return (
    <AuthLayoutWrapper
      title="Create account"
      subtitle="Sign up for free and deploy your first AI workers today"
    >
      <form onSubmit={handleRegister} className="flex flex-col gap-4">
        
        {/* Error Alert Box */}
        {errorMessage && (
          <div className="flex items-start gap-2.5 p-3.5 rounded-xl bg-red-500/10 border border-red-500/30 text-red-200 text-xs">
            <AlertCircle className="w-4.5 h-4.5 flex-shrink-0 text-red-400" />
            <span>{errorMessage}</span>
          </div>
        )}

        {/* Success Alert Box */}
        {successMessage && (
          <div className="flex items-start gap-2.5 p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-200 text-xs">
            <CheckCircle2 className="w-4.5 h-4.5 flex-shrink-0 text-emerald-400" />
            <span>{successMessage}</span>
          </div>
        )}

        {/* Full Name */}
        <Input
          label="Full name"
          type="text"
          placeholder="John Doe"
          value={fullName}
          onChange={(e) => {
            setFullName(e.target.value);
            if (nameError) setNameError("");
          }}
          error={nameError}
          icon={<User className="w-4 h-4" />}
          disabled={isLoading}
          required
        />

        {/* Email Address */}
        <Input
          label="Email address"
          type="email"
          placeholder="john@company.com"
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

        {/* Password */}
        <div>
          <Input
            label="Password"
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
          label="Confirm password"
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

        {/* Terms Checkbox */}
        <div className="flex flex-col gap-1.5 mt-1">
          <label className="flex items-start gap-2.5 text-xs text-muted hover:text-foreground cursor-pointer select-none">
            <input
              type="checkbox"
              checked={agreeTerms}
              onChange={(e) => {
                setAgreeTerms(e.target.checked);
                if (termsError) setTermsError("");
              }}
              disabled={isLoading}
              className="rounded mt-0.5 bg-slate-900 border-border text-primary focus:ring-primary focus:ring-offset-background"
            />
            <span>
              I agree to the{" "}
              <Link href="#" className="font-semibold text-primary hover:text-accent transition-colors">
                Terms of Service
              </Link>{" "}
              and{" "}
              <Link href="#" className="font-semibold text-primary hover:text-accent transition-colors">
                Privacy Policy
              </Link>
            </span>
          </label>
          {termsError && (
            <span className="text-xs text-red-400 font-medium">{termsError}</span>
          )}
        </div>

        {/* Submit */}
        <Button type="submit" variant="primary" className="w-full py-2.5 mt-2" disabled={isLoading}>
          {isLoading ? (
            <span className="flex items-center gap-2">
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              Creating agent workspace...
            </span>
          ) : (
            <span className="flex items-center gap-2">
              <ShieldCheck className="w-4.5 h-4.5" />
              Create Account
            </span>
          )}
        </Button>

        {/* Login redirect */}
        <p className="text-center text-xs text-muted mt-4">
          Already have an account?{" "}
          <Link href="/login" className="font-semibold text-primary hover:text-accent transition-colors">
            Sign In
          </Link>
        </p>

      </form>
    </AuthLayoutWrapper>
  );
}
