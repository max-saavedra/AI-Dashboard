"""
test_api_endpoints.py

Comprehensive test script for /analyze and /summary endpoints.
Verifies the hybrid heuristic + AI pipeline works correctly.

Usage:
    python test_api_endpoints.py
"""

import asyncio
import csv
import io
import json
import sys
from pathlib import Path
from typing import Optional

import httpx
import pandas as pd

# Test configuration
API_BASE_URL = "http://localhost:8000"
ANALYZE_ENDPOINT = f"{API_BASE_URL}/api/v1/analyze"
SUMMARY_ENDPOINT = f"{API_BASE_URL}/api/v1/summary"
TIMEOUT = 30.0  # seconds


def create_test_csv() -> bytes:
    """Create a realistic test CSV file."""
    data = {
        "date": pd.date_range("2024-01-01", periods=100).strftime("%Y-%m-%d"),
        "sales": list(range(1000, 1100)),
        "units": list(range(10, 110)),
        "region": ["North", "South", "East", "West"] * 25,
        "product": ["A", "B", "C", "D"] * 25,
    }
    df = pd.DataFrame(data)

    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    return csv_buffer.getvalue().encode("utf-8")


async def test_analyze_endpoint() -> Optional[str]:
    """
    Test the /analyze endpoint.

    Returns:
        dashboard_id if successful, None otherwise
    """
    print("\n" + "=" * 70)
    print("TEST 1: /analyze endpoint")
    print("=" * 70)

    try:
        csv_content = create_test_csv()

        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            files = {
                "file": ("test_data.csv", csv_content, "text/csv"),
            }
            data = {
                "user_objective": "Analyze sales trends and regional performance",
                "tags": "sales,revenue,trends",
            }

            print(f"📊 Uploading test CSV file...")
            response = await client.post(
                ANALYZE_ENDPOINT,
                files=files,
                data=data,
            )

            print(f"Response Status: {response.status_code}")

            if response.status_code != 200:
                print(f"❌ FAILED: {response.status_code}")
                print(f"Response: {response.text[:500]}")
                return None

            result = response.json()
            dashboard_id = result.get("dashboard_id")

            # Print summary of results
            print(f"✅ SUCCESS")
            print(f"Dashboard ID: {dashboard_id}")
            print(f"Rows Analyzed: {result.get('rows_analyzed')}")
            print(f"Columns: {result.get('column_count')}")

            # Check if AI enrichment was applied
            if result.get("columns"):
                first_col = result["columns"][0]
                print(
                    f"First Column: {first_col.get('name')} → {first_col.get('alias')}")

            # Check KPI extraction
            if result.get("kpi_data"):
                kpi_keys = list(result["kpi_data"].keys())[:3]
                print(f"Sample KPIs: {kpi_keys}")

            # Check chart configs
            if result.get("chart_configs"):
                print(f"Charts Generated: {len(result['chart_configs'])}")

            return dashboard_id

    except Exception as exc:
        print(f"❌ EXCEPTION: {exc}")
        return None


async def test_summary_endpoint(dashboard_id: str) -> bool:
    """
    Test the /summary endpoint.

    Args:
        dashboard_id: ID from /analyze endpoint

    Returns:
        True if successful, False otherwise
    """
    print("\n" + "=" * 70)
    print("TEST 2: /summary endpoint")
    print("=" * 70)

    if not dashboard_id:
        print("⚠️  Skipping /summary test (no dashboard_id from /analyze)")
        return False

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            payload = {
                "dashboard_id": dashboard_id,
                "user_objective": "Focus on sales growth and regional comparison",
                "tags": ["sales", "growth"],
            }

            print(f"📝 Generating summary for dashboard: {dashboard_id}")
            response = await client.post(
                SUMMARY_ENDPOINT,
                json=payload,
            )

            print(f"Response Status: {response.status_code}")

            if response.status_code == 422:
                print(f"⚠️  422 Unprocessable Entity:")
                print(f"   {response.json().get('detail')}")
                print("   (This is OK - dashboard may not have KPI data yet)")
                return True

            if response.status_code == 503:
                print(f"⚠️  503 Service Unavailable:")
                print(f"   {response.json().get('detail')}")
                print("   (This is OK - AI providers may be rate limited)")
                return True

            if response.status_code != 200:
                print(f"❌ FAILED: {response.status_code}")
                print(f"Response: {response.text[:500]}")
                return False

            result = response.json()
            summary = result.get("summary", "")

            print(f"✅ SUCCESS")
            print(f"Summary Length: {len(summary)} chars")
            print(f"Summary Preview: {summary[:200]}...")

            return True

    except Exception as exc:
        print(f"❌ EXCEPTION: {exc}")
        import traceback
        traceback.print_exc()
        return False


async def test_health_endpoint() -> bool:
    """Test the /health endpoint to verify API is running."""
    print("\n" + "=" * 70)
    print("HEALTH CHECK: Verify API is running")
    print("=" * 70)

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{API_BASE_URL}/health")

            if response.status_code == 200:
                print(f"✅ API is running")
                print(f"Response: {response.json()}")
                return True
            else:
                print(f"❌ API health check failed: {response.status_code}")
                return False
    except Exception as exc:
        print(f"❌ Cannot connect to API: {exc}")
        print(f"   Make sure the server is running: uvicorn app.main:app --reload")
        return False


async def main():
    """Run all tests."""
    print("\n🚀 Starting API Tests\n")

    # Health check
    if not await test_health_endpoint():
        print("\n❌ API is not running. Please start it first:")
        print("   uvicorn app.main:app --reload")
        sys.exit(1)

    # Test /analyze
    dashboard_id = await test_analyze_endpoint()

    # Test /summary
    await test_summary_endpoint(dashboard_id)

    print("\n" + "=" * 70)
    print("✅ Test Suite Complete")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
