
import json
import math
import os
import urllib.error
import urllib.request
from html import escape
from pathlib import Path
from colorsys import hsv_to_rgb

USERNAME = os.environ.get("GITHUB_USERNAME", "0xbabyalien")
OUTPUT = Path("assets/language-stats.svg")
TOKEN = os.environ.get("GH_STAT")

SVG_WIDTH = 800
CX = 250
CY = 250
RING_RADIUS = 160
PIE_RADIUS = 80
DURATION = 8.0

COLORS = {
    "HTML": "#e34c26",
    "CSS": "#a371f7",
    "JavaScript": "#f1e05a",
    "TypeScript": "#3178c6",
    "Python": "#58a6ff",
    "Java": "#d29922",
    "C++": "#f34b7d",
    "C": "#555555",
    "C#": "#178600",
    "PHP": "#4F5D95",
    "Shell": "#89e051",
    "Go": "#00ADD8",
    "Rust": "#dea584",
    "Ruby": "#701516",
    "Dart": "#00B4AB",
    "Kotlin": "#A97BFF",
    "Swift": "#F05138",
    "Objective-C": "#438eff",
    "Scala": "#DC322F",
    "R": "#198CE7",
    "Lua": "#000080",
    "Perl": "#0298c3",
    "PowerShell": "#5391FE",
    "HCL": "#844FBA",
    "Elixir": "#6E4A7E",
    "Clojure": "#5881D8",
    "Julia": "#9558B2",
    "Makefile": "#427819",
    "Dockerfile": "#384d54",
    "Vue": "#41B883",
    "Svelte": "#FF3E00",
    "Jupyter Notebook": "#DA5B0B",
    "Assembly": "#6E4C13",
    "Vim Script": "#199f4b",
    "WebAssembly": "#654FF0",
    "TeX": "#3D6117",
    "Markdown": "#083fa1",
    "YAML": "#cb171e",
    "JSON": "#292929",
    "SQL": "#e38c00",
}


HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "github-language-stats",
}

if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"


def fetch_github_data(url):
    request = urllib.request.Request(url, headers=HEADERS)

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    except urllib.error.URLError as error:
        raise RuntimeError(
            f"Failed to fetch data from {url}: {error}"
        ) from error


def get_all_repositories(username):
    if not TOKEN:
        raise RuntimeError(
            "GH_STAT is not set. A token is required to read "
            "private repositories."
        )

    token_owner = fetch_github_data(
        "https://api.github.com/user"
    ).get("login", "")

    if token_owner.lower() != username.lower():
        raise RuntimeError(
            f"The token belongs to '{token_owner}', but USERNAME "
            f"is '{username}'. Use a token from the same account."
        )

    repositories = []
    page = 1

    while True:
        url = (
            "https://api.github.com/user/repos"
            f"?affiliation=owner&visibility=all"
            f"&sort=updated&per_page=100&page={page}"
        )

        batch = fetch_github_data(url)

        if not batch:
            break

        repositories.extend(
            repo for repo in batch
            if not repo.get("fork", False)
        )

        page += 1

    public_count = sum(
        1 for repo in repositories if not repo.get("private")
    )
    private_count = len(repositories) - public_count

    print(
        f"Found {public_count} public and "
        f"{private_count} private repositories."
    )

    return repositories


def get_language_totals(repositories):
    totals = {}

    for repo in repositories:
        owner = repo["owner"]["login"]
        name = repo["name"]

        url = (
            f"https://api.github.com/repos/"
            f"{owner}/{name}/languages"
        )

        try:
            languages = fetch_github_data(url)
        except RuntimeError as error:
            print(f"Skipping {name}: {error}")
            continue

        for language, byte_count in languages.items():
            totals[language] = (
                totals.get(language, 0) + byte_count
            )

    return totals


def get_language_color(language, index=0):
    if language in COLORS:
        return COLORS[language]

    hue = (index * 0.618033988749895) % 1.0
    saturation = 0.62
    value = 0.95

    red, green, blue = hsv_to_rgb(
        hue, saturation, value
    )

    return "#{:02x}{:02x}{:02x}".format(
        round(red * 255),
        round(green * 255),
        round(blue * 255),
    )


def generate_svg(totals):
    all_sorted = sorted(
        (
            (language, count)
            for language, count in totals.items()
            if count > 0
        ),
        key=lambda item: item[1],
        reverse=True,
    )

    if not all_sorted:
        return ""

    total_bytes = sum(
        count for _, count in all_sorted
    )

    if total_bytes <= 0:
        return ""

    language_count = len(all_sorted)

    legend_top = 130
    legend_spacing = 30
    legend_bottom_padding = 30

    svg_height = max(
        500,
        legend_top
        + language_count * legend_spacing
        + legend_bottom_padding,
    )

    ring_circ = 2 * math.pi * RING_RADIUS
    pie_circ = 2 * math.pi * PIE_RADIUS

    css_keyframes = []
    chart_items = []
    legends = []

    cumulative_percent = 0.0

    animation_start = 3.0
    animation_end = 96.0
    animation_range = animation_end - animation_start
    slice_time = animation_range / language_count

    for i, (language, byte_count) in enumerate(all_sorted):
        percent = byte_count / total_bytes * 100
        color = get_language_color(language, i)

        ring_dash_len = percent / 100 * ring_circ
        ring_offset = -cumulative_percent / 100 * ring_circ

        pie_dash_len = percent / 100 * pie_circ
        rotation = -90 + cumulative_percent / 100 * 360

        mid_angle_deg = (
            cumulative_percent + percent / 2
        ) * 3.6

        mid_angle_rad = math.radians(
            mid_angle_deg - 90
        )

        text_x = CX + math.cos(mid_angle_rad) * 100
        text_y = CY + math.sin(mid_angle_rad) * 100

        t0 = animation_start + i * slice_time
        t1 = t0 + min(0.1, slice_time * 0.03)
        t2 = t0 + slice_time * 0.25
        t3 = t0 + slice_time * 0.60
        t4 = t0 + slice_time * 0.90
        t_end = min(100.0, t4 + 0.1)

        css_keyframes.append(f"""
        @keyframes wipe-pie-{i} {{
            0%, {t0:.4f}% {{
                opacity: 0;
                stroke-dasharray: 0 {pie_circ:.2f};
                stroke-dashoffset: 0;
            }}
            {t1:.4f}% {{
                opacity: 1;
                stroke-dasharray: 0 {pie_circ:.2f};
                stroke-dashoffset: 0;
                animation-timing-function:
                    cubic-bezier(0.4, 0, 0.2, 1);
            }}
            {t2:.4f}% {{
                stroke-dasharray:
                    {pie_dash_len:.2f} {pie_circ:.2f};
                stroke-dashoffset: 0;
                opacity: 1;
            }}
            {t3:.4f}% {{
                stroke-dasharray:
                    {pie_dash_len:.2f} {pie_circ:.2f};
                stroke-dashoffset: 0;
                opacity: 1;
                animation-timing-function:
                    cubic-bezier(0.4, 0, 0.2, 1);
            }}
            {t4:.4f}% {{
                stroke-dasharray: 0 {pie_circ:.2f};
                stroke-dashoffset: -{pie_dash_len:.2f};
                opacity: 1;
            }}
            {t_end:.4f}%, 100% {{
                opacity: 0;
                stroke-dasharray: 0 {pie_circ:.2f};
                stroke-dashoffset: 0;
            }}
        }}

        @keyframes text-fade-{i} {{
            0%, {t0:.4f}% {{ opacity: 0; }}
            {t2:.4f}%, {t3:.4f}% {{ opacity: 1; }}
            {t4:.4f}%, 100% {{ opacity: 0; }}
        }}
        """)

        chart_items.append(f"""
        <g class="chart-item">
            <circle
                cx="{CX}"
                cy="{CY}"
                r="{RING_RADIUS}"
                fill="transparent"
                stroke="{color}"
                stroke-width="4"
                stroke-dasharray="
                    {max(0.1, ring_dash_len - 4):.2f}
                    {ring_circ:.2f}
                "
                stroke-dashoffset="{ring_offset:.2f}"
                class="ring"
            />

            <circle
                cx="{CX}"
                cy="{CY}"
                r="{PIE_RADIUS}"
                stroke="{color}"
                class="inner-pie"
                style="
                    transform: rotate({rotation:.4f}deg);
                    animation: wipe-pie-{i} {DURATION}s infinite;
                "
            />

            <text
                x="{text_x:.2f}"
                y="{text_y:.2f}"
                class="pie-text"
                fill="#ffffff"
                style="animation: text-fade-{i} {DURATION}s infinite;"
            >{percent:.1f}%</text>
        </g>
        """)

        legend_y = legend_top + i * legend_spacing

        legends.append(f"""
        <g class="legend-item"
           transform="translate(520, {legend_y})">
            <rect
                x="0"
                y="-10"
                width="14"
                height="14"
                rx="3"
                fill="{color}"
            />
            <text
                x="24"
                y="2"
                fill="#f0f6fc"
                font-size="13"
                font-family="sans-serif"
            >{escape(language)} · {percent:.1f}%</text>
        </g>
        """)

        cumulative_percent += percent

    svg_template = f"""<svg
    xmlns="http://www.w3.org/2000/svg"
    width="{SVG_WIDTH}"
    height="{svg_height}"
    viewBox="0 0 {SVG_WIDTH} {svg_height}"
>
  <defs>
    <filter
        id="shadow"
        x="-100%"
        y="-100%"
        width="300%"
        height="300%"
    >
      <feDropShadow
          dx="2"
          dy="4"
          stdDeviation="3"
          flood-color="#000000"
          flood-opacity="0.5"
      />
    </filter>

    <mask id="ring-mask">
      <circle
          cx="{CX}"
          cy="{CY}"
          r="{RING_RADIUS}"
          fill="none"
          stroke="white"
          stroke-width="10"
          stroke-dasharray="{ring_circ:.2f}"
          stroke-dashoffset="{ring_circ:.2f}"
          style="animation: draw-ring {DURATION}s infinite;"
      />
    </mask>

    <style>
      .bg {{
        fill: #0d1117;
      }}

      .ring {{
        transform: rotate(-90deg);
        transform-origin: {CX}px {CY}px;
        stroke-linecap: round;
        mask: url(#ring-mask);
      }}

      @keyframes draw-ring {{
        0% {{
          stroke-dashoffset: {ring_circ:.2f};
          opacity: 1;
        }}
        3% {{
          stroke-dashoffset: 0;
          opacity: 1;
        }}
        98% {{
          stroke-dashoffset: 0;
          opacity: 1;
        }}
        98.1%, 100% {{
          stroke-dashoffset: 0;
          opacity: 0;
        }}
      }}

      .inner-pie {{
        fill: transparent;
        stroke-width: 160;
        transform-origin: {CX}px {CY}px;
        filter: url(#shadow);
      }}

      .pie-text {{
        font-family: sans-serif;
        font-size: 16px;
        font-weight: bold;
        text-anchor: middle;
        dominant-baseline: middle;
        opacity: 0;
        pointer-events: none;
      }}

      {''.join(css_keyframes)}
    </style>
  </defs>

  <rect
      width="100%"
      height="100%"
      class="bg"
      rx="15"
  />

  <g id="chart-container">
    {''.join(chart_items)}
  </g>

  <g id="legends">
    {''.join(legends)}
  </g>
</svg>"""

    return svg_template


def main():
    print(f"Fetching repository data for {USERNAME}...")

    repositories = get_all_repositories(USERNAME)
    totals = get_language_totals(repositories)

    if totals:
        svg_output = generate_svg(totals)

        OUTPUT.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        OUTPUT.write_text(
            svg_output,
            encoding="utf-8",
        )

        print(
            f"Successfully rendered {OUTPUT} "
            f"with {len(totals)} programming languages."
        )
    else:
        print("No programming languages found.")


if __name__ == "__main__":
    main()
