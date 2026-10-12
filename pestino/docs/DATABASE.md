# Pestino — Database design

PostgreSQL 13+. No extensions are required (`gen_random_uuid()` is built in). Schema: `backend/migrations/001_init.sql`.
Run with `npm run db:migrate`. Each migration runs in a transaction.

## Entities

| Table | Purpose | Key points |
|---|---|---|
| `users` | Farmers, experts, admins | `phone` unique (normalised `09XXXXXXXXX`); `role` in farmer/expert/admin; `is_active` |
| `otp_codes` | One-time login codes | Stores only `code_hash` (keyed HMAC); `attempts`, `expires_at`, `consumed_at` |
| `refresh_tokens` | Rotating sessions | `family_id` groups a rotation chain; `token_hash` unique; `replaced_by`; `revoked_at` |
| `farms` | Orchard profile | Owned by `user_id`; soft delete (`deleted_at`); variety, tree age, irrigation, soil |
| `trees` | Individual trees in a farm | `farm_id` cascade; `planted_year` between 1300 and 1500 (Jalali) |
| `images` | Metadata of uploaded photos | `storage_key` unique (random); `sha256`; file bytes are not in the DB |
| `knowledge_articles` | Knowledge base entries | `kind` in pest/disease/nutrient/environmental; JSONB lists; `is_published` |
| `pests` | 1:1 extension for `kind = pest` | scientific name, damage type, monitoring method |
| `diseases` | 1:1 extension for `kind = disease` | pathogen, pathogen type |
| `knowledge_references` | Citations | `citation` unique; `url`, `doi`, `year`, `verified` |
| `article_references` | M:N article ↔ reference | composite primary key |
| `analyses` | One image analysis | `status` pending/completed/failed; `result` JSONB (the report); `confidence` 0–100; soft delete |
| `subscriptions` | Plan history | `plan` free/premium; `status`; `provider`, `provider_ref`, `expires_at` |

## Relationships

```
users 1─∗ farms 1─∗ trees
users 1─∗ images 1─1 analyses ∗─1 users
farms 1─∗ analyses (nullable, SET NULL on delete)
knowledge_articles 1─1 pests | diseases
knowledge_articles ∗─∗ knowledge_references  (via article_references)
knowledge_articles 1─∗ analyses (primary_issue_slug, SET NULL on delete)
users 1─∗ subscriptions
```

## Indexes

- `analyses (user_id, created_at DESC) WHERE deleted_at IS NULL`: history paging.
- `analyses (user_id, created_at) WHERE status <> 'failed'`: monthly quota counting.
- `analyses (farm_id)`, `farms (user_id) WHERE deleted_at IS NULL`, `trees (farm_id)`.
- `knowledge_articles (kind) WHERE is_published`.
- `otp_codes (phone, created_at DESC)`, `refresh_tokens (user_id)`, `refresh_tokens (family_id)`.

## Data protection

- Phone numbers are the only directly identifying field besides a name. Both are shown only to their owner.
- OTP codes and refresh tokens are stored hashed. Plain values never reach the database.
- Deleting a user cascades to farms, trees, images, analyses, and subscriptions.
- Analyses are soft-deleted (`deleted_at`) so that quota and audit history remain consistent.

## Known gaps (planned)

- Image bytes are on the local disk configured by `UPLOAD_DIR`. Move to private object storage
  (for example S3-compatible) before scaling beyond one server, and keep signed, time-limited URLs only.
- Expert review workflow for references (`verified` is currently set by a curator, not an in-app flow).
- Payment and store receipt tables are reserved in `subscriptions`; receipt verification is not built yet.
