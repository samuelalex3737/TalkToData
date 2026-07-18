import type { InputHTMLAttributes, TextareaHTMLAttributes } from "react";

import { cn } from "@/lib/utils";

export function Input({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={cn(
        "h-12 w-full rounded-2xl border border-slate-200 bg-white/90 px-4 text-sm text-ink shadow-sm outline-none transition placeholder:text-slate-400 focus:border-signal focus:ring-2 focus:ring-signal/30 dark:border-slate-800 dark:bg-slate-900/90 dark:text-white",
        className,
      )}
      {...props}
    />
  );
}

export function Textarea({ className, ...props }: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea
      className={cn(
        "min-h-32 w-full rounded-[24px] border border-slate-200 bg-white/90 px-4 py-3 text-sm text-ink shadow-sm outline-none transition placeholder:text-slate-400 focus:border-signal focus:ring-2 focus:ring-signal/30 dark:border-slate-800 dark:bg-slate-900/90 dark:text-white",
        className,
      )}
      {...props}
    />
  );
}
