import { cn } from "@/lib/utils";

type BadgeVariant = "default" | "critical" | "high" | "medium" | "low" | "success" | "neutral";

interface PBBadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  className?: string;
}

const variantStyles: Record<BadgeVariant, string> = {
  default:  "bg-surface-muted text-bronze-dark border-border-default",
  critical: "bg-danger-light text-danger border-danger/20",
  high:     "bg-warning-light text-warning border-warning/20",
  medium:   "bg-ivory-warm text-bronze-dark border-bronze/15",
  low:      "bg-surface-muted text-bronze-dark/60 border-border-subtle",
  success:  "bg-success-light text-success border-success/20",
  neutral:  "bg-surface text-charcoal-light border-border-default",
};

export function PBBadge({ children, variant = "default", className }: PBBadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center px-2.5 py-0.5 text-xs font-semibold rounded-full border whitespace-nowrap",
        variantStyles[variant],
        className
      )}
    >
      {children}
    </span>
  );
}
