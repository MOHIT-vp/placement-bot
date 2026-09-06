"use client";

import { useEffect, useRef, useState } from "react";
import { cn } from "@/lib/utils";

interface ScoreGaugeProps {
  score: number;
  maxScore?: number;
  size?: number;
  strokeWidth?: number;
  label?: string;
  className?: string;
}

export function ScoreGauge({
  score,
  maxScore = 100,
  size = 180,
  strokeWidth = 10,
  label,
  className,
}: ScoreGaugeProps) {
  const [animated, setAnimated] = useState(false);
  const [displayScore, setDisplayScore] = useState(0);
  const ref = useRef<SVGSVGElement>(null);

  const r = (size - strokeWidth) / 2;
  const circ = 2 * Math.PI * r;
  const pct = Math.min(score / maxScore, 1);
  const offset = circ - pct * circ;

  // Determine color based on score
  const scoreColor =
    score >= 75 ? "#2D8A4E" : score >= 55 ? "#C4820B" : "#C53030";
  const scoreColorLight =
    score >= 75
      ? "rgba(45,138,78,0.12)"
      : score >= 55
      ? "rgba(196,130,11,0.12)"
      : "rgba(197,48,48,0.12)";

  const qualityLabel =
    score >= 80
      ? "Strong trajectory"
      : score >= 65
      ? "Competitive profile"
      : score >= 50
      ? "Building momentum"
      : "Getting started";

  useEffect(() => {
    const timer = setTimeout(() => setAnimated(true), 100);
    return () => clearTimeout(timer);
  }, []);

  // Animate the number counting up
  useEffect(() => {
    if (!animated) return;
    const duration = 800;
    const start = performance.now();
    const target = Math.round(score);

    function tick(now: number) {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      // Ease out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplayScore(Math.round(eased * target));
      if (progress < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  }, [animated, score]);

  return (
    <div className={cn("flex flex-col items-center gap-3", className)}>
      <div className="relative" style={{ width: size, height: size }}>
        <svg
          ref={ref}
          viewBox={`0 0 ${size} ${size}`}
          className="transform -rotate-90"
          style={{ width: size, height: size }}
        >
          {/* Track */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={r}
            fill="none"
            stroke="rgba(192,133,82,0.1)"
            strokeWidth={strokeWidth}
          />
          {/* Fill */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={r}
            fill="none"
            stroke={scoreColor}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={circ}
            strokeDashoffset={animated ? offset : circ}
            style={{
              transition: "stroke-dashoffset 1s cubic-bezier(0.16, 1, 0.3, 1)",
            }}
          />
        </svg>
        {/* Center content */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="type-data-lg" style={{ color: scoreColor }}>
            {displayScore}
          </span>
          <span className="type-micro mt-0.5" style={{ color: scoreColor, opacity: 0.7 }}>
            /{maxScore}
          </span>
        </div>
      </div>
      {/* Quality label below gauge */}
      <div
        className="px-3 py-1 rounded-full text-xs font-semibold"
        style={{ backgroundColor: scoreColorLight, color: scoreColor }}
      >
        {label || qualityLabel}
      </div>
    </div>
  );
}
