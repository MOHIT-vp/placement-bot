# Deployment — Placement Readiness & Career Intelligence Portal

## 1. Container Architecture

```yaml
# docker-compose.yml
services:
  postgres:
    image: pgvector/pgvector:pg16
    ports: ["5432:5432"]
    volumes: [postgres_data:/var/lib/postgresql/data]
    environment:
      POSTGRES_DB: placement_portal
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    healthcheck:
      test: pg_isready -U ${DB_USER}

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
    healthcheck:
      test: redis-cli ping

  backend:
    build: ./backend
    ports: ["8000:8000"]
    depends_on:
      postgres: { condition: service_healthy }
      redis: { condition: service_healthy }
    environment:
      DATABASE_URL: postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@postgres:5432/placement_portal
      REDIS_URL: redis://redis:6379/0
      SECRET_KEY: ${SECRET_KEY}
      LLM_API_KEY: ${LLM_API_KEY}
      CORS_ORIGINS: http://localhost:3000
    volumes:
      - uploads:/app/uploads

  celery-worker:
    build: ./backend
    command: celery -A app.worker worker -l info
    depends_on: [postgres, redis, backend]
    environment: # Same as backend

  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    depends_on: [backend]
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000/api/v1

volumes:
  postgres_data:
  uploads:
```

---

## 2. Environment Configuration

### .env.example
```bash
# Database
DB_USER=placement_user
DB_PASSWORD=change_me_in_production
DB_NAME=placement_portal

# Security
SECRET_KEY=change-this-to-64-char-random-string
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# LLM
LLM_PROVIDER=google  # or openai
LLM_API_KEY=your-api-key-here
LLM_MODEL=gemini-1.5-flash  # or gpt-4o-mini

# Redis
REDIS_URL=redis://redis:6379/0

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

# CORS
CORS_ORIGINS=http://localhost:3000

# File uploads
MAX_UPLOAD_SIZE_MB=5
UPLOAD_DIR=/app/uploads

# Agent config
MAX_RETRIES=3
TOKEN_BUDGET=100000
RUN_TIMEOUT_SECONDS=300
```

---

## 3. Build & Run

### Development
```bash
# Start services
docker-compose up -d postgres redis

# Backend (local)
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
python scripts/seed_mock_data.py
uvicorn app.main:app --reload --port 8000

# Frontend (local)
cd frontend
npm install
npm run dev

# Celery worker (local)
celery -A app.worker worker -l info
```

### Docker (full stack)
```bash
cp .env.example .env  # Edit with real values
docker-compose up --build -d
docker-compose exec backend alembic upgrade head
docker-compose exec backend python scripts/seed_mock_data.py
```

---

## 4. Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

---

## 5. Health Checks

| Service | Endpoint | Expected |
|---------|----------|----------|
| Backend API | `GET /api/v1/admin/system/health` | `{"status": "healthy"}` |
| PostgreSQL | `pg_isready` | Exit code 0 |
| Redis | `redis-cli ping` | `PONG` |
| Frontend | `GET /` | HTTP 200 |

---

## 6. Monitoring & Logging

### Structured Logging
```python
import structlog

logger = structlog.get_logger()
logger.info("agent_executed",
    run_id=run_id,
    agent="resume_agent",
    duration_ms=1234,
    token_usage={"prompt": 500, "completion": 200}
)
```

### Observability
- Every workflow has a `run_id` and `correlation_id`
- Full trace from Coordinator → Agents → Validation → Approval → Publish
- Agent execution metrics in `agent_executions` table
- Token usage tracked per agent per run

---

## 7. Backup & Recovery

- PostgreSQL: Daily pg_dump (configurable via cron)
- File uploads: Volume backup
- Redis: RDB snapshots (configured in redis.conf)
- All backups exclude secrets
