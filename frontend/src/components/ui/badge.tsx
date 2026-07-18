import type { HTMLAttributes } from "react";

import { cn } from "@/lib/utils";

const tones = {
  neutral: "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-100",
  safe: "bg-emerald-100 text-emerald-800 dark:bg-emerald-500/20 dark:text-emerald-200",
  blocked: "bg-rose-100 text-rose-800 dark:bg-rose-500/20 dark:text-rose-200",
  warning: "bg-amber-100 text-amber-900 dark:bg-amber-500/20 dark:text-amber-100",
};

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  tone?: keyof typeof tones;
}

export function Badge({ className, tone = "neutral", ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-3 py-1 text-xs font-medium uppercase tracking-[0.14em]",
        tones[tone],
        className,
      )}
      {...props}
    />
  );
}
