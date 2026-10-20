import json
import math
import os
import urllib.error
import urllib.request
from html import escape
from pathlib import Path

USERNAME = os.environ.get("GITHUB_USERNAME", "0xbabyalien")
OUTPUT = Path("assets/language-stats.svg")
TOKEN = os.environ.get("GH_STATS_TOKEN") or os.environ.get("GITHUB_TOKEN")

SVG_WIDTH = 800
SVG_HEIGHT = 500
CX = 250
CY = 250
RING_RADIUS = 160
PIE_RADIUS = 80

COLORS = {
    "HTML": "#e34c26", "CSS": "#a371f7", "JavaScript": "#f1e05a",
    "TypeScript": "#3178c6", "Python": "#58a6ff", "Java": "#d29922",
    "C++": "#f34b7d", "C#": "#8b949e", "PHP": "#4F5D95", "Shell": "#89e051",
    "Go": "#00ADD8", "Rust": "#dea584", "Ruby": "#701516", "Dart": "#00B4AB",
    "Other": "#8b949e",
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
        raise RuntimeError(f"Failed to fetch data from {url}: {error}")

def get_all_public_repositories(username):
    repositories = []
    page = 1
    while True:
        url = f"https://api.github.com/users/{username}/repos?type=owner&sort=updated&per_page=100&page={page}"
        batch = fetch_github_data(url)
        if not batch: break
        repositories.extend(r for r in batch if not r.get("fork", False))
        page += 1
    return repositories

def get_language_totals(repositories):
    totals = {}
    for repo in repositories:
        url = f"https://api.github.com/repos/{repo['owner']['login']}/{repo['name']}/languages"
        for lang, count in fetch_github_data(url).items():
            totals[lang] = totals.get(lang, 0) + count
    return totals

def generate_svg(totals):
    if not totals: return ""

    # Process all languages: keep top 4 and combine the rest into "Other"
    all_sorted = sorted(totals.items(), key=lambda i: i[1], reverse=True)
    if len(all_sorted) > 5:
        top_4 = all_sorted[:4]
        other_bytes = sum(count for _, count in all_sorted[4:])
        sorted_langs = top_4 + [("Other", other_bytes)]
    else:
        sorted_langs = all_sorted

    total_bytes = sum(count for _, count in sorted_langs)
    
    # Circle Math Calculations
    ring_circ = 2 * math.pi * RING_RADIUS
    pie_circ = 2 * math.pi * PIE_RADIUS
    
    # SVG Element Builder Variables
    css_keyframes = []
    chart_items = []
    legends = []
    
    cumulative_percent = 0
    duration = 8.0 # Total animation cycle duration
    
    for i, (lang, byte_count) in enumerate(sorted_langs):
        percent = (byte_count / total_bytes) * 100
        color = COLORS.get(lang, "#8b949e")
        
        # Calculate Outer Ring (Static but segmented)
        ring_dash_len = (percent / 100) * ring_circ
        ring_offset = -(cumulative_percent / 100) * ring_circ
        
        # Calculate Inner Pie (Wipe Animation)
        pie_dash_len = (percent / 100) * pie_circ
        rotation = -90 + (cumulative_percent / 100) * 360
        
        # Calculate Percentage Text Position (Trigonometry)
        mid_angle_deg = cumulative_percent * 3.6 + (percent / 2) * 3.6
        mid_angle_rad = math.radians(mid_angle_deg - 90)
        
        text_x = CX + math.cos(mid_angle_rad) * 100
        text_y = CY + math.sin(mid_angle_rad) * 100

        # Keyframe Animation Timing Setup
        total_items = len(sorted_langs)
        slice_time = 100 / total_items 
        
        start_time = max(3.0, i * slice_time) 
        end_time = (i + 1) * slice_time
        
        t0 = start_time
        t1 = start_time + 0.1
        t2 = start_time + (slice_time * 0.25)
        t3 = start_time + (slice_time * 0.6)
        t4 = start_time + (slice_time * 0.9)
        t_end = t4 + 0.1
        
        # CSS Generator per language
        css_keyframes.append(f"""
        @keyframes wipe-pie-{i} {{
            0%, {t0:.1f}% {{ opacity: 0; stroke-dasharray: 0 {pie_circ:.1f}; stroke-dashoffset: 0; }}
            {t1:.1f}% {{ opacity: 1; stroke-dasharray: 0 {pie_circ:.1f}; stroke-dashoffset: 0; animation-timing-function: cubic-bezier(0.4, 0, 0.2, 1); }}
            {t2:.1f}% {{ stroke-dasharray: {pie_dash_len:.1f} {pie_circ:.1f}; stroke-dashoffset: 0; opacity: 1; }}
            {t3:.1f}% {{ stroke-dasharray: {pie_dash_len:.1f} {pie_circ:.1f}; stroke-dashoffset: 0; opacity: 1; animation-timing-function: cubic-bezier(0.4, 0, 0.2, 1); }}
            {t4:.1f}% {{ stroke-dasharray: 0 {pie_circ:.1f}; stroke-dashoffset: -{pie_dash_len:.1f}; opacity: 1; }}
            {t_end:.1f}%, 100% {{ opacity: 0; stroke-dasharray: 0 {pie_circ:.1f}; stroke-dashoffset: 0; }}
        }}
        @keyframes text-fade-{i} {{
            0%, {t0 + 2:.1f}%, {t4:.1f}%, 100% {{ opacity: 0; }}
            {t2:.1f}%, {t3:.1f}% {{ opacity: 1; }}
        }}
        """)
        
        # Chart Element Generator
        chart_items.append(f"""
        <g class="chart-item">
            <circle cx="{CX}" cy="{CY}" r="{RING_RADIUS}" fill="transparent" stroke="{color}" 
                    stroke-width="4" stroke-dasharray="{max(0.1, ring_dash_len - 4):.1f} {ring_circ:.1f}" 
                    stroke-dashoffset="{ring_offset:.1f}" class="ring"/>
            <circle cx="{CX}" cy="{CY}" r="{PIE_RADIUS}" stroke="{color}" class="inner-pie" 
                    style="transform: rotate({rotation:.1f}deg); animation: wipe-pie-{i} {duration}s infinite;"/>
            <text x="{text_x:.1f}" y="{text_y:.1f}" class="pie-text" fill="#ffffff" 
                  style="animation: text-fade-{i} {duration}s infinite;">{percent:.1f}%</text>
        </g>
        """)

        # Legend Generator
        legends.append(f"""
        <g class="legend-item" transform="translate(520, {150 + i * 40})">
            <rect x="0" y="-10" width="14" height="14" rx="3" fill="{color}"/>
            <text x="30" y="2" fill="#f0f6fc" font-size="16" font-family="sans-serif">{escape(lang)}</text>
        </g>
        """)

        cumulative_percent += percent

    # Assemble main SVG structure
    svg_template = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_WIDTH}" height="{SVG_HEIGHT}" viewBox="0 0 {SVG_WIDTH} {SVG_HEIGHT}">
  <defs>
    <filter id="shadow" x="-100%" y="-100%" width="300%" height="300%">
      <feDropShadow dx="2" dy="4" stdDeviation="3" flood-color="#000000" flood-opacity="0.5" />
    </filter>

    <mask id="ring-mask">
      <circle cx="{CX}" cy="{CY}" r="{RING_RADIUS}" fill="none" stroke="white" stroke-width="10" 
              stroke-dasharray="{ring_circ:.1f}" stroke-dashoffset="{ring_circ:.1f}" 
              style="animation: draw-ring {duration}s infinite;" />
    </mask>

    <style>
      .bg {{ fill: #0d1117; }} 
      .ring {{
        transform: rotate(-90deg);
        transform-origin: {CX}px {CY}px;
        stroke-linecap: round;
        mask: url(#ring-mask);
      }}
      @keyframes draw-ring {{
        0% {{ stroke-dashoffset: {ring_circ:.1f}; opacity: 1; }}
        3% {{ stroke-dashoffset: 0; opacity: 1; }}
        98% {{ stroke-dashoffset: 0; opacity: 1; }}
        98.1%, 100% {{ stroke-dashoffset: 0; opacity: 0; }}
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
      }}
      {''.join(css_keyframes)}
    </style>
  </defs>

  <rect width="100%" height="100%" class="bg" rx="15" />

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
    repos = get_all_public_repositories(USERNAME)
    totals = get_language_totals(repos)
    
    if totals:
        svg_output = generate_svg(totals)
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(svg_output, encoding="utf-8")
        print(f"Successfully rendered {OUTPUT} with all languages included!")
    else:
        print("No programming languages found.")

if __name__ == "__main__":
    main()
