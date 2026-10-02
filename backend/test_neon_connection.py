import sys
import os
from sqlalchemy import text, inspect

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Ensure root workspace is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.config import settings
from backend.app.core.database import engine

def test_neon_connection():
    print("=" * 75)
    print("NEON SERVERLESS POSTGRESQL CONNECTIVITY & HEALTH VERIFICATION")
    print("=" * 75)

    print(f"\n[Step 1] Inspecting Database Configuration...")
    raw_url = settings.DATABASE_URL
    norm_url = settings.SQLALCHEMY_DATABASE_URI

    # Mask credentials for safe display
    def mask_uri(uri: str) -> str:
        if "@" in uri:
            prefix, rest = uri.split("@", 1)
            scheme = prefix.split("://")[0]
            return f"{scheme}://****:****@{rest}"
        return uri

    print(f"  - Configured DATABASE_URL: {mask_uri(raw_url)}")
    print(f"  - Normalized SQLAlchemy URI: {mask_uri(norm_url)}")

    # Assert normalization features
    assert norm_url.startswith("postgresql://"), f"URL scheme must start with postgresql:// (got {norm_url})"
    if "localhost" not in norm_url and "127.0.0.1" not in norm_url:
        assert "sslmode=" in norm_url, "Remote connections must include sslmode parameter"
        print("✓ Verified: SSL enforcement (sslmode=require) present for remote database.")

    # [Step 2] Testing Connection Ping & Latency
    print(f"\n[Step 2] Testing Connection Ping (`SELECT 1`)...")
    try:
        with engine.connect() as conn:
            res = conn.execute(text("SELECT 1")).scalar()
            assert res == 1, f"Expected 1, got {res}"
        print("✓ Database ping succeeded! Connection active.")
    except Exception as e:
        print(f"❌ Database ping failed: {e}")
        sys.exit(1)

    # [Step 3] Inspecting Existing Database Tables
    print(f"\n[Step 3] Inspecting Tables in target Database...")
    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    print(f"✓ Found {len(table_names)} tables in database:")
    for tbl in sorted(table_names):
        print(f"  - {tbl}")

    print("\n" + "=" * 75)
    print("NEON CONNECTIVITY VERIFICATION PASSED SUCCESSFULLY! 🚀")
    print("=" * 75)

if __name__ == "__main__":
    test_neon_connection()
