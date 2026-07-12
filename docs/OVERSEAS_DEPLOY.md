# Overseas Deployment Guide (release/overseas)

> Domain: `genz.ltd`
> Infrastructure: Vultr VPS (Singapore) + Cloudflare CDN + Let's Encrypt

## DNS Records (Cloudflare)

| Type | Name | Content | Proxy |
|------|------|---------|-------|
| A | `@` | `VPS_IP` | ON |
| A | `api` | `VPS_IP` | ON |
| A | `tspace` | `VPS_IP` | ON |

Cloudflare SSL/TLS mode: **Full (Strict)**

## Subdomain Routing

| Subdomain | Purpose | Backend |
|-----------|---------|---------|
| `genz.ltd` | PlanetX B2C SPA + API fallback | `docker/nginx.conf` → `planetx/dist`, `/v1/*` → backend |
| `api.genz.ltd` | API only | `/v1/*` → backend |
| `tspace.genz.ltd` | T-space B2B SaaS SPA | `saas/dist` |

## Third-party Callback URLs

Configure these in the respective dashboards once the VPS is live:

| Service | Setting | URL |
|---------|---------|-----|
| Google OAuth | Authorized JS origins | `https://genz.ltd` |
| Google OAuth | Redirect URI | `https://api.genz.ltd/v1/auth/google/callback` |
| Stripe | Webhook endpoint | `https://api.genz.ltd/v1/payment/stripe/webhook` |
| Stripe | Success URL | `https://genz.ltd/pricing?status=success` |
| Stripe | Cancel URL | `https://genz.ltd/pricing?status=cancel` |

## One-click Deploy

Run as root on the fresh Ubuntu 22.04 VPS:

```bash
curl -fsSL https://raw.githubusercontent.com/szpeter2026/looma-zervi/release/overseas/scripts/deploy-overseas.sh | bash
```

Or manually:

```bash
git clone -b release/overseas https://gitee.com/szbenyx/looma-zervi.git /opt/looma-zervi
cd /opt/looma-zervi
cp backend/.env.example backend/.env
# Edit backend/.env with real secrets
# Then run: cd docker && docker compose up -d --build
```

## Post-deploy Checklist

- [ ] Update `backend/.env` with real `OPENAI_API_KEY`, `GOOGLE_CLIENT_*`, `STRIPE_*`
- [ ] Restart containers: `cd /opt/looma-zervi/docker && docker compose restart`
- [ ] Verify `https://genz.ltd/health` returns HTTP 200
- [ ] Verify `https://api.genz.ltd/health` returns HTTP 200
- [ ] Verify Google OAuth sign-in works end-to-end
- [ ] Verify Stripe checkout creates a checkout session
- [ ] Add Stripe webhook endpoint and grab the webhook signing secret
- [ ] (Optional) Turn on Cloudflare "Always Use HTTPS" + "Auto Minify"
