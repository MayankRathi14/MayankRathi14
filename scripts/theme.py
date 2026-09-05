"""
theme.py — shared visual language for every generated SVG, so the
header, portrait, info card, heatmap, badges, and stat cards all
read as one coherent terminal aesthetic instead of five separate
one-off scripts.
"""

BG = "#0d1117"
BG_ALT = "#161b22"
BG_GRADIENT_TOP = "#0d1117"
BG_GRADIENT_BOTTOM = "#131a2a"

BORDER = "#30363d"
BORDER_GLOW = "#39d353"

TEXT = "#c9d1d9"
TEXT_BRIGHT = "#f0f6fc"
MUTED = "#8b949e"

GREEN = "#39d353"
GREEN_BRIGHT = "#69f0a0"
CYAN = "#56d4dd"
PURPLE = "#bd93f9"
ORANGE = "#ffb86c"
PINK = "#ff79c6"
RED = "#ff5555"

DOT_RED, DOT_YELLOW, DOT_GREEN = "#ff5f56", "#ffbd2e", "#27c93f"

FONT = "monospace"

CARD_WIDTH = 860  # shared width so every full-width section lines up


def glow_defs(glow_id: str, color: str, std_dev: float = 4.5) -> str:
    """A reusable soft-glow filter, tinted to `color`."""
    return f'''
    <filter id="{glow_id}" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="{std_dev}" result="blur" />
      <feFlood flood-color="{color}" flood-opacity="0.55" result="color" />
      <feComposite in="color" in2="blur" operator="in" result="glow" />
      <feMerge>
        <feMergeNode in="glow" />
        <feMergeNode in="SourceGraphic" />
      </feMerge>
    </filter>
    '''


def panel_frame(width: float, height: float, rx: float = 12,
                 border_color: str = BORDER, glow: bool = False,
                 glow_filter_id: str = "") -> str:
    """Rounded panel background + border, optionally glowing."""
    filter_attr = f' filter="url(#{glow_filter_id})"' if glow else ""
    return (
        f'<rect width="{width}" height="{height}" rx="{rx}" ry="{rx}" '
        f'fill="{BG}" />'
        f'<rect x="0.75" y="0.75" width="{width - 1.5}" height="{height - 1.5}" '
        f'rx="{rx}" ry="{rx}" fill="none" stroke="{border_color}" '
        f'stroke-width="1.5"{filter_attr} />'
    )


def titlebar(width: float, title: str, pad_x: float = 20, h: float = 34) -> str:
    return f'''
    <rect width="{width}" height="{h}" rx="12" ry="12" fill="{BG_ALT}" />
    <rect y="{h - 12}" width="{width}" height="12" fill="{BG_ALT}" />
    <circle cx="{pad_x + 6}" cy="{h / 2}" r="6" fill="{DOT_RED}" />
    <circle cx="{pad_x + 28}" cy="{h / 2}" r="6" fill="{DOT_YELLOW}" />
    <circle cx="{pad_x + 50}" cy="{h / 2}" r="6" fill="{DOT_GREEN}" />
    <text x="{width / 2}" y="{h / 2 + 4.5}" font-size="12" fill="{MUTED}"
          text-anchor="middle" font-family="{FONT}">{title}</text>
    '''


def escape_xml(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
