#!/usr/bin/env python3
"""
render_skills_badges.py — tech stack as grouped, color-coded chips
that pop in with a staggered scale+fade, grouped by category with
a colored accent per group instead of one flat undifferentiated list.

Usage:
    python scripts/render_skills_badges.py [skills-badges.svg]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from theme import CARD_WIDTH, BG, TEXT, MUTED, FONT, escape_xml  # noqa: E402

WIDTH = CARD_WIDTH

GROUPS = [
    ("Languages", "#56d4dd", ["Python", "Java", "C++", "SQL", "JavaScript", "TypeScript"]),
    ("Backend & Web", "#39d353", ["FastAPI", "Flask", "React"]),
    ("AI / ML", "#bd93f9", ["LangChain", "OpenAI", "FAISS", "Sentence Transformers",
                             "PyTorch", "PyTorch Geometric", "Hugging Face"]),
    ("Data & DB", "#ffb86c", ["MongoDB", "PostgreSQL", "MySQL"]),
    ("Tools", "#ff79c6", ["Git", "GitHub"]),
]

PAD_X = 20
GROUP_LABEL_H = 26
CHIP_H = 28
CHIP_GAP_X = 8
CHIP_GAP_Y = 10
GROUP_GAP_Y = 20
CHAR_W = 7.1
CHIP_PAD_X = 16

STAGGER = 0.035
DUR = 0.35


def chip_width(text: str) -> float:
    return len(text) * CHAR_W + CHIP_PAD_X * 2


def layout_group(items: list[str], max_width: float):
    """Greedy-wrap chips into rows; return list of rows, each a list of (text, width)."""
    rows, row, row_w = [], [], 0.0
    for item in items:
        w = chip_width(item)
        if row and row_w + CHIP_GAP_X + w > max_width:
            rows.append(row)
            row, row_w = [], 0.0
        row.append((item, w))
        row_w += (CHIP_GAP_X if row_w else 0) + w
    if row:
        rows.append(row)
    return rows


def build_svg() -> str:
    max_w = WIDTH - PAD_X * 2
    y_cursor = 30
    body = []
    chip_index = 0

    for group_name, color, items in GROUPS:
        body.append(
            f'<circle cx="{PAD_X + 4}" cy="{y_cursor - 5}" r="4" fill="{color}" />'
            f'<text x="{PAD_X + 16}" y="{y_cursor}" font-family="{FONT}" '
            f'font-size="12.5" font-weight="bold" fill="{color}">'
            f'{escape_xml(group_name)}</text>'
        )
        y_cursor += GROUP_LABEL_H

        rows = layout_group(items, max_w)
        for row in rows:
            x_cursor = PAD_X
            for text, w in row:
                delay = round(chip_index * STAGGER, 3)
                body.append(
                    f'<g transform="translate({x_cursor + w / 2:.1f},{y_cursor + CHIP_H / 2:.1f})" '
                    f'opacity="0" style="animation:chipIn {DUR}s cubic-bezier(.2,0,.2,1) '
                    f'{delay}s forwards">'
                    f'<g transform="translate({-w / 2:.1f},{-CHIP_H / 2:.1f})">'
                    f'<rect width="{w:.1f}" height="{CHIP_H}" rx="8" ry="8" '
                    f'fill="{BG}" stroke="{color}" stroke-width="1.3" stroke-opacity="0.8" />'
                    f'<rect width="{w:.1f}" height="{CHIP_H}" rx="8" ry="8" '
                    f'fill="{color}" fill-opacity="0.08" />'
                    f'<text x="{w / 2:.1f}" y="{CHIP_H / 2 + 4.5}" text-anchor="middle" '
                    f'font-family="{FONT}" font-size="11.5" fill="{TEXT}">'
                    f'{escape_xml(text)}</text>'
                    f'</g></g>'
                )
                x_cursor += w + CHIP_GAP_X
                chip_index += 1
            y_cursor += CHIP_H + CHIP_GAP_Y
        y_cursor += GROUP_GAP_Y - CHIP_GAP_Y

    height = y_cursor + 4

    style = '''
    <style>
      @keyframes chipIn {
        0%   { opacity: 0; transform: scale(0.75); }
        70%  { opacity: 1; transform: scale(1.05); }
        100% { opacity: 1; transform: scale(1); }
      }
    </style>
    '''

    svg = f'''<svg viewBox="0 0 {WIDTH} {height:.0f}" width="{WIDTH}" height="{height:.0f}"
     xmlns="http://www.w3.org/2000/svg" font-family="{FONT}">
  <defs>{style}</defs>
  <rect width="100%" height="100%" fill="transparent" />
{"".join(body)}
</svg>'''
    return svg


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "skills-badges.svg"
    Path(out).write_text(build_svg(), encoding="utf-8")
    print(f"Done -> {out}")


if __name__ == "__main__":
    main()
