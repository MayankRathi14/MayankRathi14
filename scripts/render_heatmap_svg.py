#!/usr/bin/env python3
"""
render_heatmap_svg.py — render data/contributions.json as the
classic 53-week x 7-day GitHub contribution calendar, with a
diagonal line-after-line slide-down reveal (CSS keyframes, plays
once on load, then freezes — no looping "glow").

Usage:
    python scripts/render_heatmap_svg.py [contributions.json] [contrib-heatmap.svg]
"""
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

IN_DEFAULT = "data/contributions.json"
OUT_DEFAULT = "contrib-heatmap.svg"

# none -> brightest (level 5 is a neon top end, used only for the
# single best day so the graph has one moment of extra pop).
PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]

BOX = 11
GAP = 3
CELL = BOX + GAP
LEFT_PAD = 28      # room for day-of-week labels
TOP_PAD = 20        # room for month labels
BOTTOM_PAD = 34      # room for legend
RIGHT_PAD = 46

DAY_LABELS = {1: "Mon", 3: "Wed", 5: "Fri"}  # sparse labels like GitHub's own UI
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

STAGGER = 0.018     # seconds per diagonal step (col + row)
DUR = 0.32


def escape_xml(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def build_weeks(days: list[dict]) -> list[list[dict | None]]:
    """Group flat day list into Sunday-starting weeks (columns)."""
    by_date = {d["date"]: d for d in days}
    dates = sorted(by_date.keys())
    first = datetime.strptime(dates[0], "%Y-%m-%d")
    last = datetime.strptime(dates[-1], "%Y-%m-%d")

    # Pad backward to the Sunday on/before the first date.
    start = first - timedelta(days=(first.weekday() + 1) % 7)
    # Pad forward to the Saturday on/after the last date.
    end = last + timedelta(days=(5 - last.weekday()) % 7)

    weeks = []
    cur = start
    week = []
    while cur <= end:
        key = cur.strftime("%Y-%m-%d")
        week.append(by_date.get(key))
        if cur.weekday() == 5:  # Saturday closes a week
            weeks.append(week)
            week = []
        cur += timedelta(days=1)
    if week:
        weeks.append(week)
    return weeks


def month_label_positions(weeks: list[list[dict | None]]) -> list[tuple[int, str]]:
    """Return (week_index, month_name) the first time each month appears,
    skipping a label if it would crowd the previous one (e.g. a
    near-empty leading week)."""
    raw = []
    seen_month = None
    for wi, week in enumerate(weeks):
        for day in week:
            if day is None:
                continue
            m = int(day["date"][5:7])
            if m != seen_month:
                raw.append((wi, MONTHS[m - 1]))
                seen_month = m
            break

    min_gap_weeks = 3
    labels = []
    for wi, name in raw:
        if labels and (wi - labels[-1][0]) < min_gap_weeks:
            continue
        labels.append((wi, name))
    return labels


def build_svg(payload: dict) -> str:
    days = payload["days"]
    stats = payload["stats"]
    username = payload.get("username", "")

    weeks = build_weeks(days)
    n_weeks = len(weeks)

    width = LEFT_PAD + n_weeks * CELL + RIGHT_PAD
    height = TOP_PAD + 7 * CELL + BOTTOM_PAD

    # Find the single best day to render at the "neon" top palette level.
    best_date = stats.get("best_day", {}).get("date")

    boxes = []
    for wi, week in enumerate(weeks):
        for di, day in enumerate(week):
            x = LEFT_PAD + wi * CELL
            y = TOP_PAD + di * CELL

            if day is None:
                continue

            level = day["level"]
            color = PALETTE[min(level, 4)]
            is_best = day["date"] == best_date and level > 0
            if is_best:
                color = PALETTE[5]

            delay = round((wi + di) * STAGGER, 3)
            title = f'{day["count"]} contributions on {day["date"]}'

            if is_best:
                # A separate blurred halo sits behind the cell: it fades
                # in once the diagonal reveal reaches it, then pulses
                # forever. Kept off the cell itself so we never stack
                # two animations on the same element/property.
                fade_in_dur = 0.5
                pulse_start = round(delay + DUR + fade_in_dur, 3)
                boxes.append(
                    f'<rect x="{x - 4}" y="{y - 4}" width="{BOX + 8}" height="{BOX + 8}" '
                    f'rx="4" ry="4" fill="{color}" opacity="0" filter="url(#cellGlow)">'
                    f'<animate attributeName="opacity" from="0" to="0.55" '
                    f'dur="{fade_in_dur}s" begin="{delay + DUR}s" fill="freeze" />'
                    f'<animate attributeName="opacity" values="0.55;0.22;0.55" '
                    f'dur="2.2s" begin="{pulse_start}s" repeatCount="indefinite" />'
                    f'</rect>'
                )

            boxes.append(
                f'<rect class="cell" x="{x}" y="{y}" width="{BOX}" height="{BOX}" '
                f'rx="2.5" ry="2.5" fill="{color}" opacity="0" '
                f'style="animation-delay:{delay}s">'
                f'<title>{escape_xml(title)}</title>'
                f'</rect>'
            )

    # Day-of-week labels (Mon/Wed/Fri, GitHub-style sparse labeling).
    day_labels = []
    for di, label in DAY_LABELS.items():
        y = TOP_PAD + di * CELL + BOX - 1
        day_labels.append(
            f'<text x="{LEFT_PAD - 8}" y="{y}" font-size="9" fill="#8b949e" '
            f'text-anchor="end" font-family="monospace">{label}</text>'
        )

    # Month labels along the top.
    month_labels = []
    for wi, name in month_label_positions(weeks):
        x = LEFT_PAD + wi * CELL
        month_labels.append(
            f'<text x="{x}" y="{TOP_PAD - 8}" font-size="9" fill="#8b949e" '
            f'font-family="monospace">{name}</text>'
        )

    # Legend: Less -> More
    legend_y = height - 14
    legend_start_x = width - RIGHT_PAD - (5 * (BOX + 3)) - 40
    legend_boxes = []
    for i, color in enumerate(PALETTE[:5]):
        lx = legend_start_x + 32 + i * (BOX + 3)
        legend_boxes.append(
            f'<rect x="{lx}" y="{legend_y - BOX + 3}" width="{BOX}" height="{BOX}" '
            f'rx="2.5" ry="2.5" fill="{color}" />'
        )
    legend = (
        f'<text x="{legend_start_x}" y="{legend_y + 1}" font-size="9" fill="#8b949e" '
        f'font-family="monospace">Less</text>'
        + "".join(legend_boxes) +
        f'<text x="{legend_start_x + 32 + 5 * (BOX + 3) + 6}" y="{legend_y + 1}" '
        f'font-size="9" fill="#8b949e" font-family="monospace">More</text>'
    )

    # Stats footer, left-aligned.
    total = stats.get("total", 0)
    footer = (
        f'<text x="{LEFT_PAD}" y="{legend_y + 1}" font-size="10.5" fill="#c9d1d9" '
        f'font-family="monospace">{total:,} contributions in the last year'
        f'{" · " + username if username else ""}</text>'
    )

    max_delay = round((n_weeks + 6) * STAGGER, 3)

    style = f'''
    <style>
      .cell {{
        animation-name: reveal;
        animation-duration: {DUR}s;
        animation-timing-function: cubic-bezier(0.2, 0, 0.2, 1);
        animation-fill-mode: forwards;
        animation-iteration-count: 1;
      }}
      @keyframes reveal {{
        from {{ opacity: 0; transform: translateY(-10px); }}
        to   {{ opacity: 1; transform: translateY(0); }}
      }}
    </style>
    '''

    defs = style + f'''
    <filter id="cellGlow" x="-200%" y="-200%" width="500%" height="500%">
      <feGaussianBlur stdDeviation="3.5" />
    </filter>
    <linearGradient id="topAccent" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#39d353" />
      <stop offset="50%" stop-color="#56d4dd" />
      <stop offset="100%" stop-color="#bd93f9" />
    </linearGradient>
    '''

    panel_pad = 18
    full_w = width + panel_pad * 2
    full_h = height + panel_pad * 2

    svg = f'''<svg viewBox="0 0 {full_w} {full_h}" width="{full_w}" height="{full_h}"
     xmlns="http://www.w3.org/2000/svg" font-family="monospace">
  <defs>{defs}</defs>
  <rect width="{full_w}" height="{full_h}" rx="14" ry="14" fill="#0d1117" />
  <rect x="1" y="1" width="{full_w - 2}" height="{full_h - 2}" rx="14" ry="14"
        fill="none" stroke="#30363d" stroke-width="1.3" />
  <rect x="2" y="2" width="{full_w - 4}" height="3" fill="url(#topAccent)" />
  <g transform="translate({panel_pad},{panel_pad})">
{"".join(month_labels)}
{"".join(day_labels)}
{"".join(boxes)}
{legend}
{footer}
  </g>
</svg>'''
    return svg


def main():
    in_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(IN_DEFAULT)
    out_path = sys.argv[2] if len(sys.argv) > 2 else OUT_DEFAULT

    if not in_path.exists():
        print(f"Error: {in_path} not found. Run fetch_contributions.py first.")
        sys.exit(1)

    payload = json.loads(in_path.read_text(encoding="utf-8"))
    print(f"Rendering heatmap for {payload.get('username', '?')} "
          f"({len(payload['days'])} days) ...")

    svg = build_svg(payload)
    Path(out_path).write_text(svg, encoding="utf-8")
    print(f"Done -> {out_path}")


if __name__ == "__main__":
    main()
