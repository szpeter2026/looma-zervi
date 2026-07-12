# GenZ Web — genz.ltd (Stripe review site)

**Branch:** `release/overseas`  
**Brand:** GenZ · **Product:** PlanetX · **Tagline:** AI Career Growth Partner

Marketing static site for Stripe merchant review and USD subscription positioning.
Pricing aligns with `backend/contracts/payment.v1.json` (region=US).

See: `docs/OVERSEAS_DEPLOY.md`

## Pages

| URL | File |
|-----|------|
| `/` | `index.html` |
| `/pricing` | `pricing.html` |
| `/legal/privacy` | `legal/privacy.html` |
| `/legal/terms` | `legal/terms.html` |
| `/legal/refund` | `legal/refund.html` |

## Stripe blockers (before submission)

1. **`assets/config.js` → `legalEntityName`** — Hong Kong company English name (CR + Stripe must match)
2. **Deploy to VPS** — `bash scripts/deploy-genz-web.sh` (or full `deploy-overseas.sh`)
3. **Paid tier CTAs** — show **Join waitlist** until Stripe Checkout is wired (not "Subscribe")

## Hong Kong legal entity (one file)

```js
// assets/config.js
legalEntityName: "Your Company Limited",
```

Updates footer + Terms automatically.

## Local preview

```bash
cd frontend/packages/genz-web
pnpm dev
# http://localhost:5180
```

## Production deploy

On overseas VPS after `git pull`:

```bash
bash scripts/deploy-genz-web.sh
```

Nginx serves `/var/www/genz-web` at `genz.ltd` and `www.genz.ltd`. `vercel.json` includes clean URL rewrites for `/pricing` and `/legal/*` if deploying to Vercel.

## Hong Kong legal entity (one file)

```js
// assets/config.js
legalEntityName: "YEDALL LIMITED",
```

## Pricing note (non-blocking)

Supporter at $1.99/mo has high Stripe fee ratio (~18%). Consider raising to $4.99+ or
Free → Pro only in a future `payment.v1.json` revision.
