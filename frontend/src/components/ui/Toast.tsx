"use client";

import * as React from "react";
import { X } from "lucide-react";
import { Button } from "@/components/ui/button";

export interface ToastProps {
  id: string;
  title?: string;
  description?: string;
  type?: "success" | "error" | "info";
  onClose?: () => void;
}

const colors: Record<string, string> = {
  success: "bg-emerald-500/10 border-emerald-500/20 text-emerald-300",
  error: "bg-rose-500/10 border-rose-500/20 text-rose-300",
  info: "bg-slate-700/10 border-white/10 text-muted",
};

export default function Toast({ id, title, description, type = "info", onClose }: ToastProps) {
  return (
    <div className={`rounded-xl border px-4 py-3 shadow-md ${colors[type]} flex items-start gap-3 max-w-sm`} role="status" aria-live="polite">
      <div className="flex-1">
        {title && <div className="text-sm font-semibold">{title}</div>}
        {description && <div className="text-xs text-muted mt-1">{description}</div>}
      </div>
      <div>
        <Button variant="ghost" size="sm" onClick={onClose} aria-label="Close notification">
          <X className="w-4 h-4" />
        </Button>
      </div>
    </div>
  );
}
