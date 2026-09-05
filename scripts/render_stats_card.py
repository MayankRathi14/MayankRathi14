#!/usr/bin/env python3
"""
render_stats_card.py — a neofetch-style panel of public GitHub
numbers (repos, stars, followers, member-since) plus a small top
languages bar chart, animated as a staggered scale-in "counter" pop
per stat (SVG can't interpolate digit text, so each number pops in
with a slight overshoot instead of a true count-up).

Usage:
    python scripts/render_stats_card.py [github_stats.json] [stats-card.svg]
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from theme import BG, BG_ALT, BORDER, TEXT, TEXT_BRIGHT, MUTED, GREEN, CYAN, PURPLE, FONT, titlebar, escape_xml  # noqa: E402

IN_DEFAULT = "data/github_stats.json"
OUT_DEFAULT = "stats-card.svg"

WIDTH = 420
TITLEBAR_H = 34

STAT_COLORS = [GREEN, CYAN, PURPLE, "#ffb86c"]
STAGGER = 0.12
DUR = 0.5

LANG_COLORS = {
    "Python": "#3572A5", "TypeScript": "#3178c6", "JavaScript": "#f1e05a",
    "Jupyter Notebook": "#DA5B0B", "Java": "#b07219", "C++": "#f34b7d",
    "HTML": "#e34c26", "CSS": "#563d7c",
}


def build_svg(stats: dict) -> str:
    stat_blocks = [
        ("Repos", stats.get("public_repos", 0)),
        ("Stars", stats.get("total_stars", 0)),
        ("Followers", stats.get("followers", 0)),
        ("Since", stats.get("member_since", "?")),
    ]

    block_w = (WIDTH - 40) / 4
    stats_y = TITLEBAR_H + 46

    stat_svg = []
    for i, (label, value) in enumerate(stat_blocks):
        cx = 20 + block_w * i + block_w / 2
        color = STAT_COLORS[i % len(STAT_COLORS)]
        delay = round(i * STAGGER, 3)
        stat_svg.append(
            f'<g transform="translate({cx:.1f},{stats_y:.1f})" opacity="0" '
            f'style="animation:popIn {DUR}s cubic-bezier(.34,1.56,.64,1) {delay}s forwards">'
            f'<text text-anchor="middle" font-family="{FONT}" font-size="22" '
            f'font-weight="bold" fill="{color}">{escape_xml(str(value))}</text>'
            f'<text text-anchor="middle" y="20" font-family="{FONT}" font-size="10.5" '
            f'fill="{MUTED}">{escape_xml(label)}</text>'
            f'</g>'
        )

    # Divider under the stat row
    divider_y = stats_y + 34
    divider = f'<line x1="20" y1="{divider_y}" x2="{WIDTH - 20}" y2="{divider_y}" stroke="{BORDER}" stroke-width="1" />'

    # Top languages mini bar chart (each bar gets its own keyframe since
    # SVG/CSS can't parameterize a keyframe's target value per-element).
    langs = stats.get("top_languages", [])
    lang_y = divider_y + 24
    bar_keyframes = []
    bar_elems = []
    if langs:
        max_count = max(l["count"] for l in langs)
        bar_max_w = WIDTH - 40 - 130
        for i, lang in enumerate(langs):
            y = lang_y + i * 22
            color = LANG_COLORS.get(lang["name"], CYAN)
            bar_w = max(6, bar_max_w * lang["count"] / max_count)
            delay = round(0.4 + i * 0.08, 3)
            anim_name = f"growBar{i}"
            bar_keyframes.append(
                f'@keyframes {anim_name} {{ from {{ width: 0; }} to {{ width: {bar_w:.1f}px; }} }}'
            )
            bar_elems.append(
                f'<text x="20" y="{y + 10.5}" font-family="{FONT}" font-size="10.5" '
                f'fill="{TEXT}">{escape_xml(lang["name"])}</text>'
                f'<rect x="135" y="{y}" width="0" height="9" rx="4" ry="4" fill="{color}" '
                f'style="animation:{anim_name} {DUR}s cubic-bezier(.2,0,.2,1) {delay}s forwards" />'
            )
        lang_body = (
            f'<text x="20" y="{lang_y - 10}" font-family="{FONT}" font-size="10.5" '
            f'fill="{MUTED}">Top languages</text>'
        ) + "".join(bar_elems)
        height = lang_y + len(langs) * 22 + 16
    else:
        lang_body = ""
        height = lang_y + 10

    style = f'''
    <style>
      @keyframes popIn {{
        0%   {{ opacity: 0; transform: scale(0.5); }}
        60%  {{ opacity: 1; transform: scale(1.12); }}
        100% {{ opacity: 1; transform: scale(1); }}
      }}
      {"".join(bar_keyframes)}
    </style>
    '''

    svg = f'''<svg viewBox="0 0 {WIDTH} {height:.0f}" width="{WIDTH}" height="{height:.0f}"
     xmlns="http://www.w3.org/2000/svg" font-family="{FONT}">
  <defs>{style}</defs>
  <rect width="{WIDTH}" height="{height:.0f}" rx="12" ry="12" fill="{BG}" stroke="{BORDER}" stroke-width="1.3" />
  <g>{titlebar(WIDTH, "gh --stat", h=TITLEBAR_H)}</g>
{"".join(stat_svg)}
{divider}
{lang_body}
</svg>'''
    return svg


def main():
    in_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(IN_DEFAULT)
    out_path = sys.argv[2] if len(sys.argv) > 2 else OUT_DEFAULT

    if not in_path.exists():
        print(f"Error: {in_path} not found. Run fetch_github_stats.py first.")
        sys.exit(1)

    stats = json.loads(in_path.read_text(encoding="utf-8"))
    print(f"Rendering stats card for {stats.get('username', '?')} ...")
    Path(out_path).write_text(build_svg(stats), encoding="utf-8")
    print(f"Done -> {out_path}")


if __name__ == "__main__":
    main()
