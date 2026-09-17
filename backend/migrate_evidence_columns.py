"""
Migration script: Add Phase 8 & Phase 9 columns to SQLite tables if they do not exist.
"""
from backend.app.core.database import engine
from sqlalchemy import text, inspect

def migrate():
    inspector = inspect(engine)
    existing_ev_cols = [c["name"] for c in inspector.get_columns("complaint_evidence_checks")]
    existing_img_cols = [c["name"] for c in inspector.get_columns("complaint_images")]

    ev_cols_to_add = [
        ("verification_decision", "VARCHAR DEFAULT 'VERIFIED'"),
        ("geo_status", "VARCHAR DEFAULT 'MATCH'"),
        ("gps_accuracy", "FLOAT"),
        ("freshness_status", "VARCHAR DEFAULT 'FRESH'"),
        ("semantic_match_status", "VARCHAR DEFAULT 'MATCH'"),
        ("semantic_confidence", "FLOAT DEFAULT 1.0"),
        ("image_category", "VARCHAR"),
        ("is_reused_image", "BOOLEAN DEFAULT FALSE"),
        ("reused_complaint_id", "INTEGER"),
        ("perceptual_hash", "VARCHAR"),
        ("quality_check", "VARCHAR"),
        ("gate_reasons", "TEXT"),
    ]

    img_cols_to_add = [
        ("perceptual_hash", "VARCHAR"),
        ("bounding_boxes", "TEXT"),
        ("quality_status", "VARCHAR"),
    ]

    with engine.connect() as conn:
        for col_name, col_type in ev_cols_to_add:
            if col_name not in existing_ev_cols:
                print(f"Adding {col_name} to complaint_evidence_checks...")
                conn.execute(text(f"ALTER TABLE complaint_evidence_checks ADD COLUMN {col_name} {col_type}"))
                conn.commit()

        for col_name, col_type in img_cols_to_add:
            if col_name not in existing_img_cols:
                print(f"Adding {col_name} to complaint_images...")
                conn.execute(text(f"ALTER TABLE complaint_images ADD COLUMN {col_name} {col_type}"))
                conn.commit()

    print("Migration completed successfully.")

if __name__ == "__main__":
    migrate()
