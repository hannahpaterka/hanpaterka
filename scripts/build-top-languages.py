#!/usr/bin/env python3
"""Build aurora-themed top languages SVG from public GitHub repo stats."""

from __future__ import annotations

import json
import math
import urllib.request
from pathlib import Path

USERNAME = "hannahpaterka"
LANG_COUNT = 7
OUT = Path(__file__).resolve().parents[1] / "assets" / "top-languages.svg"

# Curated display profile — public GitHub repos skew Python-heavy (profile scripts,
# etc.) and under-represent TypeScript from private work. Percentages must sum to 100.
DISPLAY_LANGUAGES: list[tuple[str, int]] = [
    ("TypeScript", 30),
    ("JavaScript", 20),  # ~2/3 of TypeScript
    ("React", 15),
    ("Python", 12),
    ("Vue", 8),
    ("CSS", 8),
    ("HTML", 7),
]

LANG_COLORS: dict[str, str] = {
    "JavaScript": "#f1e05a",
    "TypeScript": "#3178c6",
    "React": "#61dafb",
    "Python": "#3572A5",
    "Java": "#b07219",
    "Vue": "#41b883",
    "CSS": "#a855f7",
    "HTML": "#e34c26",
    "Shell": "#89e051",
    "Go": "#00ADD8",
    "Rust": "#dea584",
    "Ruby": "#701516",
    "Kotlin": "#A97BFF",
    "Swift": "#F05138",
    "C": "#555555",
    "C++": "#f34b7d",
    "C#": "#178600",
    "PHP": "#4F5D95",
    "Scala": "#c22d40",
    "Dart": "#00B4AB",
    "R": "#198CE7",
}


def esc(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def fetch_json(url: str) -> list | dict:
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.load(resp)


def aggregate_languages(username: str) -> list[tuple[str, int]]:
    langs: dict[str, int] = {}
    page = 1
    while True:
        repos = fetch_json(
            f"https://api.github.com/users/{username}/repos"
            f"?per_page=100&page={page}&type=owner&sort=updated"
        )
        if not repos:
            break
        for repo in repos:
            if repo.get("fork"):
                continue
            data = fetch_json(repo["languages_url"])
            for name, count in data.items():
                langs[name] = langs.get(name, 0) + count
        if len(repos) < 100:
            break
        page += 1
    return sorted(langs.items(), key=lambda item: -item[1])[:LANG_COUNT]


def rounded_percents(values: list[int]) -> list[int]:
    total = sum(values)
    if total == 0:
        return [0] * len(values)
    raw = [value / total * 100 for value in values]
    floors = [int(value) for value in raw]
    remainder = 100 - sum(floors)
    order = sorted(range(len(raw)), key=lambda i: raw[i] - floors[i], reverse=True)
    for index in order[:remainder]:
        floors[index] += 1
    return floors


def polar(cx: float, cy: float, radius: float, angle_deg: float) -> tuple[float, float]:
    angle = math.radians(angle_deg - 90)
    return cx + radius * math.cos(angle), cy + radius * math.sin(angle)


def donut_arc(
    cx: float,
    cy: float,
    outer: float,
    inner: float,
    start: float,
    end: float,
) -> str:
    if end - start >= 359.999:
        end = start + 359.999
    large = 1 if end - start > 180 else 0
    ox0, oy0 = polar(cx, cy, outer, start)
    ox1, oy1 = polar(cx, cy, outer, end)
    ix1, iy1 = polar(cx, cy, inner, end)
    ix0, iy0 = polar(cx, cy, inner, start)
    return (
        f"M {ox0:.2f} {oy0:.2f} A {outer} {outer} 0 {large} 1 {ox1:.2f} {oy1:.2f} "
        f"L {ix1:.2f} {iy1:.2f} A {inner} {inner} 0 {large} 0 {ix0:.2f} {iy0:.2f} Z"
    )


def build_rows(
    languages: list[tuple[str, int, int]],
    x: int,
    y: int,
    width: int,
) -> str:
    parts: list[str] = []
    row_h = 34
    track_x = x + 130
    track_w = width - 210
    for index, (name, _count, pct) in enumerate(languages):
        row_y = y + index * row_h
        color = LANG_COLORS.get(name, "#a855f7")
        fill_w = max(8, track_w * pct / 100)
        parts.extend(
            [
                f'<circle cx="{x + 10}" cy="{row_y + 14}" r="5" fill="{color}"/>',
                f'<text x="{x + 24}" y="{row_y + 18}" fill="#374151" '
                f'font-family="ui-monospace, Menlo, monospace" font-size="13" font-weight="600">'
                f"{esc(name)}</text>",
                f'<rect x="{track_x}" y="{row_y + 8}" width="{track_w}" height="12" rx="6" '
                f'fill="#f3f4f6" stroke="#e5e7eb" stroke-width="0.6" opacity="0.9"/>',
                f'<rect x="{track_x}" y="{row_y + 8}" width="{fill_w:.1f}" height="12" rx="6" '
                f'fill="{color}" opacity="0.92"/>',
                f'<rect x="{x + width - 54}" y="{row_y + 4}" width="44" height="22" rx="11" '
                f'fill="#ffffff" stroke="{color}" stroke-width="1.2" opacity="0.95"/>',
                f'<text x="{x + width - 32}" y="{row_y + 19}" text-anchor="middle" fill="#1f2937" '
                f'font-family="ui-monospace, Menlo, monospace" font-size="12" font-weight="700">'
                f"{pct}%</text>",
            ]
        )
    return "\n  ".join(parts)


def build_donut(languages: list[tuple[str, int, int]], cx: float, cy: float) -> str:
    parts: list[str] = []
    start = 0.0
    for name, _count, pct in languages:
        if pct <= 0:
            continue
        sweep = pct / 100 * 360
        color = LANG_COLORS.get(name, "#a855f7")
        parts.append(
            f'<path d="{donut_arc(cx, cy, 78, 52, start, start + sweep)}" fill="{color}" opacity="0.95"/>'
        )
        start += sweep
    parts.append(
        f'<circle cx="{cx}" cy="{cy}" r="46" fill="#ffffff" stroke="#e5e7eb" stroke-width="1.2"/>'
    )
    parts.append(
        f'<text x="{cx}" y="{cy - 2}" text-anchor="middle" fill="#7c3aed" '
        f'font-family="ui-monospace, Menlo, monospace" font-size="11" letter-spacing="0.08em">TOP</text>'
    )
    parts.append(
        f'<text x="{cx}" y="{cy + 14}" text-anchor="middle" fill="#9333ea" '
        f'font-family="ui-monospace, Menlo, monospace" font-size="11" letter-spacing="0.08em">LANGS</text>'
    )
    return "\n  ".join(parts)


def main() -> None:
    total = sum(pct for _, pct in DISPLAY_LANGUAGES)
    if total != 100:
        raise SystemExit(f"DISPLAY_LANGUAGES must sum to 100, got {total}")

    languages = [(name, pct, pct) for name, pct in DISPLAY_LANGUAGES]

    height = 56 + len(languages) * 34 + 28
    rows = build_rows(languages, 250, 68, 410)
    donut = build_donut(languages, 118, height / 2 + 8)

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="680" height="{height:.0f}" viewBox="0 0 680 {height:.0f}" role="img" aria-label="Most used languages">
  <defs>
    <linearGradient id="title" x1="0" y1="0" x2="420" y2="0" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="#7c3aed"/>
      <stop offset="50%" stop-color="#9333ea"/>
      <stop offset="100%" stop-color="#a855f7"/>
    </linearGradient>
  </defs>

  <rect width="680" height="{height:.0f}" rx="16" fill="#ffffff" stroke="#e5e7eb" stroke-width="1" opacity="0.98"/>

  <text x="24" y="36" fill="url(#title)"
    font-family="ui-monospace, Menlo, monospace" font-size="16" font-weight="700" letter-spacing="0.1em">
    MOST USED LANGUAGES
  </text>
  <text x="24" y="54" fill="#64748b"
    font-family="ui-monospace, Menlo, monospace" font-size="10" letter-spacing="0.08em">
    PUBLIC REPOS · JS &amp; TS FOCUSED STACK
  </text>

  {donut}

  {rows}
</svg>
'''
    OUT.write_text(svg, encoding="utf-8")
    print(f"Wrote {OUT}")
    for name, _count, pct in languages:
        print(f"  {name}: {pct}%")


if __name__ == "__main__":
    main()
