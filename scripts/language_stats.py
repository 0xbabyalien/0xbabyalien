import json
import math
import os
import urllib.request
from datetime import datetime
from html import escape
from pathlib import Path
from zoneinfo import ZoneInfo

USERNAME = os.environ.get("GITHUB_USERNAME", "0xbabyalien")
OUTPUT = Path("assets/language-stats.svg")

TOKEN = os.environ.get("GH_STATS_TOKEN") or os.environ.get("GITHUB_TOKEN")

HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"

COLORS = {
    "HTML": "#e34c26",
    "CSS": "#a371f7",
    "JavaScript": "#f1e05a",
    "TypeScript": "#3178c6",
    "Python": "#58a6ff",
    "Java": "#d29922",
    "C++": "#f34b7d",
    "C#": "#8b949e",
    "C": "#8b949e",
    "PHP": "#4F5D95",
    "Shell": "#89e051",
    "Go": "#00ADD8",
    "Rust": "#dea584",
    "Ruby": "#701516",
    "Dart": "#00B4AB",
    "Kotlin": "#A97BFF",
    "Swift": "#F05138",
    "Vue": "#41B883",
    "Jupyter Notebook": "#DA5B0B",
}


def github_get(url):
    request = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def get_all_public_repositories(username):
    repositories = []
    page = 1

    while True:
        url = (
            f"https://api.github.com/users/{username}/repos"
            f"?type=owner&per_page=100&page={page}"
        )
        batch = github_get(url)

        if not batch:
            break

        repositories.extend(batch)
        page += 1

    return repositories


def get_all_language_totals(repositories):
    language_totals = {}

    for repository in repositories:
        owner = repository["owner"]["login"]
        name = repository["name"]
        url = f"https://api.github.com/repos/{owner}/{name}/languages"
        repository_languages = github_get(url)

        for language, byte_count in repository_languages.items():
            language_totals[language] = (
                language_totals.get(language, 0) + byte_count
            )

    return language_totals


def place_bubbles(bubbles, width=720):
    """Place circles without overlap and return positions and total height."""
    margin_x = 38
    top = 112
    gap = 12
    row_gap = 22
    max_radius = 54
    min_radius = 30
    usable_width = width - 2 * margin_x

    # Scale circle area by language share while keeping every label readable.
    max_value = max(item["bytes"] for item in bubbles)

    for item in bubbles:
        share = item["bytes"] / max_value
        item["radius"] = min_radius + (max_radius - min_radius) * math.sqrt(share)

    positions = []
    row = []
    x = margin_x

    for item in bubbles:
        radius = item["radius"]
        diameter = radius * 2

        if row and x + diameter > width - margin_x:
            row_y = top + max_radius + len(positions) * (2 * max_radius + row_gap)

            for row_item in row:
                positions.append(
                    (
                        row_item,
                        row_item["_x"],
                        row_y,
                    )
                )

            row = []
            x = margin_x

        if x + diameter > width - margin_x:
            item["radius"] = min_radius
            radius = min_radius
            diameter = radius * 2

        item["_x"] = x + radius
        row.append(item)
        x += diameter + gap

    if row:
        row_y = top + max_radius + len(positions) * (2 * max_radius + row_gap)

        for row_item in row:
            positions.append(
                (
                    row_item,
                    row_item["_x"],
                    row_y,
                )
            )

    # Center bubbles within each row and verify circle-to-circle clearance.
    rows = {}
    for item, cx, cy in positions:
        rows.setdefault(cy, []).append((item, cx, cy))

    centered_positions = []

    for cy, row_items in rows.items():
        left_edge = min(cx - item["radius"] for item, cx, _ in row_items)
        right_edge = max(cx + item["radius"] for item, cx, _ in row_items)
        row_width = right_edge - left_edge
        offset = (width - row_width) / 2 - left_edge

        centered_positions.extend(
            (item, cx + offset, cy)
            for item, cx, cy in row_items
        )

    for i, (first, x1, y1) in enumerate(centered_positions):
        for second, x2, y2 in centered_positions[i + 1:]:
            distance = math.hypot(x2 - x1, y2 - y1)
            required_distance = first["radius"] + second["radius"] + 8

            if distance < required_distance:
                raise ValueError(
                    "Bubble overlap detected. "
                    "Increase the SVG width or reduce bubble sizes."
                )

    last_bottom = max(
        cy + item["radius"]
        for item, _, cy in centered_positions
    )
    height = math.ceil(last_bottom + 58)

    return centered_positions, height


def make_bubble(index, language, percentage, cx, cy, radius):
    color = COLORS.get(language, "#8b949e")

    # Smaller circles get smaller text; textLength prevents long labels
    # from extending beyond their bubble.
    label_size = 13 if radius >= 50 else 11 if radius >= 38 else 9
    percentage_size = 11 if radius >= 45 else 9
    max_text_width = max(28, radius * 1.55)

    return f"""
    <g class="bubble bubble-{index}" style="--delay:{-index * 0.7:.1f}s">
      <circle cx="{cx:.1f}" cy="{cy:.1f}" r="{radius:.1f}"
              fill="{color}" stroke="{color}" stroke-width="1.5"
              filter="url(#shadow)"/>
      <circle cx="{cx:.1f}" cy="{cy:.1f}" r="{radius - 1:.1f}"
              fill="url(#gloss)" pointer-events="none"/>
      <ellipse cx="{cx - radius * 0.28:.1f}"
               cy="{cy - radius * 0.58:.1f}"
               rx="{radius * 0.32:.1f}"
               ry="{max(3, radius * 0.11):.1f}"
               fill="#ffffff" opacity=".40"
               filter="url(#softGlow)" pointer-events="none"/>
      <path d="M {cx - radius * 0.53:.1f} {cy - radius * 0.49:.1f}
               Q {cx - radius * 0.28:.1f} {cy - radius * 0.78:.1f}
                 {cx - radius * 0.02:.1f} {cy - radius * 0.53:.1f}"
            fill="none" stroke="#ffffff" stroke-opacity=".68"
            stroke-width="{max(1, radius * 0.025):.1f}"
            stroke-linecap="round" pointer-events="none"/>
      <circle class="spark"
              cx="{cx + radius * 0.56:.1f}"
              cy="{cy - radius * 0.40:.1f}"
              r="{max(1.2, radius * 0.035):.1f}"
              fill="#ffffff" filter="url(#softGlow)"
              pointer-events="none"/>
      <g clip-path="url(#clip-{index})">
        <rect class="sweep"
              x="{cx - radius * 1.5:.1f}"
              y="{cy - radius * 1.2:.1f}"
              width="{radius * 3:.1f}"
              height="{radius * 2.4:.1f}"
              fill="url(#shineBand)"
              transform="rotate(-25 {cx:.1f} {cy:.1f})"
              pointer-events="none"/>
      </g>
      <text x="{cx:.1f}" y="{cy - 2:.1f}" text-anchor="middle"
            textLength="{max_text_width:.1f}" lengthAdjust="spacingAndGlyphs"
            fill="#ffffff" font-size="{label_size}" font-weight="700">
        {escape(language)}
      </text>
      <text x="{cx:.1f}" y="{cy + 17:.1f}" text-anchor="middle"
            fill="#ffffff" font-size="{percentage_size}" font-weight="700">
        {percentage:.2f}%
      </text>
    </g>
"""


def build_svg(username, repositories, language_totals):
    if not language_totals:
        raise SystemExit(
            f"No language data found for {username}'s public repositories."
        )

    total_bytes = sum(language_totals.values())

    if total_bytes <= 0:
        raise SystemExit("No language bytes found.")

    languages = sorted(
        language_totals.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    bubble_data = [
        {
            "language": language,
            "bytes": byte_count,
            "percentage": byte_count / total_bytes * 100,
        }
        for language, byte_count in languages
    ]

    positioned, height = place_bubbles(bubble_data)

    clip_paths = []
    bubble_groups = []

    for index, (item, cx, cy) in enumerate(positioned):
        radius = item["radius"]
        language = item["language"]

        clip_paths.append(
            f'<clipPath id="clip-{index}">'
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{radius:.1f}"/>'
            f"</clipPath>"
        )

        bubble_groups.append(
            make_bubble(
                index=index,
                language=language,
                percentage=item["percentage"],
                cx=cx,
                cy=cy,
                radius=radius,
            )
        )

    updated = datetime.now(ZoneInfo("Asia/Jakarta")).strftime(
        "%Y-%m-%d %H:%M WIB"
    )

    repository_count = len(repositories)
    language_count = len(languages)

    return f"""<svg xmlns="http://www.w3.org/2000/svg"
     width="720" height="{height}" viewBox="0 0 720 {height}"
     role="img" aria-labelledby="title desc">
  <title id="title">Repository Language Bubbles</title>
  <desc id="desc">
    Combined language statistics for {escape(username)}'s public repositories
  </desc>

  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#171e2b"/>
      <stop offset="1" stop-color="#0b1018"/>
    </linearGradient>

    <linearGradient id="shineBand" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#ffffff" stop-opacity="0"/>
      <stop offset=".42" stop-color="#ffffff" stop-opacity="0"/>
      <stop offset=".50" stop-color="#ffffff" stop-opacity=".8"/>
      <stop offset=".58" stop-color="#ffffff" stop-opacity="0"/>
      <stop offset="1" stop-color="#ffffff" stop-opacity="0"/>
    </linearGradient>

    <radialGradient id="gloss" cx="32%" cy="20%" r="80%">
      <stop offset="0" stop-color="#ffffff" stop-opacity=".38"/>
      <stop offset=".28" stop-color="#ffffff" stop-opacity=".12"/>
      <stop offset=".58" stop-color="#ffffff" stop-opacity="0"/>
    </radialGradient>

    <filter id="shadow" x="-45%" y="-45%" width="190%" height="190%">
      <feDropShadow dx="0" dy="7" stdDeviation="7"
                    flood-color="#000000" flood-opacity=".33"/>
    </filter>

    <filter id="softGlow" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="2.2" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>

    {''.join(clip_paths)}

    <style>
      text {{
        font-family: Arial, Helvetica, sans-serif;
      }}

      .bubble {{
        transform-box: fill-box;
        transform-origin: center;
        animation: drift 9.5s ease-in-out infinite;
        animation-delay: var(--delay);
      }}

      .sweep {{
        animation: sweep 4.6s ease-in-out infinite;
        opacity: 0;
      }}

      .spark {{
        transform-box: fill-box;
        transform-origin: center;
        animation: spark 2.8s ease-in-out infinite alternate;
      }}

      @keyframes drift {{
        0%, 100% {{ transform: translate(0, 0); }}
        28% {{ transform: translate(5px, -7px); }}
        63% {{ transform: translate(-4px, -10px); }}
        82% {{ transform: translate(-6px, -2px); }}
      }}

      @keyframes sweep {{
        0%, 18% {{ transform: translateX(-150%); opacity: 0; }}
        28% {{ opacity: .7; }}
        70% {{ opacity: .42; }}
        88%, 100% {{ transform: translateX(150%); opacity: 0; }}
      }}

      @keyframes spark {{
        0% {{ opacity: .15; transform: scale(.75); }}
        55% {{ opacity: .88; transform: scale(1.16); }}
        100% {{ opacity: .28; transform: scale(.85); }}
      }}

      @media (prefers-reduced-motion: reduce) {{
        .bubble, .sweep, .spark {{
          animation: none;
        }}
        .sweep {{
          display: none;
        }}
        .spark {{
          opacity: .5;
        }}
      }}
    </style>
  </defs>

  <rect x="8" y="8" width="704" height="{height - 16}" rx="22"
        fill="url(#bg)" stroke="#30363d"/>

  <text x="32" y="42" fill="#f0f6fc" font-size="18" font-weight="700">
    Repository Language Bubbles
  </text>
  <text x="32" y="62" fill="#8b949e" font-size="11">
    {escape(username)} · {repository_count} public repositories · {language_count} languages
  </text>

  {''.join(bubble_groups)}

  <text x="688" y="{height - 18}" text-anchor="end"
        fill="#8b949e" font-size="9">
    UPDATED {updated}
  </text>
</svg>
"""


repositories = get_all_public_repositories(USERNAME)
language_totals = get_all_language_totals(repositories)
svg_content = build_svg(USERNAME, repositories, language_totals)

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(svg_content, encoding="utf-8")

print(
    f"Updated {OUTPUT} with "
    f"{len(language_totals)} languages from "
    f"{len(repositories)} public repositories."
        )
