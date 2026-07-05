FROM python:3.12-slim

RUN useradd -m appuser

WORKDIR /app

COPY pyproject.toml .
COPY src/ ./src/
RUN pip install --no-cache-dir .

COPY alembic/ ./alembic/
COPY alembic.ini .

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/')"

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]