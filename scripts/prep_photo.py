#!/usr/bin/env python3
"""
prep_photo.py — turn a normal photo into a clean grayscale source
ready for ASCII conversion.

Usage:
    python scripts/prep_photo.py source-photo.jpg [output.png]

Pipeline:
    1. Remove the background with rembg so only the subject remains.
    2. Composite the cutout onto pure white (so background -> blank
       glyphs later instead of dark noise).
    3. Convert to grayscale and boost local contrast with OpenCV's
       CLAHE, which is what gives a flatly-lit face real highlights
       and shadows instead of collapsing into a gray blob.

Output: a grayscale PNG, ready for make_ascii_svg.py.
"""
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from rembg import remove


def prep_photo(input_path: str, output_path: str = "source-prepped.png") -> None:
    print(f"[1/3] Loading {input_path} ...")
    with open(input_path, "rb") as f:
        input_bytes = f.read()

    print("[2/3] Removing background (rembg) ...")
    cutout_bytes = remove(input_bytes)
    cutout = Image.open(__import__("io").BytesIO(cutout_bytes)).convert("RGBA")

    # Composite onto pure white so the background maps to the
    # blank end of the ASCII ramp (white -> space glyph).
    white_bg = Image.new("RGBA", cutout.size, (255, 255, 255, 255))
    composited = Image.alpha_composite(white_bg, cutout).convert("RGB")

    print("[3/3] Boosting local contrast (CLAHE) ...")
    img_array = np.array(composited)
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)

    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    contrasted = clahe.apply(gray)

    Image.fromarray(contrasted).save(output_path)
    print(f"Done -> {output_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/prep_photo.py source-photo.jpg [output.png]")
        sys.exit(1)

    src = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else "source-prepped.png"

    if not Path(src).exists():
        print(f"Error: {src} not found")
        sys.exit(1)

    prep_photo(src, out)
