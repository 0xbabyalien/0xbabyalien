
import json
import os
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo
from html import escape
from pathlib import Path

repository = os.environ["GITHUB_REPOSITORY"]
token = os.environ["GITHUB_TOKEN"]

request = urllib.request.Request(
    f"https://api.github.com/repos/{repository}/languages",
    headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
)

with urllib.request.urlopen(request, timeout=30) as response:
    languages = json.load(response)

total = sum(languages.values())

if total == 0:
    raise SystemExit("No language data found.")

colors = {
    "HTML": "#e34c26",
    "CSS": "#563d7c",
    "JavaScript": "#f1e05a",
    "TypeScript": "#3178c6",
    "Python": "#3572A5",
    "Java": "#b07219",
    "C++": "#f34b7d",
    "C": "#555555",
    "PHP": "#4F5D95",
    "Shell": "#89e051",
    "Go": "#00ADD8",
    "Rust": "#dea584",
    "Ruby": "#701516",
    "Dart": "#00B4AB"
}

items = sorted(languages.items(), key=lambda item: item[1], reverse=True)

width = 720
row_height = 34
height = 120 + len(items) * row_height
bar_x = 24
bar_y = 76
bar_width = width - 48
bar_height = 14

svg = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
    '<rect width="100%" height="100%" rx="12" fill="#0d1117" stroke="#30363d"/>',
    '<g font-family="Arial, Helvetica, sans-serif" fill="#e6edf3">',
    '<text x="24" y="34" font-size="19" font-weight="bold">Repository Language Statistics</text>',
    f'<text x="24" y="56" font-size="11" fill="#8b949e">{escape(repository)}</text>'
]

x = bar_x

for language, size in items:
    segment_width = bar_width * size / total
    color = colors.get(language, "#8b949e")
    svg.append(
        f'<rect x="{x:.2f}" y="{bar_y}" width="{segment_width:.2f}" height="{bar_height}" fill="{color}"/>'
    )
    x += segment_width

for index, (language, size) in enumerate(items):
    y = 119 + index * row_height
    percentage = size / total * 100
    color = colors.get(language, "#8b949e")

    svg.extend([
        f'<circle cx="30" cy="{y - 4}" r="5" fill="{color}"/>',
        f'<text x="46" y="{y}" font-size="13">{escape(language)}</text>',
        f'<text x="{width - 24}" y="{y}" font-size="13" text-anchor="end" fill="#8b949e">{percentage:.2f}%</text>'
    ])

updated = datetime.now(ZoneInfo("Asia/Jakarta")).strftime("%Y-%m-%d %H:%M WIB")

svg.extend([
    f'<text x="24" y="{height - 18}" font-size="10" fill="#8b949e">Last updated: {updated}</text>',
    '</g>',
    '</svg>'
])

output = Path("assets/language-stats.svg")
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text("\n".join(svg), encoding="utf-8")

print(f"Updated {output}")
