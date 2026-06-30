import { useEffect } from 'react'

const SAAS_URL = import.meta.env.VITE_SAAS_URL || 'http://localhost:5174/'

/**
 * Redirect /narrative to the T-space (SaaS) experience.
 * In dev this jumps to the SaaS Vite dev server (5174);
 * in production set VITE_SAAS_URL to the T-space domain.
 */
export default function NarrativeRedirect() {
  useEffect(() => {
    window.location.href = SAAS_URL
  }, [])

  return null
}
