"use client";

import React from "react";

interface AnimatedPersonProps {
  className?: string;
}

export function AnimatedPerson({ className = "" }: AnimatedPersonProps) {
  return (
    <div className={`relative h-full min-h-0 flex items-start justify-center overflow-hidden ${className}`}>
      <div
        style={{
          width: "min(600px, 100%)",
          height: "100%",
          position: "relative",
          maskImage: "linear-gradient(to bottom, black 0%, black 60%, transparent 100%)",
          WebkitMaskImage: "linear-gradient(to bottom, black 0%, black 60%, transparent 100%)",
        }}
      >
        <video
          autoPlay
          loop
          muted
          playsInline
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
            objectPosition: "center top",
            display: "block",
            mixBlendMode: "multiply",
          }}
        >
          <source src="/ajja.mp4" type="video/mp4" />
        </video>
      </div>
    </div>
  );
}
