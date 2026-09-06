"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { liquidGlass } from "@/lib/liquid-glass";
import { cn } from "@/lib/utils";

export function Navbar() {
  const glassRef = useRef<HTMLDivElement>(null);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  useEffect(() => {
    const el = glassRef.current;
    if (!el) return;
    const instance = liquidGlass(el, {
      scale: -60,
      chroma: 3,
      border: 0.05,
      mapBlur: 8,
      blur: 6,
      saturate: 1.2,
      fallbackBlur: 12,
    });
    return () => instance.destroy();
  }, []);

  return (
    <header className="fixed top-0 left-0 right-0 z-50 flex justify-center px-4 pt-4">
      <nav
        ref={glassRef}
        className={cn(
          "liquid-glass rounded-[20px] px-6 py-3 flex items-center gap-8 max-w-5xl w-full",
          "transition-all duration-300",
          scrolled && "shadow-lg"
        )}
      >
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2 shrink-0">
          <span className="font-semibold text-charcoal text-2xl tracking-tight font-stardom">
            NEXUS
          </span>
        </Link>

        {/* Center links — hidden on small screens */}
        <div className="hidden md:flex items-center gap-6 ml-auto">
          <Link
            href="/"
            className="text-sm text-bronze-dark/70 hover:text-charcoal transition-colors"
          >
            Product
          </Link>
          <Link
            href="/#how-it-works"
            className="text-sm text-bronze-dark/70 hover:text-charcoal transition-colors"
          >
            How it works
          </Link>
          <Link
            href="/onboarding"
            className="text-sm text-bronze-dark/70 hover:text-charcoal transition-colors"
          >
            For Students
          </Link>
          <Link
            href="/officer"
            className="text-sm text-bronze-dark/70 hover:text-charcoal transition-colors"
          >
            For Placement Cells
          </Link>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-3 ml-auto md:ml-0">
          <Link
            href="/onboarding"
            className="inline-flex items-center px-5 py-2 text-sm font-semibold text-white bg-orange hover:bg-orange-deep rounded-[10px] transition-all press-down shadow-sm"
          >
            Start Assessment
          </Link>
        </div>
      </nav>
    </header>
  );
}
