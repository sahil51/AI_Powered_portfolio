"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Mail, Lock, Eye, EyeOff, Sparkles, AlertCircle, CheckCircle2 } from "lucide-react";
import { AuthLayoutWrapper } from "@/components/auth-layout-wrapper";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

const GoogleIcon = (props: React.SVGProps<SVGSVGElement>) => (
  <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor" {...props}>
    <path d="M12.24 10.285V13.4h6.887c-.275 1.565-1.88 4.604-6.887 4.604-4.33 0-7.859-3.579-7.859-8s3.53-8 7.859-8c2.46 0 4.105 1.025 5.047 1.926l2.427-2.334C17.955 2.192 15.34 1 12.24 1 6.133 1 1.18 5.925 1.18 12s4.953 11 11.06 11c6.373 0 10.596-4.475 10.596-10.77 0-.725-.078-1.285-.177-1.945H12.24z" />
  </svg>
);

const GithubIcon = (props: React.SVGProps<SVGSVGElement>) => (
  <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round" {...props}>
    <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22" />
  </svg>
);

export default function Login() {
  const router = useRouter();
  const [email, setEmail] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [emailError, setEmailError] = React.useState("");
  const [passwordError, setPasswordError] = React.useState("");
  
  const [showPassword, setShowPassword] = React.useState(false);
  const [rememberMe, setRememberMe] = React.useState(false);
  
  // UX states
  const [isLoading, setIsLoading] = React.useState(false);
  const [errorMessage, setErrorMessage] = React.useState("");
  const [successMessage, setSuccessMessage] = React.useState("");

  const validate = () => {
    let isValid = true;
    setEmailError("");
    setPasswordError("");

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
    }

    return isValid;
  };

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage("");
    setSuccessMessage("");

    if (!validate()) return;

    setIsLoading(true);

    // Simulate login authentication
    setTimeout(() => {
      setIsLoading(false);
      // Hardcoded check for simulation
      if (email.toLowerCase() === "recruit@lucy.ai" && password === "lucy123") {
        setSuccessMessage("Authentication successful! Redirecting to the dashboard...");
        setTimeout(() => {
          router.push("/dashboard");
        }, 700);
      } else {
        setErrorMessage("Invalid credentials. Try using 'recruit@lucy.ai' with password 'lucy123' to login.");
      }
    }, 1500);
  };

  return (
    <AuthLayoutWrapper
      title="Welcome back"
      subtitle="Sign in to your account to manage your AI workers"
    >
      <form onSubmit={handleLogin} className="flex flex-col gap-5">
        
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

        {/* Password Field */}
        <div className="relative">
          <Input
            label="Password"
            type={showPassword ? "text" : "password"}
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
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute right-3.5 top-[38px] text-muted hover:text-foreground transition-colors"
            tabIndex={-1}
          >
            {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
          </button>
        </div>

        {/* Remember me & Forgot Pass row */}
        <div className="flex items-center justify-between text-xs sm:text-sm">
          <label className="flex items-center gap-2 text-muted hover:text-foreground cursor-pointer select-none">
            <input
              type="checkbox"
              checked={rememberMe}
              onChange={(e) => setRememberMe(e.target.checked)}
              disabled={isLoading}
              className="rounded bg-slate-900 border-border text-primary focus:ring-primary focus:ring-offset-background"
            />
            Remember me
          </label>
          
          <Link
            href="/forgot-password"
            className="font-semibold text-primary hover:text-accent transition-colors"
          >
            Forgot password?
          </Link>
        </div>

        {/* Sign In Trigger Button */}
        <Button type="submit" variant="primary" className="w-full py-2.5 mt-2" disabled={isLoading}>
          {isLoading ? (
            <span className="flex items-center gap-2">
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              Authenticating credentials...
            </span>
          ) : (
            "Sign In"
          )}
        </Button>

        {/* Social Dividers */}
        <div className="relative flex items-center justify-center my-2">
          <div className="absolute inset-x-0 h-px bg-border/40" />
          <span className="relative z-10 px-3 text-[11px] font-bold uppercase tracking-wider text-muted/60 bg-[#121929] rounded-md">
            Or continue with
          </span>
        </div>

        {/* Social Actions Buttons */}
        <div className="grid grid-cols-2 gap-3">
          <Button
            type="button"
            variant="secondary"
            className="py-2 flex items-center justify-center gap-2 text-xs font-semibold"
            onClick={() => alert("Google sign-in initiated (Mock)")}
            disabled={isLoading}
          >
            <GoogleIcon />
            Google
          </Button>
          <Button
            type="button"
            variant="secondary"
            className="py-2 flex items-center justify-center gap-2 text-xs font-semibold"
            onClick={() => alert("GitHub sign-in initiated (Mock)")}
            disabled={isLoading}
          >
            <GithubIcon />
            GitHub
          </Button>
        </div>

        {/* Footnote links */}
        <p className="text-center text-xs text-muted mt-4">
          Don&apos;t have an account?{" "}
          <Link href="/register" className="font-semibold text-primary hover:text-accent transition-colors">
            Register for free
          </Link>
        </p>

      </form>
    </AuthLayoutWrapper>
  );
}
