/**
 * PlanetX Tabs — pure UI component.
 * Features: horizontal/vertical tabs, animated underline, icon support.
 *
 * No store, no API — all data via props.
 */
import type { PlanetXTabsProps, PlanetXTabItem } from "./types";

export default function PlanetXTabs({
  items,
  activeTab,
  onChange,
  variant = "default",
  orientation = "horizontal",
  fullWidth = false,
}: PlanetXTabsProps) {
  const activeIndex = items.findIndex((item) => item.value === activeTab);

  const containerStyle: React.CSSProperties = {
    display: "flex",
    flexDirection: orientation === "vertical" ? "column" : "row",
    gap: orientation === "vertical" ? "var(--px-spacing-xs)" : "var(--px-spacing-sm)",
    width: fullWidth ? "100%" : "auto",
  };

  const tabStyle = (item: PlanetXTabItem): React.CSSProperties => {
    const isActive = activeTab === item.value;
    const base: React.CSSProperties = {
      position: "relative",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      gap: "var(--px-spacing-xs)",
      padding: orientation === "vertical" 
        ? "var(--px-spacing-sm) var(--px-spacing-md)" 
        : "var(--px-spacing-sm) var(--px-spacing-lg)",
      background: "transparent",
      border: "none",
      color: isActive ? "var(--px-color-text-bright)" : "var(--px-color-text-muted)",
      cursor: "pointer",
      fontSize: "var(--px-font-size-sm)",
      fontWeight: isActive ? "var(--px-font-weight-bold)" : "var(--px-font-weight-medium)",
      transition: "var(--px-anim-normal)",
      borderRadius: variant === "pills" ? "var(--px-radius-full)" : "var(--px-radius-md)",
      ...(fullWidth && orientation === "horizontal" ? { flex: 1 } : {}),
      ...(fullWidth && orientation === "vertical" ? { width: "100%" } : {}),
    };

    if (variant === "pills" && isActive) {
      return {
        ...base,
        background: "var(--px-color-primary)",
        color: "var(--px-color-text-on-primary)",
        boxShadow: "var(--px-shadow-glow)",
      };
    }

    return base;
  };

  const hoverStyle = (): React.CSSProperties => {
    if (variant === "pills") {
      return {
        background: "var(--px-color-primary-light)",
        color: "var(--px-color-primary)",
      };
    }
    return {
      color: "var(--px-color-text)",
    };
  };

  return (
    <div style={containerStyle}>
      {items.map((item) => (
        <button
          key={item.value}
          onClick={() => onChange?.(item.value)}
          style={tabStyle(item)}
          onMouseEnter={(e) => {
            if (activeTab !== item.value) {
              Object.assign(e.currentTarget.style, hoverStyle());
            }
          }}
          onMouseLeave={(e) => {
            if (activeTab !== item.value) {
              e.currentTarget.style.background = "transparent";
              e.currentTarget.style.color = "var(--px-color-text-muted)";
            }
          }}
        >
          {item.icon && (
            <span style={{ fontSize: "1.1em", display: "flex", alignItems: "center" }}>
              {item.icon}
            </span>
          )}
          {item.label}
          {item.badge && (
            <span
              style={{
                background: "var(--px-color-primary-light)",
                color: "var(--px-color-primary)",
                fontSize: "0.7rem",
                fontWeight: "bold",
                padding: "1px 6px",
                borderRadius: "var(--px-radius-full)",
                marginLeft: "var(--px-spacing-xs)",
              }}
            >
              {item.badge}
            </span>
          )}
        </button>
      ))}
      
      {/* Animated underline (for default variant only) */}
      {variant === "default" && orientation === "horizontal" && activeIndex >= 0 && (
        <div
          style={{
            position: "absolute",
            bottom: 0,
            left: 0,
            height: 2,
            background: "var(--px-color-primary)",
            transition: "var(--px-anim-slow) cubic-bezier(0.34, 1.56, 0.64, 1)",
            transform: `translateX(${activeIndex * 100}%)`,
            width: `calc(100% / ${items.length})`,
          }}
        />
      )}
    </div>
  );
}
