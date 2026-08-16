# KittyNails 💅

A nail appointment booking application for a Korean nail art studio in Berlin. Clients upload nail inspiration photos, get AI-powered price estimates, and book appointments. The nail artist manages everything through an admin panel.

## Current Status

### ✅ Implemented
- **AI nail analysis** — clients upload a photo, Claude (via Amazon Bedrock) classifies nail length, design complexity, and whether extensions are needed, then returns a price estimate
- **3 nail types**: Japanese Manicure (€30, 60 min), Regular (€40, 90 min), Extensions (€55, 150 min)
- **3 design tiers** (for Regular/Extensions only): Simple (+€0), Medium (+€10), Advanced (+€20, +30 min)
- **Japanese Manicure** — separate fixed-price flow that skips AI analysis entirely
- **Appointment booking** with real-time slot availability (filters past times, respects bookings)
- **Slot conflict detection** — re-checks availability before confirming a booking
- **Admin panel** — manage nail types, design tiers, availability rules, blocked times, appointments
- **JWT auth** for admin endpoints
- **Rate limiting** on public endpoints
- **Frontend** — React + Vite with booking modal, services display, gallery

### 🔜 Next Up
- **Stripe integration** — €15 deposit at booking to prevent no-shows
- **Email validation** — confirmation emails after booking
- **AWS deployment** — Lambda + API Gateway (backend), S3 + CloudFront (frontend), Aurora PostgreSQL (DB)

## Tech Stack

- **Backend**: FastAPI (Python 3.12) + Mangum (Lambda adapter)
- **Database**: PostgreSQL + SQLAlchemy (async)
- **AI**: Claude Sonnet 4.6 on Amazon Bedrock (structured output)
- **Validation**: Pydantic v2
- **Migrations**: Alembic
- **Frontend**: React + TypeScript + Vite + Tailwind CSS + Radix UI
- **Testing**: PyTest (async)
- **Linting**: Ruff
- **Deployment** (planned): AWS Lambda + API Gateway, S3 + CloudFront, Aurora PostgreSQL

## Architecture

```
┌─────────────────┐     ┌──────────────────────┐     ┌────────────────┐
│  React Frontend │────▶│  FastAPI Backend      │────▶│  PostgreSQL    │
│  (S3+CloudFront)│     │  (Lambda + API GW)    │     │  (Aurora)      │
└─────────────────┘     └──────────────────────┘     └────────────────┘
                              │          │
                              ▼          ▼
                        ┌──────────┐ ┌──────────────┐
                        │ Bedrock  │ │   Stripe     │
                        │ (Claude) │ │  (planned)   │
                        └──────────┘ └──────────────┘
```

## Local Development

### Prerequisites

- Python 3.12+
- Docker & Docker Compose (for PostgreSQL)
- AWS credentials configured (for Bedrock AI analysis)

### Setup

```bash
# Clone the repo
git clone <repo-url>
cd KittyNails

# Start PostgreSQL and the app
docker compose up

# The API will be available at http://localhost:8000
# Swagger docs at http://localhost:8000/docs
```

### Running without Docker

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Copy env file and configure
cp .env.example .env

# Run database migrations
alembic upgrade head

# Start the server
uvicorn src.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Running Tests

```bash
pytest
```

### Linting

```bash
ruff check .
ruff format .
```

## Project Structure

```
src/
├── main.py                    # FastAPI app entry point + Mangum handler
├── config.py                  # Settings (Pydantic BaseSettings)
├── database.py                # SQLAlchemy async engine + session
├── models/                    # SQLAlchemy models
│   ├── appointment.py         # Appointment with optional design_tier
│   ├── nail_type.py           # Nail types (Japanese Manicure, Regular, Extensions)
│   ├── design_tier.py         # Design tiers (Simple, Medium, Advanced)
│   ├── availability_rules.py  # Weekly schedule rules
│   └── blocked_time.py        # Blocked time ranges
├── schemas/                   # Pydantic request/response schemas
│   ├── nail_analysis.py       # AI classification models
│   ├── appointment.py         # Booking create/response
│   └── ...
├── routers/                   # API route handlers
│   ├── nail_analysis.py       # POST /api/analyze-nails
│   ├── appointments.py        # POST /api/appointments
│   ├── slots.py               # GET /api/slots, /api/slots/dates
│   ├── nail_types.py          # GET /api/nail-types (public)
│   ├── design_tiers.py        # GET /api/design-tiers (public)
│   └── admin/                 # Admin-only endpoints (JWT protected)
├── services/                  # Business logic layer
│   ├── nail_analysis_service.py  # Bedrock AI classification + pricing
│   ├── appointment_service.py    # Booking creation + conflict detection
│   ├── slots_service.py          # Available slot/date computation
│   └── ...
└── auth.py                    # JWT auth helpers

frontend/
├── src/
│   ├── api.ts                 # API client functions
│   ├── App.tsx                # Router + layout
│   ├── components/
│   │   ├── BookingModal.tsx   # Multi-step booking flow
│   │   ├── Services.tsx       # Nail types + design tiers display
│   │   ├── Gallery.tsx        # Photo gallery
│   │   ├── Footer.tsx         # Address + links
│   │   └── ...
│   └── admin/                 # Admin panel pages
└── ...
```

## API Overview

### Public Endpoints

| Method | Path                                          | Description                       |
|--------|-----------------------------------------------|-----------------------------------|
| GET    | /api/nail-types                               | List active nail types            |
| GET    | /api/design-tiers                             | List active design tiers          |
| POST   | /api/analyze-nails                            | AI photo analysis → price estimate|
| GET    | /api/slots?nail_type_id=&date=&design_tier_id=| Get available slots for date      |
| GET    | /api/slots/dates?nail_type_id=&year=&month=   | Get dates with availability       |
| POST   | /api/appointments                             | Book an appointment               |

### Admin Endpoints (JWT required)

| Method | Path                                 | Description              |
|--------|--------------------------------------|--------------------------|
| POST   | /api/admin/nail-types                | Create nail type         |
| PUT    | /api/admin/nail-types/{id}           | Update nail type         |
| POST   | /api/admin/design-tiers              | Create design tier       |
| PUT    | /api/admin/design-tiers/{id}         | Update design tier       |
| POST   | /api/admin/availability-rules        | Create availability rule |
| PUT    | /api/admin/availability-rules/{id}   | Update availability rule |
| DELETE | /api/admin/availability-rules/{id}   | Delete availability rule |
| POST   | /api/admin/blocked-times             | Block a time range       |
| DELETE | /api/admin/blocked-times/{id}        | Remove blocked time      |
| GET    | /api/admin/appointments              | List appointments        |
| PATCH  | /api/admin/appointments/{id}/cancel  | Cancel appointment       |
| PATCH  | /api/admin/appointments/{id}/no-show | Mark as no-show          |
| PATCH  | /api/admin/appointments/{id}/complete| Mark as completed        |

## Business Logic

### Pricing
- **Japanese Manicure**: fixed €30 (no design tier)
- **Regular / Extensions**: base price + design tier addon
  - Regular €40 + Simple €0 / Medium €10 / Advanced €20
  - Extensions €55 + Simple €0 / Medium €10 / Advanced €20

### AI Analysis Flow
1. Client uploads nail inspiration photo
2. Claude classifies: nail length, design complexity, extensions (natural/extensions)
3. Backend maps classifications → nail type + design tier
4. Returns price estimate to client
5. Client proceeds to pick date/time and book

### Japanese Manicure Flow
- Skips AI analysis entirely
- Client clicks "Japanese Manicure" button → goes directly to date/time → confirm

### Slot Availability
- Slots generated from availability rules (per weekday)
- Past times filtered out (for today)
- Booked appointments and blocked times excluded
- Re-checked before final booking submission

## Environment Variables

Key variables (see `.env.example`):

- `DATABASE_URL` — PostgreSQL connection string
- `ADMIN_USERNAME` / `ADMIN_PASSWORD_HASH` — Admin login
- `JWT_SECRET` — JWT signing key
- `AWS_REGION` — Bedrock region (eu-central-1)
- `NAIL_ANALYSIS_MODEL` — Bedrock model ID (eu.anthropic.claude-sonnet-4-6)

## Contact

- Instagram: [@kittynails_berlin](https://www.instagram.com/kittynails_berlin/)
- Address: Stallschreiberstraße 16, 10179 Berlin
