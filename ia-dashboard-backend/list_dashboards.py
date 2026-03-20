"""
list_dashboards.py

Lista todos los dashboards en la base de datos y su estado
(útil para debugging).
"""

import asyncio
from sqlalchemy import select
from app.models.database import Dashboard, Chat
from app.models.session import AsyncSessionLocal
from app.core.logging import get_logger

logger = get_logger(__name__)


async def list_all_dashboards():
    """List all dashboards with their data status."""
    print("\n" + "=" * 80)
    print("DASHBOARDS IN DATABASE")
    print("=" * 80)

    async with AsyncSessionLocal() as session:
        stmt = select(Dashboard).order_by(Dashboard.created_at.desc())
        result = await session.execute(stmt)
        dashboards = result.scalars().all()

        if not dashboards:
            print("\n⚠️  No dashboards found in database")
            print("   Run /analyze endpoint first to create test data")
            return

        print(f"\n📊 Found {len(dashboards)} dashboard(s)\n")

        for i, dashboard in enumerate(dashboards, 1):
            print(f"{i}. Dashboard: {dashboard.id}")
            print(f"   Created: {dashboard.created_at}")

            # Get chat info
            stmt_chat = select(Chat).where(Chat.id == dashboard.chat_id)
            chat_result = await session.execute(stmt_chat)
            chat = chat_result.scalars().first()

            if chat:
                print(
                    f"   User: {chat.user_id if chat.user_id else '(Anonymous)'}")

            # Data status
            print(
                f"   ✓ KPI data: {bool(dashboard.kpi_data)} ({len(str(dashboard.kpi_data))} bytes)")
            print(
                f"   ✓ Cleaned data: {bool(dashboard.cleaned_data)} ({len(str(dashboard.cleaned_data))} bytes)")
            print(
                f"   ✓ AI Insights: {bool(dashboard.ai_insights)} keys: {list(dashboard.ai_insights.keys()) if dashboard.ai_insights else '(empty)'}")

            if dashboard.ai_insights:
                if "dataset_summary" in dashboard.ai_insights:
                    print(
                        f"     - dataset_summary: {len(dashboard.ai_insights['dataset_summary'])} chars")
                if "executive_summary" in dashboard.ai_insights:
                    print(
                        f"     - executive_summary: {len(dashboard.ai_insights['executive_summary'])} chars")

            print(f"   ✓ Charts: {len(dashboard.chart_config)} configs")
            print()


if __name__ == "__main__":
    asyncio.run(list_all_dashboards())
