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

    last_row_begin = round((len(ascii_rows) - 1) * ROW_STAGGER, 3)
    final_cursor_start = round(last_row_begin + ROW_DURATION + 0.15, 3)
    last_row_width = len(ascii_rows[-1]) * CHAR_W if ascii_rows else 0
    final_cursor_y = 10 + (len(ascii_rows) - 1) * CHAR_H

    final_cursor = (
        f'<rect x="{10 + last_row_width + 2:.1f}" y="{final_cursor_y - CHAR_H + 1:.1f}" '
        f'width="{CHAR_W * 0.9:.2f}" height="{CHAR_H - 2:.2f}" fill="{CURSOR_COLOR}" opacity="0">'
        f'<animate attributeName="opacity" values="0;1;0" dur="1s" '
        f'begin="{final_cursor_start}s" repeatCount="indefinite" />'
        f'</rect>'
    )

    panel_pad = 16
    titlebar_h = 32
    full_w = width + panel_pad * 2
    full_h = height + panel_pad * 2 + titlebar_h

    titlebar = f'''
    <rect width="{full_w:.0f}" height="{titlebar_h}" rx="14" ry="14" fill="#161b22" />
    <rect y="{titlebar_h - 14}" width="{full_w:.0f}" height="14" fill="#161b22" />
    <circle cx="26" cy="{titlebar_h / 2}" r="6" fill="#ff5f56" />
    <circle cx="48" cy="{titlebar_h / 2}" r="6" fill="#ffbd2e" />
    <circle cx="70" cy="{titlebar_h / 2}" r="6" fill="#27c93f" />
    <text x="{full_w / 2:.0f}" y="{titlebar_h / 2 + 4.5}" font-size="12" fill="#8b949e"
          text-anchor="middle" font-family="monospace">whoami.sh</text>
    '''

    svg = f'''<svg viewBox="0 0 {full_w:.0f} {full_h:.0f}" width="{full_w:.0f}" height="{full_h:.0f}"
     xmlns="http://www.w3.org/2000/svg" font-family="monospace">
  <defs>
{"".join(defs)}
    <linearGradient id="asciiBorderGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#39d353" />
      <stop offset="50%" stop-color="#56d4dd" />
      <stop offset="100%" stop-color="#bd93f9" />
    </linearGradient>
    <filter id="asciiGlow" x="-30%" y="-30%" width="160%" height="160%">
      <feGaussianBlur stdDeviation="2.5" result="b" />
      <feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge>
    </filter>
    <clipPath id="asciiRounded">
      <rect width="{full_w:.0f}" height="{full_h:.0f}" rx="14" ry="14" />
    </clipPath>
  </defs>
  <g clip-path="url(#asciiRounded)">
    <rect width="{full_w:.0f}" height="{full_h:.0f}" fill="{BG_COLOR if BG_COLOR != 'transparent' else '#0d1117'}" />
    {titlebar}
    <g transform="translate({panel_pad},{titlebar_h + panel_pad - 10})">
{"".join(rows_svg)}
{final_cursor}
    </g>
  </g>
  <rect x="1" y="1" width="{full_w - 2:.0f}" height="{full_h - 2:.0f}" rx="14" ry="14"
        fill="none" stroke="url(#asciiBorderGrad)" stroke-width="1.6" filter="url(#asciiGlow)" />
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
