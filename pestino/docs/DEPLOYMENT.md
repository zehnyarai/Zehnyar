# Pestino — Backend deployment

## Requirements

- Node.js 20.11 or newer, npm.
- PostgreSQL 13 or newer (no extensions needed), with a dedicated database and user.
- A reverse proxy or load balancer that terminates TLS (Nginx, Caddy, or a cloud LB). Set `TRUST_PROXY` to the number of proxy hops.
- Persistent disk for uploads (`UPLOAD_DIR`) or, preferably, object storage (see `DATABASE.md`, known gaps).
- A Gemini API key with billing and a data-usage policy that fits the privacy policy.

## Environment

Validated at start-up by `src/config/env.ts`. The process refuses to start on invalid values.

| Variable | Required | Notes |
|---|---|---|
| `NODE_ENV` | yes | `production` in production |
| `PORT`, `HOST` | no | default 8080, 0.0.0.0 |
| `DATABASE_URL` | yes | `postgres://user:pass@host:5432/pestino` |
| `DATABASE_SSL` | no | `true` for managed databases that require TLS |
| `JWT_ACCESS_SECRET` | yes | ≥ 32 random characters. Generate with `openssl rand -base64 48` |
| `OTP_HMAC_SECRET` | yes | ≥ 32 random characters, must differ from the JWT secret in production |
| `OTP_DEV_ECHO` | yes | must be `false` in production |
| `GEMINI_API_KEY` | yes | server-side only; never shipped to the app |
| `GEMINI_MODEL`, `GEMINI_TIMEOUT_MS` | no | default `gemini-2.5-flash`, 45 s |
| `UPLOAD_DIR`, `MAX_UPLOAD_MB` | no | default `./storage/uploads`, 8 MB |
| `FREE_MONTHLY_ANALYSES`, `FREE_MAX_FARMS` | no | default 5 and 1 |
| `CORS_ORIGINS` | no | comma-separated; the mobile app does not need CORS |
| `TRUST_PROXY` | no | default 1 |
| `ACCESS_TOKEN_TTL_SECONDS`, `REFRESH_TOKEN_TTL_DAYS`, `OTP_TTL_SECONDS`, `OTP_MAX_ATTEMPTS` | no | defaults 900, 60, 120, 5 |
| `AUTH_RATE_LIMIT_PER_15MIN`, `GLOBAL_RATE_LIMIT_PER_15MIN` | no | defaults 100 and 600 |

SMS: production OTP delivery must be connected to an SMS provider in `src/lib/sms.ts`. Until it is,
the OTP cannot reach real users. This is a launch blocker.

## Steps

```bash
cd pestino/backend
npm ci
npm run typecheck
npm test                       # requires TEST_DATABASE_URL
npm run build                  # emits dist/src/*.js
npm run db:migrate             # applies migrations/ in order
npm run db:seed                # loads knowledge/*.json (idempotent)
NODE_ENV=production node --env-file=/etc/pestino/backend.env dist/src/server.js
```

Run the process under systemd or a container with a non-root user. Example systemd unit:

```ini
[Service]
User=pestino
WorkingDirectory=/opt/pestino/backend
EnvironmentFile=/etc/pestino/backend.env
ExecStart=/usr/bin/node dist/src/server.js
Restart=always
```

Health check: `GET /health` returns 200 when the process and database are reachable.

## Operations

- **Backups:** nightly `pg_dump` with point-in-time recovery if the provider supports it. Test a restore each month.
- **Uploads:** back up `UPLOAD_DIR` or the object-storage bucket together with the database. Image rows and files must stay consistent.
- **Logs:** JSON logs to stdout. Do not log tokens, OTP codes, or full phone numbers. Forward to your log platform.
- **Secrets rotation:** rotating `JWT_ACCESS_SECRET` invalidates access tokens (users refresh automatically). Rotating `OTP_HMAC_SECRET` invalidates pending codes only.
- **Scaling:** the API is stateless. Run several instances behind the LB once uploads are on shared storage.
- **Quota reset:** monthly limits use the UTC calendar month (`currentQuotaWindowStart`).

## Pre-launch checklist

- [ ] Real SMS provider connected and tested in Iran.
- [ ] `OTP_DEV_ECHO=false`, secrets ≥ 32 chars and unique, `NODE_ENV=production`.
- [ ] HTTPS only, HSTS through the proxy, and the API host matches the app's `API_BASE_URL`.
- [ ] Gemini key restricted to the backend host and monitored for spend.
- [ ] Knowledge references reviewed by an expert before `verified` is set.
- [ ] Privacy policy and terms published at the URLs in `core/config/app_config.dart`.
- [ ] Backup restore test completed.
