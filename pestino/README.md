# Pestino (پستینو)

AI assistant for pistachio growers: Persian-first Flutter app plus a Node.js/TypeScript API.

- `backend/`: REST API, PostgreSQL schema, Gemini Vision proxy, knowledge base, tests.
- `mobile/`: Flutter app (Android and iOS), Clean Architecture per feature.
- `docs/`: [Architecture](docs/ARCHITECTURE.md), [Database](docs/DATABASE.md), [API spec](docs/API_SPEC.md), [Backend deployment](docs/DEPLOYMENT.md), [Mobile build and store release](docs/RELEASE.md).

Quick start:

```bash
cd backend && npm ci && npm run typecheck && npm test
cd ../mobile && tool/bootstrap.sh
```

Status: backend complete and tested. The mobile code has not been compiled on a Flutter toolchain yet.
Blocking items before launch: SMS provider for OTP delivery, store IAP receipt verification, and expert review of knowledge references.
