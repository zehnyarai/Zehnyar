# Admin panel & AI controls

**Status:** backend API and the in-app admin panel are implemented. Field-help buttons are in the farm form. Tests run against PostgreSQL (see `backend/test`).

The admin panel lives inside the mobile app. It is reached from the profile (admin accounts only) or from the **ورود مدیران** link on the login page. It uses its own password sign-in, not the farmer OTP flow.

## Goal

Operators manage every Gemini-powered feature from an admin area, without a redeploy:

- set, rotate or clear the Gemini API key (write-only, encrypted at rest);
- choose the default model and a per-feature model override;
- turn each AI feature on or off, and turn all AI off with one switch;
- set daily limits per plan for text helpers, and read usage and cost-relevant metrics;
- review an audit trail of every admin change.

The Gemini key never leaves the backend. The mobile app never receives it, and the admin API never returns it.

## Architecture

```
Admin web panel ──HTTPS──► /api/v1/admin/*  (requireAuth + DB role check = admin)
Mobile app      ──HTTPS──► /api/v1/ai/*     (requireAuth; plan + daily limits)
                              │
                 AiAssistService / AnalysesService
                              │  resolveFeature()  → enabled? model? limits? prompt?
                              ▼
                 AiSettingsService.resolveRuntime() → key (DB, decrypted) or env fallback, model, timeout, kill switch
                              ▼
                 GeminiVisionClient → generativelanguage.googleapis.com (key in header only)
                              │
                 ai_usage_logs / admin_audit_logs (never store the key)
```

Resolution order:

| Setting | Source order |
|---|---|
| API key | `ai_settings.gemini_api_key_enc` (decrypted) → env `GEMINI_API_KEY` |
| Model | feature `model` → `ai_settings.default_model` → env `GEMINI_MODEL` |
| Timeout | `ai_settings.timeout_ms` → env `GEMINI_TIMEOUT_MS` |
| Global switch | `ai_settings.ai_enabled` (false = every AI call returns 503 `AI_DISABLED`) |

A stored key that cannot be decrypted (for example after the master secret changes) is an error (`AI_KEY_UNREADABLE`). It does not silently fall back to the env key.

## Feature catalogue

| Key | Kind | Editable prompt | Purpose |
|---|---|---|---|
| `image_analysis` | vision | **no** | Photo diagnosis. The safety-critical prompt and JSON schema stay in code. Admin can switch it, set the model, and set temperature and output size. |
| `farm_form_help` | text | yes | Short help or validation for one farm form field. |
| `report_explain` | text | yes | Rewrites a technical report section in plain Persian. |

Editable prompts are always followed by the non-removable rules in `TEXT_SAFETY_RULES_FA` (no pesticide dosage, no 100% certainty, no fabricated references, expert referral). A prompt edit cannot remove them.

## Safety guarantees for text features

1. The user's field value is wrapped as quoted data, not instructions.
2. Every output passes `isUnsafeAdvice()`. Pesticide dosage or dangerous mixing is replaced with the standard referral sentence, and `UNSAFE_ADVICE_REPLACED` is returned in `flags`.
3. Every response carries the AI disclaimer.
4. Daily limits are enforced before the upstream call, so a blocked request costs nothing.

## Quotas

- `image_analysis` keeps the monthly plan quota (`FREE_MONTHLY_ANALYSES`). The admin feature limits are per-day caps on top of it (defaults are high).
- Text helpers use a **rolling 24-hour** window per user and feature: `daily_limit_free` for free users, `daily_limit_premium` for premium (resolved from `subscriptions`).
- Failed upstream calls are metered with their error code and do not count toward the user's limit.

## Database (migration 002)

| Table | Purpose |
|---|---|
| `ai_settings` | Singleton row (`id = 1`). Encrypted key, last four characters for display, default model, timeout, global switch, last editor. |
| `ai_feature_configs` | One row per feature key. Switch, model, prompt, output size, temperature, daily limits, `version` (incremented on each change). |
| `ai_usage_logs` | One row per Gemini call: user, feature, model, status (`ok`, `error`, `blocked`, `unsafe_replaced`), tokens, latency, error code. |
| `admin_audit_logs` | Who changed what and when. Stores changed field names and never values of secrets. |

Secrets: the key is encrypted with AES-256-GCM. The data key is derived from `AI_SETTINGS_ENCRYPTION_KEY` with HKDF-SHA256 and a fresh 96-bit IV per write (`src/lib/secretbox.ts`).

## Admin API (`/api/v1/admin`, role `admin` required)

Admin status is re-read from the database on every request, so revoking admin takes effect immediately.

| Method | Path | Body | Response |
|---|---|---|---|
| GET | `/ai/settings` | – | `{ settings }`: `keySource` (`database` / `environment` / `none`), `keyConfigured`, `keyHint` (last 4), `defaultModel`, `timeoutMs`, `aiEnabled` |
| PUT | `/ai/settings` | `{ apiKey?, clearApiKey?, defaultModel?, timeoutMs?, aiEnabled? }` (strict) | `{ settings }`. `apiKey` is validated (`[A-Za-z0-9_-]{20,200}`) and is never returned. |
| POST | `/ai/settings/test` | – | `{ result: { ok, model, latencyMs, errorCode? } }`. Sends `سلام` with a 16-token cap. |
| GET | `/ai/features` | – | `{ items }` with prompt, limits, version |
| PATCH | `/ai/features/:key` | any subset of `enabled, model, systemPrompt, maxOutputTokens, temperature, dailyLimitFree, dailyLimitPremium` | `{ item }`. `systemPrompt` on `image_analysis` returns `400 PROMPT_NOT_EDITABLE`. |
| GET | `/ai/usage?days=1..90` | – | `{ items: [{ feature, status, calls, inputTokens, outputTokens, avgLatencyMs }] }` |
| GET | `/audit?limit=1..200` | – | `{ items }` newest first |
| GET | `/stats` | – | `{ stats }`: users, analyses (24 h, 7 d, failed), premium subscriptions, AI calls, errors, tokens (7 d) |
| GET | `/users?q=&limit=` | – | `{ items }`: id, phone, name, role, isActive, last login. Search by phone or name. |
| PATCH | `/users/:userId` | `{ isActive }` | `{ user }`. Deactivating revokes the user's refresh tokens. Admins cannot deactivate themselves. |
| POST | `/auth/login` | `{ phone, password }` | `{ user, tokens }`. Public, not under the admin guard. |

Errors use the standard envelope `{ error: { code, message } }`. Codes added here: `ADMIN_REQUIRED` (403), `PROMPT_NOT_EDITABLE` (400), `ENCRYPTION_NOT_CONFIGURED` (400), `AI_DISABLED` (503), `AI_NOT_CONFIGURED` (503), `AI_KEY_UNREADABLE` (503).

## User API (`/api/v1/ai`, any authenticated user)

| Method | Path | Notes |
|---|---|---|
| GET | `/ai/features` | Lists enabled and disabled text helpers so the app can show or hide buttons. |
| POST | `/ai/assist` | Body: `{ feature: "farm_form_help" \| "report_explain", field (≤60), value (≤500), context? }`. Response: `{ feature, text, model, disclaimer, flags, remainingToday }`. Errors: `AI_FEATURE_DISABLED` (403), `AI_QUOTA_EXCEEDED` (402), `AI_DISABLED` (503). |

## Admin sign-in and accounts

Admins sign in with a phone number and password at `POST /api/v1/admin/auth/login`. This is separate from farmer OTP login.

- Passwords are hashed with scrypt (`N=32768, r=8, p=1`, random 16-byte salt). Only the hash is stored.
- Minimum policy: 12 characters, letters and digits, no spaces.
- After **5 consecutive wrong passwords** the account is locked for **15 minutes** (`429 ACCOUNT_LOCKED`). A successful login resets the counter.
- Every failure returns the same `401 INVALID_CREDENTIALS`, so the response does not reveal which numbers are admins. The login endpoint has a per-IP limit of 20 requests per 15 minutes.
- Every attempt (`admin.login`, `admin.login_failed`, `admin.login_locked`) is written to the audit log. Passwords are never logged.
- The returned tokens are normal access and refresh tokens. The admin role is still re-checked in the database on every admin request.

## Bootstrapping the first admin

There is no sign-up path for admins. Run once on the server, after the user has logged in with OTP at least once. The password comes from the environment, so it does not appear in shell history:

```bash
cd pestino/backend
ADMIN_PASSWORD='choose-a-long-password-2026' npm run admin:promote -- 09XXXXXXXXX  # grant
npm run admin:promote -- 09XXXXXXXXX --revoke                                     # revoke
```

Granting admin without a valid `ADMIN_PASSWORD` is refused. The action is written to `admin_audit_logs` with `actor = null`, `details.via = "cli"`.

## Operational notes

- Set `AI_SETTINGS_ENCRYPTION_KEY` in production (enforced at startup). Store it in the secret manager, and back it up separately from the database. Without it the DB key cannot be decrypted.
- Gemini access depends on region. Host the backend where the Gemini API is reachable and where your privacy policy allows sending farm photos and location text to Google.
- Usage rows are never pruned automatically. Add a retention job (for example 13 months) before production.

## In-app admin panel (Flutter)

Four tabs:

1. **آمار**: users, analyses, premium subscriptions, AI calls, errors and tokens (7 days).
2. **هوش مصنوعی**: write-only Gemini key (save, delete, test), default model, timeout, global AI switch; per-feature switch, daily limits, model, and system prompt (for editable features).
3. **کاربران**: search and activate or deactivate accounts (with confirmation).
4. **ممیزی**: audit log of admin actions and sign-in events.

Farm form: each of the variety, irrigation and soil fields has a sparkle button that calls `POST /ai/assist` with the field value and farm context. The answer appears in a sheet with the disclaimer and the remaining daily quota.

## Not yet built

- Two-factor sign-in for admins (planned: OTP after the password).
- Price per token and monthly cost estimate (token counts are stored, prices are not).
- A retention job for usage and audit logs.
