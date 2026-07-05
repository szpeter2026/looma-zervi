/**
 * Token utilities for non-CSS contexts (Canvas API, JS string colors).
 *
 * CSS custom properties (var(--px-...)) cannot be used directly in Canvas 2D
 * API calls like ctx.fillStyle. This helper reads computed CSS variable values
 * at runtime with a cached fallback.
 */

const cache = new Map<string, string>()

/**
 * Read a CSS custom property from :root, with fallback.
 * Results are cached per variable name for the session.
 */
export function getToken(name: string, fallback: string): string {
  if (cache.has(name)) return cache.get(name)!
  if (typeof window === 'undefined') return fallback
  const val = getComputedStyle(document.documentElement)
    .getPropertyValue(name)
    .trim()
  const result = val || fallback
  cache.set(name, result)
  return result
}

/** Clear the token cache (useful if theme changes at runtime). */
export function clearTokenCache(): void {
  cache.clear()
}

/** Pre-built token accessor for Canvas / JS contexts. */
export const px = {
  get bgCard()         { return getToken('--px-color-bg-card', '#0D0D1A') },
  get bgPage()         { return getToken('--px-color-bg-page', '#080810') },
  get bgSurface()      { return getToken('--px-color-bg-surface', '#1A1A2E') },
  get bgPurple()       { return getToken('--px-color-bg-purple', '#1A0A2E') },
  get bgGreen()        { return getToken('--px-color-bg-green', '#0A1A0A') },
  get accent()         { return getToken('--px-color-accent', '#C8FF50') },
  get textMuted()      { return getToken('--px-color-text-muted', '#B8B8C8') },
  get textBright()     { return getToken('--px-color-text-bright', '#E8E8F0') },
  get textOnPrimary()  { return getToken('--px-color-text-on-primary', '#ffffff') },
  get primary()        { return getToken('--px-color-primary', '#6C63FF') },
  get primaryBright()  { return getToken('--px-color-primary-bright', '#7c6ff7') },
  get primarySoft()    { return getToken('--px-color-primary-soft', '#C4B5FD') },
  get purpleDeep()     { return getToken('--px-color-purple-deep', '#6B3FA0') },
  get violet()         { return getToken('--px-color-violet', '#8B5CF6') },
  get pink()           { return getToken('--px-color-pink', '#FF2D95') },
  get cyan()           { return getToken('--px-color-cyan', '#00E5FF') },
  get gold()           { return getToken('--px-color-gold', '#FFD700') },
  get danger()         { return getToken('--px-color-danger', '#FF4757') },
  get success()        { return getToken('--px-color-success', '#00D9A3') },
  get successBright()  { return getToken('--px-color-success-bright', '#55efc4') },
  get coral()          { return getToken('--px-color-coral', '#ff7675') },
  get orange()         { return getToken('--px-color-orange', '#e17055') },
  get yellow()         { return getToken('--px-color-yellow', '#f9ca24') },
  get amber()          { return getToken('--px-color-amber', '#fdcb6e') },
  get lavender()       { return getToken('--px-color-lavender', '#a29bfe') },
  get teal()           { return getToken('--px-color-teal', '#4ecdc4') },
  get textTertiary()   { return getToken('--px-color-text-tertiary', '#6a6a7a') },
  get textSoft()       { return getToken('--px-color-text-soft', '#c8c8d4') },
  get textPurpleTint() { return getToken('--px-color-text-purple-tint', '#e0dfff') },
  get bgDeeper()       { return getToken('--px-color-bg-deeper', '#12121a') },
  get bgSurfaceAlt()   { return getToken('--px-color-bg-surface-alt', '#1a1a28') },
  get bgSurfaceDim()   { return getToken('--px-color-bg-surface-dim', '#161620') },
  get bgHoverSolid()   { return getToken('--px-color-bg-hover-solid', '#252540') },
  get borderSolid()    { return getToken('--px-color-border-solid', '#1e1e2e') },
  get neutralDark()    { return getToken('--px-color-neutral-dark', '#333') },
  get textDim()        { return getToken('--px-color-text-dim', '#555577') },
}
