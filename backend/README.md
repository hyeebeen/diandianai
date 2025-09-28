# DianDian Logistics API

AI-driven logistics management platform backend API service.

## Features

- FastAPI + Instructor AI framework
- Multi-tenant architecture with PostgreSQL Row-Level Security
- Real-time GPS tracking and route optimization
- AI-powered logistics assistant
- Celery async task processing

## Development

```bash
# Install dependencies
uv sync

# Run development server
uv run uvicorn src.main:app --reload

# Run migrations
uv run alembic upgrade head
```

## Technology Stack

- FastAPI
- SQLAlchemy + asyncpg
- PostgreSQL
- Celery + RabbitMQ
- Instructor AI
- Pydantic