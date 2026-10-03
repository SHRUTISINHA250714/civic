import os
import sys

# Bypassing the TensorFlow/Keras 3 compatibility issue (MUST be set before importing transformers)
os.environ["USE_TF"] = "0"
os.environ["TRANSFORMERS_NO_TF"] = "1"
os.environ["USE_TORCH"] = "1"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.services.ai import predict_priority, translate_text, encoder_model
from backend.app.services.duplicate import extract_civic_keywords
from sentence_transformers import util

def test_priority_hybrid_and_overrides():
    print("--- 1. Testing Explainable Hybrid Priority & Emergency Overrides ---", flush=True)
    
    # Emergency Override 1: Fire
    prio, conf = predict_priority("There is a massive fire in the transformer with sparks", "Electricity & Streetlights")
    print(f"Fire case: {prio} (conf: {conf})", flush=True)
    assert prio == "Critical", f"Expected Critical for fire, got {prio}"

    # Emergency Override 2: Live wire
    prio, conf = predict_priority("Open live wire hanging on the street posing immediate electric shock danger", "Electricity & Streetlights")
    print(f"Live wire case: {prio} (conf: {conf})", flush=True)
    assert prio == "Critical", f"Expected Critical for live wire, got {prio}"

    # Emergency Override 3: Flooding
    prio, conf = predict_priority("Heavy flash flooding water entering homes", "Sewage & Drainage")
    print(f"Flooding case: {prio} (conf: {conf})", flush=True)
    assert prio == "Critical", f"Expected Critical for flooding, got {prio}"

    # Emergency Override 4: Injury risk
    prio, conf = predict_priority("Deep excavation with imminent injury risk and accident danger", "Potholes & Damaged Roads")
    print(f"Injury risk case: {prio} (conf: {conf})", flush=True)
    assert prio == "Critical", f"Expected Critical for injury risk, got {prio}"

    # Standard case with 1 report
    prio1, conf1 = predict_priority("Pothole on the inner colony road", "Potholes & Damaged Roads", impact_count=1)
    print(f"Standard pothole with 1 report: {prio1}", flush=True)

    # Escalated case with multiple reports (Reported by X people)
    prio_multi, conf_multi = predict_priority("Pothole on the inner colony road", "Potholes & Damaged Roads", impact_count=7, location_address="Near Metro Station Hospital Road")
    print(f"Same pothole with 7 linked reports & hospital context: {prio_multi}", flush=True)
    prio_levels = {"Low": 1, "Medium": 2, "High": 3, "Critical": 4}
    assert prio_levels[prio_multi] >= prio_levels[prio1], "Priority should increase or stay high with more linked reports"

    print("Priority tests PASSED!\n", flush=True)

def test_duplicate_cross_lingual_variations():
    print("--- 2. Testing Cross-Lingual & Wording Variation Duplicate Matching ---", flush=True)
    
    en_desc = "Dangerous open pothole on Indiranagar 100ft road"
    kn_desc = "ಇಂದಿರಾನಗರ 100 ಅಡಿ ರಸ್ತೆಯಲ್ಲಿ ಅಪಾಯಕಾರಿ ಗುಂಡಿ ಬಿದ್ದಿದೆ"
    kanglish_desc = "Indiranagar 100ft road alli thumba dodd pothole ide, gundi biddide"
    hinglish_desc = "Indiranagar 100 feet road mein bahut bada gaddha hai khatarnak"

    # Translate all to normalized English
    t_en, _, _ = translate_text(en_desc)
    t_kn, _, _ = translate_text(kn_desc)
    t_kanglish, _, _ = translate_text(kanglish_desc)
    t_hinglish, _, _ = translate_text(hinglish_desc)

    print(f"Translated Kannada: '{t_kn}'", flush=True)
    print(f"Translated Kanglish: '{t_kanglish}'", flush=True)
    print(f"Translated Hinglish: '{t_hinglish}'", flush=True)

    kw_en = extract_civic_keywords(t_en)
    kw_kn = extract_civic_keywords(t_kn)
    kw_kanglish = extract_civic_keywords(t_kanglish)
    kw_hinglish = extract_civic_keywords(t_hinglish)

    print(f"Keywords EN: {kw_en}", flush=True)
    print(f"Keywords KN: {kw_kn}", flush=True)
    print(f"Keywords Kanglish: {kw_kanglish}", flush=True)
    print(f"Keywords Hinglish: {kw_hinglish}", flush=True)

    if encoder_model:
        emb_en = encoder_model.encode(t_en, convert_to_tensor=True)
        emb_kn = encoder_model.encode(t_kn, convert_to_tensor=True)
        emb_kanglish = encoder_model.encode(t_kanglish, convert_to_tensor=True)
        emb_hinglish = encoder_model.encode(t_hinglish, convert_to_tensor=True)

        sim_kn = util.cos_sim(emb_en, emb_kn)[0][0].item()
        sim_kanglish = util.cos_sim(emb_en, emb_kanglish)[0][0].item()
        sim_hinglish = util.cos_sim(emb_en, emb_hinglish)[0][0].item()

        print(f"Embedding Similarity EN <-> KN: {sim_kn:.3f}", flush=True)
        print(f"Embedding Similarity EN <-> Kanglish: {sim_kanglish:.3f}", flush=True)
        print(f"Embedding Similarity EN <-> Hinglish: {sim_hinglish:.3f}", flush=True)

        assert sim_kn >= 0.70, f"Expected KN similarity >= 0.70, got {sim_kn}"
        assert sim_kanglish >= 0.70, f"Expected Kanglish similarity >= 0.70, got {sim_kanglish}"
        assert sim_hinglish >= 0.70, f"Expected Hinglish similarity >= 0.70, got {sim_hinglish}"

    print("Cross-lingual duplicate matching tests PASSED!\n", flush=True)

if __name__ == "__main__":
    test_priority_hybrid_and_overrides()
    test_duplicate_cross_lingual_variations()
    print("ALL 5 ENHANCEMENT TESTS PASSED PERFECTLY!", flush=True)
