"use client";

import React from "react";

export function PlacementScorecard() {
  return (
    <div className="surface-card rounded-[24px] p-8 shadow-lg relative max-w-lg mx-auto w-full animate-slide-up bg-white/80 backdrop-blur-md border border-border-subtle">
      {/* Small floating label */}
      <div className="type-micro text-bronze-dark/50 mb-4">PLACEMENT READINESS</div>

      {/* Score display */}
      <div className="flex items-start gap-8">
        <div className="flex flex-col items-center">
          <div className="relative w-[140px] h-[140px]">
            <svg viewBox="0 0 140 140" className="transform -rotate-90 w-full h-full">
              <circle cx="70" cy="70" r="60" fill="none" stroke="rgba(192,133,82,0.1)" strokeWidth="8" />
              <circle
                cx="70" cy="70" r="60" fill="none"
                stroke="#2D8A4E" strokeWidth="8" strokeLinecap="round"
                strokeDasharray={2 * Math.PI * 60}
                strokeDashoffset={2 * Math.PI * 60 * (1 - 0.84)}
                className="transition-all duration-1000"
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-4xl font-bold text-charcoal font-[var(--font-mono)]">84</span>
              <span className="text-xs text-bronze-dark/50 font-medium">/100</span>
            </div>
          </div>
          <span className="text-xs font-semibold text-success mt-2 px-2.5 py-0.5 bg-success-light rounded-full">
            Strong Match
          </span>
        </div>

        {/* Bars */}
        <div className="flex-1 space-y-4 pt-2">
          {[
            { label: "Skills", pct: 92, color: "#2D8A4E" },
            { label: "Coding", pct: 78, color: "#C4820B" },
            { label: "Projects", pct: 88, color: "#2D8A4E" },
            { label: "Academics", pct: 81, color: "#2D8A4E" },
          ].map((bar) => (
            <div key={bar.label}>
              <div className="flex justify-between text-xs mb-1.5">
                <span className="font-medium text-charcoal">{bar.label}</span>
                <span className="font-semibold" style={{ color: bar.color }}>
                  {bar.pct}%
                </span>
              </div>
              <div className="h-1.5 bg-surface-muted rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-1000"
                  style={{ width: `${bar.pct}%`, backgroundColor: bar.color }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Floating chips */}
      <div className="flex flex-wrap gap-3 mt-6 pt-6 border-t border-border-subtle">
        {[
          { label: "+12 relevant companies", color: "text-bronze-dark" },
          { label: "3 skill gaps", color: "text-warning" },
          { label: "6 week roadmap", color: "text-orange" },
        ].map((chip) => (
          <span
            key={chip.label}
            className={`text-xs font-medium ${chip.color} bg-surface-muted px-3 py-1.5 rounded-full border border-border-subtle`}
          >
            {chip.label}
          </span>
        ))}
      </div>
    </div>
  );
}
