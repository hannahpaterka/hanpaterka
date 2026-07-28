#!/usr/bin/env python3
"""Build GitCity skyline with animated achievement cards."""

from __future__ import annotations

import math
import re
import urllib.request
from pathlib import Path

USERNAME = "hannahpaterka"
OUT = Path(__file__).resolve().parents[1] / "assets" / "gitcity-skyline.svg"
URL = f"https://gitcity.natrajx.in/api/svg?u={USERNAME}&theme=aurora"

OUT_W = 680
NATIVE_W = 400
NATIVE_H = 296
SCALE = OUT_W / NATIVE_W
SKYLINE_H = NATIVE_H * SCALE
HEADER_H = 52
OUT_H = HEADER_H + SKYLINE_H

ACHIEVEMENT_CARDS = [
    ("65M", "users on health platforms"),
    ("Mobile + Web", "responsive desktop & mobile"),
    ("2hr → 20min", "CI/CD deploy pipeline"),
    ("HIPAA", "compliant auth & data"),
    ("85%+", "test coverage"),
    ("Event-driven", "Kafka & microservices"),
]

CARD_W = 148
CARD_H = 36
CARD_GAP = 8
CARD_CYCLE_S = 18.0


def esc(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def fetch_svg(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "github-readme-builder"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        svg = resp.read().decode("utf-8")
    if "could not load skyline" in svg or "Could not fetch contributions" in svg:
        raise RuntimeError(f"GitCity error for user {USERNAME!r}: {url}")
    if "<!-- Month labels -->" not in svg:
        raise RuntimeError("GitCity SVG missing contribution skyline")
    return svg


def parse_contribution_summary(svg: str) -> str | None:
    match = re.search(
        r'<text x="20" y="30"[^>]*>([^<]+)</text>',
        svg,
    )
    if not match:
        return None
    text = match.group(1).strip()
    if "contribution" not in text.lower():
        return None
    return text


def extract_inner(svg: str) -> str:
    match = re.search(r"<svg[^>]*>(.*)</svg>", svg, re.DOTALL | re.IGNORECASE)
    if not match:
        raise RuntimeError("Could not parse GitCity SVG")
    inner = match.group(1).strip()
    inner = re.sub(
        r'<rect width="400" height="296" rx="12" fill="[^"]+"\s*/>',
        "",
        inner,
        count=1,
    )
    inner = re.sub(
        r"<!-- Header -->.*?<!-- Month labels -->",
        "<!-- Month labels -->",
        inner,
        flags=re.DOTALL,
    )
    return inner


def parse_month_positions(inner: str) -> dict[str, tuple[float, float]]:
    months: dict[str, tuple[float, float]] = {}
    for match in re.finditer(
        r'<text x="([\d.]+)" y="([\d.]+)"[^>]*>([A-Za-z]{3})</text>',
        inner,
    ):
        months[match.group(3)] = (float(match.group(1)), float(match.group(2)))
    return months


# GitCity isometric grid (derived from month column lines in the SVG).
FRONT_LABEL_OFFSET = (-6.0, 4.0)
COL_STEP = (24.0, 12.0)
DEPTH = (-36.0, 18.0)


def col_front(months: dict[str, tuple[float, float]], name: str) -> tuple[float, float]:
    x, y = months[name]
    return (x + FRONT_LABEL_OFFSET[0], y + FRONT_LABEL_OFFSET[1])


def front_ground_y(x: float) -> float:
    return 91.0 + (x - 62.0) * 156.0 / 312.0


def back_ground_y(x: float) -> float:
    return 109.0 + (x - 26.0) * 156.0 / 312.0


def lerp(
    a: tuple[float, float], b: tuple[float, float], t: float
) -> tuple[float, float]:
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


VACATION_SHIFT_RATIO = 0.13


def shift_xy(point: tuple[float, float], dx: float, dy: float) -> tuple[float, float]:
    return (point[0] + dx, point[1] + dy)


def city_vacation_zone(months: dict[str, tuple[float, float]]) -> dict[str, object]:
    mar_front = col_front(months, "Mar")
    jun_front = col_front(months, "Jun")
    mar_back = (mar_front[0] + DEPTH[0], mar_front[1] + DEPTH[1])
    jun_back = (jun_front[0] + DEPTH[0], jun_front[1] + DEPTH[1])

    shift = (
        (jun_front[0] - mar_front[0]) * VACATION_SHIFT_RATIO,
        (jun_front[1] - mar_front[1]) * VACATION_SHIFT_RATIO,
    )

    # Mar through Jun only — no overlap into Feb or Jul columns.
    zone = [
        shift_xy(mar_front, *shift),
        shift_xy(jun_front, *shift),
        shift_xy(jun_back, *shift),
        shift_xy(mar_back, *shift),
    ]
    zone_points = " ".join(f"{x:.1f},{y:.1f}" for x, y in zone)

    cx = sum(p[0] for p in zone) / len(zone)
    cy = sum(p[1] for p in zone) / len(zone)

    island_a = shift_xy(
        lerp(lerp(mar_front, jun_front, 0.28), lerp(mar_back, jun_back, 0.28), 0.62),
        *shift,
    )
    island_b = shift_xy(
        lerp(lerp(mar_front, jun_front, 0.72), lerp(mar_back, jun_back, 0.72), 0.58),
        *shift,
    )
    sun_anchor = shift_xy(lerp(mar_front, jun_front, 0.78), *shift)

    return {
        "zone_points": zone_points,
        "cx": cx,
        "cy": cy,
        "island_a": island_a,
        "island_b": island_b,
        "island_a_r": 19.0,
        "island_b_r": 18.0,
        "sun_x": sun_anchor[0] - 4,
        "sun_y": sun_anchor[1] - 14,
    }


def palm_frond(
    cx: float,
    cy: float,
    angle_deg: float,
    length: float,
    scale: float,
    fill: str,
) -> str:
    rad = math.radians(angle_deg)
    half_w = 1.7 * scale
    perp = rad + math.pi / 2

    base_lx = cx + half_w * math.cos(perp)
    base_ly = cy + half_w * math.sin(perp) * 0.55
    base_rx = cx - half_w * math.cos(perp)
    base_ry = cy - half_w * math.sin(perp) * 0.55

    tip_x = cx + length * math.sin(rad) * 0.92
    tip_y = cy + length * 0.58 + length * 0.12 * math.cos(rad)

    ctrl_x = cx + length * 0.48 * math.sin(rad)
    ctrl_y = cy - length * 0.16

    return (
        f'  <path d="M {base_lx:.1f} {base_ly:.1f} Q {ctrl_x:.1f} {ctrl_y:.1f} '
        f'{tip_x:.1f} {tip_y:.1f} Q {ctrl_x:.1f} {ctrl_y + 2.2 * scale:.1f} '
        f'{base_rx:.1f} {base_ry:.1f} Z" fill="{fill}" stroke="#14532d" '
        f'stroke-width="{0.35 * scale:.1f}" stroke-linejoin="round"/>'
    )


def beach_palm(x: float, base_y: float, scale: float = 1.0) -> str:
    trunk_h = 24 * scale
    crown_x = x + 1.2 * scale
    crown_y = base_y - trunk_h
    length = 21 * scale
    parts = [
        f'  <path d="M {x:.1f} {base_y:.1f} C {x + 4.5 * scale:.1f} {base_y - trunk_h * 0.35:.1f} '
        f'{x - 3.0 * scale:.1f} {base_y - trunk_h * 0.72:.1f} {crown_x:.1f} {crown_y:.1f}" '
        f'fill="none" stroke="#451a03" stroke-width="{1.7 * scale:.1f}" stroke-linecap="round"/>',
        f'  <path d="M {x:.1f} {base_y:.1f} C {x + 4.5 * scale:.1f} {base_y - trunk_h * 0.35:.1f} '
        f'{x - 3.0 * scale:.1f} {base_y - trunk_h * 0.72:.1f} {crown_x:.1f} {crown_y:.1f}" '
        f'fill="none" stroke="#92400e" stroke-width="{1.05 * scale:.1f}" stroke-linecap="round"/>',
        f'  <ellipse cx="{crown_x:.1f}" cy="{crown_y + 1.2 * scale:.1f}" '
        f'rx="{2.0 * scale:.1f}" ry="{1.4 * scale:.1f}" fill="#14532d" stroke="#052e16" '
        f'stroke-width="{0.3 * scale:.1f}"/>',
    ]
    frond_angles = (-72, -48, -24, 0, 24, 48, 72)
    frond_fills = ("#4ade80", "#22c55e", "#86efac", "#16a34a", "#22c55e", "#4ade80", "#16a34a")
    for angle, fill in zip(frond_angles, frond_fills):
        parts.append(palm_frond(crown_x, crown_y, angle, length, scale, fill))
    return "\n".join(parts)


def beach_umbrella(x: float, base_y: float, scale: float = 1.0) -> str:
    pole_h = 15 * scale
    top_y = base_y - pole_h
    radius = 12 * scale
    return "\n".join(
        [
            f'  <line x1="{x:.1f}" y1="{base_y:.1f}" x2="{x:.1f}" y2="{top_y:.1f}" '
            f'stroke="#78716c" stroke-width="{1.1 * scale:.1f}" stroke-linecap="round"/>',
            f'  <path d="M {x - radius:.1f} {top_y:.1f} A {radius:.1f} {radius * 0.55:.1f} '
            f'0 0 1 {x + radius:.1f} {top_y:.1f} Z" fill="#f43f5e" opacity="0.92"/>',
            f'  <path d="M {x - radius:.1f} {top_y:.1f} A {radius * 0.5:.1f} {radius * 0.28:.1f} '
            f'0 0 1 {x:.1f} {top_y:.1f} Z" fill="#ffffff" opacity="0.88"/>',
            f'  <path d="M {x:.1f} {top_y:.1f} A {radius * 0.5:.1f} {radius * 0.28:.1f} '
            f'0 0 1 {x + radius:.1f} {top_y:.1f} Z" fill="#fda4af" opacity="0.85"/>',
            f'  <ellipse cx="{x:.1f}" cy="{base_y + 0.8 * scale:.1f}" rx="{2.2 * scale:.1f}" '
            f'ry="{0.9 * scale:.1f}" fill="#d6d3d1" opacity="0.8"/>',
        ]
    )


def pina_colada(x: float, base_y: float, scale: float = 1.0) -> str:
    glass_w = 5.5 * scale
    glass_h = 11 * scale
    top_y = base_y - glass_h
    mid_y = base_y - glass_h * 0.45
    return "\n".join(
        [
            f'  <path d="M {x - glass_w * 0.55:.1f} {top_y + 1.5 * scale:.1f} '
            f'L {x - glass_w * 0.85:.1f} {base_y:.1f} L {x + glass_w * 0.85:.1f} {base_y:.1f} '
            f'L {x + glass_w * 0.55:.1f} {top_y + 1.5 * scale:.1f} Z" fill="#e2e8f0" opacity="0.95" '
            f'stroke="#94a3b8" stroke-width="{0.35 * scale:.1f}"/>',
            f'  <path d="M {x - glass_w * 0.5:.1f} {mid_y:.1f} '
            f'L {x - glass_w * 0.72:.1f} {base_y - 1.2 * scale:.1f} '
            f'L {x + glass_w * 0.72:.1f} {base_y - 1.2 * scale:.1f} '
            f'L {x + glass_w * 0.5:.1f} {mid_y:.1f} Z" fill="#fef08a" opacity="0.92"/>',
            f'  <path d="M {x - glass_w * 0.42:.1f} {top_y + 3 * scale:.1f} '
            f'L {x + glass_w * 0.42:.1f} {top_y + 3 * scale:.1f} L {x + glass_w * 0.28:.1f} {mid_y:.1f} '
            f'L {x - glass_w * 0.28:.1f} {mid_y:.1f} Z" fill="#ffffff" opacity="0.55"/>',
            f'  <line x1="{x + glass_w * 0.15:.1f}" y1="{top_y - 5 * scale:.1f}" '
            f'x2="{x + glass_w * 0.15:.1f}" y2="{top_y + 1 * scale:.1f}" stroke="#ef4444" '
            f'stroke-width="{0.55 * scale:.1f}" stroke-linecap="round"/>',
            f'  <line x1="{x - 1.2 * scale:.1f}" y1="{top_y - 1 * scale:.1f}" '
            f'x2="{x + 2.5 * scale:.1f}" y2="{top_y + 2 * scale:.1f}" stroke="#f59e0b" '
            f'stroke-width="{0.7 * scale:.1f}" stroke-linecap="round"/>',
            f'  <path d="M {x + glass_w * 0.75:.1f} {top_y + 4 * scale:.1f} '
            f'L {x + glass_w * 1.35:.1f} {top_y + 1 * scale:.1f} L {x + glass_w * 1.05:.1f} '
            f'{top_y + 6 * scale:.1f} Z" fill="#fbbf24" stroke="#d97706" '
            f'stroke-width="{0.25 * scale:.1f}"/>',
            f'  <circle cx="{x - glass_w * 0.35:.1f}" cy="{top_y + 2.5 * scale:.1f}" '
            f'r="{1.1 * scale:.1f}" fill="#ef4444" stroke="#b91c1c" stroke-width="{0.2 * scale:.1f}"/>',
        ]
    )


def island_blob_d(cx: float, cy: float, radius: float, variant: int = 0) -> str:
    profiles = (
        (1.02, 0.78, 1.14, 0.84, 1.08, 0.9, 0.94, 1.06),
        (0.9, 1.08, 0.86, 1.12, 0.92, 1.02, 1.1, 0.82),
    )
    radii = profiles[variant % len(profiles)]
    points: list[tuple[float, float]] = []
    for index, scale in enumerate(radii):
        angle = math.tau * index / len(radii) - math.pi / 2
        rx = radius * scale * 1.05
        ry = radius * scale * 0.74
        points.append((cx + rx * math.cos(angle), cy + ry * math.sin(angle)))

    start_x = (points[0][0] + points[-1][0]) / 2
    start_y = (points[0][1] + points[-1][1]) / 2
    parts = [f"M {start_x:.1f} {start_y:.1f}"]
    for index, point in enumerate(points):
        next_point = points[(index + 1) % len(points)]
        mid_x = (point[0] + next_point[0]) / 2
        mid_y = (point[1] + next_point[1]) / 2
        parts.append(f"Q {point[0]:.1f} {point[1]:.1f} {mid_x:.1f} {mid_y:.1f}")
    parts.append("Z")
    return " ".join(parts)


def round_island(cx: float, cy: float, radius: float, variant: int = 0) -> str:
    outer = island_blob_d(cx, cy + 1.4, radius * 1.08, variant)
    body = island_blob_d(cx, cy, radius, variant)
    inner = island_blob_d(cx, cy - radius * 0.12, radius * 0.78, variant)
    return (
        f'  <path d="{outer}" fill="#0369a1" opacity="0.35"/>'
        f'\n  <path d="{body}" fill="#fde68a" opacity="0.95"/>'
        f'\n  <path d="{inner}" fill="#fef3c7" opacity="0.88"/>'
    )


def sabbatical_beach_overlay(inner: str) -> str:
    if 'id="sabbatical-beach"' in inner:
        return inner

    months = parse_month_positions(inner)
    required = ("Mar", "Apr", "May", "Jun")
    if not all(month in months for month in required):
        return inner

    zone = city_vacation_zone(months)
    cx = zone["cx"]
    cy = zone["cy"]
    island_a = zone["island_a"]
    island_b = zone["island_b"]
    island_a_r = zone["island_a_r"]
    island_b_r = zone["island_b_r"]
    sun_x = zone["sun_x"]
    sun_y = zone["sun_y"]

    month_colors = {
        "Mar": "#7dd3fc",
        "Apr": "#38bdf8",
        "May": "#0ea5e9",
        "Jun": "#0284c7",
    }
    for month, color in month_colors.items():
        mx, my = months[month]
        inner = re.sub(
            rf'(<text x="{mx:g}" y="{my:g}"[^>]*fill=")[^"]+(")',
            rf"\1{color}\2",
            inner,
            count=1,
        )

    tree_a_y = island_a[1] - island_a_r * 0.28
    umbrella_x = island_b[0] + 6
    umbrella_y = island_b[1] - island_b_r * 0.18
    drink_x = island_b[0] - 14
    drink_y = island_b[1] - island_b_r * 0.12

    overlay = f"""
  <g id="sabbatical-beach" aria-label="March through June sabbatical">
    <defs>
      <clipPath id="sabbatical-clip">
        <polygon points="{zone["zone_points"]}"/>
      </clipPath>
      <linearGradient id="vacation-ocean" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#7dd3fc" stop-opacity="0.72"/>
        <stop offset="45%" stop-color="#38bdf8" stop-opacity="0.78"/>
        <stop offset="100%" stop-color="#0369a1" stop-opacity="0.88"/>
      </linearGradient>
    </defs>

    <g clip-path="url(#sabbatical-clip)">
      <polygon points="{zone["zone_points"]}" fill="url(#vacation-ocean)"/>

      <path d="M {cx - 28:.1f} {cy + 4:.1f}
        Q {cx:.1f} {cy + 8:.1f} {cx + 28:.1f} {cy + 6:.1f}"
        fill="none" stroke="#e0f2fe" stroke-width="0.9" opacity="0.45">
        <animate attributeName="opacity" values="0.2;0.55;0.2" dur="3.8s" repeatCount="indefinite"/>
      </path>
      <path d="M {cx - 18:.1f} {cy + 14:.1f}
        Q {cx + 4:.1f} {cy + 18:.1f} {cx + 22:.1f} {cy + 16:.1f}"
        fill="none" stroke="#bae6fd" stroke-width="0.75" opacity="0.35">
        <animate attributeName="opacity" values="0.12;0.42;0.12" dur="4.6s" repeatCount="indefinite"/>
      </path>

      <circle cx="{sun_x:.1f}" cy="{sun_y:.1f}" r="6" fill="#fde68a" opacity="0.85">
        <animate attributeName="opacity" values="0.7;1;0.7" dur="4.5s" repeatCount="indefinite"/>
      </circle>
    </g>

    <g aria-hidden="true">
      {round_island(island_a[0], island_a[1], island_a_r, 0)}
      {round_island(island_b[0], island_b[1], island_b_r, 1)}
      {beach_palm(island_a[0], tree_a_y, 1.05)}
      {beach_umbrella(umbrella_x, umbrella_y, 0.95)}
      {pina_colada(drink_x, drink_y, 0.9)}
    </g>
  </g>"""

    if "<!-- Legend -->" in inner:
        return inner.replace("<!-- Legend -->", overlay + "\n  <!-- Legend -->", 1)
    return inner + overlay


def card_opacity_cycle(index: int, total: int) -> tuple[str, str]:
    dim = "0.32"
    bright = "1"
    values: list[str] = []
    key_times: list[str] = []
    segment = 1.0 / total
    fade = segment * 0.12

    for step in range(total):
        start = step * segment
        fade_in = start + fade
        fade_out = (step + 1) * segment - fade
        end = (step + 1) * segment
        level = bright if step == index else dim
        values.extend([dim, level, level, dim] if step == index else [dim, dim, dim, dim])
        if step == 0:
            key_times.extend(["0", f"{fade_in:.4f}", f"{fade_out:.4f}", f"{end:.4f}"])
        else:
            key_times.extend([f"{start:.4f}", f"{fade_in:.4f}", f"{fade_out:.4f}", f"{end:.4f}"])

    key_times[-1] = "1"
    return ";".join(values), ";".join(key_times)


def sparkle_dots(x: float, y: float, phase: float) -> str:
    offsets = [(10, -6), (24, 4), (6, 8)]
    parts: list[str] = []
    for idx, (ox, oy) in enumerate(offsets):
        begin = phase + idx * 0.35
        parts.append(
            f'<circle cx="{x + ox:.1f}" cy="{y + oy:.1f}" r="1.4" fill="#c4b5fd" opacity="0">'
            f'<animate attributeName="opacity" values="0;0.95;0" dur="1.6s" '
            f'begin="{begin:.2f}s" repeatCount="indefinite"/>'
            f'<animate attributeName="r" values="0.8;1.8;0.8" dur="1.6s" '
            f'begin="{begin:.2f}s" repeatCount="indefinite"/>'
            f"</circle>"
        )
    return "\n    ".join(parts)


def achievement_cards() -> str:
    total = len(ACHIEVEMENT_CARDS)
    base_x = OUT_W - CARD_W - 16
    base_y = HEADER_H + 14
    parts: list[str] = [
        f'<text x="{base_x + 4}" y="{HEADER_H + 8}" fill="#64748b" '
        f'font-family="system-ui, -apple-system, sans-serif" font-size="9" '
        f'font-weight="700" letter-spacing="0.14em">ACHIEVEMENTS</text>',
    ]

    for index, (value, label) in enumerate(ACHIEVEMENT_CARDS):
        y = base_y + index * (CARD_H + CARD_GAP)
        opacity_vals, opacity_keys = card_opacity_cycle(index, total)
        load_begin = index * 0.22
        value_size = 13 if len(value) <= 5 else 10
        phase = index * (CARD_CYCLE_S / total)

        parts.extend(
            [
                f"<g>",
                f'  <animateTransform attributeName="transform" type="translate" '
                f'values="0,-12;0,0" dur="0.55s" begin="{load_begin:.2f}s" fill="freeze"/>',
                f'  <g opacity="0">',
                f'    <animate attributeName="opacity" values="0;1" dur="0.55s" '
                f'begin="{load_begin:.2f}s" fill="freeze"/>',
                f'    <g>',
                f'      <animate attributeName="opacity" values="{opacity_vals}" '
                f'keyTimes="{opacity_keys}" dur="{CARD_CYCLE_S:.0f}s" '
                f'begin="{load_begin + 0.55:.2f}s" repeatCount="indefinite"/>',
                f'      <rect x="{base_x}" y="{y}" width="{CARD_W}" height="{CARD_H}" '
                f'rx="10" fill="#ffffff" stroke="#e5e7eb" stroke-width="1"/>',
                f'      <rect x="{base_x}" y="{y}" width="3" height="{CARD_H}" fill="#7c3aed">',
                f'        <animate attributeName="opacity" values="0.5;1;0.5" '
                f'dur="2.4s" repeatCount="indefinite"/>',
                f"      </rect>",
                f'      <text x="{base_x + 12}" y="{y + 20}" fill="#1f2937" '
                f'font-family="ui-monospace, Menlo, monospace" font-size="{value_size}" '
                f'font-weight="700">{esc(value)}',
                f'        <animate attributeName="opacity" values="0.88;1;0.88" '
                f'dur="2.2s" repeatCount="indefinite"/>',
                f"      </text>",
                f'      <text x="{base_x + 12}" y="{y + 31}" fill="#64748b" '
                f'font-family="system-ui, -apple-system, sans-serif" font-size="7" '
                f'font-weight="600">{esc(label)}</text>',
                f"      {sparkle_dots(base_x + CARD_W - 36, y + 14, phase)}",
                f'      <rect x="{base_x + 8}" y="{y + 8}" width="{CARD_W - 16}" '
                f'height="{CARD_H - 16}" rx="8" fill="#7c3aed" opacity="0">',
                f'        <animate attributeName="opacity" values="0;0.1;0" dur="2.8s" '
                f'begin="{phase:.2f}s" repeatCount="indefinite"/>',
                f"      </rect>",
                f"    </g>",
                f"  </g>",
                f"</g>",
            ]
        )

    return "\n  ".join(parts)


def click_me_badge() -> str:
    badge_w = 96
    badge_h = 22
    rect_x = (OUT_W - badge_w) / 2
    rect_y = HEADER_H + SKYLINE_H * 0.84 - badge_h / 2
    text_x = rect_x + badge_w / 2
    text_y = rect_y + 15
    return f"""
  <g id="click-me-hint" aria-hidden="true">
    <rect x="{rect_x:.0f}" y="{rect_y:.1f}" width="{badge_w}" height="{badge_h}" rx="11"
      fill="#f5f3ff" stroke="#7c3aed" stroke-width="1.5">
      <animate attributeName="opacity" values="1;0.3;1" dur="1.1s" repeatCount="indefinite"/>
      <animate attributeName="stroke-width" values="1.5;2.5;1.5" dur="1.1s" repeatCount="indefinite"/>
    </rect>
    <text x="{text_x:.0f}" y="{text_y:.1f}" text-anchor="middle" fill="#7c3aed"
      font-family="system-ui, -apple-system, sans-serif" font-size="8.5"
      font-weight="800" letter-spacing="0.14em">CLICK ME
      <animate attributeName="opacity" values="1;0.35;1" dur="1.1s" repeatCount="indefinite"/>
    </text>
  </g>"""


def main() -> None:
    raw = fetch_svg(URL)
    inner = extract_inner(raw)
    cards = achievement_cards()
    contrib = parse_contribution_summary(raw)
    contrib_markup = ""
    if contrib:
        contrib_markup = f"""
  <text x="{OUT_W - 24:.0f}" y="30" text-anchor="end" fill="#7c3aed"
    font-family="ui-monospace, Menlo, monospace" font-size="9" font-weight="600">{esc(contrib)}</text>"""

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{OUT_W:.0f}" height="{OUT_H:.1f}" viewBox="0 0 {OUT_W:.0f} {OUT_H:.1f}" role="img" aria-label="Contribution city skyline with achievements">
  <defs>
    <radialGradient id="spotlight" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#7c3aed" stop-opacity="0.18"/>
      <stop offset="55%" stop-color="#a855f7" stop-opacity="0.06"/>
      <stop offset="100%" stop-color="#ffffff" stop-opacity="0"/>
    </radialGradient>
    <clipPath id="skyline-clip">
      <rect x="0" y="{HEADER_H}" width="{OUT_W:.0f}" height="{SKYLINE_H:.1f}"/>
    </clipPath>
  </defs>

  <rect width="{OUT_W:.0f}" height="{OUT_H:.1f}" fill="#ffffff"/>

  <text x="24" y="30" fill="#111827"
    font-family="system-ui, -apple-system, BlinkMacSystemFont, sans-serif"
    font-size="18" font-weight="800" letter-spacing="0.18em">GIT SKYLINE</text>{contrib_markup}
{click_me_badge()}

  <g clip-path="url(#skyline-clip)">
    <g transform="translate(0, {HEADER_H}) scale({SCALE:.4f})">
{inner}
    </g>

    <ellipse cx="120" cy="{HEADER_H + SKYLINE_H * 0.62:.0f}" rx="150" ry="110" fill="url(#spotlight)">
      <animate attributeName="cx" values="80;{OUT_W - 80};80" dur="10s" repeatCount="indefinite"/>
      <animate attributeName="cy" values="{HEADER_H + SKYLINE_H * 0.58:.0f};{HEADER_H + SKYLINE_H * 0.66:.0f};{HEADER_H + SKYLINE_H * 0.58:.0f}" dur="10s" repeatCount="indefinite"/>
      <animate attributeName="opacity" values="0.45;0.85;0.45" dur="10s" repeatCount="indefinite"/>
    </ellipse>

    {cards}
  </g>
</svg>
'''
    OUT.write_text(svg, encoding="utf-8")
    print(f"Wrote {OUT} ({OUT_W:.0f}x{OUT_H:.1f}, {len(ACHIEVEMENT_CARDS)} achievement cards)")


if __name__ == "__main__":
    main()
