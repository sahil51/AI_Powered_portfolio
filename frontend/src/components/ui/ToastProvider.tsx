"use client";

import * as React from "react";
import Toast, { ToastProps } from "@/components/ui/Toast";

type EnqueueOptions = Omit<ToastProps, "id">;

const ToastContext = React.createContext<{
  toast: (opts: EnqueueOptions) => void;
} | null>(null);

export function useToast() {
  const ctx = React.useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within ToastProvider");
  return ctx;
}

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = React.useState<ToastProps[]>([]);

  const toast = React.useCallback((opts: EnqueueOptions) => {
    const id = `t-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
    setToasts((t) => [...t, { id, ...opts }]);
    // auto remove
    window.setTimeout(() => {
      setToasts((t) => t.filter((x) => x.id !== id));
    }, 5000);
  }, []);

  const handleClose = (id: string) => setToasts((t) => t.filter((x) => x.id !== id));

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      <div className="fixed right-4 bottom-4 z-50 flex w-auto max-w-xs flex-col gap-3">
        {toasts.map((t) => (
          <Toast key={t.id} {...t} onClose={() => handleClose(t.id)} />
        ))}
      </div>
    </ToastContext.Provider>
  );
}
