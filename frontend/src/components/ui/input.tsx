"use client";

import * as React from "react";
import { Search, X } from "lucide-react";
import { cn } from "@/utils/cn";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  icon?: React.ReactNode;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type = "text", label, error, helperText, icon, ...props }, ref) => {
    return (
      <div className="w-full flex flex-col gap-1.5">
        {label && (
          <label className="text-sm font-semibold text-foreground/80 tracking-wide">
            {label}
          </label>
        )}
        <div className="relative flex items-center">
          {icon && (
            <div className="absolute left-3 text-muted pointer-events-none">
              {icon}
            </div>
          )}
          <input
            type={type}
            ref={ref}
            className={cn(
              "w-full bg-slate-900/40 border border-border rounded-lg py-2.5 px-4 text-sm text-foreground placeholder:text-muted/60 transition-all duration-300 focus:outline-none focus:border-primary/60 focus:ring-1 focus:ring-primary/40 focus:shadow-[0_0_15px_rgba(139,92,246,0.15)]",
              icon && "pl-10",
              error && "border-red-500/50 focus:border-red-500/80 focus:ring-red-500/20 focus:shadow-[0_0_15px_rgba(239,68,68,0.1)]",
              className
            )}
            {...props}
          />
        </div>
        {error && (
          <span className="text-xs text-red-400 font-medium">{error}</span>
        )}
        {helperText && !error && (
          <span className="text-xs text-muted font-normal">{helperText}</span>
        )}
      </div>
    );
  }
);
Input.displayName = "Input";

// ----------------------------------------------------
// SEARCH BOX
// ----------------------------------------------------
export interface SearchBoxProps extends Omit<InputProps, "icon"> {
  onClear?: () => void;
  value?: string;
}

export const SearchBox = React.forwardRef<HTMLInputElement, SearchBoxProps>(
  ({ className, onClear, value, ...props }, ref) => {
    return (
      <div className="relative w-full flex items-center">
        <Search className="absolute left-3 w-4 h-4 text-muted pointer-events-none" />
        <input
          ref={ref}
          type="text"
          value={value}
          className={cn(
            "w-full bg-slate-900/60 border border-border rounded-xl py-3 pl-10 pr-10 text-sm text-foreground placeholder:text-muted/60 backdrop-blur-md transition-all duration-300 focus:outline-none focus:border-accent/60 focus:ring-1 focus:ring-accent/40 focus:shadow-[0_0_15px_rgba(34,211,238,0.15)]",
            className
          )}
          {...props}
        />
        {value && onClear && (
          <button
            type="button"
            onClick={onClear}
            className="absolute right-3 p-1 rounded-full text-muted hover:text-foreground hover:bg-white/10 transition-colors"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        )}
      </div>
    );
  }
);
SearchBox.displayName = "SearchBox";
