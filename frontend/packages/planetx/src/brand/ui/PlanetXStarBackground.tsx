/**
 * PlanetX StarBackground — pure UI component.
 * Canvas-based starfield with pulsing animation.
 * Optionally adds floating particles for celebration scenes.
 *
 * Note: This component uses DOM elements (not canvas) for stars
 * to keep it dependency-free and easy for Storybook.
 */
import { useEffect, useRef } from "react";
import type { PlanetXStarBackgroundProps } from "./types";

export default function PlanetXStarBackground({
  starCount = 80,
  color = "var(--px-color-accent)",
  withFloatParticles = false,
}: PlanetXStarBackgroundProps) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = ref.current;
    if (!container) return;

    // Clear any previous stars
    container.innerHTML = "";

    const stars: HTMLDivElement[] = [];

    // Pulsing background stars
    for (let i = 0; i < starCount; i++) {
      const s = document.createElement("div");
      const size = Math.random() * 3 + 1;
      s.style.cssText = `
        position:absolute; border-radius:50%;
        width:${size}px; height:${size}px;
        left:${Math.random() * 100}%; top:${Math.random() * 100}%;
        background:${color}; pointer-events:none;
        animation: starPulse ${Math.random() * 3 + 2}s ease-in-out infinite;
        animation-delay: ${Math.random() * 4}s;
      `;
      container.appendChild(s);
      stars.push(s);
    }

    // Floating particles (for celebration)
    if (withFloatParticles) {
      for (let i = 0; i < 20; i++) {
        const p = document.createElement("div");
        const size = Math.random() * 4 + 2;
        p.style.cssText = `
          position:absolute; border-radius:50%;
          width:${size}px; height:${size}px;
          left:${Math.random() * 100}%; bottom:0;
          background:${color}; pointer-events:none;
          opacity:0;
          animation: particleFloat ${Math.random() * 4 + 6}s ease-in-out infinite;
          animation-delay: ${Math.random() * 8}s;
        `;
        container.appendChild(p);
        stars.push(p);
      }
    }

    return () => stars.forEach((s) => s.remove());
  }, [starCount, color, withFloatParticles]);

  return (
    <div
      ref={ref}
      style={{
        position: "fixed",
        inset: 0,
        overflow: "hidden",
        pointerEvents: "none",
        zIndex: "var(--px-z-base)",
      }}
    />
  );
}
