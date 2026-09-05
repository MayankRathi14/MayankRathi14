#!/usr/bin/env python3
"""
make_info_card.py — hand-authored neofetch-style SVG panel.

Usage:
    python scripts/make_info_card.py [output.svg]

Env:
    STATIC=1   Emit a frozen (no-animation) frame, useful for local
               Quick Look / image-viewer previews that don't render SMIL.

Content lives here as data, not the contribution graph — the graph
already covers GitHub stats, so this card is for the story numbers
can't tell (role, background, stack, highlights, socials).
"""
import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------
TITLE = "avi@github"

FIELDS = [
    ("Now", [
        "Building AI/ML systems and full-stack",
        "applications, with a focus on practical",
        "AI solutions.",
    ]),
    ("Prev", [
        "B.Tech, Computer Science & Engineering",
        "(AI & ML) — AI, machine learning,",
        "software dev & problem solving.",
    ]),
    ("Stack", [
        "Python · Java · C++ · SQL",
        "FastAPI · Flask · React · JS · TS",
        "LangChain · OpenAI · FAISS",
        "Sentence Transformers · PyTorch",
        "PyTorch Geometric · Hugging Face",
        "MongoDB · PostgreSQL · MySQL",
        "Git · GitHub",
    ]),
    ("Highlights", [
        "ArguLex — AI legal assistant (RAG,",
        "  FAISS, Sentence Transformers,",
        "  LangChain, OpenAI, PyMuPDF) for",
        "  semantic legal search & case",
        "  analysis over PDFs.",
        "FinGAT v2 — AI stock prediction",
        "  combining Graph Attention Networks",
        "  + RL across 147+ Indian stocks,",
        "  10+ sectors, auto data refresh",
        "  & retraining.",
        "Full-stack AI apps: Python/FastAPI",
        "  backends wired to modern web UIs.",
    ]),
    ("Socials", [
        "GitHub    github.com/MayankRathi14",
        "LinkedIn  linkedin.com/in/mayank-rathi-660382379",
        "Email     mayankrathi2006@gmail.com",
    ]),
]

# ---------------------------------------------------------------------------
# Style tokens — dark terminal palette
# ---------------------------------------------------------------------------
BG = "#0d1117"
BORDER = "#30363d"
TITLEBAR_BG = "#161b22"
DOT_RED, DOT_YELLOW, DOT_GREEN = "#ff5f56", "#ffbd2e", "#27c93f"
LABEL_COLOR = "#39d353"      # GitHub-green accent for keys
VALUE_COLOR = "#c9d1d9"      # light gray for values
MUTED_COLOR = "#8b949e"

FONT = "monospace"
FONT_SIZE = 12.5
LINE_H = 17
LABEL_COL_W = 92
PAD_X = 20
PAD_TOP = 54
TITLEBAR_H = 34
WIDTH = 490

STAGGER = 0.05   # seconds between successive lines
DUR = 0.35       # seconds for a line's fade+slide


def escape_xml(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def build_lines():
    """Flatten FIELDS into (label_or_None, text, is_first_of_field) rows."""
    lines = []
    for label, values in FIELDS:
        for i, v in enumerate(values):
            lines.append((label if i == 0 else None, v, i == 0))
    return lines


def build_svg(static: bool) -> str:
    lines = build_lines()
    height = PAD_TOP + len(lines) * LINE_H + 22

    body = []
    line_idx = 0
    for label, value, is_first in lines:
        y = PAD_TOP + line_idx * LINE_H
        begin = round(line_idx * STAGGER, 3)

        anim_attrs = ""
        opacity_start = "1" if static else "0"
        x_offset = 0 if static else -8

        parts = []
        if label:
            parts.append(
                f'<text x="{PAD_X}" y="{y}" font-family="{FONT}" '
                f'font-size="{FONT_SIZE}" font-weight="bold" fill="{LABEL_COLOR}">'
                f'{escape_xml(label)}</text>'
            )
        value_x = PAD_X + LABEL_COL_W
        parts.append(
            f'<text x="{value_x}" y="{y}" font-family="{FONT}" '
            f'font-size="{FONT_SIZE}" fill="{VALUE_COLOR}">{escape_xml(value)}</text>'
        )

        row = f'<g opacity="{opacity_start}" transform="translate({x_offset},0)">' + "".join(parts) + '</g>'

        if not static:
            row = (
                f'<g>'
                f'<animateTransform attributeName="transform" attributeType="XML" '
                f'type="translate" from="{x_offset} 0" to="0 0" dur="{DUR}s" '
                f'begin="{begin}s" fill="freeze" calcMode="spline" '
                f'keySplines="0.2 0 0.2 1" />'
                f'<animate attributeName="opacity" from="0" to="1" dur="{DUR}s" '
                f'begin="{begin}s" fill="freeze" />'
                + "".join(parts) +
                f'</g>'
            )
        body.append(row)
        line_idx += 1

    dots = f'''
    <circle cx="{PAD_X + 6}" cy="{TITLEBAR_H / 2 + 2}" r="6" fill="{DOT_RED}" />
    <circle cx="{PAD_X + 28}" cy="{TITLEBAR_H / 2 + 2}" r="6" fill="{DOT_YELLOW}" />
    <circle cx="{PAD_X + 50}" cy="{TITLEBAR_H / 2 + 2}" r="6" fill="{DOT_GREEN}" />
    '''

    svg = f'''<svg viewBox="0 0 {WIDTH} {height:.0f}" width="{WIDTH}" height="{height:.0f}"
     xmlns="http://www.w3.org/2000/svg" font-family="{FONT}">
  <defs>
    <clipPath id="rounded">
      <rect x="0" y="0" width="{WIDTH}" height="{height:.0f}" rx="10" ry="10" />
    </clipPath>
  </defs>
  <g clip-path="url(#rounded)">
    <rect width="{WIDTH}" height="{height:.0f}" fill="{BG}" />
    <rect width="{WIDTH}" height="{TITLEBAR_H}" fill="{TITLEBAR_BG}" />
    <rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{height:.0f} - 1" fill="none" stroke="{BORDER}" />
    {dots}
    <text x="{WIDTH / 2}" y="{TITLEBAR_H / 2 + 4.5}" font-size="12" fill="{MUTED_COLOR}"
          text-anchor="middle">{escape_xml(TITLE)}</text>
{"".join(body)}
  </g>
  <rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{height:.0f}" rx="10" ry="10"
        fill="none" stroke="{BORDER}" />
</svg>'''
    return svg


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "info-card.svg"
    static = os.environ.get("STATIC") == "1"

    print(f"Building info card ({'static' if static else 'animated'}) ...")
    svg = build_svg(static)

    Path(out).write_text(svg, encoding="utf-8")
    print(f"Done -> {out}")


if __name__ == "__main__":
    main()
