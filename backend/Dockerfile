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

# Writable root for the local media provider (MEDIA_LOCAL_ROOT=./media). This
# filesystem is ephemeral; production rejects local media and must use a durable
# provider (see docs/security.md and ADR-0014).
RUN mkdir -p /app/media && chown app:app /app/media

USER app

CMD ["python", "-m", "scripts.start"]
