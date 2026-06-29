/**
 * Simple placeholder component for scaffolding.
 * Replace with real components as code is migrated.
 */

interface PlaceholderProps {
  title: string;
  description?: string;
}

export function Placeholder({ title, description }: PlaceholderProps) {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        minHeight: "100vh",
        background: "var(--px-color-bg-deep)",
        color: "var(--px-color-text)",
        fontFamily: "system-ui, sans-serif",
      }}
    >
      <h1
        style={{
          fontSize: "2rem",
          fontWeight: 500,
          color: "var(--px-color-primary)",
          marginBottom: "8px",
        }}
      >
        PlanetX - {title}
      </h1>
      <p style={{ color: "var(--px-color-text-muted)" }}>
        {description || "This is a placeholder. Migrate real component here."}
      </p>
    </div>
  );
}
