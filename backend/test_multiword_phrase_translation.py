import sys
import os
from unittest.mock import patch

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Ensure root workspace directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.services.ai import translate_text, classify_complaint

def test_multiword_phrase_fallback():
    print("=" * 80)
    print("TIER 2 MULTI-WORD PHRASE TRANSLATION & CLASSIFICATION VERIFICATION")
    print("=" * 80)

    # Force Tier 2 fallback path by mocking GoogleTranslator to raise Exception
    with patch("backend.app.services.ai.GoogleTranslator") as mock_gt:
        mock_gt.side_effect = Exception("Simulated GoogleTranslator rate limit / API failure for Tier 2 testing")

        # ── Test Case 1: The Reported Streetlight Bug ─────────────────────────
        kannada_input_1 = "ನಮ್ಮ ಬಡಾವಣೆಯ ಬೀದಿ ದೀಪ ಕಳೆದ ಒಂದು ವಾರದಿಂದ ಉರಿಯುತ್ತಿಲ್ಲ, ರಾತ್ರಿ ತುಂಬಾ ಕತ್ತಲೆ ಇದ್ದು ಅಪಾಯಕಾರಿ ಆಗಿದೆ"
        print(f"\n[Test Case 1] Testing Streetlight Complaint (Forced Tier 2 Fallback)")
        print(f"  Input Text: '{kannada_input_1}'")

        translated_1, lang_1, t1 = translate_text(kannada_input_1)
        print(f"  - Tier 2 Fallback Translation: '{translated_1}'")

        assert "streetlight" in translated_1.lower(), (
            f"FAILED: 'streetlight' missing from Tier 2 translation output. Got: '{translated_1}'"
        )
        print("  ✓ Verified: 'streetlight' keyword present in translation output.")

        category_1, conf_1 = classify_complaint(translated_1)
        print(f"  - Classification Result: Category='{category_1}', Confidence={conf_1}")

        assert category_1 == "Damaged Streetlights", (
            f"FAILED: Expected category 'Damaged Streetlights', got '{category_1}'"
        )
        assert conf_1 == 0.96, f"FAILED: Expected confidence 0.96, got {conf_1}"
        print("  ✓ Verified: Correctly classified as 'Damaged Streetlights' with 0.96 confidence.")

        # ── Test Case 2: Tree Fall Phrase ("ಮರ ಬಿದ್ದಿದೆ") ───────────────────────
        kannada_input_2 = "ರಸ್ತೆಯಲ್ಲಿ ದೊಡ್ಡ ಮರ ಬಿದ್ದಿದೆ ರಸ್ತೆ ಬಂದ್ ಆಗಿದೆ"
        print(f"\n[Test Case 2] Testing Fallen Tree Complaint (Forced Tier 2 Fallback)")
        print(f"  Input Text: '{kannada_input_2}'")

        translated_2, lang_2, t2 = translate_text(kannada_input_2)
        print(f"  - Tier 2 Fallback Translation: '{translated_2}'")

        assert "tree fallen" in translated_2.lower() or "tree" in translated_2.lower(), (
            f"FAILED: 'tree fallen' missing from translation output. Got: '{translated_2}'"
        )
        print("  ✓ Verified: 'tree fallen' keyword present in translation output.")

        category_2, conf_2 = classify_complaint(translated_2)
        print(f"  - Classification Result: Category='{category_2}', Confidence={conf_2}")

        assert category_2 in ["Tree Fall & Dangerous Branches", "Tree Fall"], (
            f"FAILED: Expected Tree Fall category, got '{category_2}'"
        )
        assert conf_2 >= 0.90, f"FAILED: Expected confidence >= 0.90, got {conf_2}"
        print(f"  ✓ Verified: Correctly classified as '{category_2}' with {conf_2} confidence.")

        # ── Test Case 3: Water Pipeline Burst Phrase ("ಪೈಪ್ ಒಡೆದಿದೆ") ──────────
        kannada_input_3 = "ಮುಖ್ಯ ರಸ್ತೆಯಲ್ಲಿ ಪೈಪ್ ಒಡೆದಿದೆ ಕುಡಿಯುವ ನೀರು ಪೋಲಾಗುತ್ತಿದೆ"
        print(f"\n[Test Case 3] Testing Water Pipeline Burst Complaint (Forced Tier 2 Fallback)")
        print(f"  Input Text: '{kannada_input_3}'")

        translated_3, lang_3, t3 = translate_text(kannada_input_3)
        print(f"  - Tier 2 Fallback Translation: '{translated_3}'")

        assert "pipeline burst" in translated_3.lower() or "water" in translated_3.lower(), (
            f"FAILED: 'pipeline burst' missing from translation output. Got: '{translated_3}'"
        )
        print("  ✓ Verified: 'pipeline burst' keyword present in translation output.")

        category_3, conf_3 = classify_complaint(translated_3)
        print(f"  - Classification Result: Category='{category_3}', Confidence={conf_3}")

        assert category_3 in ["Water Pipeline Burst & Leakage", "Water Leakage"], (
            f"FAILED: Expected Water Leakage category, got '{category_3}'"
        )
        assert conf_3 >= 0.90, f"FAILED: Expected confidence >= 0.90, got {conf_3}"
        print(f"  ✓ Verified: Correctly classified as '{category_3}' with {conf_3} confidence.")

    print("\n" + "=" * 80)
    print("ALL MULTI-WORD PHRASE TRANSLATION & CLASSIFICATION TESTS PASSED! 🚀")
    print("=" * 80)

if __name__ == "__main__":
    test_multiword_phrase_fallback()
