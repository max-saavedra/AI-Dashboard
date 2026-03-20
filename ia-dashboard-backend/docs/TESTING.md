# API Testing Guide

## Overview

This guide explains how to test the two main endpoints:
- `/api/v1/analyze` - ETL pipeline (CSV upload + heuristic profiling + AI schema enrichment)
- `/api/v1/summary` - AI executive summary generation

## Prerequisites

1. **Environment Setup**
   ```bash
   # Activate virtual environment
   source venv/Scripts/activate  # On Windows
   # or
   . venv/bin/activate          # On Linux/Mac
   
   # Install dependencies
   pip install -r requirements.txt
   ```

2. **Environment Variables (.env)**
   ```env
   DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/ia_dashboard
   GEMINI_API_KEY=your_gemini_key_here
   OPENAI_API_KEY=your_openai_key_here (optional, backup)
   APP_DEBUG=true
   ```

3. **Database**
   ```bash
   # Verify database is running
   python verify_db_setup.py
   ```

## Running Tests

### 1. Start the API Server

```bash
uvicorn app.main:app --reload
```

Expected output:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

### 2. Run Comprehensive Tests

In a new terminal:

```bash
# Activate environment
source venv/Scripts/activate

# Run tests
python test_api_endpoints.py
```

## Expected Test Output

### Test 1: /analyze Endpoint

```
TEST 1: /analyze endpoint
======================================================================
📊 Uploading test CSV file...
Response Status: 200
✅ SUCCESS
Dashboard ID: a98b9080-e3d3-49f1-bdf1-3dbc3b135d5b
Rows Analyzed: 100
Columns: 5
First Column: date → Date
Sample KPIs: ['total_sales', 'avg_units', 'quarterly_comparison']
Charts Generated: 3
```

### Test 2: /summary Endpoint

```
TEST 2: /summary endpoint
======================================================================
📝 Generating summary for dashboard: a98b9080-e3d3-49f1-bdf1-3dbc3b135d5b
Response Status: 200
✅ SUCCESS
Summary Length: 1250 chars
Summary Preview: ## Executive Summary

The dataset shows strong sales trends...
```

## Troubleshooting

### Error: "greenlet_spawn has not been called"

**Cause**: SQLAlchemy async context issue - lazy loading after session closes

**Solutions**:
1. Ensure `expire_on_commit=False` in AsyncSessionLocal (✅ Already configured)
2. Copy all ORM data before session ends (✅ Already implemented)
3. Use `await db.commit()` not `await db.flush()` (✅ Already implemented)

### Error: "Dashboard has no KPI data"

**Cause**: /analyze didn't populate KPI data properly

**Solutions**:
1. Check ETL logs for errors
2. Verify file format is valid CSV
3. Ensure schema enrichment succeeded or fell back to heuristics

### Error: "429 Too Many Requests"

**Cause**: OpenAI/Gemini rate limit

**Solutions** (Already implemented):
1. Max 2 concurrent requests (throttling)
2. Automatic fallback: Gemini → OpenAI
3. Exponential backoff retry (3 attempts)
4. Reduced token usage (max_tokens=800)

### Error: "Cannot connect to API"

**Cause**: Server not running

**Solution**:
```bash
uvicorn app.main:app --reload
```

## Test Logs Location

Real-time logs visible in:
1. **Terminal where uvicorn is running**: HTTP requests + structlog output
2. **Database logs**: Check for "db_session_error" in output
3. **File logs**: `logs/app.log` (if file logging is configured)

## Key Metrics to Monitor

During `/analyze` request:
```
etl_completed duration_s=0.234 rows=100 columns=5
dataframe_profiled rows=100 columns=5
schema_enrichment_completed ai_enriched=true duration_s=0.845
analysis_completed duration_s=1.234
```

During `/summary` request:
```
summary_generation_request dashboard_id=... has_tags=false
ai_request_start provider=gemini
ai_request_success provider=gemini
summary_generation_completed provider=gemini summary_length=1250
```

## Advanced: Manual cURL Tests

### Test /analyze

```bash
# Create test CSV
cat > test.csv << EOF
date,sales,units,region,product
2024-01-01,1000,10,North,A
2024-01-02,1500,15,South,B
2024-01-03,1200,12,East,C
2024-01-04,1800,18,West,D
EOF

# Upload
curl -X POST http://localhost:8000/api/v1/analyze \
  -F "file=@test.csv" \
  -F "user_objective=Analyze sales trends" \
  -F "tags=sales,revenue"
```

### Test /summary

```bash
# Replace DASHBOARD_ID with value from /analyze response
curl -X POST http://localhost:8000/api/v1/summary \
  -H "Content-Type: application/json" \
  -d '{
    "dashboard_id": "DASHBOARD_ID",
    "user_objective": "Focus on sales growth",
    "tags": ["sales"]
  }'
```

## Performance Baseline

Expected times (after optimization):
- `/analyze` with 100-row CSV: 1.0-1.5s
- `/summary` with Gemini: 0.5-1.0s
- `/summary` with OpenAI fallback: 1.0-2.0s

Token usage reduction:
- Schema detection: 60-65% reduction
- Executive summary: 40-45% reduction
- Total payload: 60% reduction

## CI/CD Integration

For automated testing in pipelines:

```bash
#!/bin/bash
# Start server in background
uvicorn app.main:app &
SERVER_PID=$!

# Wait for startup
sleep 2

# Run tests
python test_api_endpoints.py
TEST_RESULT=$?

# Cleanup
kill $SERVER_PID

exit $TEST_RESULT
```
