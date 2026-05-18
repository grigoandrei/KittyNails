# KityNails 💅

A nail appointment booking application. Clients browse services, view available time slots, and book appointments with minimal friction. The nail artist manages everything through an admin panel.

## Tech Stack

- **Backend**: FastAPI (Python 3.12)
- **Database**: PostgreSQL + SQLAlchemy (async)
- **Validation**: Pydantic v2
- **Migrations**: Alembic
- **Email**: Gmail SMTP (aiosmtplib)
- **Notifications**: Telegram Bot API
- **Testing**: PyTest + Hypothesis (property-based testing)
- **CI/CD**: GitHub Actions
- **Containerization**: Docker
- **Deployment**: AWS ECS (backend), S3 + CloudFront (frontend)

## Architecture

```
┌─────────────────┐     ┌──────────────────────┐     ┌────────────────┐
│  React Frontend │────▶│  FastAPI Backend      │────▶│  PostgreSQL DB │
│  (S3+CloudFront)│     │  (ECS Container)      │     │                │
└─────────────────┘     └──────────────────────┘     └────────────────┘
                              │          │
                              ▼          ▼
                        ┌──────────┐ ┌──────────────┐
                        │Gmail SMTP│ │Telegram Bot  │
                        └──────────┘ └──────────────┘
```

## Local Development

### Prerequisites

- Python 3.12+
- Docker & Docker Compose

### Setup

```bash
# Clone the repo
git clone <repo-url>
cd KityNails

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
├── main.py                    # FastAPI app entry point
├── config.py                  # Settings (Pydantic BaseSettings)
├── database.py                # SQLAlchemy engine + session
├── models/                    # SQLAlchemy models
├── schemas/                   # Pydantic request/response schemas
├── routers/                   # API route handlers
│   └── admin/                 # Admin-only endpoints
├── services/                  # Business logic layer
├── dependencies.py            # FastAPI dependencies (auth, DB)
└── utils/                     # Helpers (sanitization, validation)
```

## API Overview

### Public Endpoints

| Method | Path                         | Description                  |
|--------|------------------------------|------------------------------|
| GET    | /api/services                | List active services         |
| GET    | /api/slots?service_id=&date= | Get available slots for date |
| GET    | /api/slots/dates?service_id= | Get dates with availability  |
| POST   | /api/appointments            | Book an appointment          |

### Admin Endpoints (API key required)

| Method | Path                                 | Description              |
|--------|--------------------------------------|--------------------------|
| POST   | /api/admin/services                  | Create service           |
| PUT    | /api/admin/services/{id}             | Update service           |
| POST   | /api/admin/availability-rules        | Create availability rule |
| DELETE | /api/admin/availability-rules/{id}   | Delete availability rule |
| POST   | /api/admin/blocked-times             | Block a time range       |
| GET    | /api/admin/appointments              | List upcoming bookings   |
| PATCH  | /api/admin/appointments/{id}/cancel  | Cancel appointment       |
| PATCH  | /api/admin/appointments/{id}/no-show | Mark as no-show          |

## Environment Variables

See `.env.example` for the full list. Key variables:

- `DATABASE_URL` — PostgreSQL connection string
- `ADMIN_API_KEY` — API key for admin endpoints
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD` — Gmail SMTP config
- `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` — Telegram notifications
- `INSTAGRAM_HANDLE` — For cancellation instructions
