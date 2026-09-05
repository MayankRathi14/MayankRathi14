#!/usr/bin/env python3
"""
render_streak_card.py — current streak / longest streak / total
contributions, pulled from data/contributions.json (already
computed by fetch_contributions.py). The current-streak flame gets
a soft looping pulse when the streak is active (>0).

Usage:
    python scripts/render_streak_card.py [contributions.json] [streak-card.svg]
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from theme import BG, BORDER, TEXT, MUTED, GREEN, ORANGE, CYAN, FONT, titlebar, escape_xml  # noqa: E402

IN_DEFAULT = "data/contributions.json"
OUT_DEFAULT = "streak-card.svg"

WIDTH = 420
TITLEBAR_H = 34
HEIGHT = TITLEBAR_H + 130


def flame_icon(cx: float, cy: float, color: str, pulsing: bool) -> str:
    pulse = ""
    if pulsing:
        pulse = (
            f'<animate attributeName="opacity" values="0.55;0.9;0.55" '
            f'dur="1.8s" repeatCount="indefinite" />'
        )
    glow = (
        f'<circle cx="{cx}" cy="{cy}" r="16" fill="{color}" opacity="0.35">'
        f'{pulse}</circle>'
    ) if pulsing else ""
    return (
        f'{glow}'
        f'<path transform="translate({cx - 9},{cy - 12}) scale(0.75)" '
        f'd="M9 0C9 5 4 6 4 11a5 5 0 0 0 10 0c0-2-1-3-1-3s2 1 2 5a7 7 0 0 1-14 0'
        f'C1 8 5 6 9 0Z" fill="{color}" />'
    )


def build_svg(data: dict) -> str:
    stats = data.get("stats", {})
    current = stats.get("current_streak", 0)
    longest = stats.get("longest_streak", 0)
    total = stats.get("total", 0)

    center_y = TITLEBAR_H + 70
    col_w = WIDTH / 3

    blocks = []

    # Current streak (with flame)
    cx1 = col_w * 0.5
    blocks.append(flame_icon(cx1, center_y - 32, ORANGE if current > 0 else MUTED, current > 0))
    blocks.append(
        f'<g style="animation:popIn 0.5s cubic-bezier(.34,1.56,.64,1) 0s forwards" opacity="0" '
        f'transform-origin="{cx1}px {center_y}px">'
        f'<text x="{cx1}" y="{center_y + 8}" text-anchor="middle" font-family="{FONT}" '
        f'font-size="26" font-weight="bold" fill="{ORANGE if current > 0 else TEXT}">{current}</text>'
        f'<text x="{cx1}" y="{center_y + 26}" text-anchor="middle" font-family="{FONT}" '
        f'font-size="10.5" fill="{MUTED}">Current streak</text>'
        f'</g>'
    )

    # Longest streak
    cx2 = col_w * 1.5
    blocks.append(
        f'<g style="animation:popIn 0.5s cubic-bezier(.34,1.56,.64,1) 0.12s forwards" opacity="0" '
        f'transform-origin="{cx2}px {center_y}px">'
        f'<text x="{cx2}" y="{center_y - 20}" text-anchor="middle" font-size="18">🏆</text>'
        f'<text x="{cx2}" y="{center_y + 8}" text-anchor="middle" font-family="{FONT}" '
        f'font-size="26" font-weight="bold" fill="{CYAN}">{longest}</text>'
        f'<text x="{cx2}" y="{center_y + 26}" text-anchor="middle" font-family="{FONT}" '
        f'font-size="10.5" fill="{MUTED}">Longest streak</text>'
        f'</g>'
    )

    # Total contributions
    cx3 = col_w * 2.5
    blocks.append(
        f'<g style="animation:popIn 0.5s cubic-bezier(.34,1.56,.64,1) 0.24s forwards" opacity="0" '
        f'transform-origin="{cx3}px {center_y}px">'
        f'<text x="{cx3}" y="{center_y - 20}" text-anchor="middle" font-size="18">📊</text>'
        f'<text x="{cx3}" y="{center_y + 8}" text-anchor="middle" font-family="{FONT}" '
        f'font-size="26" font-weight="bold" fill="{GREEN}">{total:,}</text>'
        f'<text x="{cx3}" y="{center_y + 26}" text-anchor="middle" font-family="{FONT}" '
        f'font-size="10.5" fill="{MUTED}">Contributions</text>'
        f'</g>'
    )

    dividers = (
        f'<line x1="{col_w}" y1="{TITLEBAR_H + 20}" x2="{col_w}" y2="{HEIGHT - 20}" '
        f'stroke="{BORDER}" stroke-width="1" />'
        f'<line x1="{col_w * 2}" y1="{TITLEBAR_H + 20}" x2="{col_w * 2}" y2="{HEIGHT - 20}" '
        f'stroke="{BORDER}" stroke-width="1" />'
    )

    style = '''
    <style>
      @keyframes popIn {
        0%   { opacity: 0; transform: scale(0.5); }
        60%  { opacity: 1; transform: scale(1.12); }
        100% { opacity: 1; transform: scale(1); }
      }
    </style>
    '''

    svg = f'''<svg viewBox="0 0 {WIDTH} {HEIGHT}" width="{WIDTH}" height="{HEIGHT}"
     xmlns="http://www.w3.org/2000/svg" font-family="{FONT}">
  <defs>{style}</defs>
  <rect width="{WIDTH}" height="{HEIGHT}" rx="12" ry="12" fill="{BG}" stroke="{BORDER}" stroke-width="1.3" />
  <g>{titlebar(WIDTH, "gh --streak", h=TITLEBAR_H)}</g>
  {dividers}
{"".join(blocks)}
</svg>'''
    return svg


def main():
    in_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(IN_DEFAULT)
    out_path = sys.argv[2] if len(sys.argv) > 2 else OUT_DEFAULT

    if not in_path.exists():
        print(f"Error: {in_path} not found. Run fetch_contributions.py first.")
        sys.exit(1)

    data = json.loads(in_path.read_text(encoding="utf-8"))
    print("Rendering streak card ...")
    Path(out_path).write_text(build_svg(data), encoding="utf-8")
    print(f"Done -> {out_path}")


if __name__ == "__main__":
    main()
