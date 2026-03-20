"""
debug_summary_error.py

Diagnóstico detallado del error 500 en /summary endpoint.
Este script intenta reproducir exactamente lo que hace el endpoint
y captura el error real para diagnóstico.
"""

import asyncio
import json
import sys
import uuid
from typing import Optional

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.database import Dashboard, Chat
from app.models.session import AsyncSessionLocal
from app.schemas.analysis import SummaryRequest
from app.services.ai.orchestrator import AIOrchestrator
from app.services.ai.summary_service import generate_executive_summary

logger = get_logger(__name__)


async def debug_database_state(dashboard_id: uuid.UUID) -> None:
    """Inspect the actual data in the dashboard."""
    print("\n" + "=" * 70)
    print("STEP 1: DATABASE STATE INSPECTION")
    print("=" * 70)

    async with AsyncSessionLocal() as session:
        dashboard = await session.get(Dashboard, dashboard_id)

        if not dashboard:
            print(f"❌ Dashboard not found: {dashboard_id}")
            return

        print(f"\n✓ Dashboard found: {dashboard_id}")
        print(f"  Chat ID: {dashboard.chat_id}")
        print(f"  KPI data type: {type(dashboard.kpi_data)}")
        print(f"  KPI data empty: {not dashboard.kpi_data}")

        if dashboard.kpi_data:
            print(f"  KPI data keys: {list(dashboard.kpi_data.keys())[:5]}...")
            print(f"  KPI data size: {len(str(dashboard.kpi_data))} bytes")

        print(f"\n  AI Insights type: {type(dashboard.ai_insights)}")
        print(f"  AI Insights empty: {not dashboard.ai_insights}")

        if dashboard.ai_insights:
            print(f"  AI Insights keys: {list(dashboard.ai_insights.keys())}")
            if "dataset_summary" in dashboard.ai_insights:
                summary = dashboard.ai_insights["dataset_summary"]
                print(f"  Dataset summary length: {len(summary)} chars")
                print(f"  Dataset summary preview: {summary[:100]}...")
            else:
                print("  ⚠️  No dataset_summary in ai_insights")


async def debug_endpoint_flow(dashboard_id: uuid.UUID) -> None:
    """Simulate the exact endpoint flow to find where it breaks."""
    print("\n" + "=" * 70)
    print("STEP 2: ENDPOINT FLOW SIMULATION (with error capture)")
    print("=" * 70)

    async with AsyncSessionLocal() as session:
        # Simulate _get_dashboard
        print("\n[1] Loading dashboard from database...")
        try:
            parsed_id = uuid.UUID(str(dashboard_id))
            dashboard = await session.get(Dashboard, parsed_id)

            if not dashboard:
                print(f"  ❌ Dashboard not found")
                return

            print(f"  ✓ Dashboard loaded")
        except Exception as e:
            print(f"  ❌ Error loading dashboard: {e}")
            import traceback
            traceback.print_exc()
            return

        # CRITICAL: Copy data while session is active
        print("\n[2] Copying ORM data to Python dicts...")
        try:
            kpi_payload = dict(dashboard.kpi_data or {})
            insights = dict(dashboard.ai_insights or {})
            dataset_summary = insights.get("dataset_summary", "").strip()

            print(f"  ✓ Data copied")
            print(f"    - KPI items: {len(kpi_payload)}")
            print(f"    - Insights keys: {list(insights.keys())}")
            print(f"    - Dataset summary: {len(dataset_summary)} chars")
        except Exception as e:
            print(f"  ❌ Error copying data: {e}")
            import traceback
            traceback.print_exc()
            return

        # Validation
        print("\n[3] Validating required data...")
        if not kpi_payload:
            print(f"  ❌ No KPI data - would return 422")
            return
        if not dataset_summary:
            print(f"  ❌ No dataset summary - would return 422")
            return
        print(f"  ✓ All required data present")

        # AI Generation
        print("\n[4] Calling AI orchestrator...")
        try:
            orchestrator = AIOrchestrator()

            # Build prompt
            from app.services.ai.prompts import build_executive_summary_prompt
            prompt = build_executive_summary_prompt(
                kpi_payload=kpi_payload,
                schema_summary=dataset_summary,
                user_objective="Analyze sales trends",
                user_structure=None,
                tags=None,
            )

            print(f"  - Prompt length: {len(prompt)} chars")
            print(f"  - Calling orchestrator.complete()...")

            summary = await generate_executive_summary(
                kpi_payload=kpi_payload,
                dataset_summary=dataset_summary,
                orchestrator=orchestrator,
                user_objective="Analyze sales trends",
                user_structure=None,
                tags=None,
            )

            print(f"  ✓ AI generation succeeded")
            print(f"    - Summary length: {len(summary)} chars")
            print(f"    - Provider: {orchestrator._selected_provider}")

        except Exception as e:
            print(f"  ❌ AI generation failed: {e}")
            import traceback
            traceback.print_exc()
            return

        # Persistence
        print("\n[5] Persisting changes...")
        try:
            insights["executive_summary"] = summary
            dashboard.ai_insights = insights
            await session.commit()
            print(f"  ✓ Changes committed")
        except Exception as e:
            await session.rollback()
            print(f"  ❌ Error persisting: {e}")
            import traceback
            traceback.print_exc()
            return

    print("\n" + "=" * 70)
    print("✅ ENDPOINT FLOW SUCCEEDED")
    print("=" * 70)


async def debug_http_endpoint(dashboard_id: str) -> None:
    """Test the HTTP endpoint directly to compare with flow simulation."""
    print("\n" + "=" * 70)
    print("STEP 3: HTTP ENDPOINT TEST (compare with flow simulation)")
    print("=" * 70)

    try:
        async with httpx.AsyncClient() as client:
            payload = {
                "dashboard_id": dashboard_id,
                "user_objective": "Analyze sales trends"
            }

            print(f"\nPOST http://localhost:8000/api/v1/summary")
            print(f"Payload: {json.dumps(payload, indent=2)}")

            response = await client.post(
                "http://localhost:8000/api/v1/summary",
                json=payload,
                timeout=10,
            )

            print(f"\nResponse Status: {response.status_code}")

            if response.status_code == 200:
                print("✅ ENDPOINT SUCCEEDED")
                data = response.json()
                summary = data.get("summary", "")
                print(f"Summary length: {len(summary)} chars")
                print(f"Preview: {summary[:200]}...")
            else:
                print(f"❌ ENDPOINT FAILED")
                print(f"Response: {response.text}")

    except Exception as e:
        print(f"❌ HTTP Error: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Run all diagnostic steps."""
    print("\n" + "🔍 " * 25)
    print("DEBUG: SUMMARY ENDPOINT ERROR DIAGNOSIS")
    print("🔍 " * 25)

    # Get dashboard ID from user
    dashboard_id = input("\nEnter dashboard ID to debug: ").strip()

    if not dashboard_id:
        print("No dashboard ID provided")
        sys.exit(1)

    try:
        parsed_id = uuid.UUID(dashboard_id)
    except ValueError:
        print(f"Invalid UUID: {dashboard_id}")
        sys.exit(1)

    # Run diagnostics
    await debug_database_state(parsed_id)
    await debug_endpoint_flow(parsed_id)
    await debug_http_endpoint(str(parsed_id))

    print("\n" + "=" * 70)
    print("DIAGNOSIS COMPLETE")
    print("=" * 70)
    print("\nSummary:")
    print("  - If STEP 1 shows missing data: Run /analyze first")
    print("  - If STEP 2 fails: Async/greenlet issue identified")
    print("  - If STEP 2 passes but STEP 3 fails: Endpoint middleware issue")
    print("  - If all pass: Issue is elsewhere (check uvicorn logs)")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
