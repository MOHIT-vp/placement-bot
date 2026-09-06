"use client";

import { cn } from "@/lib/utils";
import { type ButtonHTMLAttributes, forwardRef } from "react";

interface PBButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost" | "outline" | "danger";
  size?: "sm" | "md" | "lg";
}

const PBButton = forwardRef<HTMLButtonElement, PBButtonProps>(
  ({ className, variant = "primary", size = "md", children, ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(
          "inline-flex items-center justify-center font-medium transition-base press-down select-none whitespace-nowrap",
          "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-bronze",
          "disabled:opacity-40 disabled:pointer-events-none",
          {
            // Variants
            "bg-orange text-white hover:bg-orange-deep shadow-sm":
              variant === "primary",
            "bg-surface border border-border-default text-charcoal hover:bg-surface-muted":
              variant === "secondary",
            "bg-transparent text-charcoal hover:bg-surface-muted":
              variant === "ghost",
            "border border-border-strong text-charcoal hover:bg-surface-warm":
              variant === "outline",
            "bg-danger-light text-danger hover:bg-danger/10":
              variant === "danger",
            // Sizes
            "text-sm px-4 py-2 rounded-[10px] gap-2": size === "sm",
            "text-[0.9375rem] px-6 py-3 rounded-[12px] gap-2.5": size === "md",
            "text-base px-8 py-4 rounded-[14px] gap-3": size === "lg",
          },
          className
        )}
        {...props}
      >
        {children}
      </button>
    );
  }
);
PBButton.displayName = "PBButton";

export { PBButton };
