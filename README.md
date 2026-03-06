# Nail Appointment App 💅

A booking app for a nail business where clients can browse available time slots and book appointments. Built as a learning project to explore Python, FastAPI, and Pydantic.

## Tech Stack

- **FastAPI** — Web framework with automatic API docs
- **Pydantic** — Data validation and modeling
- **SQLAlchemy** — ORM for database interactions
- **SQLite** — Lightweight database (no setup needed)

## Getting Started

```bash
# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the dev server
fastapi dev src/main.py
```

Once running, visit `http://127.0.0.1:8000/docs` for the interactive API documentation.

## Project Structure

```
src/
├── main.py          # App entry point
├── models/          # Pydantic schemas (validation)
├── routers/         # API endpoints
├── services/        # Business logic
└── db/              # Database models and connection
tests/               # Test suite
```

## Features

- Browse available nail services
- View open appointment slots by date
- Book and cancel appointments
- Owner manages services, availability, and blocked times
