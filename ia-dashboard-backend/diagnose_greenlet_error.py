"""
diagnose_greenlet_error.py

Diagnoses SQLAlchemy async greenlet_spawn errors.
Simulates the /summary endpoint flow to identify where the error occurs.
"""

import asyncio
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import Dashboard, Chat
from app.models.session import AsyncSessionLocal
from app.core.logging import get_logger

logger = get_logger(__name__)


async def test_orm_access_patterns():
    """Test different ORM access patterns to find the problematic one."""

    print("\n" + "=" * 70)
    print("ORM ACCESS PATTERN DIAGNOSTICS")
    print("=" * 70)

    # Create a test dashboard for testing (if it exists, use first one)
    async with AsyncSessionLocal() as session:
        # Try to get first dashboard
        stmt = select(Dashboard).limit(1)
        result = await session.execute(stmt)
        dashboard = result.scalars().first()

        if not dashboard:
            print("⚠️  No dashboards in database. Skipping diagnostic tests.")
            print("   Please run /analyze endpoint first to create test data.")
            return

        dashboard_id = dashboard.id
        print(f"\nTesting with Dashboard ID: {dashboard_id}")

        # Test 1: Simple access within session
        print("\n[Test 1] Access within session context")
        try:
            kpi = dashboard.kpi_data
            print(f"  ✅ dashboard.kpi_data accessible: {type(kpi)}")
        except Exception as e:
            print(f"  ❌ Error: {e}")

        # Test 2: Relationship access within session
        print("\n[Test 2] Relationship access within session")
        try:
            chat_id = dashboard.chat_id
            chat = await session.get(Chat, chat_id)
            if chat:
                user_id = chat.user_id
                print(f"  ✅ dashboard.chat_id: {chat_id}")
                print(f"  ✅ chat.user_id: {user_id}")
            else:
                print(f"  ⚠️  Chat not found for ID: {chat_id}")
        except Exception as e:
            print(f"  ❌ Error: {e}")

        # Test 3: Copy data within session
        print("\n[Test 3] Copy data within session (safe pattern)")
        try:
            kpi_copy = dict(dashboard.kpi_data or {})
            insights_copy = dict(dashboard.ai_insights or {})
            print(f"  ✅ KPI data copied: {len(kpi_copy)} items")
            print(f"  ✅ Insights copied: {len(insights_copy)} items")
        except Exception as e:
            print(f"  ❌ Error: {e}")

        # Store dashboard ID for next test
        test_dashboard_id = dashboard_id

    # Test 4: Access after session closes (should fail or work depending on config)
    print("\n[Test 4] Access AFTER session closed (expected to fail)")
    try:
        # This should fail with greenlet_spawn error if lazy loading is enabled
        kpi = dashboard.kpi_data
        print(
            f"  ⚠️  Unexpectedly able to access data after session close: {type(kpi)}")
        print("     (This might indicate expire_on_commit is False)")
    except Exception as e:
        if "greenlet" in str(e):
            print(f"  ✅ greenlet_spawn error as expected: {str(e)[:80]}...")
            print("     This is CORRECT behavior with expire_on_commit=True")
        else:
            print(f"  ❌ Unexpected error: {e}")

    # Test 5: Fresh session with copied data (safe pattern)
    print("\n[Test 5] Fresh session with copied data (correct approach)")
    try:
        async with AsyncSessionLocal() as session:
            dashboard = await session.get(Dashboard, test_dashboard_id)
            if dashboard:
                # Copy ALL data while session is active
                kpi_copy = dict(dashboard.kpi_data or {})
                insights_copy = dict(dashboard.ai_insights or {})

        # Now use copied data (should be safe)
        print(f"  ✅ Using copied data outside session:")
        print(f"     KPI items: {len(kpi_copy)}")
        print(f"     Insights keys: {list(insights_copy.keys())}")
    except Exception as e:
        print(f"  ❌ Error: {e}")


async def test_endpoint_flow():
    """Simulate the /summary endpoint flow."""

    print("\n" + "=" * 70)
    print("ENDPOINT FLOW SIMULATION (/summary)")
    print("=" * 70)

    # Get first dashboard
    async with AsyncSessionLocal() as session:
        stmt = select(Dashboard).limit(1)
        result = await session.execute(stmt)
        dashboard = result.scalars().first()

        if not dashboard:
            print("⚠️  No dashboards. Skipping flow simulation.")
            return

        print(f"\n📊 Simulating /summary endpoint...")
        dashboard_id = dashboard.id

        try:
            # Step 1: Load dashboard and validate
            print("[Step 1] Load dashboard...")
            print(f"  ✅ Dashboard loaded: {dashboard_id}")

            # Step 2: Copy data (THIS IS CRITICAL - must happen in session)
            print("[Step 2] Copy data from ORM object (within session)...")
            kpi_payload = dict(dashboard.kpi_data or {})
            insights = dict(dashboard.ai_insights or {})
            dataset_summary = insights.get("dataset_summary", "").strip()
            print(f"  ✅ KPI payload: {len(kpi_payload)} items")
            print(f"  ✅ Insights: {len(insights)} items")
            print(f"  ✅ Dataset summary: {len(dataset_summary)} chars")

            # Step 3: Validate data
            print("[Step 3] Validate data...")
            if not kpi_payload:
                print(f"  ❌ No KPI data")
            else:
                print(f"  ✅ KPI data present")

            if not dataset_summary:
                print(f"  ❌ No dataset summary")
            else:
                print(f"  ✅ Dataset summary present")

            # Step 4: (Would call AI here - simulated)
            print("[Step 4] (AI generation would happen here - simulated)...")
            summary = "This is a simulated executive summary..."
            print(f"  ✅ Summary generated: {len(summary)} chars")

            # Step 5: Persist changes
            print("[Step 5] Persist changes...")
            insights["executive_summary"] = summary
            dashboard.ai_insights = insights
            await session.commit()
            print(f"  ✅ Changes committed")

        except Exception as e:
            await session.rollback()
            print(f"  ❌ Error: {e}")
            import traceback
            traceback.print_exc()


async def main():
    try:
        await test_orm_access_patterns()
        await test_endpoint_flow()
        print("\n" + "=" * 70)
        print("✅ Diagnostics Complete")
        print("=" * 70)
    except Exception as exc:
        print(f"\n❌ Fatal Error: {exc}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
