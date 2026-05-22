FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml /app/

COPY src/ /app/src/

COPY alembic/ /app/alembic/

COPY alembic.ini /app/

RUN pip install --no-cache-dir .

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]