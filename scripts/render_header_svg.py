#!/usr/bin/env python3
"""
render_header_svg.py — a wide animated banner for the very top of
the profile: a slow-breathing gradient background, a glowing frame,
and a two-line greeting that types itself in and ends on an
infinitely blinking cursor.

Usage:
    python scripts/render_header_svg.py [header-banner.svg]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from theme import CARD_WIDTH, TEXT_BRIGHT, GREEN, CYAN, PURPLE, MUTED, FONT, escape_xml  # noqa: E402

WIDTH = CARD_WIDTH
HEIGHT = 150

LINE1 = "Hi, I'm Mayank Rathi"
LINE2 = "Building AI/ML systems & full-stack products."

CHAR_W = 13.5   # approx monospace advance at this font-size
FONT_SIZE_1 = 22
FONT_SIZE_2 = 15
CHAR_W_2 = 9.2

LINE1_DUR = 0.9
LINE2_DELAY = LINE1_DUR + 0.15
LINE2_DUR = 0.9
CURSOR_START = LINE2_DELAY + LINE2_DUR


def build_svg() -> str:
    line1_w = len(LINE1) * CHAR_W
    line2_w = len(LINE2) * CHAR_W_2
    cursor_x = 40 + line2_w + 4

    defs = f'''
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0d1117">
        <animate attributeName="stop-color" values="#0d1117;#131a2a;#0d1117"
                 dur="7s" repeatCount="indefinite" />
      </stop>
      <stop offset="55%" stop-color="#111827">
        <animate attributeName="stop-color" values="#111827;#1a1033;#111827"
                 dur="7s" repeatCount="indefinite" />
      </stop>
      <stop offset="100%" stop-color="#0d1117">
        <animate attributeName="stop-color" values="#0d1117;#101d18;#0d1117"
                 dur="7s" repeatCount="indefinite" />
      </stop>
    </linearGradient>

    <linearGradient id="borderGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="{GREEN}" />
      <stop offset="50%" stop-color="{CYAN}" />
      <stop offset="100%" stop-color="{PURPLE}" />
    </linearGradient>

    <filter id="softGlow" x="-30%" y="-30%" width="160%" height="160%">
      <feGaussianBlur stdDeviation="3.2" result="b" />
      <feMerge>
        <feMergeNode in="b" />
        <feMergeNode in="SourceGraphic" />
      </feMerge>
    </filter>

    <clipPath id="wipe1">
      <rect x="0" y="-30" width="0" height="45">
        <animate attributeName="width" from="0" to="{line1_w + 20}"
                 dur="{LINE1_DUR}s" begin="0.1s" fill="freeze"
                 calcMode="spline" keySplines="0.3 0 0.2 1" />
      </rect>
    </clipPath>
    <clipPath id="wipe2">
      <rect x="0" y="-22" width="0" height="34">
        <animate attributeName="width" from="0" to="{line2_w + 20}"
                 dur="{LINE2_DUR}s" begin="{LINE2_DELAY}s" fill="freeze"
                 calcMode="spline" keySplines="0.3 0 0.2 1" />
      </rect>
    </clipPath>
    '''

    dots = (
        f'<circle cx="18" cy="18" r="6" fill="#ff5f56"/>'
        f'<circle cx="40" cy="18" r="6" fill="#ffbd2e"/>'
        f'<circle cx="62" cy="18" r="6" fill="#27c93f"/>'
    )

    line1 = (
        f'<g transform="translate(40,52)" clip-path="url(#wipe1)">'
        f'<text font-family="{FONT}" font-size="{FONT_SIZE_1}" font-weight="bold" '
        f'fill="{TEXT_BRIGHT}">{escape_xml(LINE1)}</text>'
        f'</g>'
    )

    line2 = (
        f'<g transform="translate(40,86)" clip-path="url(#wipe2)">'
        f'<text font-family="{FONT}" font-size="{FONT_SIZE_2}" fill="{GREEN}">'
        f'{escape_xml(LINE2)}</text>'
        f'</g>'
    )

    cursor = (
        f'<rect x="{cursor_x:.1f}" y="72" width="9" height="16" fill="{GREEN}" '
        f'opacity="0">'
        f'<animate attributeName="opacity" values="0;0;1;0;1;0;1;0;1;0;1"'
        f' keyTimes="0;{CURSOR_START / (CURSOR_START + 3):.3f};'
        f'{(CURSOR_START + 0.3) / (CURSOR_START + 3):.3f};'
        f'{(CURSOR_START + 0.6) / (CURSOR_START + 3):.3f};'
        f'{(CURSOR_START + 0.9) / (CURSOR_START + 3):.3f};'
        f'{(CURSOR_START + 1.2) / (CURSOR_START + 3):.3f};'
        f'{(CURSOR_START + 1.5) / (CURSOR_START + 3):.3f};'
        f'{(CURSOR_START + 1.8) / (CURSOR_START + 3):.3f};'
        f'{(CURSOR_START + 2.1) / (CURSOR_START + 3):.3f};'
        f'{(CURSOR_START + 2.4) / (CURSOR_START + 3):.3f};1"'
        f' dur="{CURSOR_START + 3}s" repeatCount="indefinite" />'
        f'</rect>'
    )

    svg = f'''<svg viewBox="0 0 {WIDTH} {HEIGHT}" width="{WIDTH}" height="{HEIGHT}"
     xmlns="http://www.w3.org/2000/svg" font-family="{FONT}">
  <defs>{defs}</defs>
  <rect width="{WIDTH}" height="{HEIGHT}" rx="14" ry="14" fill="url(#bgGrad)" />
  <rect x="1" y="1" width="{WIDTH - 2}" height="{HEIGHT - 2}" rx="14" ry="14"
        fill="none" stroke="url(#borderGrad)" stroke-width="2" filter="url(#softGlow)" />
  {dots}
  <text x="{WIDTH - 24}" y="22" font-size="11" fill="{MUTED}" text-anchor="end">mayank@github: ~</text>
  {line1}
  {line2}
  {cursor}
</svg>'''
    return svg


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "header-banner.svg"
    Path(out).write_text(build_svg(), encoding="utf-8")
    print(f"Done -> {out}")


if __name__ == "__main__":
    main()
