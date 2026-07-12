# GenZ Web — genz.ltd (Stripe review site)

Overseas marketing site for **PlanetX — Genzer AI Career Growth Partner**.

**Git branch:** `release/overseas` (Gitee `origin/release/overseas` — not a local-only branch).

Used for Stripe merchant review and USD subscription positioning. Pricing aligns with
`backend/contracts/payment.v1.json` (region=US).

See also: `docs/OVERSEAS_DEPLOY.md` (Vultr + Cloudflare + Stripe webhook on this branch).

## Domain note

| URL | Role on `release/overseas` |
|-----|----------------------------|
| `https://genz.ltd` | PlanetX SPA + API fallback (nginx) — see `OVERSEAS_DEPLOY.md` |
| `https://www.genz.ltd` | Optional: deploy **this** static `genz-web` package for Stripe review / legal pages |
| `https://api.genz.ltd` | Looma API + Stripe webhook |

If both apex and `www` are used, add a Cloudflare redirect `www` → `genz.ltd` or vice versa before Stripe submission so the Business URL matches the live site.

## Pages

| Path | File |
|------|------|
| `/` | `index.html` |
| `/pricing` | `pricing.html` |
| `/legal/privacy` | `legal/privacy.html` |
| `/legal/terms` | `legal/terms.html` |
| `/legal/refund` | `legal/refund.html` |

## Local preview

```bash
cd frontend/packages/genz-web
pnpm dev
# open http://localhost:5180
```

## Deploy (Vercel)

1. Import this repo (or subdirectory) in Vercel.
2. Set **Root Directory** to `frontend/packages/genz-web`.
3. Point `www.genz.ltd` to the Vercel project.
4. Ensure HTTPS is enabled.

`vercel.json` includes clean URL rewrites for `/pricing` and `/legal/*`.

## Hong Kong legal entity name

When the English company name is confirmed, update **one file only**:

```js
// assets/config.js
legalEntityName: "Your Hong Kong Company Limited",
```

This value is injected into the site footer and Terms of Service automatically.

## Stripe checklist

- Business URL: `https://www.genz.ltd`
- Product: AI career growth SaaS (digital subscription)
- USD plans: Free / Supporter $1.99 / Pro $5.99 (live from API or fallback)
- Support email: `support@genz.ltd`
- Policies: Privacy, Terms, Refund & Cancellation (all linked in footer)

## API

Pricing page fetches:

```text
GET https://api.genz.ltd/v1/payment/plans?region=US
```

Add `https://www.genz.ltd` to backend `CORS_ORIGINS` if the browser fetch is blocked in production.
