# Pestino API specification (v1)

Base URL: `https://<host>/api/v1`. All bodies are JSON unless noted. Times are ISO-8601 UTC.
Authentication: `Authorization: Bearer <accessToken>` (15-minute tokens; refresh with the refresh token).

## Errors

Every error uses the same shape:

```json
{ "error": { "code": "QUOTA_EXCEEDED", "message": "Monthly analysis quota exceeded", "details": null } }
```

Common codes: `VALIDATION_FAILED` (400), `UNAUTHORIZED` (401), `TOKEN_INVALID` (401), `REFRESH_REUSED` (401),
`FORBIDDEN` (403), `FARM_NOT_FOUND` / `ARTICLE_NOT_FOUND` / `ROUTE_NOT_FOUND` (404), `QUOTA_EXCEEDED` (402/429 per plan),
`FARM_LIMIT_REACHED` (403), `UNSUPPORTED_IMAGE` (400), `PAYLOAD_TOO_LARGE` (413), `RATE_LIMITED` (429),
`AI_UPSTREAM_ERROR` (502), `AI_INVALID_OUTPUT` (502), `AI_BLOCKED` (422), `PAYMENT_NOT_CONFIGURED` (501), `INTERNAL_ERROR` (500).
The app shows Persian text per code (`core/errors/app_failure.dart`).

## Rate limits

- Auth endpoints: `AUTH_RATE_LIMIT_PER_15MIN` per IP (default 100 per 15 minutes).
- All routes: `GLOBAL_RATE_LIMIT_PER_15MIN` per IP (default 600 per 15 minutes).
- `POST /analyses`: 10 requests per 10 minutes.

## Auth

Public (no token): `/auth/*`, `/subscriptions/plans`, `/health`. Everything else requires a bearer token.

| Method | Path | Body / notes | Response |
|---|---|---|---|
| POST | `/auth/otp/request` | `{ "phone": "09121234567" }` | 202 `{ "expiresIn": 120, "devCode"?: "123456" }` (`devCode` only when `OTP_DEV_ECHO=true`, never in production) |
| POST | `/auth/otp/verify` | `{ "phone", "code": "123456" }` | 200 `{ "user", "isNewUser", "tokens": { "accessToken", "accessTokenExpiresIn", "refreshToken" } }` |
| POST | `/auth/refresh` | `{ "refreshToken" }` (rotates) | 200 `{ "tokens": { ... } }` |
| POST | `/auth/logout` | `{ "refreshToken" }` | 204 |

## Profile

| Method | Path | Body | Response |
|---|---|---|---|
| GET | `/me` | — | 200 `{ "user": { "id", "phone", "fullName", "province", "city", "role" } }` |
| PATCH | `/me` | any of `fullName`, `province`, `city` (strict) | 200 `{ "user": ... }` |

## Farms

| Method | Path | Body | Response |
|---|---|---|---|
| GET | `/farms` | — | 200 `{ "items": [Farm] }` |
| POST | `/farms` | Farm input (below) | 201 `{ "farm": Farm }`; 403 `FARM_LIMIT_REACHED` |
| GET | `/farms/:farmId` | — | 200 `{ "farm": Farm }` |
| PATCH | `/farms/:farmId` | partial Farm input | 200 `{ "farm": Farm }` |
| DELETE | `/farms/:farmId` | — | 204 (soft delete) |
| GET | `/farms/:farmId/trees` | — | 200 `{ "items": [Tree] }` |
| POST | `/farms/:farmId/trees` | `{ "label", "plantedYear"?, "variety"? }` | 201 `{ "tree": Tree }` |
| DELETE | `/farms/:farmId/trees/:treeId` | — | 204 |

Farm input (strict, unknown keys rejected): `name` (2–120), `province` (2–80), `city` (2–80),
`latitude`, `longitude`, `areaHectares` (≥ 0), `pistachioVariety` (≤ 80), `averageTreeAge` (0–150),
`irrigationMethod` ∈ `drip | flood | sprinkler | micro_sprinkler | rainfed | other`, `soilType` (≤ 40), `soilNotes` (≤ 1000).
Farm: `id, name, province, city, latitude, longitude, areaHectares, pistachioVariety, averageTreeAge, irrigationMethod, soilType, soilNotes, createdAt, updatedAt`.
Tree: `id, farmId, label, plantedYear, variety, createdAt`.

## Analyses

| Method | Path | Notes |
|---|---|---|
| POST | `/analyses` | `multipart/form-data`. Fields: `image` (file, required, JPEG/PNG/WEBP, ≤ `MAX_UPLOAD_MB`), `category` (required), `season` (required), `farmId` (UUID, optional), `treeAgeYears` (0–150, optional), `location` (≤ 200), `userNotes` (≤ 1000). 201 `{ "analysis": Analysis }` with `report`. Synchronous; allow up to ~60 s. |
| GET | `/analyses?limit=20&cursor=&farmId=` | 200 `{ "items": [AnalysisSummary], "nextCursor": ISO \| null }` |
| GET | `/analyses/:analysisId` | 200 `{ "analysis": Analysis }` |
| GET | `/analyses/:analysisId/image` | image bytes (owner only) |
| DELETE | `/analyses/:analysisId` | 204 (soft delete) |
| GET | `/analyses/usage` | 200 `{ "usage": { "plan", "planName", "monthlyLimit", "used", "remaining", "resetsAt" } }`. `monthlyLimit: null` means unlimited. |

`category`: `leaf | fruit_cluster | trunk | pest | soil`. `season`: `spring | summer | autumn | winter`.

Analysis summary: `id, status (pending|completed|failed), category, season, farmId, imageId, treeAgeYears, location, userNotes, primaryIssueSlug, primaryTitle, confidence, confidenceLabel, errorMessage, createdAt, completedAt`.
`Analysis` = summary + `report` (list endpoint omits `report`).

Report (`report` JSON, `schemaVersion: 1`):

```json
{
  "summary": "…",
  "category": { "code": "leaf", "label": "برگ" },
  "season": { "code": "spring", "label": "بهار" },
  "imageQuality": { "usable": true, "issues": [] },
  "detectedSubject": "…",
  "diagnosis": { "title": "…", "knowledgeSlug": "pistachio-psylla", "isHealthy": false, "confidence": 78, "confidenceLabel": "…" },
  "observedSymptoms": ["…"],
  "alternatives": [{ "knowledgeSlug": null, "title": "…", "confidence": 15, "reason": "…" }],
  "recommendedActions": [{ "text": "…", "priority": "immediate | soon | monitor" }],
  "additionalInfoNeeded": ["…"],
  "references": [{ "citation": "…", "url": null, "doi": null, "year": 2019, "verified": false }],
  "disclaimer": "…",
  "meta": { "model", "promptVersion", "safetyFlags", "latencyMs", "generatedAt" }
}
```

Note: `references` contains only entries from the curated knowledge base. `verified: false` means expert review is pending.

## Knowledge

| Method | Path | Notes |
|---|---|---|
| GET | `/knowledge?kind=pest&q=psylla` | Requires bearer token. `kind` ∈ `pest | disease | nutrient | environmental`. 200 `{ "items": [KnowledgeSummary] }` |
| GET | `/knowledge/:slug` | Requires bearer token. 200 `{ "article": KnowledgeArticle }`; 404 `ARTICLE_NOT_FOUND` |

KnowledgeSummary: `slug, kind, titleFa, titleEn, summaryFa`.
KnowledgeArticle: summary fields + `symptoms[], causes[], management[], images[], attributes` (pest: `scientificName, damageType, monitoringMethod`; disease: `pathogen, pathogenType`; otherwise null), `references[]`.

## Subscriptions

| Method | Path | Response |
|---|---|---|
| GET | `/subscriptions/plans` | 200 `{ "items": [PlanInfo] }` |
| GET | `/subscriptions/me` | 200 `{ "plan": PlanInfo }` |
| POST | `/subscriptions/checkout` | 501 `PAYMENT_NOT_CONFIGURED` until a payment provider is enabled |

PlanInfo: `code, nameFa, monthlyAnalyses (null = unlimited), maxFarms (null = unlimited), advancedReports, pdfExport`.

## Health

`GET /health` (outside `/api/v1`): liveness with a database check.


## Admin & AI controls

Admin endpoints (`/admin/*`) and user AI helpers (`/ai/*`) are specified in [ADMIN_AI.md](ADMIN_AI.md).
