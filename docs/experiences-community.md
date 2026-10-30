# Community migration experiences

## Product behavior

- Anyone can read approved stories. Stories are not treated as official immigration guidance.
- Submission fields: destination, journey stage, optional route label, title, story, and optional display name.
- Contact details and external links detected in user text are rejected. No attachments, phone number, email address, or assessment answers are requested.
- New entries are private to moderators while `pending`; only a moderator can publish, reject, or hide an entry.
- Readers can report a published story. Reported stories appear in the administrator moderation view.
- The submitting device receives an anonymous client token; its hash is stored with the entry. The token is held in secure device storage where supported and permits that device to delete its own entry. No account or legal name is needed.
- The server enforces a small per-token submission limit and one report per token per story. Submission-rate hashes are pruned after one day. These are abuse-friction measures, not identity verification.

## API

- `GET /api/experiences` — approved stories only; optional `destination`, `stage`, `limit`, `offset` filters.
- `POST /api/experiences` — submit for moderation; requires `X-Experience-Client-Token`.
- `DELETE /api/experiences/{id}` — delete the caller's own entry using the same device token.
- `POST /api/experiences/{id}/report` — report an approved story with a short reason.
- `GET /api/admin/experiences?status=pending|reported|...` — moderator queue, administrator session required.
- `POST /api/admin/experiences/{id}/review` — set `approved`, `rejected`, or `hidden`; administrator session required.

Story records live in `experiences.sqlite3`, using `EXPERIENCES_DB_PATH` when set, otherwise the existing `PAYMENTS_DATA_DIR`. The deployment must retain that configured data path if community posts are expected to survive a service restart or redeploy; an ephemeral filesystem is not durable storage.

## Moderation checklist

Before publishing, check that the story:

1. does not expose names, contact information, case numbers, passport/identity details, or another person's private data;
2. is presented as a personal account rather than an official rule or guaranteed outcome;
3. contains no fraud, harassment, discriminatory abuse, spam, or solicitation;
4. does not misrepresent anecdotal dates, fees, or outcomes as current official requirements.

When a story is reported for privacy or harmful content, hide it while reviewing. Users should be encouraged to verify requirements and fees through the official authority for their destination.
