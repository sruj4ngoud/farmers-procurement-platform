Alembic migrations for the farmer procurement PostgreSQL schema.

From `backend/`:

    alembic upgrade head
    alembic downgrade -1
    alembic revision --autogenerate -m "describe change"

`DATABASE_URL` must be set in the environment or a local `.env` file.
The checked-in `alembic.ini` URL is a placeholder only.
