/**
 * PlanetX TextArea — pure UI component.
 */
import { useState } from "react";
import type { PlanetXTextAreaProps } from "./types";

export default function PlanetXTextArea({
  value,
  onChange,
  placeholder = "",
  disabled = false,
  error = false,
  label,
  helperText,
  rows = 4,
  maxLength,
}: PlanetXTextAreaProps) {
  const [focused, setFocused] = useState(false);

  const style: React.CSSProperties = {
    width: "100%",
    padding: "10px 12px",
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
    resize: "vertical",
    boxSizing: "border-box",
    lineHeight: "var(--px-line-height-normal)",
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
      <textarea
        value={value}
        onChange={(e) => onChange?.(e.target.value)}
        placeholder={placeholder}
        disabled={disabled}
        rows={rows}
        maxLength={maxLength}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        style={style}
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
