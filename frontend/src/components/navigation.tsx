import { DatabaseZap, History, ShieldCheck, Sparkles } from "lucide-react";
import { NavLink } from "react-router-dom";

import { cn } from "@/lib/utils";

const items = [
  { to: "/", label: "Ask", icon: DatabaseZap },
  { to: "/history", label: "History", icon: History },
  { to: "/guardrails", label: "Guardrails", icon: ShieldCheck },
  { to: "/about", label: "About", icon: Sparkles },
];

export function Navigation() {
  return (
    <nav className="flex flex-wrap items-center gap-2">
      {items.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          className={({ isActive }) =>
            cn(
              "inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium transition",
              isActive
                ? "bg-ink text-white"
                : "bg-white/75 text-slate-700 hover:bg-white dark:bg-slate-900/75 dark:text-slate-200",
            )
          }
        >
          <item.icon className="h-4 w-4" />
          {item.label}
        </NavLink>
      ))}
    </nav>
  );
}
