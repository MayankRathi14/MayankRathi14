#!/usr/bin/env python3
"""
make_ascii_svg.py — convert a prepped grayscale photo into a
self-typing, monochrome ASCII-art SVG.

Usage:
    python scripts/make_ascii_svg.py [source-prepped.png] [avi-ascii.svg]

How it works:
    - Downsample the image to a character grid (~COLS x ROWS).
    - Map each cell's average brightness to a glyph on a density
      ramp (bright -> sparse, dark -> dense).
    - Render one row of monospace <text> per image row.
    - Wrap each row in a clipPath whose reveal rect animates from
      width 0 -> full width (SMIL <animate>), staggered top to
      bottom, so the portrait looks like it's typing itself in.
    - A small "cursor" block rides the leading edge of each row's
      wipe, then the whole thing freezes (fill="freeze"), no loop.

Only monochrome fill is used on purpose: per-character rainbow
coloring is what makes most ASCII art look noisy instead of clean.
"""
import sys
from pathlib import Path

from PIL import Image

# Bright (sparse) -> dark (dense). Leading space clears background to nothing.
RAMP = " .`:-=+*cs#%@"

COLS = 100
ROWS = 53

FONT_SIZE = 8
CHAR_W = FONT_SIZE * 0.6   # approx monospace advance width
CHAR_H = FONT_SIZE * 1.0

FILL_COLOR = "#c9d1d9"      # light gray, monochrome
BG_COLOR = "transparent"
CURSOR_COLOR = "#39d353"    # small accent block riding the wipe edge

ROW_STAGGER = 0.045         # seconds between each row starting
ROW_DURATION = 0.28         # seconds for a single row to wipe in


def image_to_ascii_rows(img: Image.Image, cols: int, rows: int) -> list[str]:
    img = img.convert("L")
    resized = img.resize((cols, rows))
    pixels = resized.load()

    ramp_len = len(RAMP)
    ascii_rows = []
    for y in range(rows):
        row_chars = []
        for x in range(cols):
            brightness = pixels[x, y]  # 0 (dark) - 255 (bright)
            # bright -> low index (sparse), dark -> high index (dense)
            idx = int((255 - brightness) / 255 * (ramp_len - 1))
            row_chars.append(RAMP[idx])
        ascii_rows.append("".join(row_chars))
    return ascii_rows


def escape_xml(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def build_svg(ascii_rows: list[str]) -> str:
    width = COLS * CHAR_W + 20
    height = ROWS * CHAR_H + 20

    defs = []
    rows_svg = []

    for i, row in enumerate(ascii_rows):
        row_text = escape_xml(row)
        row_width = len(row) * CHAR_W
        y = 10 + i * CHAR_H
        begin = round(i * ROW_STAGGER, 3)
        clip_id = f"clip{i}"

        # Clip rect wipes from width 0 -> full row width, then freezes.
        defs.append(
            f'<clipPath id="{clip_id}">'
            f'<rect x="10" y="{y - CHAR_H}" width="0" height="{CHAR_H + 2}">'
            f'<animate attributeName="width" from="0" to="{row_width}" '
            f'dur="{ROW_DURATION}s" begin="{begin}s" fill="freeze" '
            f'calcMode="spline" keySplines="0.4 0 0.2 1" />'
            f'</rect>'
            f'</clipPath>'
        )

        # Small cursor block that rides the wipe edge, then vanishes.
        cursor = (
            f'<rect x="10" y="{y - CHAR_H + 1}" width="{CHAR_W * 0.9:.2f}" '
            f'height="{CHAR_H - 2:.2f}" fill="{CURSOR_COLOR}" opacity="0">'
            f'<animate attributeName="opacity" values="0;1;1;0" '
            f'keyTimes="0;0.01;0.9;1" dur="{ROW_DURATION}s" begin="{begin}s" '
            f'fill="freeze" />'
            f'<animate attributeName="x" from="10" to="{10 + row_width}" '
            f'dur="{ROW_DURATION}s" begin="{begin}s" fill="freeze" '
            f'calcMode="spline" keySplines="0.4 0 0.2 1" />'
            f'</rect>'
        )

        rows_svg.append(
            f'<g clip-path="url(#{clip_id})">'
            f'<text x="10" y="{y}" font-family="monospace" '
            f'font-size="{FONT_SIZE}" fill="{FILL_COLOR}" '
            f'xml:space="preserve">{row_text}</text>'
            f'</g>'
            f'{cursor}'
        )

    svg = f'''<svg viewBox="0 0 {width:.0f} {height:.0f}" width="{width:.0f}" height="{height:.0f}"
     xmlns="http://www.w3.org/2000/svg" font-family="monospace">
  <defs>
{"".join(defs)}
  </defs>
  <rect width="100%" height="100%" fill="{BG_COLOR}" />
{"".join(rows_svg)}
</svg>'''
    return svg


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "source-prepped.png"
    out = sys.argv[2] if len(sys.argv) > 2 else "mayank-ascii.svg"

    if not Path(src).exists():
        print(f"Error: {src} not found. Run prep_photo.py first.")
        sys.exit(1)

    img = Image.open(src)
    print(f"Converting {src} to {COLS}x{ROWS} ASCII grid ...")
    ascii_rows = image_to_ascii_rows(img, COLS, ROWS)

    print("Building self-typing SVG ...")
    svg = build_svg(ascii_rows)

    Path(out).write_text(svg, encoding="utf-8")
    print(f"Done -> {out}")


if __name__ == "__main__":
    main()
