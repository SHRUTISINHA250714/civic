"""
Migration script: Add impact_count column to complaints table in PostgreSQL/SQLite and initialize it.
"""
from backend.app.core.database import engine
from sqlalchemy import text, inspect

def migrate():
    inspector = inspect(engine)
    existing_cols = [c["name"] for c in inspector.get_columns("complaints")]

    with engine.connect() as conn:
        if "impact_count" not in existing_cols:
            print("Adding impact_count column to complaints...")
            # For PostgreSQL / SQLite compatibility
            conn.execute(text("ALTER TABLE complaints ADD COLUMN IF NOT EXISTS impact_count INTEGER DEFAULT 1;"))
            conn.commit()
            print("Added impact_count column.")
        else:
            print("impact_count column already exists.")

        # Backfill impact_count for all records:
        # Default is 1. If complaint has child reports in duplicate_complaint_mappings or duplicate_of_complaint_id,
        # update it to 1 + child count.
        print("Backfilling impact_count values...")
        conn.execute(text("""
            UPDATE complaints
            SET impact_count = 1
            WHERE impact_count IS NULL;
        """))
        conn.commit()

        # Update parent complaints with count of linked child reports
        conn.execute(text("""
            UPDATE complaints c
            SET impact_count = 1 + sub.child_count
            FROM (
                SELECT duplicate_of_complaint_id AS parent_id, COUNT(*) AS child_count
                FROM complaints
                WHERE duplicate_of_complaint_id IS NOT NULL
                GROUP BY duplicate_of_complaint_id
            ) sub
            WHERE c.id = sub.parent_id;
        """))
        conn.commit()
        print("Backfill completed successfully.")

if __name__ == "__main__":
    migrate()
