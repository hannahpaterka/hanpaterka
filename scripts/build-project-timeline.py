#!/usr/bin/env python3
"""Build featured-work tile SVG for GitHub README."""

from __future__ import annotations

from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "assets" / "project-timeline.svg"
FEATURED_OUT = Path(__file__).resolve().parents[1] / "assets" / "featured-work.svg"
CARD_DIR = Path(__file__).resolve().parents[1] / "assets" / "project-cards"

SVG_W = 680
TILE_W = SVG_W
TILE_GAP = 28
PAD = 20
RADIUS = 10
BORDER_INSET = 1.25

PROJECTS = [
    {
        "id": "bwell",
        "company": "B.well",
        "accent": "#7c3aed",
        "metric": "65M+",
        "metric_label": "users served",
        "title": "Connected Health",
        "subtitle": "Enterprise healthcare platform",
        "url": "https://www.icanbwell.com/",
        "achievements": [
            "75% faster feature delivery for Walgreens & Samsung",
            "Monolith → React micro-frontends & NestJS microservices",
            "Releases 2hr → 20min · 85%+ test coverage",
            "HIPAA Cognito/SSO, IAM & Kafka event pipelines",
        ],
        "tech": ["React", "TypeScript", "NestJS", "Kafka", "AWS", "GraphQL"],
    },
    {
        "id": "business-portal",
        "company": "Independent",
        "accent": "#6d28d9",
        "metric": "End-to-end",
        "metric_label": "portal delivery",
        "title": "Business Portals",
        "subtitle": "Invoicing, maps & vendor coordination",
        "url": "https://github.com/hannahpaterka/busines-portal-readme",
        "achievements": [
            "Spring Boot portal for invoices, work orders & scheduling",
            "Maps, messaging & vendor tools for field teams",
            "PostgreSQL schemas & secure role-based REST APIs",
        ],
        "tech": ["Java", "Spring Boot", "PostgreSQL", "JavaScript", "Bootstrap"],
    },
    {
        "id": "kronos",
        "company": "Kronos",
        "accent": "#8b5cf6",
        "metric": "Automation",
        "metric_label": "ops & workflows",
        "title": "Business Management",
        "subtitle": "Spring Boot · office & field teams",
        "url": "https://github.com/hannahpaterka/busines-portal-readme",
        "achievements": [
            "85% fewer data entry errors & support calls via automation",
            "Invoicing, payments, scheduling & job tracking",
            "Zero-downtime deploys · desktop & mobile portals",
        ],
        "tech": ["Java", "Spring Boot", "PostgreSQL", "Bootstrap", "Heroku"],
    },
]


def esc(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def wrap_text(text: str, max_chars: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        trial = " ".join([*current, word])
        if len(trial) <= max_chars:
            current.append(word)
        else:
            if current:
                lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    return lines


def achievement_block(x: int, y: int, achievements: list[str], max_w: int) -> tuple[str, int]:
    parts: list[str] = []
    cy = y
    line_h = 12
    max_chars = max(30, int(max_w / 5.4) - 2)
    for achievement in achievements:
        lines = wrap_text(achievement, max_chars)
        for index, line in enumerate(lines):
            bullet_x = x if index == 0 else x
            text_x = x + 10
            if index == 0:
                parts.append(
                    f'<text x="{bullet_x}" y="{cy + 4 + index * line_h}" fill="#7c3aed" '
                    f'font-family="system-ui, -apple-system, sans-serif" font-size="9">•</text>'
                )
            parts.append(
                f'<text x="{text_x}" y="{cy + 4 + index * line_h}" fill="#374151" '
                f'font-family="system-ui, -apple-system, sans-serif" font-size="9">'
                f"{esc(line)}</text>"
            )
        cy += 6 + len(lines) * line_h
    return "\n    ".join(parts), cy


def tech_pills(x: int, y: int, tech: list[str], max_w: int) -> tuple[str, int]:
    parts: list[str] = []
    pill_h = 17
    gap_x = 5
    gap_y = 5
    cx = x
    cy = y - 11
    row_start = cx
    for label in tech:
        pill_w = max(32, len(label) * 5.4 + 12)
        if cx + pill_w > x + max_w:
            cx = row_start
            cy += pill_h + gap_y
        parts.extend(
            [
                f'<rect x="{cx:.1f}" y="{cy:.1f}" width="{pill_w:.1f}" height="{pill_h}" '
                f'rx="8" fill="#ffffff" stroke="#e5e7eb" stroke-width="1"/>',
                f'<text x="{cx + pill_w / 2:.1f}" y="{cy + 11.5}" text-anchor="middle" '
                f'fill="#475569" font-family="ui-monospace, Menlo, monospace" '
                f'font-size="7.5">{esc(label)}</text>',
            ]
        )
        cx += pill_w + gap_x
    return "\n    ".join(parts), cy + pill_h + 4


def defs_block() -> str:
    parts = ['<defs>']
    for index, project in enumerate(PROJECTS):
        pid = project["id"]
        delay = index * 1.5
        accent = project["accent"]
        parts.append(
            f'''  <linearGradient id="border-shine-{pid}" x1="0" y1="0" x2="{SVG_W}" y2="0" gradientUnits="userSpaceOnUse">
    <stop offset="0%" stop-color="#e5e7eb"/>
    <stop offset="40%" stop-color="#e5e7eb"/>
    <stop offset="50%" stop-color="{accent}"/>
    <stop offset="60%" stop-color="#e5e7eb"/>
    <stop offset="100%" stop-color="#e5e7eb"/>
    <animate attributeName="x1" values="-320;{SVG_W}" dur="4.5s" begin="{delay}s" repeatCount="indefinite"/>
    <animate attributeName="x2" values="360;{SVG_W + 680}" dur="4.5s" begin="{delay}s" repeatCount="indefinite"/>
  </linearGradient>'''
        )
        if project.get("url"):
            parts.append(
                f'''  <linearGradient id="title-shine-{pid}" x1="0" y1="0" x2="320" y2="0" gradientUnits="userSpaceOnUse">
    <stop offset="0%" stop-color="#111827"/>
    <stop offset="40%" stop-color="#111827"/>
    <stop offset="50%" stop-color="{accent}"/>
    <stop offset="60%" stop-color="#111827"/>
    <stop offset="100%" stop-color="#111827"/>
    <animate attributeName="x1" values="-180;320" dur="4.5s" begin="{delay}s" repeatCount="indefinite"/>
    <animate attributeName="x2" values="140;640" dur="4.5s" begin="{delay}s" repeatCount="indefinite"/>
  </linearGradient>'''
            )
    parts.append("</defs>")
    return "\n".join(parts)


def tile_header(project: dict, y: int) -> str:
    metric_w = max(
        96,
        len(project["metric"]) * 7 + 28,
        len(project["metric_label"]) * 6.2 + 28,
    )
    badge_h = 36
    metric_x = TILE_W - PAD - metric_w - 6
    badge_y = y + 12
    return "\n    ".join(
        [
            f'<text x="{PAD}" y="{y + 22}" fill="#64748b" '
            f'font-family="ui-monospace, Menlo, monospace" font-size="8" font-weight="700" '
            f'letter-spacing="0.14em">{esc(project["company"].upper())}</text>',
            f'<rect x="{metric_x:.1f}" y="{badge_y}" width="{metric_w:.1f}" height="{badge_h}" rx="11" '
            f'fill="#ffffff" stroke="{project["accent"]}" stroke-width="1.2" opacity="0.95">',
            f'  <animate attributeName="opacity" values="0.82;1;0.82" dur="3s" repeatCount="indefinite"/>',
            f"</rect>",
            f'<text x="{metric_x + metric_w / 2:.1f}" y="{badge_y + 15}" text-anchor="middle" '
            f'fill="{project["accent"]}" font-family="system-ui, -apple-system, sans-serif" '
            f'font-size="9.5" font-weight="700">{esc(project["metric"])}</text>',
            f'<text x="{metric_x + metric_w / 2:.1f}" y="{badge_y + 28}" text-anchor="middle" '
            f'fill="#64748b" font-family="system-ui, -apple-system, sans-serif" font-size="6.5">'
            f'{esc(project["metric_label"])}</text>',
        ]
    )


def title_block(project: dict, y: int) -> str:
    pid = project["id"]
    title_y = y + 58
    if project.get("url"):
        return "\n    ".join(
            [
                f'<text x="{PAD}" y="{title_y}" fill="url(#title-shine-{pid})" '
                f'font-family="system-ui, -apple-system, sans-serif" font-size="16" '
                f'font-weight="700">{esc(project["title"])}</text>',
                f'<text x="{PAD}" y="{title_y + 18}" fill="#64748b" '
                f'font-family="system-ui, -apple-system, sans-serif" font-size="8.5">'
                f"{esc(project['subtitle'])}</text>",
            ]
        )
    return "\n    ".join(
        [
            f'<text x="{PAD}" y="{title_y}" fill="#111827" '
            f'font-family="system-ui, -apple-system, sans-serif" font-size="16" '
            f'font-weight="700">{esc(project["title"])}</text>',
            f'<text x="{PAD}" y="{title_y + 18}" fill="#64748b" '
            f'font-family="system-ui, -apple-system, sans-serif" font-size="8.5">'
            f"{esc(project['subtitle'])}</text>",
        ]
    )


def tile_height(project: dict) -> int:
    content_w = TILE_W - PAD * 2
    _, ach_end = achievement_block(PAD, 100, project["achievements"], content_w)
    _, tech_end = tech_pills(PAD, ach_end + 14, project["tech"], content_w)
    return max(148, tech_end + PAD)


def tile(project: dict, y: int, tile_h: int, delay: float) -> str:
    pid = project["id"]
    accent = project["accent"]
    content_w = TILE_W - PAD * 2
    achievements, ach_end = achievement_block(PAD, y + 100, project["achievements"], content_w)
    tech, _ = tech_pills(PAD, ach_end + 14, project["tech"], content_w)

    inner_w = TILE_W - BORDER_INSET * 2
    inner_h = tile_h - BORDER_INSET * 2
    return "\n  ".join(
        [
            f'<!-- {esc(project["company"])} tile -->',
            f'<rect x="{BORDER_INSET}" y="{y + BORDER_INSET}" width="{inner_w}" height="{inner_h}" '
            f'rx="{RADIUS}" fill="none" stroke="{accent}" stroke-width="5" opacity="0.18">',
            f'  <animate attributeName="opacity" values="0.08;0.35;0.08" dur="3.2s" begin="{delay}s" '
            f'repeatCount="indefinite"/>',
            f"</rect>",
            f'<rect x="{BORDER_INSET}" y="{y + BORDER_INSET}" width="{inner_w}" height="{inner_h}" '
            f'rx="{RADIUS}" fill="#ffffff" stroke="url(#border-shine-{pid})" stroke-width="2.5"/>',
            f"  {tile_header(project, y)}",
            f"  {title_block(project, y)}",
            f"  {achievements}",
            f"  {tech}",
        ]
    )


def imagemap_coords(heights: list[int]) -> str:
    y = 0
    areas: list[str] = []
    for project, h in zip(PROJECTS, heights):
        if project.get("url"):
            areas.append(
                f'    <area shape="rect" coords="0,{y},{SVG_W},{y + h}" '
                f'href="{project["url"]}" alt="{esc(project["title"])}" />'
            )
        y += h + TILE_GAP
    return "\n".join(areas)


def main() -> None:
    heights = [tile_height(p) for p in PROJECTS]
    y = 0
    rendered: list[str] = []
    for index, (project, tile_h) in enumerate(zip(PROJECTS, heights)):
        rendered.append(tile(project, y, tile_h, index * 1.5))
        y += tile_h + TILE_GAP

    svg_h = y - TILE_GAP if y else 0
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="{svg_h}" viewBox="0 0 {SVG_W} {svg_h}" preserveAspectRatio="xMidYMid meet" role="img" aria-label="Featured work">
{defs_block()}
  <rect width="{SVG_W}" height="{svg_h}" fill="#ffffff"/>
  {"  ".join(rendered)}
</svg>
'''
    OUT.write_text(svg, encoding="utf-8")
    FEATURED_OUT.write_text(svg, encoding="utf-8")

    CARD_DIR.mkdir(parents=True, exist_ok=True)
    for index, (project, tile_h) in enumerate(zip(PROJECTS, heights)):
        label = project["title"]
        if project.get("url"):
            label = f"{label} — linked project"
        card_svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="{tile_h}" viewBox="0 0 {SVG_W} {tile_h}" preserveAspectRatio="xMidYMid meet" role="img" aria-label="{esc(label)}">
{defs_block()}
  {tile(project, 0, tile_h, index * 1.5)}
</svg>
'''
        (CARD_DIR / f'{project["id"]}.svg').write_text(card_svg, encoding="utf-8")

    map_snippet = imagemap_coords(heights)
    print(f"Wrote {OUT} ({SVG_W}x{svg_h})")
    print(f"Wrote {FEATURED_OUT} ({SVG_W}x{svg_h})")
    print(f"Wrote {len(PROJECTS)} tiles in {CARD_DIR}")
    print("Image map coords:")
    print(map_snippet)


if __name__ == "__main__":
    main()
