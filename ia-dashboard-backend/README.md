# IA Dashboard – Backend

FastAPI backend for intelligent Excel/CSV analysis with AI-powered insights,
dynamic dashboard configuration, and executive summary generation.

## 🔐 Authentication

This backend uses **JWT authentication** via Supabase.

**Frontend must:**
1. Call `POST /api/v1/auth/login` with email and password to get JWT token
2. Include token in all protected endpoint requests: `Authorization: Bearer <token>`

⚠️ **If you're getting 401 Unauthorized errors:**
- See [AUTHENTICATION_SOLUTION.md](./docs/AUTHENTICATION_SOLUTION.md)
- See [FRONTEND_AUTH_GUIDE.md](./docs/FRONTEND_AUTH_GUIDE.md)
- See [IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md)
- Run test script: `python scripts/test_auth.py`

## Stack

- Python 3.11+
- FastAPI (async)
- Pandas + openpyxl
- Google Gemini 1.5 Flash (primary AI)
- OpenAI GPT-4o (fallback AI)
- PostgreSQL via Supabase
- Docker / GCP Cloud Run

## Local Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # fill in your keys
uvicorn app.main:app --reload
```

## Run Tests

```bash
pytest tests/ -v
```

## Project Structure

```
app/
  api/v1/endpoints/   # Route handlers
  core/               # Config, security, logging
  services/
    etl/              # File ingestion and cleaning
    ai/               # AI orchestration (Gemini + OpenAI fallback)
    dashboard/        # Chart config generation, KPI extraction
  models/             # SQLAlchemy ORM models
  schemas/            # Pydantic request/response schemas
  utils/              # Shared helpers
tests/
  unit/
  integration/
```
