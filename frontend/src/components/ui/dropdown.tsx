"use client";

import * as React from "react";
import { ChevronDown, Check } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/utils/cn";

export interface DropdownOption {
  value: string;
  label: string;
}

export interface DropdownProps {
  options: DropdownOption[];
  selectedValue: string;
  onChange: (value: string) => void;
  placeholder?: string;
  label?: string;
  className?: string;
}

export function Dropdown({
  options,
  selectedValue,
  onChange,
  placeholder = "Select option",
  label,
  className,
}: DropdownProps) {
  const [isOpen, setIsOpen] = React.useState(false);
  const containerRef = React.useRef<HTMLDivElement>(null);

  const selectedOption = options.find((opt) => opt.value === selectedValue);

  // Close when clicking outside
  React.useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div className={cn("relative w-full flex flex-col gap-1.5", className)} ref={containerRef}>
      {label && (
        <label className="text-sm font-semibold text-foreground/80 tracking-wide">
          {label}
        </label>
      )}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full bg-slate-900/60 border border-border rounded-lg py-2.5 px-4 text-sm text-foreground flex items-center justify-between transition-all duration-300 focus:outline-none focus:border-primary/60 focus:ring-1 focus:ring-primary/40 focus:shadow-[0_0_15px_rgba(139,92,246,0.15)] text-left backdrop-blur-md"
      >
        <span className={cn(!selectedOption && "text-muted/60")}>
          {selectedOption ? selectedOption.label : placeholder}
        </span>
        <ChevronDown
          className={cn(
            "w-4 h-4 text-muted transition-transform duration-300",
            isOpen && "rotate-180 text-primary"
          )}
        />
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.ul
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 4 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2, ease: "easeOut" }}
            className="absolute z-50 left-0 right-0 top-full glass-panel rounded-xl shadow-xl shadow-black/40 py-1 overflow-hidden max-h-60 overflow-y-auto"
          >
            {options.length === 0 ? (
              <li className="px-4 py-2.5 text-sm text-muted">No options available</li>
            ) : (
              options.map((option) => {
                const isSelected = option.value === selectedValue;
                return (
                  <li key={option.value}>
                    <button
                      type="button"
                      onClick={() => {
                        onChange(option.value);
                        setIsOpen(false);
                      }}
                      className={cn(
                        "w-full text-left px-4 py-2.5 text-sm flex items-center justify-between transition-colors",
                        isSelected
                          ? "bg-primary/20 text-accent font-medium"
                          : "text-foreground/90 hover:bg-white/5 hover:text-foreground"
                      )}
                    >
                      {option.label}
                      {isSelected && <Check className="w-4 h-4 text-accent" />}
                    </button>
                  </li>
                );
              })
            )}
          </motion.ul>
        )}
      </AnimatePresence>
    </div>
  );
}
