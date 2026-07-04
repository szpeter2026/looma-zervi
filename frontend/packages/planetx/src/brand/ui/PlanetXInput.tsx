/**
 * PlanetX Input — pure UI component.
 * States: default / focus / error / disabled
 * Sizes: sm / md
 */
import { useState } from "react";
import type { PlanetXInputProps } from "./types";

export default function PlanetXInput({
  value,
  onChange,
  placeholder = "",
  disabled = false,
  error = false,
  size = "md",
  label,
  helperText,
  type = "text",
  maxLength,
}: PlanetXInputProps) {
  const [focused, setFocused] = useState(false);

  const heights: Record<string, string> = {
    sm: "var(--px-input-height-sm)",
    md: "var(--px-input-height-md)",
  };

  const inputStyle: React.CSSProperties = {
    width: "100%",
    height: heights[size],
    padding: "var(--px-input-padding)",
    background: disabled ? "var(--px-color-bg-deep)" : focused ? "var(--px-input-bg-focus)" : "var(--px-input-bg)",
    border: error
      ? "var(--px-input-border-error)"
      : focused
      ? "var(--px-input-border-focus)"
      : "var(--px-input-border)",
    borderRadius: "var(--px-input-radius)",
    color: disabled ? "var(--px-color-text-dim)" : "var(--px-color-text)",
    fontSize: "var(--px-input-font-size)",
    fontFamily: "var(--px-font-family)",
    outline: "none",
    transition: "var(--px-anim-fast)",
    boxSizing: "border-box",
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "var(--px-spacing-xs)" }}>
      {label && (
        <label style={{
          color: "var(--px-label-color)",
          fontSize: "var(--px-label-font-size)",
          letterSpacing: "var(--px-letter-spacing-wide)",
          fontWeight: "var(--px-font-weight-medium)",
        }}>
          {label}
        </label>
      )}
      <input
        type={type}
        value={value}
        onChange={(e) => onChange?.(e.target.value)}
        placeholder={placeholder}
        disabled={disabled}
        maxLength={maxLength}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        style={inputStyle}
      />
      {helperText && (
        <span style={{
          fontSize: "var(--px-label-font-size)",
          color: error ? "var(--px-helper-error)" : "var(--px-helper-color)",
        }}>
          {helperText}
        </span>
      )}
    </div>
  );
}
