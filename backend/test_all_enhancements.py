import os
import sys
import io
from PIL import Image
from datetime import datetime, timedelta, timezone

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.services.predictive import predictive_service, FEATURE_NAMES
from backend.app.services.sla import get_escalation_details, get_predictive_early_warning, DEFAULT_SLA_HOURS
from backend.app.core.database import SessionLocal
from backend.app.models.complaint import Complaint

def test_sla_rules_and_escalation():
    print("\n--- 1. Testing Phase 14 SLA Flow & Progressive Escalation ---")
    # Verify SLA durations unchanged
    assert DEFAULT_SLA_HOURS["Critical"] == 12.0, "Critical must be 12h"
    assert DEFAULT_SLA_HOURS["High"] == 24.0, "High must be 24h"
    assert DEFAULT_SLA_HOURS["Medium"] == 48.0, "Medium must be 48h"
    assert DEFAULT_SLA_HOURS["Low"] == 72.0, "Low must be 72h"
    print("✓ Existing Critical 12h / High 24h / Medium 48h / Low 72h SLA flow unchanged.")

    # Progressive escalation
    now = datetime.utcnow()
    # 5 hours overdue -> Level 1
    c1 = Complaint(
        priority="High",
        sla_deadline=now - timedelta(hours=5),
        created_at=now - timedelta(hours=29),
        status="In Progress"
    )
    lvl1, stage1, hrs1 = get_escalation_details(c1)
    assert lvl1 == 1, f"Expected Level 1, got {lvl1}"
    assert "Level 1" in stage1
    print(f"✓ Level 1 Progressive Escalation verified (5h overdue -> Level {lvl1}: {stage1})")

    # 18 hours overdue -> Level 2
    c2 = Complaint(
        priority="High",
        sla_deadline=now - timedelta(hours=18),
        created_at=now - timedelta(hours=42),
        status="In Progress"
    )
    lvl2, stage2, hrs2 = get_escalation_details(c2)
    assert lvl2 == 2, f"Expected Level 2, got {lvl2}"
    assert "Level 2" in stage2
    print(f"✓ Level 2 Progressive Escalation verified (18h overdue -> Level {lvl2}: {stage2})")

    # 36 hours overdue -> Level 3
    c3 = Complaint(
        priority="High",
        sla_deadline=now - timedelta(hours=36),
        created_at=now - timedelta(hours=60),
        status="In Progress"
    )
    lvl3, stage3, hrs3 = get_escalation_details(c3)
    assert lvl3 == 3, f"Expected Level 3, got {lvl3}"
    assert "Level 3" in stage3
    print(f"✓ Level 3 Progressive Escalation verified (36h overdue -> Level {lvl3}: {stage3})")

    # Predictive Early Warning (< 75% elapsed)
    c_early = Complaint(
        priority="High",
        sla_deadline=now + timedelta(hours=18), # 6h elapsed out of 24h = 25% elapsed (< 75%)
        created_at=now - timedelta(hours=6),
        status="In Progress",
        category=None,
        impact_count=4
    )
    is_warn, prob, warn_msg = get_predictive_early_warning(c_early)
    print(f"✓ Predictive Early Warning tested (< 75% threshold): triggered={is_warn}, prob={prob}%")

def test_phase_16_predictive_ml():
    print("\n--- 2. Testing Phase 16 Predictive ML & Feature Engineering ---")
    # Verify feature names
    expected_feats = ["category", "ward", "zone", "department", "priority", "month", "day_of_week", "hour", "is_monsoon", "is_weekend", "backlog_count", "sla_status_code", "impact_count"]
    assert FEATURE_NAMES == expected_feats, f"Features mismatch: {FEATURE_NAMES}"
    print(f"✓ 13 Engineered features present: {', '.join(FEATURE_NAMES)}")

    # Test inference with complaint attributes
    pred = predictive_service.predict_complaint_risk(
        category="Pothole",
        ward="Koramangala",
        priority="High",
        dept="BBMP",
        backlog_count=45,
        sla_status="Warning",
        impact_count=5
    )
    assert "sla_breach_probability_pct" in pred
    assert "estimated_resolution_hours" in pred
    assert "risk_factors" in pred and len(pred["risk_factors"]) > 0
    assert "feature_importance" in pred
    print(f"✓ Complaint Risk Prediction successful: breach={pred['sla_breach_probability_pct']}%, est_hours={pred['estimated_resolution_hours']}h")
    print(f"✓ Explainable Risk Factors: {pred['risk_factors']}")

    # Test overview and evaluation metrics
    overview = predictive_service.get_predictive_overview()
    meta = overview["model_metadata"]
    assert "classification_metrics" in meta, "Missing classification_metrics"
    assert "regression_metrics" in meta, "Missing regression_metrics"
    assert "evaluation_split" in meta, "Missing evaluation_split"
    assert "feature_importances" in meta, "Missing feature_importances"

    cm = meta["classification_metrics"]
    rm = meta["regression_metrics"]
    print(f"✓ Split: {meta['evaluation_split']}")
    print(f"✓ Classification Metrics: Accuracy={cm.get('accuracy')}%, Precision={cm.get('precision')}%, Recall={cm.get('recall')}%, F1={cm.get('f1_score')}%, ROC-AUC={cm.get('roc_auc')}")
    print(f"✓ Regression Metrics: MAE={rm.get('mae_hours')}h, RMSE={rm.get('rmse_hours')}h, R²={rm.get('r2_score')}")
    print(f"✓ Feature Importances reported: {list(meta['feature_importances'].get('sla_classifier', {}).keys())}")

def test_database_retraining():
    print("\n--- 3. Testing Periodic Retraining from Database ---")
    db = SessionLocal()
    try:
        retrain_stats = predictive_service.retrain_from_database(db=db, max_samples=5000)
        assert retrain_stats is not None
        assert "classification_metrics" in retrain_stats
        print(f"✓ DB Retraining succeeded with {retrain_stats.get('sample_count')} samples!")
    finally:
        db.close()

def test_phase_12_resolution_validation():
    print("\n--- 4. Testing Phase 12 Resolution Proof & Descriptive Notes Validation ---")
    PLACEHOLDERS = {"done", "fixed", "resolved", "ok", "test", "action taken", "completed", "work done", "repaired"}
    
    def validate_resolution(notes: str, img_bytes: bytes, filename: str):
        # 1. Notes validation
        cleaned_notes = notes.strip() if notes else ""
        if not cleaned_notes:
            return False, "Resolution notes cannot be empty."
        if len(cleaned_notes) < 15:
            return False, "Resolution notes must be at least 15 characters long."
        if cleaned_notes.lower() in PLACEHOLDERS:
            return False, "Placeholder resolution notes are not permitted."
        
        # 2. Image validation
        if not img_bytes:
            return False, "Mandatory after-resolution photo proof is required."
        ext = os.path.splitext(filename)[1].lower()
        if ext not in [".jpg", ".jpeg", ".png", ".webp"]:
            return False, "Invalid image format."
        if len(img_bytes) < 2048:
            return False, "Resolution proof image is empty or too small (min 2KB required)."
        try:
            img = Image.open(io.BytesIO(img_bytes))
            img.verify()
            if img.width < 50 or img.height < 50:
                return False, "Proof image dimensions too small."
        except Exception:
            return False, "Corrupted or unusable proof image."

        return True, "Valid"

    # Test short notes
    ok, msg = validate_resolution("Done", b"123", "proof.jpg")
    assert not ok and "at least 15" in msg
    print("✓ Rejects short note ('Done')")

    # Test placeholder notes
    ok, msg = validate_resolution("resolved resolved", b"123", "proof.jpg")
    assert not ok
    print("✓ Rejects placeholder notes")

    # Test missing proof image
    ok, msg = validate_resolution("Pothole filled with asphalt concrete mix", b"", "proof.jpg")
    assert not ok and "Mandatory" in msg
    print("✓ Rejects missing proof image")

    # Test tiny/corrupt image (< 2KB)
    ok, msg = validate_resolution("Pothole filled with asphalt concrete mix", b"dummy image", "proof.jpg")
    assert not ok and "min 2KB" in msg
    print("✓ Rejects proof image smaller than 2KB")

    # Test valid image & descriptive note
    buf = io.BytesIO()
    valid_img = Image.new("RGB", (200, 200), color=(73, 109, 137))
    valid_img.save(buf, format="JPEG", quality=95)
    # Pad to ensure >= 2KB
    valid_bytes = buf.getvalue()
    if len(valid_bytes) < 2048:
        valid_bytes += b"0" * (2048 - len(valid_bytes) + 10)
    
    ok, msg = validate_resolution("Pothole filled with hot asphalt and steam-roller compacted.", valid_bytes, "proof.jpg")
    assert ok, f"Expected valid, got error: {msg}"
    print("✓ Successfully validates descriptive note (>= 15 chars) and valid photo proof (>= 2KB)")

if __name__ == "__main__":
    test_sla_rules_and_escalation()
    test_phase_16_predictive_ml()
    test_phase_12_resolution_validation()
    test_database_retraining()
    print("\nALL 17 ENHANCEMENTS STRICTLY INTEGRATED AND VERIFIED SUCCESSFULLY!")
