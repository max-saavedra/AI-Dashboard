"""
analyze_summary_request.py

Real-time analyzer for /summary endpoint requests.
Logs request/response details to help diagnose async errors.

Usage:
    1. Start the API server (uvicorn app.main:app --reload)
    2. Run this analyzer in another terminal: python analyze_summary_request.py
    3. Make POST requests to /summary
    4. Watch the analyzer output for greenlet/async issues
"""

import asyncio
import json
import logging
import sys
import time
from datetime import datetime

import httpx

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# En analyze_summary_request.py
API_BASE = "http://127.0.0.1:8000/api/v1"  # Cambia localhost por 127.0.0.1
HEALTH_ENDPOINT = f"{API_BASE}/health"
ANALYZE_ENDPOINT = f"{API_BASE}/analyze"
SUMMARY_ENDPOINT = f"{API_BASE}/summary"


async def check_api_health():
    """Verify API is running."""
    print("\n" + "=" * 70)
    print("PRE-FLIGHT CHECKS")
    print("=" * 70)

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(HEALTH_ENDPOINT, timeout=5)
            if response.status_code == 200:
                print(f"✅ API is running at {API_BASE}")
                return True
            else:
                print(f"❌ API returned {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ Cannot reach API: {e}")
        print(f"   Make sure uvicorn is running: uvicorn app.main:app --reload")
        return False


async def create_test_dashboard():
    """Create a test dashboard by uploading CSV."""
    print("\n" + "=" * 70)
    print("CREATING TEST DATA")
    print("=" * 70)

    # Use existing test CSV file
    csv_path = "test_data_dirty.csv"

    try:
        with open(csv_path, "rb") as f:
            csv_content = f.read()
        print(f"✓ Loaded CSV from {csv_path} ({len(csv_content)} bytes)")
    except FileNotFoundError:
        print(f"❌ CSV file not found: {csv_path}")
        return None

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            # Files parameter should use tuple format
            files = {"file": ("test_data_dirty.csv", csv_content, "text/csv")}
            data = {
                "name": "Test Dashboard",
            }

            print(f"Uploading CSV to {ANALYZE_ENDPOINT}...")
            print(f"  - File: test_data_dirty.csv")
            print(f"  - Size: {len(csv_content)} bytes")

            start_time = time.time()

            response = await client.post(
                ANALYZE_ENDPOINT,
                files=files,
                data=data,
            )

            elapsed = time.time() - start_time
            print(f"\nResponse status: {response.status_code}")
            print(f"Response time: {elapsed:.2f}s")

            if response.status_code == 200:
                resp_data = response.json()
                dashboard_id = resp_data.get("dashboard_id")
                print(f"✅ Dashboard created: {dashboard_id}")
                return dashboard_id
            else:
                print(f"❌ Failed to create dashboard")
                print(f"Status: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"Error: {error_data}")
                except:
                    print(f"Response: {response.text[:500]}")
                return None
    except Exception as e:
        print(f"❌ Error uploading CSV: {e}")
        import traceback
        traceback.print_exc()
        return None
        return None

    except Exception as e:
        print(f"❌ Error: {e}")
        return None


async def test_summary_endpoint(dashboard_id: str):
    """Test the /summary endpoint and capture details."""
    print("\n" + "=" * 70)
    print("TESTING SUMMARY ENDPOINT")
    print("=" * 70)

    payload = {
        "dashboard_id": dashboard_id,
        "user_objective": "Analyze sales performance and trends",
    }

    print(f"\nRequest Details:")
    print(f"  Endpoint: POST {SUMMARY_ENDPOINT}")
    print(f"  Payload: {json.dumps(payload, indent=2)}")

    try:
        async with httpx.AsyncClient() as client:
            print(f"\nSending request...")
            start_time = time.time()

            response = await client.post(
                SUMMARY_ENDPOINT,
                json=payload,
                timeout=120,
            )

            elapsed = time.time() - start_time

            print(f"\n✓ Request completed in {elapsed:.2f}s")
            print(f"\nResponse Details:")
            print(f"  Status Code: {response.status_code}")
            print(f"  Headers: {dict(response.headers)}")

            if response.status_code == 200:
                data = response.json()
                print(f"\n✅ SUCCESS - Summary generated")
                print(f"  Summary preview: {data.get('summary', '')[:200]}...")
                return True

            elif response.status_code == 422:
                print(f"\n⚠️  422 - Missing required data")
                print(f"  Detail: {response.json().get('detail')}")
                print(f"  This is expected if analysis didn't generate KPIs")
                return False

            elif response.status_code == 503:
                print(f"\n⚠️  503 - AI provider unavailable")
                print(f"  Detail: {response.json().get('detail')}")
                print(f"  This is expected if API keys are invalid")
                return False

            elif response.status_code == 500:
                print(f"\n❌ 500 - Internal Server Error")
                print(f"  Response: {response.text[:500]}")
                print(f"\n  This might be the greenlet_spawn error!")
                print(f"  Check logs for: 'greenlet_spawn has not been called'")
                return False

            else:
                print(f"\n❓ Unexpected status code")
                print(f"  Response: {response.text[:500]}")
                return False

    except asyncio.TimeoutError:
        print(f"\n❌ Request timeout (30s)")
        print(f"  The endpoint took too long to respond")
        return False

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def analyze_request_flow():
    """Analyze the complete endpoint flow."""
    print("\n" + "=" * 70)
    print("FLOW ANALYSIS")
    print("=" * 70)

    print("""
The /summary endpoint flow:

1. [FastAPI] Receive POST request with dashboard_id
   ↓
2. [Dependency] Get database session (AsyncSession)
   ↓
3. [Database] Load Dashboard ORM object
   ↓
4. [CRITICAL] Copy ORM data to Python dicts:
   - kpi_payload = dict(dashboard.kpi_data or {})
   - insights = dict(dashboard.ai_insights or {})
   ↓
5. [Validation] Check KPI and dataset_summary are present
   ↓
6. [AI] Call orchestrator.complete() - LONG ASYNC OPERATION (1-5s)
   - Provider: Gemini (primary) or OpenAI (fallback)
   - Token cost: ~2000-3000 tokens (optimized from 8000)
   ↓
7. [Persistence] Update dashboard.ai_insights with summary
   ↓
8. [Transaction] await db.commit()  ← CRITICAL: NOT flush()
   ↓
9. [Response] Return SummaryResponse with generated summary

KEY POINTS:
✓ Data copied at step 4 (while session is active)
✓ Commit at step 8 (not flush)
✓ No ORM field access after step 6 (async operation)
✓ Result: No greenlet_spawn errors, 200 OK response
    """)


async def run_interactive_mode():
    """Interactive mode for testing."""
    print("\n" + "=" * 70)
    print("INTERACTIVE MODE")
    print("=" * 70)

    while True:
        print("\nOptions:")
        print("  1. Create test dashboard")
        print("  2. Test summary endpoint")
        print("  3. Show flow analysis")
        print("  4. Exit")

        choice = input("Select option (1-4): ").strip()

        if choice == "1":
            dashboard_id = await create_test_dashboard()
            if dashboard_id:
                # Save for next test
                with open(".test_dashboard_id", "w") as f:
                    f.write(dashboard_id)

        elif choice == "2":
            # Try to load saved dashboard_id
            try:
                with open(".test_dashboard_id", "r") as f:
                    dashboard_id = f.read().strip()
            except FileNotFoundError:
                dashboard_id = input("Enter dashboard ID: ").strip()

            if dashboard_id:
                await test_summary_endpoint(dashboard_id)

        elif choice == "3":
            await analyze_request_flow()

        elif choice == "4":
            print("\nGoodbye!")
            break

        else:
            print("Invalid option")


async def main():
    """Run the analyzer."""
    print("\n" + "🔍 " * 20)
    print("API REQUEST ANALYZER - /summary ENDPOINT")
    print("🔍 " * 20)

    # Check health
    if not await check_api_health():
        print("\nExiting: API not available")
        sys.exit(1)

    # Run tests
    dashboard_id = await create_test_dashboard()

    if not dashboard_id:
        print("\n⚠️  Could not create test dashboard")
        print("   Proceeding to interactive mode for manual testing")
    else:
        # Test endpoint
        success = await test_summary_endpoint(dashboard_id)

        if success:
            print("\n" + "=" * 70)
            print("✅ ALL CHECKS PASSED")
            print("=" * 70)
            print("\nConclusions:")
            print("  • No greenlet_spawn errors detected")
            print("  • /summary endpoint is working correctly")
            print("  • AI provider successfully generated summary")
        else:
            print("\n" + "=" * 70)
            print("⚠️  TEST COMPLETED WITH ISSUES")
            print("=" * 70)

    # Offer interactive mode
    print("\n")
    if input("Enable interactive mode? (y/n): ").lower() == "y":
        await run_interactive_mode()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
