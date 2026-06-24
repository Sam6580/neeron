export const APP_NAME = "NEERON";
export const APP_TAGLINE = "AI Engine Alpha — Active";

export const NAV_ITEMS = [
  { label: "Command Center", href: "/", icon: "dashboard" },
  { label: "Tank Management", href: "/tanks", icon: "tanks" },
  { label: "Analytics", href: "/analytics", icon: "analytics" },
  { label: "Biosecurity", href: "/biosecurity", icon: "biosecurity" },
  { label: "Health", href: "/health", icon: "health" },
] as const;

export const SECONDARY_NAV_ITEMS = [
  { label: "Settings", href: "/settings", icon: "settings" },
] as const;

export const FOOTER_NAV_ITEMS = [
  { label: "Documentation", href: "/docs", icon: "docs" },
  { label: "Support", href: "/support", icon: "support" },
] as const;

export const HEALTH_SCORE_THRESHOLDS = {
  good: 80,
  warning: 60,
} as const;

export const SPECIES = "Atlantic Salmon" as const;
