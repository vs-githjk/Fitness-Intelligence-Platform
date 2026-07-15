FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml .
COPY app ./app
RUN pip install --no-cache-dir . \
    && addgroup --system app \
    && adduser --system --ingroup app --home /app app

COPY --chown=app:app alembic.ini .
COPY --chown=app:app alembic ./alembic
COPY --chown=app:app scripts ./scripts

USER app

CMD ["python", "-m", "scripts.start"]
