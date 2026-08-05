# KittyNails — Claude Context

## Project

Nail salon booking app for a German salon. FastAPI backend + React/TypeScript frontend, deploying to AWS (Lambda + API Gateway + RDS + CloudFront/S3). Active branch: `feature/ai-nail-classification`.

## Stack

**Backend:** Python 3.12, FastAPI, SQLAlchemy 2.0 async (asyncpg), Pydantic v2, Alembic, Mangum (Lambda adapter), slowapi (rate limiting), python-jose + passlib/bcrypt (JWT auth)

**Frontend:** React 18 + TypeScript, Vite, Tailwind v4, react-router-dom, framer-motion, sonner, react-hook-form, @radix-ui/react-dialog

**AI:** Claude on Amazon Bedrock — `eu.anthropic.claude-sonnet-4-6` via `AnthropicBedrock` (`anthropic[bedrock]` package). EU regional inference (`eu-central-1`) for GDPR. Structured output via `client.messages.parse(output_format=NailClassification)`.

**DB:** PostgreSQL 16. Local: `podman compose up -d db` (container `kittynails-db-1`, port 5432). Test DB: `kittynails_test`.

**Node:** Managed via mise — `eval "$(mise activate bash)"` or direct path `/Users/grigoanr/.local/share/mise/installs/node/20.20.0/bin/node`. Uses Node 20.20.0 (Node 18 breaks Vite).

## Running locally

```bash
# DB only (backend runs outside Docker to avoid .env interpolation issues)
podman compose up -d db

# Backend
source .venv/bin/activate
uvicorn src.main:app --reload   # http://localhost:8000

# Frontend
cd frontend
eval "$(mise activate bash)"
npm run dev                     # http://localhost:5173

# Tests
source .venv/bin/activate
python -m pytest

# Migrations
source .venv/bin/activate
alembic upgrade head
```

## Key decisions made

- **No `Service` model** — replaced with `NailType × DesignTier` (3×3 matrix). Old `services` table dropped in migration `19a839927e25`.
- **AI classifies, backend prices** — `NailClassification` schema has no price/duration fields. The model only returns `nail_type`, `design_tier`, `confidence`, `reasoning`. Price and duration are always computed server-side from DB rows.
- **`quoted_price` snapshot** — price is locked at booking time so owner price changes don't affect existing bookings.
- **Bedrock over direct API** — IAM auth (Lambda role, no API key to manage). `eu.` prefix for EU data residency (+10% but cents at this volume). Model: `eu.anthropic.claude-sonnet-4-6` (native structured-output GA on Bedrock).
- **Rate limits** — 5/hour on `/api/analyze-nails`, 10/hour on `/api/appointments`. Disabled in tests via `limiter.enabled = False` in conftest.
- **`bcrypt==4.0.1`** pinned — bcrypt 5.x is incompatible with passlib.
- **`AWS_REGION`** — has a default in config (`eu-central-1`) but will be overridden by the ambient `AWS_REGION` env var in a dev shell. In Lambda, AWS sets it automatically to the deployed region.

## DB schema (current)

```
nail_types       — id, name, price, duration_minutes, sort_order, is_active, timestamps
design_tiers     — id, name, price, duration_minutes, sort_order, is_active, timestamps
appointments     — id, nail_type_id, design_tier_id, client_email,
                   start_time, end_time, status, quoted_price,
                   ai_confidence, ai_reasoning, created_at
availability_rules — id, day_of_week, start_time, end_time, created_at
blocked_times    — id, start_time, end_time, reason, created_at
```

Seeded values: Short €30/60min · Regular €40/75min · Extensions €55/120min; Simple €10/15min · Medium €25/45min · Advanced €45/90min

## API routes

```
POST  /api/analyze-nails          Upload photo → AI classification + estimate (5/hour)
GET   /api/nail-types             Active nail types (sorted by sort_order)
GET   /api/design-tiers           Active design tiers (sorted by sort_order)
GET   /api/slots/?nail_type_id=&design_tier_id=&date=
GET   /api/slots/dates?nail_type_id=&design_tier_id=&year=&month=
POST  /api/appointments           Book (10/hour)

POST  /api/admin/login
GET/POST     /api/admin/nail-types
PUT          /api/admin/nail-types/{id}
GET/POST     /api/admin/design-tiers
PUT          /api/admin/design-tiers/{id}
GET/POST     /api/admin/availability-rules
DELETE/PUT   /api/admin/availability-rules/{id}
GET/POST     /api/admin/blocked-times
DELETE       /api/admin/blocked-times/{id}
GET          /api/admin/appointments/
PATCH        /api/admin/appointments/{id}/cancel|no-show|complete
```

## What's done (phases 1–8)

- **Phase 1** — `NailType` + `DesignTier` models, migration `fe36bbe93579` (seeds 6 rows, clears old appointments, reworks FKs), migration `19a839927e25` (drops services table). Applied and verified.
- **Phase 2** — `anthropic[bedrock]` dep, `AWS_REGION` + `NAIL_ANALYSIS_MODEL` config, `.env` updated.
- **Phase 3** — schemas: `nail_type.py`, `design_tier.py`, `nail_analysis.py` (with `NailClassification` structured-output schema + enums), updated `appointment.py`.
- **Phase 4** — services: `nail_type_crud.py`, `design_tier_crud.py`, `nail_analysis_service.py` (Bedrock call, lazy cached client, server-side pricing), refactored `slots_service.py` + `appointment_service.py`.
- **Phase 5** — routers: all new nail-type/design-tier/analysis routers, updated slots router, rewired `main.py`, deleted old services routers + files.
- **Phase 6** — tests: 71 passing. Mocks Bedrock client via `unittest.mock.patch`. 3 pre-existing failures in `test_availability_rules` / `test_blocked_times` (Pydantic validator raises 422, tests expect 400 — pre-dates this feature branch).
- **Phase 7** — Admin frontend: `NailTypesPage.tsx` + `DesignTiersPage.tsx` (CRUD with sort_order, is_active toggle), updated `admin/api.ts` (removed Service, added NailType/DesignTier), updated `AdminLayout.tsx` nav (Nail Types + Design Tiers), updated `App.tsx` routing, deleted `ServicesPage.tsx`.
- **Phase 8** — Public booking flow rewritten: photo upload → AI estimate card (confidence badge, price, duration, reasoning) → slot picker (uses nail_type_id + design_tier_id) → client info + confirm. Updated `api.ts` (analyzeNails, new slots/appointment signatures), rewrote `BookingModal.tsx` (4 steps), updated `Services.tsx` (pricing grid: nail types + design tiers), updated `Footer.tsx`.

## What's remaining

**Next session — Pricing & duration tuning**
- Adjust seeded `nail_types` prices/durations (currently: Short €30/60min, Regular €40/75min, Extensions €55/120min) — these are too high
- Adjust seeded `design_tiers` prices/durations (currently: Simple €10/15min, Medium €25/45min, Advanced €45/90min) — also too high
- Create an Alembic migration to update the seed values (or update the existing seed migration if it hasn't shipped)
- Refine the `SYSTEM_PROMPT` in `src/services/nail_analysis_service.py` to better guide the model on time estimates — the model should understand how long each nail type and design tier actually takes (helps it classify ambiguous photos more accurately by factoring in realistic service complexity)
- Test the updated pricing locally with the mock and verify the frontend displays correct totals

**Infrastructure & deployment (after pricing is settled)**
- AWS account setup + Bedrock model access (Frankfurt, `eu-central-1`)
- Lambda IAM role with `bedrock:InvokeModel` permission on `eu.anthropic.claude-sonnet-4-6`
- End-to-end Bedrock test with a real nail photo (verifies image content-block wire format)
- Email confirmation via AWS SES (decided in earlier session)
- Fix the 3 pre-existing test failures (422 vs 400 for Pydantic validators)
- Update README.md (currently describes old services-based architecture)
- CI: add `TEST_DATABASE_URL` secret (currently only in local `.env`)

## Known issues / gotchas

- **Local Bedrock testing** — `AWS_REGION=eu-central-1` must be set explicitly (dev shell overrides with `us-west-2`). Without Bedrock access, mock `_classify_image` in `nail_analysis_service.py` to test the full UI flow (see `test_analysis_local.py` pattern in the session notes).
- Hardcoded test dates (`2026-08-10`) will rot — should compute relative to `date.today()`.
- `ruff check .` has 90 pre-existing errors on this branch (unsorted imports, unused `import pytest` in test files). Not blocking CI yet but worth a cleanup pass.
- `import pytest` unused warning in all test files — pytest discovers tests via its runner, the import is unnecessary.
- Local `AWS_REGION=us-west-2` (Amazon dev shell) overrides `.env`'s `eu-central-1` for config. Bedrock test locally needs `AWS_REGION=eu-central-1` prefixed.
