"use client";

import * as React from "react";

interface SkeletonProps {
  className?: string;
}

export default function Skeleton({ className = "h-4 w-full rounded-md" }: SkeletonProps) {
  return <div className={`bg-slate-800/60 animate-[var(--animate-pulse-slow)] ${className}`} />;
}
