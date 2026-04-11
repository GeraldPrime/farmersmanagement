"""
Compress login background images to ~500 KB.
Run locally:  python compress_images.py
Run on server: python compress_images.py  (same command)
"""

import os
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    raise SystemExit("Pillow is not installed. Run: pip install Pillow")

# ── Config ────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
IMAGE_DIR = BASE_DIR / "farmers" / "static" / "assets" / "images" / "imageoptions"
TARGET_KB  = 500          # target max file size in KB
MAX_WIDTH  = 1920         # pixels — enough for a full-HD background
JPEG_START = 85           # start quality here and step down if needed
JPEG_MIN   = 30           # never go below this quality

IMAGES = [
    "beautiful-atlantic-landscape.jpg",
    "beautiful-mountain-lake-background-remix.jpg",
]
# ──────────────────────────────────────────────────────────────────────────────


def compress(path: Path, target_kb: int) -> None:
    target_bytes = target_kb * 1024

    img = Image.open(path).convert("RGB")

    # Resize if wider than MAX_WIDTH (keep aspect ratio)
    if img.width > MAX_WIDTH:
        ratio = MAX_WIDTH / img.width
        new_size = (MAX_WIDTH, int(img.height * ratio))
        img = img.resize(new_size, Image.LANCZOS)
        print(f"  Resized to {new_size[0]}×{new_size[1]}")

    original_bytes = path.stat().st_size
    quality = JPEG_START

    while quality >= JPEG_MIN:
        img.save(path, "JPEG", quality=quality, optimize=True, progressive=True)
        new_bytes = path.stat().st_size
        if new_bytes <= target_bytes:
            break
        quality -= 5

    print(
        f"  {path.name}: "
        f"{original_bytes / 1024:.0f} KB → {new_bytes / 1024:.0f} KB  "
        f"(quality={quality})"
    )


def main():
    print(f"Target: ≤ {TARGET_KB} KB per image\n")
    for name in IMAGES:
        path = IMAGE_DIR / name
        if not path.exists():
            print(f"  SKIPPED (not found): {path}")
            continue
        print(f"Processing: {name}")
        compress(path, TARGET_KB)
    print("\nDone.")


if __name__ == "__main__":
    main()
