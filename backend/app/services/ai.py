import os
import time
from typing import Tuple, Dict, Any
from langdetect import detect
from deep_translator import GoogleTranslator
from sentence_transformers import SentenceTransformer, util
from ultralytics import YOLO

# Bypassing the TensorFlow/Keras Keras 3 compatibility issue
os.environ["USE_TF"] = "NO"
os.environ["TRANSFORMERS_NO_TF"] = "1"
os.environ["USE_TORCH"] = "1"

# Initialize models
print("Initializing AI SentenceTransformer Model...")
try:
    # Small model (90MB), runs fast on CPU
    encoder_model = SentenceTransformer('all-MiniLM-L6-v2')
    print("SentenceTransformer loaded.")
except Exception as e:
    print("Failed to load SentenceTransformer:", e)
    encoder_model = None

print("Initializing AI YOLO Model...")
try:
    # Lightweight COCO model, downloads automatically if not cached (~12MB)
    yolo_model = YOLO("yolov8n.pt")
    print("YOLO model loaded.")
except Exception as e:
    print("Failed to load YOLO:", e)
    yolo_model = None

# Predefined categories and their semantic descriptions for classification
CATEGORIES = [
    "Garbage",
    "Pothole",
    "Water Leakage",
    "No Water Supply",
    "Streetlight",
    "Sewage Overflow",
    "Tree Fall",
    "Road Damage",
    "Illegal Dumping",
    "Others"
]

CATEGORY_PROTOTYPES = {
    "Garbage": "garbage dump trash waste bin litter rubbish sweeping not done stinking pile of waste",
    "Pothole": "pothole road crater street hole cracked asphalt deep pit driving hazard pothole on highway",
    "Water Leakage": "water leakage main pipe burst running water tap leak pipeline broken flooding water wasting",
    "No Water Supply": "no water supply dry taps drinking water shortage low water pressure no municipal water",
    "Streetlight": "streetlight not working dark road street light broken lamp off bulb fuse black street at night",
    "Sewage Overflow": "sewage overflow blocked drain open manhole gutter water stinking sewer leak drainage backup",
    "Tree Fall": "tree fallen down blocked road branch broken uprooted tree storm wind damage blocking path",
    "Road Damage": "road damage broken sidewalk pavement cutting asphalt cracked footpath encroachment curb broken",
    "Illegal Dumping": "illegal dumping debris construction waste concrete bricks empty site trash disposal unauthorized dump",
    "Others": "general complaint animal rescue stray dog noise pollution illegal banners advertisement hoarding park maintenance"
}

# Local translation lookup dict for offline fallback
KANNADA_CIVIC_DICTIONARY = {
    "ಗುಂಡಿ": "pothole",
    "ರಸ್ತೆ": "road",
    "ಕಸ": "garbage",
    "ಕಸದ": "garbage",
    "ಕಸದ ರಾಶಿ": "garbage pile",
    "ನೀರು": "water",
    "ನೀರಿನ ಸೋರಿಕೆ": "water leak",
    "ಬೀದಿ ದೀಪ": "street light",
    "ಬೀದಿ ದೀಪಗಳು": "street lights",
    "ಚರಂಡಿ": "drainage",
    "ಮ್ಯಾನ್ಹೋಲ್": "manhole",
    "ಮರ ಬಿದ್ದಿದೆ": "tree fallen",
    "ಮರದ ಕೊಂಬೆ": "tree branch",
    "ನೀರು ಸರಬರಾಜು ಇಲ್ಲ": "no water supply"
}

def translate_text(text: str) -> Tuple[str, str, float]:
    """
    Detects language (English, Kannada, Hinglish) and translates to English.
    Returns (translated_text, detected_lang, time_taken).
    """
    start_time = time.time()
    detected_lang = "en"
    translated_text = text
    
    # Clean input
    text = text.strip()
    if not text:
        return "", "en", 0.0
        
    try:
        # Detect language
        detected_lang = detect(text)
    except Exception:
        # Fallback to English if detection fails
        detected_lang = "en"
        
    # Translate if not English
    if detected_lang != "en":
        try:
            # Use deep-translator to translate to English
            translator = GoogleTranslator(source='auto', target='en')
            translated_text = translator.translate(text)
        except Exception as e:
            print(f"Translation API failed: {e}. Using local rule-based translation fallback...")
            # Simple local fallback translation for Kannada keywords
            words = text.split()
            translated_words = []
            for w in words:
                translated_words.append(KANNADA_CIVIC_DICTIONARY.get(w, w))
            translated_text = " ".join(translated_words)
            
    time_taken = time.time() - start_time
    return translated_text, detected_lang, time_taken

def classify_complaint(text: str) -> Tuple[str, float]:
    """
    Classifies complaint text into predefined categories using SentenceTransformer semantic similarity.
    """
    if not encoder_model:
        return "Others", 0.50
        
    try:
        # Encode target prototypes
        category_texts = [CATEGORY_PROTOTYPES[cat] for cat in CATEGORIES]
        category_embeddings = encoder_model.encode(category_texts, convert_to_tensor=True)
        
        # Encode input text
        text_embedding = encoder_model.encode(text, convert_to_tensor=True)
        
        # Compute cosine similarity
        cos_scores = util.cos_sim(text_embedding, category_embeddings)[0]
        
        # Find best match
        best_idx = cos_scores.argmax().item()
        confidence = float(cos_scores[best_idx].item())
        
        # Standardize confidence to be between 0.1 and 0.99
        normalized_confidence = max(0.1, min(0.99, confidence))
        
        return CATEGORIES[best_idx], normalized_confidence
    except Exception as e:
        print("Classification failed:", e)
        return "Others", 0.50

def predict_priority(text: str, category_name: str) -> Tuple[str, float]:
    """
    Predicts priority (Low, Medium, High, Critical) based on category defaults and urgency keywords.
    """
    text_lower = text.lower()
    
    # Priority indicators
    critical_keywords = ["manhole", "accident", "injured", "danger", "dead", "hospital", "blocking main road", "gushing", "broken electric wire", "sparking", "flood"]
    high_keywords = ["water logging", "overflowing", "stinking", "cannot walk", "damage to car", "kids", "children", "elderly", "leakage", "dark street", "theft", "unusable"]
    
    # Base priority mapping
    category_defaults = {
        "Garbage": "Medium",
        "Pothole": "Medium",
        "Water Leakage": "Medium",
        "No Water Supply": "High",
        "Streetlight": "Low",
        "Sewage Overflow": "High",
        "Tree Fall": "Medium",
        "Road Damage": "Low",
        "Illegal Dumping": "Medium",
        "Others": "Low"
    }
    
    base_priority = category_defaults.get(category_name, "Medium")
    
    # Check for keyword upgrades
    predicted_priority = base_priority
    confidence = 0.85
    
    if any(k in text_lower for k in critical_keywords):
        predicted_priority = "Critical"
        confidence = 0.95
    elif any(k in text_lower for k in high_keywords):
        if base_priority not in ["Critical", "High"]:
            predicted_priority = "High"
            confidence = 0.90
            
    # Adjust for specific categories
    if category_name == "Streetlight" and "crime" in text_lower or "theft" in text_lower or "scared" in text_lower:
        predicted_priority = "High"
        confidence = 0.80
        
    return predicted_priority, confidence

def verify_image(image_path: str, category_name: str) -> Tuple[bool, float]:
    """
    Verifies if the uploaded image matches a municipal/outdoor street context using YOLO.
    Checks for the presence of street elements like roads, cars, poles, etc.
    """
    if not yolo_model:
        # Fallback if YOLO failed to load
        return True, 0.75
        
    if not os.path.exists(image_path):
        return False, 0.0
        
    try:
        # Run YOLO inference
        results = yolo_model(image_path, verbose=False)
        
        # Extract detected class names
        detected_objects = []
        for r in results:
            for c in r.boxes.cls:
                detected_objects.append(yolo_model.names[int(c)])
                
        print(f"YOLO detected objects in image: {detected_objects}")
        
        # Define street/outdoor objects that validate municipal complaints
        outdoor_indicators = {
            "car", "truck", "bus", "motorcycle", "bicycle", "person", "dog", "cat", 
            "traffic light", "fire hydrant", "stop sign", "bench", "potted plant"
        }
        
        # Verify based on detected objects
        matching_indicators = [obj for obj in detected_objects if obj in outdoor_indicators]
        
        # Heuristics:
        # If the image contains a computer screen, cell phone, or strictly indoor objects like sofa, bed, etc., reject it
        indoor_indicators = {"tv", "laptop", "mouse", "keyboard", "cell phone", "sofa", "bed", "refrigerator"}
        is_indoor_device = any(obj in detected_objects for obj in indoor_indicators)
        
        # Verified if outdoor elements present, and not an indoor screenshot/device photo
        if len(matching_indicators) > 0 and not is_indoor_device:
            # Verified
            confidence = min(0.99, 0.70 + (0.05 * len(detected_objects)))
            return True, confidence
        elif len(detected_objects) == 0:
            # No objects detected at all (e.g. close-up of a road hole or garbage pile)
            # This is normal for close-up complaint shots, so we verify but with moderate confidence
            return True, 0.65
        elif is_indoor_device:
            # Device screen / indoor shot
            return False, 0.90
        else:
            # Only indoor items found
            return False, 0.70
            
    except Exception as e:
        print("YOLO image verification failed:", e)
        # Fallback
        return True, 0.50
