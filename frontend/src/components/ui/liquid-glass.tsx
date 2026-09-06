"use client";

import { useRef, useEffect, type ReactNode } from "react";
import { liquidGlass, type LiquidGlassOptions } from "@/lib/liquid-glass";
import { cn } from "@/lib/utils";

interface LiquidGlassProps {
  children: ReactNode;
  className?: string;
  /** Options passed directly to the liquidGlass engine */
  opts?: LiquidGlassOptions;
}

/**
 * React wrapper around the liquid-glass refraction engine.
 *
 * Applies real SVG displacement refraction on Chromium;
 * falls back to frosted blur on Safari/Firefox.
 *
 * Use the `liquid-glass` CSS class on this component for the
 * warm-tinted material dressing (tint, inner highlight, shadow).
 */
export function LiquidGlass({
  children,
  className,
  opts,
}: LiquidGlassProps) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const instance = liquidGlass(el, {
      scale: -80,
      chroma: 4,
      border: 0.06,
      mapBlur: 10,
      blur: 4,
      saturate: 1.3,
      fallbackBlur: 14,
      ...opts,
    });

    return () => {
      instance.destroy();
    };
  }, [opts]);

  return (
    <div ref={ref} className={cn("liquid-glass", className)}>
      {children}
    </div>
  );
}
