import json
import math
import os
import random
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

SVG_WIDTH = 720
SIDE_MARGIN = 22
TOP = 112
PACKING_GAP = 4
MIN_RADIUS = 24
MAX_RADIUS = 53
MIN_ANIMATION_GAP = 13

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


def get_language_totals(repositories):
    totals = {}

    for repository in repositories:
        owner = repository["owner"]["login"]
        name = repository["name"]
        url = f"https://api.github.com/repos/{owner}/{name}/languages"

        repository_languages = github_get(url)

        for language, byte_count in repository_languages.items():
            totals[language] = totals.get(language, 0) + byte_count

    return totals


def circles_overlap(x, y, radius, placed, gap):
    for other in placed:
        distance = math.hypot(x - other["x"], y - other["y"])
        if distance < radius + other["radius"] + gap:
            return True
    return False


def candidate_positions(placed, radius, width, height, gap):
    center_x = width / 2
    center_y = height / 2

    yield center_x, center_y

    # Search outward from the center.
    for ring in range(1, 90):
        ring_distance = ring * 2.5
        sample_count = max(24, ring * 16)

        for step in range(sample_count):
            angle = 2 * math.pi * step / sample_count
            yield (
                center_x + math.cos(angle) * ring_distance,
                center_y + math.sin(angle) * ring_distance,
            )

    # Test positions around circles already placed.
    for other in placed:
        distance = radius + other["radius"] + gap

        for step in range(72):
            angle = 2 * math.pi * step / 72
            yield (
                other["x"] + math.cos(angle) * distance,
                other["y"] + math.sin(angle) * distance,
            )


def try_pack(items, width, height, gap):
    placed = []

    for item in items:
        radius = item["radius"]
        chosen = None

        for x, y in candidate_positions(
            placed,
            radius,
            width,
            height,
            gap,
        ):
            if (
                x < radius + 3
                or x > width - radius - 3
                or y < radius + 3
                or y > height - radius - 3
            ):
                continue

            if not circles_overlap(x, y, radius, placed, gap):
                chosen = (x, y)
                break

        if chosen is None:
            return None

        item["x"], item["y"] = chosen
        placed.append(item)

    return placed


def pack_circles(language_data):
    if not language_data:
        return [], 220

    largest_value = max(item["bytes"] for item in language_data)

    for item in language_data:
        share = item["bytes"] / largest_value
        item["radius"] = MIN_RADIUS + (
            MAX_RADIUS - MIN_RADIUS
        ) * math.sqrt(share)

    # Large circles are placed first for a more compact cluster.
    ordered = sorted(
        language_data,
        key=lambda item: item["radius"],
        reverse=True,
    )

    pack_width = SVG_WIDTH - 2 * SIDE_MARGIN
    gap = PACKING_GAP
    height = max(230, int(math.sqrt(len(ordered)) * 190))
    placed = None

    # If the layout does not fit, add height; then reduce spacing if necessary.
    for attempt in range(18):
        placed = try_pack(ordered, pack_width, height, gap)

        if placed is not None:
            break

        if attempt % 2 == 0:
            height += 140
        else:
            gap = max(1, gap - 1)

    if placed is None:
        raise RuntimeError(
            "Could not place all language bubbles in the SVG layout."
        )

    min_x = min(item["x"] - item["radius"] for item in placed)
    max_x = max(item["x"] + item["radius"] for item in placed)
    min_y = min(item["y"] - item["radius"] for item in placed)
    max_y = max(item["y"] + item["radius"] for item in placed)

    cluster_width = max_x - min_x
    horizontal_shift = (pack_width - cluster_width) / 2 - min_x
    vertical_shift = TOP - min_y

    for item in placed:
        item["x"] += horizontal_shift + SIDE_MARGIN
        item["y"] += vertical_shift

    final_bottom = max(
        item["y"] + item["radius"]
        for item in placed
    )
    svg_height = math.ceil(final_bottom + 48)

    # Check that every initial circle is inside the canvas and non-overlapping.
    for index, first in enumerate(placed):
        if (
            first["x"] - first["radius"] < 8
            or first["x"] + first["radius"] > SVG_WIDTH - 8
            or first["y"] - first["radius"] < 8
            or first["y"] + first["radius"] > svg_height - 8
        ):
            raise RuntimeError(
                f"Bubble for {first['language']} is outside the SVG canvas."
            )

        for second in placed[index + 1:]:
            distance = math.hypot(
                second["x"] - first["x"],
                second["y"] - first["y"],
            )

            if distance < first["radius"] + second["radius"] + gap:
                raise RuntimeError("Bubble overlap detected.")

    return placed, svg_height


def make_bubble(index, item, total_bytes):
    language = item["language"]
    radius = item["radius"]
    cx = item["x"]
    cy = item["y"]
    percentage = item["bytes"] / total_bytes * 100
    fill_color = COLORS.get(language, "#8b949e")

    if radius >= 46:
        label_size = 12
        percentage_size = 10
    elif radius >= 34:
        label_size = 10
        percentage_size = 9
    else:
        label_size = 8
        percentage_size = 8

    text_width = max(26, radius * 1.55)

    return f"""
    <g class="bubble bubble-{index}">
      <circle class="bubble-outline"
              cx="{cx:.2f}" cy="{cy:.2f}" r="{radius:.2f}"
              fill="{fill_color}" fill-opacity=".96"
              stroke="#0ad" stroke-width="1.5"
              filter="url(#shadow)"/>

      <circle cx="{cx:.2f}" cy="{cy:.2f}" r="{radius - 1:.2f}"
              fill="url(#gloss)" pointer-events="none"/>

      <ellipse cx="{cx - radius * 0.28:.2f}"
               cy="{cy - radius * 0.58:.2f}"
               rx="{radius * 0.32:.2f}"
               ry="{max(3, radius * 0.11):.2f}"
               fill="#ffffff" opacity=".40"
               filter="url(#softGlow)" pointer-events="none"/>

      <path d="M {cx - radius * 0.53:.2f} {cy - radius * 0.49:.2f}
               Q {cx - radius * 0.28:.2f} {cy - radius * 0.78:.2f}
                 {cx - radius * 0.02:.2f} {cy - radius * 0.53:.2f}"
            fill="none" stroke="#ffffff" stroke-opacity=".68"
            stroke-width="{max(1, radius * 0.025):.2f}"
            stroke-linecap="round" pointer-events="none"/>

      <circle class="spark"
              cx="{cx + radius * 0.56:.2f}"
              cy="{cy - radius * 0.40:.2f}"
              r="{max(1.2, radius * 0.035):.2f}"
              fill="#ffffff" filter="url(#softGlow)"
              pointer-events="none"/>

      <g clip-path="url(#clip-{index})">
        <rect class="sweep"
              x="{cx - radius * 1.5:.2f}"
              y="{cy - radius * 1.2:.2f}"
              width="{radius * 3:.2f}"
              height="{radius * 2.4:.2f}"
              fill="url(#shineBand)"
              transform="rotate(-25 {cx:.2f} {cy:.2f})"
              pointer-events="none"/>
      </g>

      <text x="{cx:.2f}" y="{cy - 2:.2f}" text-anchor="middle"
            textLength="{text_width:.2f}"
            lengthAdjust="spacingAndGlyphs"
            fill="#ffffff" font-size="{label_size}" font-weight="700">
        {escape(language)}
      </text>

      <text x="{cx:.2f}" y="{cy + 15:.2f}" text-anchor="middle"
            fill="#ffffff" font-size="{percentage_size}" font-weight="700">
        {percentage:.2f}%
      </text>
    </g>
"""


def make_global_animation_css(bubbles):
    rules = []

    for index, item in enumerate(bubbles):
        rng = random.Random(f"{item['language']}-{index}")

        dx1 = rng.randint(-2, 2)
        dy1 = rng.randint(-2, 2)
        dx2 = rng.randint(-3, 3)
        dy2 = rng.randint(-3, 3)
        dx3 = rng.randint(-2, 2)
        dy3 = rng.randint(-2, 2)
        duration = rng.randint(10, 17)
        delay = -rng.uniform(0, duration)

        rules.append(
            f"""
      .bubble-{index} {{
        animation-name: drift-{index};
        animation-duration: {duration}s;
        animation-delay: {delay:.2f}s;
      }}

      @keyframes drift-{index} {{
        0%, 100% {{ transform: translate(0, 0); }}
        28% {{ transform: translate({dx1}px, {dy1}px); }}
        62% {{ transform: translate({dx2}px, {dy2}px); }}
        84% {{ transform: translate({dx3}px, {dy3}px); }}
      }}
"""
        )

    return "
".join(rules)


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

    language_data = [
        {"language": language, "bytes": byte_count}
        for language, byte_count in languages
    ]

    bubbles, svg_height = pack_circles(language_data)

    clip_paths = []
    bubble_groups = []

    for index, item in enumerate(bubbles):
        cx = item["x"]
        cy = item["y"]
        radius = item["radius"]

        clip_paths.append(
            f'<clipPath id="clip-{index}">'
            f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{radius:.2f}"/>'
            f"</clipPath>"
        )

        bubble_groups.append(make_bubble(index, item, total_bytes))

    updated = datetime.now(ZoneInfo("Asia/Jakarta")).strftime(
        "%Y-%m-%d %H:%M WIB"
    )
    animation_css = make_global_animation_css(bubbles)

    return f"""<svg xmlns="http://www.w3.org/2000/svg"
     width="{SVG_WIDTH}" height="{svg_height}"
     viewBox="0 0 {SVG_WIDTH} {svg_height}"
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
        animation-timing-function: ease-in-out;
        animation-iteration-count: infinite;
      }}

      .bubble-outline {{
        stroke: #0ad;
        stroke-width: 1.5;
        animation: outline-pulse 2s ease-in-out infinite alternate;
      }}

      @keyframes outline-pulse {{
        from {{
          stroke: #0ad;
          stroke-width: 1.5;
          stroke-opacity: .95;
        }}
        to {{
          stroke: #a819bb;
          stroke-width: 1.8;
          stroke-opacity: .9;
        }}
      }}

      {animation_css}

      .sweep {{
        animation: sweep 4.6s ease-in-out infinite;
        opacity: 0;
      }}

      .spark {{
        transform-box: fill-box;
        transform-origin: center;
        animation: spark 2.8s ease-in-out infinite alternate;
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
        .bubble, .bubble-outline, .sweep, .spark {{
          animation: none !important;
        }}

        .bubble-outline {{
          stroke: #0ad;
          stroke-width: 1.5;
          stroke-opacity: .95;
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

  <rect x="8" y="8" width="{SVG_WIDTH - 16}" height="{svg_height - 16}"
        rx="22" fill="url(#bg)" stroke="#30363d"/>

  <text x="32" y="42" fill="#f0f6fc" font-size="18" font-weight="700">
    Repository Language Bubbles
  </text>

  <text x="32" y="62" fill="#8b949e" font-size="11">
    {escape(username)} · {len(repositories)} public repositories · {len(languages)} languages
  </text>

  {''.join(bubble_groups)}

  <text x="{SVG_WIDTH - 32}" y="{svg_height - 18}" text-anchor="end"
        fill="#8b949e" font-size="9">
    UPDATED {updated}
  </text>
</svg>
"""


repositories = get_all_public_repositories(USERNAME)
language_totals = get_language_totals(repositories)
svg_content = build_svg(USERNAME, repositories, language_totals)

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(svg_content, encoding="utf-8")

print(
    f"Updated {OUTPUT} with {len(language_totals)} languages "
    f"from {len(repositories)} public repositories."
)
