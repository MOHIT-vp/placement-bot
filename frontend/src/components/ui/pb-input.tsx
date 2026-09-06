"use client";

import { cn } from "@/lib/utils";
import { forwardRef, type InputHTMLAttributes, type ReactNode } from "react";

interface PBInputProps extends InputHTMLAttributes<HTMLInputElement> {
  icon?: ReactNode;
  rightIcon?: ReactNode;
  error?: string;
  label?: string;
  hint?: string;
}

const PBInput = forwardRef<HTMLInputElement, PBInputProps>(
  ({ className, icon, rightIcon, error, label, hint, id, placeholder, value, ...props }, ref) => {
    const inputId = id || props.name;
    
    // We force placeholder to be at least a space so the :placeholder-shown pseudo-class works
    const finalPlaceholder = placeholder || " ";

    return (
      <div className="space-y-1.5 w-full">
        <div className="relative flex rounded-[12px] w-full">
          {icon && (
            <div className="absolute left-3.5 top-1/2 -translate-y-1/2 text-charcoal pointer-events-none z-10">
              {icon}
            </div>
          )}
          
          <input
            ref={ref}
            id={inputId}
            value={value}
            placeholder={finalPlaceholder}
            className={cn(
              "peer w-full bg-surface border border-border-default rounded-[12px] py-3 text-[0.9375rem]",
              "text-charcoal focus:outline-none focus:border-bronze focus:ring-2 focus:ring-bronze/15",
              "transition-all duration-200",
              // Hide placeholder when not focused so it doesn't overlap with the floating label
              "placeholder-transparent focus:placeholder-bronze-dark/35", 
              icon ? "pl-11" : "px-4",
              rightIcon ? "pr-11" : "pr-4",
              error && "border-danger focus:border-danger focus:ring-danger/15",
              className
            )}
            {...props}
          />
          
          {label && (
            <label
              htmlFor={inputId}
              className={cn(
                "absolute top-1/2 translate-y-[-50%] bg-surface px-1 font-medium text-bronze-dark/80 pointer-events-none duration-150 transition-all",
                "block whitespace-nowrap overflow-hidden text-ellipsis max-w-[calc(100%-1rem)]",
                // Focused state: float up
                "peer-focus:top-0 peer-focus:left-3 peer-focus:text-xs peer-focus:text-bronze",
                // Not empty (placeholder is not shown): float up
                "peer-[:not(:placeholder-shown)]:top-0 peer-[:not(:placeholder-shown)]:left-3 peer-[:not(:placeholder-shown)]:text-xs",
                // Adjust initial left padding based on icon presence
                icon ? "left-10" : "left-3"
              )}
            >
              {label}
              {hint && (
                <span className="font-normal text-bronze-dark/60 ml-1.5">
                  {hint}
                </span>
              )}
            </label>
          )}

          {rightIcon && (
            <div className="absolute right-3.5 top-1/2 -translate-y-1/2 z-10">
              {rightIcon}
            </div>
          )}
        </div>
        {error && (
          <p className="text-sm text-danger font-medium flex items-center gap-1.5">
            {error}
          </p>
        )}
      </div>
    );
  }
);
PBInput.displayName = "PBInput";

export { PBInput };
