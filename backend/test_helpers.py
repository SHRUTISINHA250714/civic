"""
Shared test helper utilities for CivicAI Karnataka regression and unit test suites.
Generates deterministic, high-quality synthetic JPEG images for evidence and perceptual hash testing.
"""
import os
import tempfile
from typing import List, Optional
import numpy as np
from PIL import Image, ImageDraw

_ACTIVE_TEMP_FILES: List[str] = []


def generate_test_image(seed: int = 42, width: int = 640, height: int = 480, prefix: str = "test_img_") -> str:
    """
    Generates a deterministic synthetic JPEG image file with seeded noise and geometric features.
    
    Guarantees:
      - Valid JPEG decodable by OpenCV and PIL (dimensions width x height).
      - Passes check_image_quality: blur_score >= 25.0, mean brightness between 25.0 and 245.0.
      - Produces a valid 64-bit dHash (16 hex chars).
      - Deterministic: same seed -> identical dHash (Hamming = 0).
      - Distinct: different seeds -> different dHashes (Hamming distance typically > 20, well above 16).
    """
    rng = np.random.RandomState(seed)

    # Base mid-tone canvas (around 120-135 luminance)
    base_lum = rng.randint(110, 140)
    img_arr = np.full((height, width, 3), base_lum, dtype=np.uint8)

    # Seeded noise for texture and edge contrast
    noise = rng.randint(-35, 35, (height, width, 3))
    img_arr = np.clip(img_arr.astype(np.int32) + noise, 0, 255).astype(np.uint8)

    pil_img = Image.fromarray(img_arr)
    draw = ImageDraw.Draw(pil_img)

    # Deterministic geometric shapes (rectangles, ellipses) with high contrast
    for _ in range(8):
        x1 = rng.randint(0, width - 150)
        y1 = rng.randint(0, height - 120)
        x2 = x1 + rng.randint(60, 180)
        y2 = y1 + rng.randint(50, 140)
        color = (rng.randint(20, 235), rng.randint(20, 235), rng.randint(20, 235))
        if rng.rand() > 0.5:
            draw.rectangle([x1, y1, x2, y2], fill=color)
        else:
            draw.ellipse([x1, y1, x2, y2], fill=color)

    # Write out to tempfile
    fd, path = tempfile.mkstemp(prefix=prefix, suffix=".jpg")
    os.close(fd)
    pil_img.save(path, format="JPEG", quality=90)

    _ACTIVE_TEMP_FILES.append(path)
    return path


def get_test_image_bytes(seed: int = 42, width: int = 640, height: int = 480) -> bytes:
    """Returns the raw JPEG bytes of a generated test image."""
    path = generate_test_image(seed=seed, width=width, height=height)
    try:
        with open(path, "rb") as f:
            return f.read()
    finally:
        cleanup_temp_images(path)


def cleanup_temp_images(*paths: str) -> None:
    """Removes specified test images or all tracked temp files."""
    targets = list(paths) if paths else list(_ACTIVE_TEMP_FILES)
    for p in targets:
        try:
            if p and os.path.exists(p):
                os.unlink(p)
        except OSError:
            pass
        if p in _ACTIVE_TEMP_FILES:
            _ACTIVE_TEMP_FILES.remove(p)
