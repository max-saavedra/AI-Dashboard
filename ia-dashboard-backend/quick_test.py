"""
quick_test.py

Test rápido para verificar si el problema es en la validación de datos
o en la ejecución del flujo.
"""

import asyncio
import uuid
from sqlalchemy import select

from app.models.database import Dashboard
from app.models.session import AsyncSessionLocal


async def quick_test():
    print("\n" + "=" * 70)
    print("QUICK TEST: Dashboard Data Validation")
    print("=" * 70)

    async with AsyncSessionLocal() as session:
        # Get the first dashboard
        stmt = select(Dashboard).limit(1)
        result = await session.execute(stmt)
        dashboard = result.scalars().first()

        if not dashboard:
            print("\n❌ NO DASHBOARDS FOUND")
            print("   Run /analyze endpoint first")
            return False

        dashboard_id = dashboard.id
        print(f"\n✓ Found dashboard: {dashboard_id}")

        # Check 1: KPI Data
        print("\n[Check 1] KPI Data")
        print(f"  - Exists: {bool(dashboard.kpi_data)}")
        print(f"  - Type: {type(dashboard.kpi_data)}")
        print(
            f"  - Length: {len(dashboard.kpi_data) if dashboard.kpi_data else 0} items")
        if dashboard.kpi_data:
            print(f"  - Keys: {list(dashboard.kpi_data.keys())[:5]}")

        if not dashboard.kpi_data:
            print("  ⚠️  NO KPI DATA - This is why /summary returns 422")
            return False

        # Check 2: AI Insights
        print("\n[Check 2] AI Insights")
        print(f"  - Exists: {bool(dashboard.ai_insights)}")
        print(f"  - Type: {type(dashboard.ai_insights)}")
        print(
            f"  - Keys: {list(dashboard.ai_insights.keys()) if dashboard.ai_insights else '(empty)'}")

        if not dashboard.ai_insights:
            print("  ⚠️  NO AI INSIGHTS")

        # Check 3: Dataset Summary
        print("\n[Check 3] Dataset Summary")
        if dashboard.ai_insights and "dataset_summary" in dashboard.ai_insights:
            summary = dashboard.ai_insights["dataset_summary"]
            print(f"  - Exists: True")
            print(f"  - Length: {len(summary)} chars")
            print(f"  - Preview: {summary[:100]}...")
        else:
            print(f"  - Exists: False")
            print("  ⚠️  NO DATASET SUMMARY - This is why /summary returns 422")
            return False

        # Check 4: Cleaned Data
        print("\n[Check 4] Cleaned Data")
        print(f"  - Exists: {bool(dashboard.cleaned_data)}")
        if dashboard.cleaned_data:
            if isinstance(dashboard.cleaned_data, list):
                print(f"  - Rows: {len(dashboard.cleaned_data)}")
                if dashboard.cleaned_data and isinstance(dashboard.cleaned_data[0], dict):
                    print(
                        f"  - First row keys: {list(dashboard.cleaned_data[0].keys())}")
            else:
                print(f"  - Type: {type(dashboard.cleaned_data)}")
                print(
                    f"  - Keys: {list(dashboard.cleaned_data.keys()) if isinstance(dashboard.cleaned_data, dict) else 'N/A'}")

        # Check 5: Try to copy data like endpoint does
        print("\n[Check 5] Data Copying (ORM → Python dict)")
        try:
            kpi_copy = dict(dashboard.kpi_data or {})
            insights_copy = dict(dashboard.ai_insights or {})
            print(f"  ✓ KPI copied: {len(kpi_copy)} items")
            print(f"  ✓ Insights copied: {len(insights_copy)} items")
            print("  ✓ NO GREENLET ERROR")
        except Exception as e:
            print(f"  ❌ ERROR copying data: {e}")
            import traceback
            traceback.print_exc()
            return False

        print("\n" + "=" * 70)
        print("✅ ALL CHECKS PASSED")
        print("=" * 70)
        print("\nDashboard is ready for /summary endpoint")
        print(f"Dashboard ID: {dashboard_id}")
        print("\nTry this curl command:")
        print(f'''curl -X POST http://localhost:8000/api/v1/summary \\
  -H "Content-Type: application/json" \\
  -d '{{
    "dashboard_id": "{dashboard_id}",
    "user_objective": "Analyze trends"
  }}'
''')
        return True


if __name__ == "__main__":
    success = asyncio.run(quick_test())
    exit(0 if success else 1)
