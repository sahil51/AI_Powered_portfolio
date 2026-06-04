"use client";

import * as React from "react";
import { motion, HTMLMotionProps } from "framer-motion";
import { cn } from "@/utils/cn";

// ----------------------------------------------------
// BASE CARD
// ----------------------------------------------------
export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  hoverEffect?: boolean;
  glow?: boolean;
}

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, hoverEffect = true, glow = false, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          "glass-panel rounded-2xl p-6 overflow-hidden relative transition-all duration-300",
          hoverEffect && "glass-panel-hover hover:-translate-y-1",
          glow && "shadow-lg shadow-primary/10 border-primary/20",
          className
        )}
        {...props}
      >
        {/* Glow border overlays */}
        {glow && (
          <div className="absolute inset-0 bg-gradient-to-r from-primary/10 via-transparent to-accent/10 pointer-events-none opacity-50" />
        )}
        {children}
      </div>
    );
  }
);
Card.displayName = "Card";

// ----------------------------------------------------
// CARD SUB-COMPONENTS (shadcn-compatible)
// ----------------------------------------------------
export const CardHeader = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn("flex flex-col space-y-1.5 pb-6", className)} {...props} />
  )
);
CardHeader.displayName = "CardHeader";

export const CardTitle = React.forwardRef<HTMLHeadingElement, React.HTMLAttributes<HTMLHeadingElement>>(
  ({ className, ...props }, ref) => (
    <h3 ref={ref} className={cn("text-lg font-semibold leading-none tracking-tight text-foreground", className)} {...props} />
  )
);
CardTitle.displayName = "CardTitle";

export const CardDescription = React.forwardRef<HTMLParagraphElement, React.HTMLAttributes<HTMLParagraphElement>>(
  ({ className, ...props }, ref) => (
    <p ref={ref} className={cn("text-sm text-muted", className)} {...props} />
  )
);
CardDescription.displayName = "CardDescription";

export const CardContent = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn("pt-0", className)} {...props} />
  )
);
CardContent.displayName = "CardContent";

export const CardFooter = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn("flex items-center pt-4 border-t border-border", className)} {...props} />
  )
);
CardFooter.displayName = "CardFooter";

// ----------------------------------------------------
// STATS CARD
// ----------------------------------------------------
export interface StatsCardProps extends Omit<HTMLMotionProps<"div">, "ref"> {
  value: string;
  label: string;
}

export const StatsCard = React.forwardRef<HTMLDivElement, StatsCardProps>(
  ({ className, value, label, ...props }, ref) => {
    return (
      <motion.div
        ref={ref}
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.5, ease: "easeOut" }}
        whileHover={{ scale: 1.05 }}
        className={cn(
          "glass-panel rounded-2xl p-6 flex flex-col items-center justify-center text-center glass-panel-hover cursor-default relative overflow-hidden",
          className
        )}
        {...props}
      >
        {/* Inner ambient light */}
        <div className="absolute -bottom-10 -right-10 w-24 h-24 rounded-full bg-accent/10 blur-xl pointer-events-none" />
        <div className="absolute -top-10 -left-10 w-24 h-24 rounded-full bg-primary/10 blur-xl pointer-events-none" />

        <span className="text-4xl md:text-5xl font-black bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent mb-2">
          {value}
        </span>
        <span className="text-sm md:text-base text-muted font-medium tracking-wide uppercase">
          {label}
        </span>
      </motion.div>
    );
  }
);
StatsCard.displayName = "StatsCard";

// ----------------------------------------------------
// FEATURE CARD
// ----------------------------------------------------
export interface FeatureCardProps extends React.HTMLAttributes<HTMLDivElement> {
  icon: React.ReactNode;
  title: string;
  description: string;
  tags?: string[];
  actionLabel?: string;
  onActionClick?: () => void;
}

export const FeatureCard = React.forwardRef<HTMLDivElement, FeatureCardProps>(
  ({ className, icon, title, description, tags, actionLabel, onActionClick, ...props }, ref) => {
    return (
      <Card
        ref={ref}
        className={cn("flex flex-col justify-between h-full group", className)}
        {...props}
      >
        <div>
          {/* Glowing Icon Wrapper */}
          <div className="w-12 h-12 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary group-hover:text-accent group-hover:border-accent/40 group-hover:bg-accent/10 transition-all duration-300 mb-6 shadow-inner">
            {icon}
          </div>

          <h3 className="text-xl font-bold text-foreground mb-3 group-hover:text-primary transition-colors duration-300">
            {title}
          </h3>
          <p className="text-sm text-muted leading-relaxed mb-6">
            {description}
          </p>
        </div>

        <div>
          {tags && tags.length > 0 && (
            <div className="flex flex-wrap gap-1.5 mb-6">
              {tags.map((tag) => (
                <span
                  key={tag}
                  className="text-xs px-2.5 py-0.5 rounded-full bg-slate-900/80 border border-border text-muted font-medium"
                >
                  {tag}
                </span>
              ))}
            </div>
          )}

          {actionLabel && (
            <button
              onClick={onActionClick}
              className="text-sm font-semibold text-accent hover:text-foreground flex items-center gap-1.5 transition-colors group/btn"
            >
              {actionLabel}
              <span className="transform transition-transform group-hover/btn:translate-x-1 duration-300">
                &rarr;
              </span>
            </button>
          )}
        </div>
      </Card>
    );
  }
);
FeatureCard.displayName = "FeatureCard";

// ----------------------------------------------------
// TESTIMONIAL CARD
// ----------------------------------------------------
export interface TestimonialCardProps extends React.HTMLAttributes<HTMLDivElement> {
  quote: string;
  author: string;
  role: string;
  company: string;
  avatarUrl?: string;
}

export const TestimonialCard = React.forwardRef<HTMLDivElement, TestimonialCardProps>(
  ({ className, quote, author, role, company, avatarUrl, ...props }, ref) => {
    // Generate initials for placeholder avatar
    const initials = author
      .split(" ")
      .map((n) => n[0])
      .join("")
      .substring(0, 2)
      .toUpperCase();

    return (
      <Card ref={ref} className={cn("flex flex-col justify-between h-full", className)}>
        {/* Quote Icon SVG */}
        <div className="text-primary/30 mb-6">
          <svg className="w-8 h-8 fill-current" viewBox="0 0 32 32">
            <path d="M10 8c-3.3 0-6 2.7-6 6v10c0 1.1.9 2 2 2h10c1.1 0 2-.9 2-2V14c0-1.1-.9-2-2-2h-6c0-2.2 1.8-4 4-4 1.1 0 2-.9 2-2s-.9-2-2-2c-.3 0-.7.1-1 .2C13.8 8.1 11.9 8 10 8zm14 0c-3.3 0-6 2.7-6 6v10c0 1.1.9 2 2 2h10c1.1 0 2-.9 2-2V14c0-1.1-.9-2-2-2h-6c0-2.2 1.8-4 4-4 1.1 0 2-.9 2-2s-.9-2-2-2c-.3 0-.7.1-1 .2C27.8 8.1 25.9 8 24 8z" />
          </svg>
        </div>

        <p className="text-base text-foreground/90 italic leading-relaxed mb-8 flex-grow">
          &ldquo;{quote}&rdquo;
        </p>

        <div className="flex items-center gap-4 border-t border-border pt-4">
          {avatarUrl ? (
            <img
              src={avatarUrl}
              alt={author}
              className="w-10 h-10 rounded-full object-cover border border-primary/30"
            />
          ) : (
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary to-accent flex items-center justify-center text-xs font-bold text-slate-900 border border-white/10 shadow-md">
              {initials}
            </div>
          )}
          
          <div>
            <h4 className="text-sm font-bold text-foreground leading-none mb-1">
              {author}
            </h4>
            <p className="text-xs text-muted leading-none">
              {role} at <span className="text-accent">{company}</span>
            </p>
          </div>
        </div>
      </Card>
    );
  }
);
TestimonialCard.displayName = "TestimonialCard";
