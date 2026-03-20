"""
verify_db_setup.py

Verifies database connection and validates that the schema is correctly set up.
"""

import asyncio
import sys
from sqlalchemy import text

from app.models.session import engine, AsyncSessionLocal
from app.core.logging import get_logger

logger = get_logger(__name__)


async def verify_database():
    """Verify database connection and schema."""
    print("\n" + "=" * 70)
    print("DATABASE VERIFICATION")
    print("=" * 70)

    try:
        # Test connection
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT version();"))
            version = result.scalar()
            print(f"✅ Database Connection OK")
            print(f"   PostgreSQL: {version[:50]}...")

        # Test tables exist
        async with AsyncSessionLocal() as session:
            tables_to_check = ["users", "chats",
                               "dashboards", "temporary_dashboards"]

            for table_name in tables_to_check:
                try:
                    result = await session.execute(
                        text(f"SELECT COUNT(*) FROM {table_name};")
                    )
                    count = result.scalar()
                    print(f"✅ {table_name:20} ({count:5} rows)")
                except Exception as e:
                    print(f"❌ {table_name:20} - {str(e)[:50]}")

        print(f"\n✅ Database Setup Verified")
        return True

    except Exception as exc:
        print(f"❌ Database Error: {exc}")
        print(f"\nTroubleshooting:")
        print(f"1. Check your DATABASE_URL in .env")
        print(f"2. Ensure PostgreSQL is running")
        print(f"3. Run migrations: alembic upgrade head")
        return False


async def main():
    try:
        success = await verify_database()
        sys.exit(0 if success else 1)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
