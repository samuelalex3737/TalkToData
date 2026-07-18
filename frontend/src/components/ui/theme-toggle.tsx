import { MoonStar, SunMedium } from "lucide-react";

import { Button } from "./button";

interface ThemeToggleProps {
  dark: boolean;
  onToggle: () => void;
}

export function ThemeToggle({ dark, onToggle }: ThemeToggleProps) {
  return (
    <Button variant="secondary" className="gap-2" onClick={onToggle}>
      {dark ? <SunMedium className="h-4 w-4" /> : <MoonStar className="h-4 w-4" />}
      {dark ? "Light mode" : "Dark mode"}
    </Button>
  );
}
