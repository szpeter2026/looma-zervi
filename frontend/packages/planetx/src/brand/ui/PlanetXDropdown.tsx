/**
 * PlanetX Dropdown — pure UI component.
 * Features: trigger element, menu positioning, keyboard navigation.
 *
 * No store, no API — all data via props.
 */
import { useState, useEffect, useRef } from "react";
import type { PlanetXDropdownProps } from "./types";

export default function PlanetXDropdown({
  trigger,
  items,
  align = "left",
  width = "200px",
  onSelect,
  disabled = false,
}: PlanetXDropdownProps) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setIsOpen(false);
    };

    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
      document.addEventListener("keydown", handleEscape);
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("keydown", handleEscape);
    };
  }, [isOpen]);

  const handleItemClick = (item: { value: string; label: string; icon?: React.ReactNode }) => {
    onSelect?.(item.value);
    setIsOpen(false);
  };

  const alignStyles: Record<string, React.CSSProperties> = {
    left: { left: 0 },
    right: { right: 0 },
    center: { left: "50%", transform: "translateX(-50%)" },
  };

  return (
    <div
      ref={dropdownRef}
      style={{
        position: "relative",
        display: "inline-block",
      }}
    >
      {/* Trigger */}
      <div
        onClick={() => !disabled && setIsOpen(!isOpen)}
        style={{
          cursor: disabled ? "not-allowed" : "pointer",
          opacity: disabled ? 0.5 : 1,
        }}
      >
        {trigger}
      </div>

      {/* Dropdown menu */}
      {isOpen && (
        <div
          style={{
            position: "absolute",
            top: "100%",
            marginTop: "var(--px-spacing-xs)",
            background: "var(--px-color-bg-card)",
            borderRadius: "var(--px-radius-md)",
            border: "1px solid var(--px-border-default)",
            boxShadow: "var(--px-shadow-card)",
            minWidth: width,
            zIndex: "var(--px-z-dropdown)",
            animation: "fadeIn 150ms ease-out",
            ...alignStyles[align],
          }}
        >
          {items.map((item, index) => (
            <div
              key={item.value}
              onClick={() => handleItemClick(item)}
              style={{
                padding: "var(--px-spacing-sm) var(--px-spacing-md)",
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: "var(--px-spacing-sm)",
                transition: "var(--px-anim-fast)",
                borderBottom: index < items.length - 1 ? "1px solid var(--px-border-subtle)" : "none",
                color: item.disabled ? "var(--px-color-text-dim)" : "var(--px-color-text)",
              }}
              onMouseEnter={(e) => {
                if (!item.disabled) {
                  e.currentTarget.style.background = "var(--px-color-bg-hover)";
                }
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = "transparent";
              }}
            >
              {item.icon && (
                <span style={{ fontSize: "1.1em", display: "flex", alignItems: "center" }}>
                  {item.icon}
                </span>
              )}
              <span
                style={{
                  flex: 1,
                  fontSize: "var(--px-font-size-sm)",
                  fontWeight: item.disabled ? "normal" : "var(--px-font-weight-medium)",
                }}
              >
                {item.label}
              </span>
              {item.rightIcon && (
                <span style={{ fontSize: "0.9em", opacity: 0.7 }}>{item.rightIcon}</span>
              )}
            </div>
          ))}
        </div>
      )}

      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(-4px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
}
