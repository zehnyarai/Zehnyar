# Pestino (پستینو) — Architecture

Pestino is an AI assistant for pistachio growers. The user photographs a leaf, fruit cluster,
trunk, pest or soil; the backend sends the image to Gemini Vision with pistachio-specific rules,
validates the answer, and returns a Persian report with confidence, alternatives, actions,
and references.

## 1. Components

```
┌────────────────────┐   HTTPS + JWT    ┌────────────────────────┐    ┌──────────────┐
│ Flutter app        │ ───────────────▶ │ Node.js / TypeScript   │ ─▶ │ PostgreSQL   │
│ (Android, iOS)     │                  │ REST API (Express 5)   │    └──────────────┘
│ Riverpod + GoRouter│ ◀─────────────── │  - auth, farms, analyses│   ┌──────────────┐
│ Dio, secure storage│                  │  - knowledge, plans    │ ─▶ │ Private image│
└────────────────────┘                  │  - Gemini proxy        │    │ storage      │
                                        └───────────┬────────────┘    └──────────────┘
                                                    │ server-side only
                                                    ▼
                                        ┌────────────────────────┐
                                        │ Google Gemini Vision   │
                                        │ (API key lives here)   │
                                        └────────────────────────┘
```

Rules that follow from this design:
- The Gemini API key exists only in backend environment variables. The mobile app never calls Gemini.
- The mobile app only holds its own access and refresh tokens, stored in the platform secure storage
  (Keychain on iOS, Keystore on Android through `flutter_secure_storage`).
- The backend is the single source of truth for plan limits (`planCatalog`). The app mirrors them for display only.

## 2. Mobile app (`pestino/mobile`)

Clean Architecture, one folder per feature, three layers per feature:

```
lib/
  app/            app root (MaterialApp.router, fa-IR locale, RTL), router.dart (route contract)
  core/
    config/       compile-time config (API_BASE_URL via --dart-define)
    di/           composition root: every repository provider is wired here
    errors/       AppFailure: maps DioException and API error codes to Persian messages
    network/      ApiClient (Dio) with bearer auth and single-flight refresh on 401
    storage/      TokenStore (flutter_secure_storage)
    theme/        colour system and Material theme (Vazirmatn font)
    utils/        Persian helpers: Jalali calendar, Persian digits, season/category labels
    widgets/      shared widgets (cards, empty/error/loading states, confidence ring)
  features/
    auth/         OTP login: domain / data / presentation
    splash/       session restore
    farms/        farm CRUD and trees
    analysis/     image capture, submission, report, usage banner
    history/      cursor-paginated analyses
    dashboard/    home screen
    knowledge/    knowledge base list and article
    profile/      profile, onboarding
    subscription/ plans and paywall
    shell/        bottom navigation
```

Dependency rule: presentation depends on domain interfaces; data implements them; `core/di`
is the only place that knows concrete classes.

Navigation: `go_router`. The redirect guard sends unauthenticated users to login, and authenticated
users with no province to onboarding. Reports open with `extra: Analysis`, so the report
renders immediately after submission without a second request.

Localisation and layout: `fa-IR` with RTL forced at the root. Dates are shown in the Jalali calendar.
Digits are Persian. Layouts adapt to width (for example, the dashboard grid switches to 4 columns above 600 dp).

## 3. Backend (`pestino/backend`)

```
src/
  app.ts, server.ts       Express app, security middleware, routing under /api/v1
  config/env.ts           zod-validated environment; refuses to start with weak or missing secrets
  db/                     pool, migration runner
  lib/                    errors (AppError), logger, phone normalisation, crypto, storage, SMS
  middleware/             requireAuth, validation, error handler (stable JSON error shape)
  modules/
    auth/                 OTP, refresh-token rotation, logout, /me
    farms/                farms and trees (plan limit on farm count)
    analyses/             quota, upload, pipeline, history
    ai/                   Gemini client, prompt, report schema, safety filter
    knowledge/            read-only knowledge base API
    subscriptions/        plan catalogue, current plan, checkout (not yet enabled)
migrations/               SQL migrations (001_init.sql)
knowledge/                curated knowledge base content (articles.json, references.json)
test/                     unit and integration tests
```

Security controls in the backend:
- Helmet, CORS allowlist, JSON body limit of 100 kB.
- Auth endpoints: per-IP rate limit (`AUTH_RATE_LIMIT_PER_15MIN`), per-phone OTP cooldown and hourly cap.
- OTP: only a keyed hash is stored (`OTP_HMAC_SECRET`); limited attempts; short TTL.
- Refresh tokens are rotated on every use and stored hashed. Reuse of a revoked token revokes the whole family.
- Every farm and analysis query is scoped to the authenticated user. Other users' records return 404.
- Uploads are validated by MIME type and size (`MAX_UPLOAD_MB`). Images are stored with random keys, not user-supplied names.
- Failed AI calls are recorded with status `failed` and do not consume the monthly quota.

## 4. AI pipeline

1. Quota check against the user's plan (`FREE_MONTHLY_ANALYSES` for free, unlimited for premium).
2. Store the image on private storage, then create an `analyses` row with status `pending`.
3. Call Gemini Vision with the pistachio expert prompt, the knowledge catalogue (slugs and symptoms),
   and the user's context (category, season, tree age, location, notes).
4. Validate the response against a strict schema (`report.schema.ts`). Invalid output is an error, not a guess.
5. Safety filter (`safety.ts`): reject or rewrite any dangerous pesticide instruction, any absolute
   certainty claim, and any unsupported reference. The mandatory disclaimer is always attached.
6. Attach references only from the verified knowledge base. Each reference carries a `verified` flag.
   Unverified references are shown to the user with a "در انتظار بازبینی" (pending review) badge.
7. Persist the report in `analyses.result` as `status = completed`.

Rules the prompt enforces: act as a pistachio expert; never claim 100% certainty; never replace an expert;
never give pesticide names, doses, or application instructions. Management advice stays at the level of
principles (IPM, monitoring, cultural practices), and the report points to an expert for chemical control.

## 5. Monetisation

- Plans: `free` (monthly analysis cap, 1 farm by default) and `premium` (unlimited analyses, up to 50 farms,
  advanced reports, PDF export). Entitlements are computed server-side in `resolvePlan`.
- `subscriptions` table is provider-agnostic (`provider` can be a Zarinpal/IDPay gateway, Bazaar IAP,
  Myket IAP, Google Play, or App Store).
- Checkout currently returns `501 PAYMENT_NOT_CONFIGURED`. The app shows this as a Persian message.
  Receipt verification with each store is not implemented yet.

## 6. Knowledge base

Four kinds of entry, each with a slug, Persian and English titles, a Persian summary, symptoms, causes,
management principles, and references:
- `pest`: psylla, stink bug, fruit moth, wood borers, mites (with scientific name, damage type, monitoring method)
- `disease`: gummosis and root rot, panicle and shoot blight, septoria leaf spot, alternaria leaf blight
- `nutrient`: nitrogen, iron, zinc, potassium, magnesium deficiency
- `environmental`: drought, heat, cold damage, soil salinity

Content lives in `backend/knowledge/*.json`, is loaded into PostgreSQL by `npm run db:seed`, and is
served via `/api/v1/knowledge`. Every reference must be verified by an expert before `verified` is set to `true`.
Do not add DOIs or citations that have not been checked against the source.
