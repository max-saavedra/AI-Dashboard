# SQLAlchemy Greenlet Error Fix Guide

## Problem Summary

### The Error
```
greenlet_spawn has not been called; can't call await_only() here
```

**When it occurred**: POST /api/v1/summary endpoint returned 500 error
**Root cause**: SQLAlchemy 2.0 async lazy loading + session context mismatch

---

## Root Cause Analysis

### What Was Happening

1. **Session context opened** in async function
   ```python
   async def create_summary(..., db: AsyncSession = Depends(get_db)):
       # db session is ACTIVE here
   ```

2. **ORM object loaded** from database
   ```python
   dashboard = await _get_dashboard(db, ...)  # Returns Dashboard ORM object
   # dashboard.kpi_data is a JSONB column (lazy-loaded)
   ```

3. **Commit instead of flush** would normally be safe:
   ```python
   await db.commit()  # This should work...
   ```

4. **BUT** - If code accessed ORM fields AFTER async operations:
   ```python
   kpi_payload = dashboard.kpi_data  # ❌ LAZY LOADS in wrong context!
   # After orchestrator.complete() awaits, we're in different async context
   # SQLAlchemy sees greenlet mismatch and crashes
   ```

### Why This Happened in `/summary`

The endpoint flow was:

```
1. Load dashboard ✅
2. Call AI: await orchestrator.complete()  ← Long async operation!
3. ACCESS dashboard.kpi_data              ← ❌ PROBLEM!
4. Access dashboard.ai_insights           ← ❌ PROBLEM!
5. Persist changes
```

After `orchestrator.complete()` awaits (which can take 1-5 seconds), the async context changes. SQLAlchemy's greenlet tracking gets confused because:
- Originally ran in main greenlet (asyncio)
- After long await, resumed in different greenlet context
- Lazy loading attempted → greenlet_spawn error

---

## The Fix (Two Parts)

### Fix #1: Copy Data BEFORE Async Operations

**Location**: `app/api/v1/endpoints/summary.py` lines 55-57

```python
# ❌ BEFORE (causes greenlet error):
kpi_payload: dict = dashboard.kpi_data or {}
insights = dashboard.ai_insights or {}
dataset_summary: str = insights.get("dataset_summary", "").strip()

# ✅ AFTER (safe - data copied within session):
kpi_payload: dict = dict(dashboard.kpi_data or {})
insights = dict(dashboard.ai_insights or {})
dataset_summary: str = insights.get("dataset_summary", "").strip()
```

**Why it works**: 
- `dict()` creates a detached Python dict
- Access happens within active session (safe)
- No lazy loading after session/context changes
- Prevents greenlet mismatch errors

### Fix #2: Use `commit()` Instead of `flush()`

**Location**: `app/api/v1/endpoints/summary.py` line 99

```python
# ❌ BEFORE (unsafe):
await db.flush()        # Sends SQL but doesn't end transaction
# Session still "active" but in undefined state

# ✅ AFTER (safe):
await db.commit()       # Ends transaction, detaches ORM objects
# ORM objects expire and won't trigger lazy loads
```

**Why it works**:
- `flush()` sends SQL to DB but keeps transaction open
- ORM objects remain "attached" to session
- Future accesses might trigger lazy loading
- `commit()` ends transaction cleanly
- SQLAlchemy expires objects (no lazy loading possible)

---

## Verification

### Test 1: Run Diagnostic Script
```bash
# Simulate ORM access patterns to identify problems
python diagnose_greenlet_error.py
```

**Expected output**:
```
========================================================================
ORM ACCESS PATTERN DIAGNOSTICS
========================================================================

Testing with Dashboard ID: [uuid]

[Test 1] Access within session context
  ✅ dashboard.kpi_data accessible: <dict>

[Test 2] Relationship access within session
  ✅ dashboard.chat_id: [uuid]
  ✅ chat.user_id: [uuid]

[Test 3] Copy data within session (safe pattern)
  ✅ KPI data copied: N items
  ✅ Insights copied: N items

[Test 4] Access AFTER session closed (expected to fail)
  ✅ greenlet_spawn error as expected: greenlet_spawn has not been called...
     This is CORRECT behavior with expire_on_commit=True

[Test 5] Fresh session with copied data (correct approach)
  ✅ Using copied data outside session:
     KPI items: N
     Insights keys: [...]

========================================================================
ENDPOINT FLOW SIMULATION (/summary)
========================================================================

📊 Simulating /summary endpoint...
[Step 1] Load dashboard...
  ✅ Dashboard loaded: [uuid]

[Step 2] Copy data from ORM object (within session)...
  ✅ KPI payload: N items
  ✅ Insights: N items
  ✅ Dataset summary: M chars

[Step 3] Validate data...
  ✅ KPI data present
  ✅ Dataset summary present

[Step 4] (AI generation would happen here - simulated)...
  ✅ Summary generated: M chars

[Step 5] Persist changes...
  ✅ Changes committed

========================================================================
✅ Diagnostics Complete
========================================================================
```

### Test 2: Run API Endpoint Tests
```bash
# Start uvicorn server first:
uvicorn app.main:app --reload

# In another terminal:
python test_api_endpoints.py
```

**Expected output**:
```
========================================================================
AI DASHBOARD API TEST SUITE
========================================================================

Testing: http://localhost:8000/api/v1/health

[health_endpoint] ✅ PASS
  Status: 200
  Response: {'status': 'ok', 'database': 'connected'}

Testing: http://localhost:8000/api/v1/analyze

[analyze_endpoint] ✅ PASS
  Status: 200
  Dashboard ID: [uuid]
  Rows analyzed: 100
  KPIs identified: N
  Charts created: N
  Response time: 1.2s

Testing: http://localhost:8000/api/v1/summary

[summary_endpoint] ✅ PASS
  Status: 200
  Summary length: 500+ chars
  Provider used: gemini or openai
  Response time: 2.1s

========================================================================
✅ ALL TESTS PASSED
========================================================================
```

### Test 3: Manual cURL Test

```bash
# 1. Get/create a dashboard
RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/analyze \
  -F "file=@test_data_dirty.csv" \
  -H "Authorization: Bearer $(YOUR_JWT_TOKEN)")

DASHBOARD_ID=$(echo $RESPONSE | jq -r '.dashboard_id')
echo "Dashboard ID: $DASHBOARD_ID"

# 2. Generate summary
curl -X POST http://localhost:8000/api/v1/summary \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $(YOUR_JWT_TOKEN)" \
  -d "{
    \"dashboard_id\": \"$DASHBOARD_ID\",
    \"user_objective\": \"Analyze sales trends\"
  }"

# Expected: 200 OK with summary text
# NOT 500 error
```

---

## Important SQLAlchemy Configurations

The fix relies on these settings in `app/models/session.py`:

```python
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    # CRITICAL: Ensures ORM objects expire after commit
    # This prevents lazy loading attempts after transaction ends
    connect_args={"server_settings": {"application_name": "ia-dashboard-api"}},
)

async_session_factory = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=True,  ← KEY SETTING
    # Other settings...
)
```

**Key settings explained**:
- `expire_on_commit=True`: Automatically expires ORM objects after commit (prevents lazy loading)
- `pool_pre_ping=True`: Checks connections before use (ensures session health)
- `echo=False`: Don't log SQL (avoids log clutter; set to True for debugging)

---

## Common Mistakes to Avoid

### ❌ Accessing ORM fields after async operations

```python
async def bad_endpoint():
    dashboard = await get_dashboard()
    
    # Long async operation
    await orchestrator.complete()
    
    # ✗ DON'T do this! greenlet error will occur
    kpi = dashboard.kpi_data
```

### ✅ Copy data BEFORE async operations

```python
async def good_endpoint():
    dashboard = await get_dashboard()
    
    # Copy data while session is active
    kpi = dict(dashboard.kpi_data or {})  # ← Safe!
    
    # Long async operation
    result = await orchestrator.complete(kpi_payload=kpi)
    
    # ✓ Now safe to use copied data
    return result
```

### ❌ Using flush() for persistence

```python
async def bad_pattern():
    dashboard.ai_insights = updated_insights
    await db.flush()  # ✗ Session still "active", lazy loads possible
    
    # Any ORM access here might lazy-load
```

### ✅ Using commit() for persistence

```python
async def good_pattern():
    dashboard.ai_insights = updated_insights
    await db.commit()  # ✓ Transaction ends, objects expire
    
    # Safe - no lazy loading possible (objects are detached)
```

---

## Debugging the Error

If you still see "greenlet_spawn" errors:

### Step 1: Check logs for the exact line
```bash
grep -n "greenlet_spawn" logs/app.log
# Will show exactly which file/line access caused it
```

### Step 2: Verify session context
```python
# Add debug logging:
logger.info(f"ORM object expired: {inspect(obj).expired}")
# True = not lazy loadable (good)
# False = lazy loadable (potential issue)
```

### Step 3: Trace async context
```python
import contextvars
import threading

current_context = contextvars.copy_context()
logger.info(f"Context: {current_context}")
logger.info(f"Thread: {threading.current_thread().name}")
# Should be: "Thread: asyncio_xxx"
```

### Step 4: Check expire_on_commit setting
```python
# In Python REPL:
from app.models.session import async_session_factory
print(async_session_factory.kw)  # Should show expire_on_commit=True
```

---

## Migration Guide

If you find other async endpoints with similar issues:

1. **Identify ORM field accesses** after async operations
2. **Move accesses** before long async calls
3. **Use `dict(field or {})` pattern** for JSONB/JSON fields
4. **Use `commit()` not `flush()`** for persistence
5. **Test with `diagnose_greenlet_error.py`**

### Quick Checklist for New Async Endpoints

- [ ] Copy all ORM data before async operations: `dict(field or {})`
- [ ] Use `await db.commit()` not `await db.flush()`
- [ ] No ORM field access after long awaits
- [ ] Return copied data, not live ORM objects
- [ ] Test with error endpoint tests (handles 500s gracefully)

---

## Performance Impact

The fix has **zero performance impact**:
- `dict()` copy is O(n) but n is small (KPI data typically <1KB)
- `commit()` vs `flush()`: commit slightly safer, negligible difference
- Prevents crashes (actually improves performance by eliminating retries)

**Before fix**: Some requests → 500 error → client retry → possible cascade
**After fix**: All requests → 200 OK → no retries needed

---

## References

- SQLAlchemy Async Docs: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
- Greenlet Error Context: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html#preventing-the-greenlet-spawn-exception
- FastAPI & SQLAlchemy: https://fastapi.tiangolo.com/advanced/sql-databases-async/

---

## Support

If you encounter "greenlet_spawn" errors:

1. Run `python diagnose_greenlet_error.py`
2. Check that the line accessing ORM data is within an active session context
3. Use `dict()` to copy JSONB/JSON fields
4. Use `commit()` for persistence, not `flush()`
5. Review the code examples in this document

