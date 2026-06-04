"use client";

import * as React from "react";
import { motion, HTMLMotionProps } from "framer-motion";
import { cn } from "@/utils/cn"; // Custom class merger

export interface ButtonProps extends Omit<HTMLMotionProps<"button">, "ref"> {
  variant?: "primary" | "secondary" | "ghost" | "outline";
  size?: "sm" | "md" | "lg";
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", size = "md", children, ...props }, ref) => {
    const baseStyles = "inline-flex items-center justify-center font-medium rounded-lg transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-primary/50 focus:ring-offset-2 focus:ring-offset-background disabled:opacity-50 disabled:pointer-events-none gap-2";
    
    const variants = {
      primary: "bg-primary hover:bg-secondary text-foreground shadow-lg shadow-primary/20 hover:shadow-primary/35 border border-primary/30",
      secondary: "bg-slate-900/60 hover:bg-slate-800/80 text-foreground border border-primary/20 hover:border-primary/50 shadow-md backdrop-blur-md",
      ghost: "text-muted hover:text-foreground hover:bg-white/5",
      outline: "bg-transparent border border-accent/40 text-accent hover:bg-accent/10 hover:border-accent/80 hover:shadow-lg hover:shadow-accent/10",
    };

    const sizes = {
      sm: "px-3 py-1.5 text-xs",
      md: "px-4 py-2 text-sm",
      lg: "px-6 py-3 text-base rounded-xl",
    };

    return (
      <motion.button
        ref={ref}
        whileHover={{ scale: 1.02, y: -1 }}
        whileTap={{ scale: 0.98 }}
        className={cn(baseStyles, variants[variant], sizes[size], className)}
        {...props}
      >
        {children}
      </motion.button>
    );
  }
);

Button.displayName = "Button";
