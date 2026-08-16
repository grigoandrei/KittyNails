# KittyNails — Claude Context

## Project

Nail salon booking app for a Korean nail art studio in Berlin. FastAPI backend + React/TypeScript frontend, deploying to AWS (Lambda + API Gateway + Aurora PostgreSQL + CloudFront/S3).

## Stack

**Backend:** Python 3.12, FastAPI, SQLAlchemy 2.0 async (asyncpg), Pydantic v2, Alembic, Mangum (Lambda adapter), slowapi (rate limiting), python-jose + passlib/bcrypt (JWT auth)

**Frontend:** React 18 + TypeScript, Vite, Tailwind v4, react-router-dom, sonner, react-hook-form, @radix-ui/react-dialog, lucide-react, clsx, tailwind-merge

**AI:** Claude Sonnet 4.6 on Amazon Bedrock — `eu.anthropic.claude-sonnet-4-6` (geo inference profile) via `AnthropicBedrock` (`anthropic[bedrock]` package). EU regional inference (`eu-central-1`). Flat structured output via `client.messages.parse(output_format=NailClassification)`.

**Email:** AWS SES via `boto3`. Confirmation emails sent as FastAPI background tasks immediately after booking. Reminder emails sent 24h before via a separate Lambda on an hourly EventBridge schedule.

**Payments:** Stripe Checkout Sessions via `stripe` Python SDK. €15 non-refundable deposit collected at booking. Hosted checkout page (Stripe handles card input, 3D Secure, PCI compliance). Webhook confirms or cancels appointment based on payment outcome.

**DB:** PostgreSQL 16. Local: `docker compose up -d` (container, port 5432). Test DB: `kittynails_test`.

**Node:** Managed via mise — Node 20.20.0.

## Running locally

```bash
# DB only (backend runs outside Docker to avoid .env interpolation issues)
docker compose up -d db

# Backend
source .venv/bin/activate
uvicorn src.main:app --reload   # http://localhost:8000

# Frontend
cd frontend
npm run dev                     # http://localhost:5173

# Tests
source .venv/bin/activate
python -m pytest

# Migrations
source .venv/bin/activate
alembic upgrade head
```

## Key decisions

- **Nail types × Design tiers** — 3 nail types (Japanese Manicure, Regular, Extensions) × 3 design tiers (Simple, Medium, Advanced). Japanese Manicure is fixed-price and doesn't use design tiers.
- **design_tier_id is nullable** — Japanese Manicure bookings have `design_tier_id = NULL`.
- **AI classifies, backend prices** — `NailClassification` is a flat Pydantic model (to avoid Bedrock grammar compilation timeouts). Returns `length`, `design_complexity`, `extensions` classifications. Backend maps `extensions` → nail type, `design_complexity` → design tier. Price/duration always computed server-side.
- **`quoted_price` snapshot** — price is locked at booking time.
- **Bedrock geo inference profile** — `eu.anthropic.claude-sonnet-4-6` routes within EU regions. Base model ID `anthropic.claude-sonnet-4-6` doesn't support on-demand in eu-central-1.
- **Flat NailClassification schema** — nested objects + 15 booleans caused "Grammar compilation timed out" on Bedrock. Simplified to flat fields with enum values.
- **SES email confirmation** — sends styled HTML confirmation email as a background task right after booking. Sends reminder 24h before. Both fault-tolerant (never break the booking flow).
- **SES_ENABLED flag** — disables email sending in dev/test without code changes.
- **Reminder Lambda** — separate handler (`src/reminder_handler.py`) queries appointments in a 23–25h-ahead window. 2-hour window avoids missed sends even with slight EventBridge drift, while hourly trigger interval prevents duplicate sends.
- **Berlin timezone display** — all email times are formatted in Europe/Berlin regardless of how they're stored (UTC in DB).
- **Slot conflict pre-check** — frontend re-fetches slots before submitting booking to catch stale state.
- **Stripe Checkout for deposits** — €15 deposit via Stripe Checkout Sessions (hosted page). Flow: create appointment as PENDING_PAYMENT → redirect to Stripe → webhook confirms (BOOKED) or expires (CANCELED). Confirmation email fires only after successful payment (in webhook handler).
- **PENDING_PAYMENT blocks slots** — both BOOKED and PENDING_PAYMENT appointments are treated as occupied in slot availability and conflict detection. When a Stripe session expires (24h), the webhook handler cancels the appointment, freeing the slot.
- **Stripe webhook verification** — `stripe.Webhook.construct_event()` with `STRIPE_WEBHOOK_SECRET` ensures only legitimate Stripe events are processed.
- **Timezone handling** — appointments stored in UTC. Slot generation uses `astimezone(None)` to convert to local time before comparing with naive slot times.
- **Past slot filtering** — `get_available_slots` skips any slot with `start_time <= now`.
- **Rate limits** — 5/hour on `/api/analyze-nails`, 10/hour on `/api/appointments`. Disabled in tests.

## DB schema (current)

```
nail_types       — id (uuid), name, price, duration_minutes, sort_order, is_active, timestamps
                   Seeded: Japanese Manicure €30/60min (sort 0) · Regular €40/90min (sort 1) · Extensions €55/150min (sort 2)

design_tiers     — id (uuid), name, price, duration_minutes, sort_order, is_active, timestamps
                   Seeded: Simple €0/0min · Medium €10/0min · Advanced €20/30min

appointments     — id, nail_type_id (FK), design_tier_id (FK, nullable), client_email,
                   start_time, end_time, status (PENDING_PAYMENT|BOOKED|CANCELED|COMPLETED|NO_SHOW),
                   quoted_price, ai_confidence, ai_reasoning,
                   stripe_session_id, stripe_payment_intent_id, created_at

availability_rules — id, day_of_week (0-6), start_time, end_time, created_at
blocked_times    — id, start_time, end_time, reason, created_at
```

## API routes

```
POST  /api/analyze-nails          Upload photo → AI classification + estimate (5/hour)
GET   /api/nail-types             Active nail types (sorted by sort_order)
GET   /api/design-tiers           Active design tiers (sorted by sort_order)
GET   /api/slots/?nail_type_id=&date=&design_tier_id=  (design_tier_id optional)
GET   /api/slots/dates?nail_type_id=&year=&month=&design_tier_id=  (design_tier_id optional)
POST  /api/appointments           Book directly without payment (design_tier_id optional) (10/hour)
POST  /api/checkout/create-session  Create appointment + Stripe Checkout → returns checkout_url (10/hour)
POST  /api/webhooks/stripe        Stripe webhook (checkout.session.completed / expired)

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

## Frontend flows

### AI Analysis Flow (Regular / Extensions)
1. Photo upload step → "Get AI Estimate" button
2. Claude classifies: length, design_complexity, extensions
3. Backend maps → nail type + design tier, returns price estimate
4. Estimate card shown → user proceeds to date/time → confirm + book

### Japanese Manicure Flow
1. Photo upload step → "Japanese Manicure" button (with description)
2. Skips AI analysis and estimate steps entirely
3. Goes directly to date/time → confirm + book (no design_tier_id sent)

### Confirmation card shows
- Service name, price, date/time
- Instagram DM link (@kittynails_berlin)

## Migrations (in order)

1. `f2ac01aa1092` — create services + appointments tables
2. `6b265ca6e5b9` — create availability_rules table
3. `6c6cf084bf3d` / `89f6a4c70376` — create blocked_times table
4. `304250ea92fd` — timezone-aware timestamps
5. `df7d1ac1f4cc` — make appointment timestamps timezone-aware
6. `fe36bbe93579` — add nail_types + design_tiers, rework appointments (drop service_id, add nail_type_id + design_tier_id + quoted_price + ai fields, seed 3×3)
7. `19a839927e25` — drop unused services table
8. `a1b2c3d4e5f6` — update design tier pricing (Simple €0/0min, Medium €10/0min, Advanced €20/30min)
9. `b2c3d4e5f6a7` — remove Short nail type, update Regular to 90min, Extensions to 150min
10. `c3d4e5f6a7b8` — add Japanese Manicure (€30/60min), make design_tier_id nullable
11. `d4e5f6a7b8c9` — add stripe_session_id, stripe_payment_intent_id columns, PENDING_PAYMENT status

## What's remaining (next session)

1. **Frontend Stripe integration** — redirect to checkout URL after booking confirmation step
   - Call `POST /api/checkout/create-session` instead of `POST /api/appointments`
   - Handle success/cancelled redirect pages
   - Show the publishable key for any client-side Stripe.js needs

2. **AWS deployment**
   - Lambda + API Gateway (backend) — Mangum already configured
   - S3 + CloudFront (frontend)
   - Aurora PostgreSQL (DB)
   - Lambda IAM role with `bedrock:InvokeModel` + `ses:SendEmail` permissions
   - Environment variables via Lambda config
   - Register Stripe webhook endpoint in Stripe dashboard (production URL)

## Do this before deployment

### 1. Verify SES sender identity
- Verify the sender email/domain in SES (`noreply@kittynails.de`)
- If still in SES sandbox: request production access (sandbox only allows sending to verified addresses)
- Alternatively verify the domain `kittynails.de` via DNS (DKIM + SPF records) for better deliverability

### 2. Set up the reminder Lambda
- Create a second Lambda function with handler `src.reminder_handler.handler`
- Give it the same VPC/security group config as the main Lambda (needs DB access)
- Create an EventBridge Scheduler rule: **rate(1 hour)** targeting this Lambda
- Set the same environment variables as the main Lambda (`DATABASE_URL`, `SES_SENDER_EMAIL`, `SES_REGION`, `SES_ENABLED=true`)

### 3. IAM permissions for Lambdas
- Main Lambda role needs: `bedrock:InvokeModel`, `ses:SendEmail`, `ses:SendRawEmail`
- Reminder Lambda role needs: `ses:SendEmail`, `ses:SendRawEmail`
- Both need VPC execution permissions if in VPC (ENI create/delete/describe)
- Resource scope SES permissions to the verified sender identity ARN

### 4. Environment variables (Lambda config)
```
DATABASE_URL=postgresql+asyncpg://<user>:<pass>@<aurora-endpoint>:5432/kittynails
ADMIN_USERNAME=cata
ADMIN_PASSWORD_HASH=<bcrypt hash>
JWT_SECRET=<generate new secret for prod>
AWS_REGION=eu-central-1
NAIL_ANALYSIS_MODEL=eu.anthropic.claude-sonnet-4-6
SES_SENDER_EMAIL=noreply@kittynails.de
SES_REGION=eu-central-1
SES_ENABLED=true
STUDIO_NAME=KittyNails Berlin
STUDIO_ADDRESS=Stallschreiberstraße 16, 10179 Berlin
STUDIO_INSTAGRAM=https://www.instagram.com/kittynails_berlin/
```

### 5. Database
- Run `alembic upgrade head` against Aurora PostgreSQL
- Seed nail types and design tiers (migrations handle this)
- Create availability rules via admin panel

### 6. Frontend
- Build: `cd frontend && npm run build`
- Upload `dist/` to S3, serve via CloudFront
- Set API base URL to the API Gateway endpoint

### 7. DNS & HTTPS
- Point `kittynails.de` (or subdomain) to CloudFront distribution
- ACM certificate for the domain
- API Gateway custom domain (e.g., `api.kittynails.de`)

### 8. Stripe production setup
- Complete business verification in the Stripe dashboard (identity, bank account for payouts)
- Switch from test keys (`sk_test_...`) to live keys (`sk_live_...`, `pk_live_...`)
- Register a production webhook endpoint: `https://api.kittynails.de/api/webhooks/stripe`
  - Events to listen for: `checkout.session.completed`, `checkout.session.expired`
- Get the live webhook signing secret and set `STRIPE_WEBHOOK_SECRET` in Lambda env vars
- Test with a real €15 payment to confirm the full flow works end-to-end

### Testing Stripe locally
```bash
# Forward Stripe webhooks to your local server
stripe listen --forward-to localhost:8000/api/webhooks/stripe

# Test card: 4242 4242 4242 4242, any future expiry, any CVC
# 3D Secure test card: 4000 0025 0000 3155
```

## Known issues / gotchas

- **Bedrock model ID** — must use `eu.anthropic.claude-sonnet-4-6` (geo inference profile), NOT `anthropic.claude-sonnet-4-6` (fails with "on-demand not supported"). The `eu.` prefix routes within EU.
- **Grammar compilation timeout** — if you add fields to `NailClassification`, keep the schema flat. Nested objects with many fields cause Bedrock structured output to timeout.
- **`visible_details` max_length** — set to 1000 chars because Claude can be verbose.
- **Timezone in slot comparison** — appointments are stored in UTC but slots are generated as naive local times. Must use `astimezone(None)` (not `replace(tzinfo=None)`) when comparing.
- **`@lru_cache` on `get_client()`** — means the Bedrock client is created once per process. If you change `.env` model/region, restart the server.
- **Email tests need no DB** — unit tests for `email_service.py` override the conftest `setup_database` fixture at class level to avoid needing PostgreSQL. Integration tests that use `client` fixture require the DB running.
- **Reminder deduplication** — the 23–25h window + 1-hour trigger rate means each appointment only falls in the window once. If the trigger interval changes, adjust the window to avoid double-sends.
- **SES sandbox limitation** — in sandbox mode, SES can only send to verified email addresses. Must request production access before real clients can receive emails.
- **3 pre-existing test failures** in `test_availability_rules` / `test_blocked_times` — Pydantic validator raises 422, tests expect 400. Not related to our features.
- **`ruff check .`** has pre-existing lint errors (unsorted imports in files we didn't touch). Our modified files are clean.
- Hardcoded test dates (`2026-08-10`) will rot — should compute relative to `date.today()`.
