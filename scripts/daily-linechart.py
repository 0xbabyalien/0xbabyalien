import os, requests
from datetime import datetime, timedelta, timezone

USERNAME = "0xbabyalien"
TOKEN = os.environ["GH_TOKEN"]
DAYS = 30

query = """
query($login:String!, $from:DateTime!, $to:DateTime!){
  user(login:$login){
    contributionsCollection(from:$from, to:$to){
      contributionCalendar{
        weeks{ contributionDays{ date contributionCount } }
      }
    }
  }
}
"""
now = datetime.now(timezone.utc)
from_date = now - timedelta(days=DAYS)
variables = {"login": USERNAME, "from": from_date.isoformat(), "to": now.isoformat()}

res = requests.post("https://api.github.com/graphql",
  json={"query": query, "variables": variables},
  headers={"Authorization": f"Bearer {TOKEN}"}).json()

days = []
for week in res["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]:
    for d in week["contributionDays"]:
        days.append(d)

days = days[-DAYS:]
counts = [d["contributionCount"] for d in days]
total = sum(counts)

max_count = max(counts) if counts else 0
MAX_Y = max(15, ((max_count + 4) // 5) * 5)

def y_for(count):
    return 144 - (count / MAX_Y * 104) if MAX_Y > 0 else 144

VIEW_W = 600
LEFT, RIGHT = 32, 588
CHART_W = RIGHT - LEFT

points = []
poly_points = [f"{LEFT},144"]
for i, d in enumerate(days):
    x = LEFT + i * (CHART_W / (DAYS - 1))
    y = y_for(d["contributionCount"])
    points.append((x, y, d))
    poly_points.append(f"{x:.1f},{y:.1f}")
poly_points.append(f"{RIGHT},144")

points_str = " ".join([f"{x:.1f},{y:.1f}" for x,y,_ in points])
polygon_str = " ".join(poly_points)

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="170" viewBox="0 0 {VIEW_W} 170" role="img" aria-label="Daily GitHub activity line chart - last {DAYS} days">
<style>
.bg{{fill:#fff}} .t{{font:9px -apple-system,Segoe UI,Arial,sans-serif;fill:#57606a}}
.h{{font:600 12px -apple-system,Segoe UI,Arial,sans-serif;fill:#1f2328}}
.g{{stroke:#d8dee4;stroke-width:1}} .a{{fill:#0ad;opacity:.2}} .ln{{fill:none;stroke:#a819bb;stroke-width:2;stroke-linejoin:round;stroke-linecap:round}} .d{{fill:#fff;stroke:#216e39;stroke-width:1.5}}
@media (prefers-color-scheme: dark){{.bg{{fill:#0d1117}} .t{{fill:#8b949e}} .h{{fill:#e6edf3}} .g{{stroke:#30363d}} .a{{fill:#0ad}} .ln{{stroke:#0ad}} .d{{fill:#0d1117;stroke:#a819bb}}}}
</style>
<rect class="bg" width="100%" height="100%" rx="8"/>
<text x="{LEFT}" y="20" class="h">activity</text>
<text x="{RIGHT}" y="20" class="t" text-anchor="end">{total} contributions / {DAYS} days</text>
'''

for val in [0, round(MAX_Y*0.33), round(MAX_Y*0.66), MAX_Y]:
    y = y_for(val)
    svg += f'<line x1="{LEFT}" x2="{RIGHT}" y1="{y:.1f}" y2="{y:.1f}" class="g"/><text x="26" y="{y+3:.1f}" class="t" text-anchor="end">{val}</text>n'

svg += f'<polygon points="{polygon_str}" class="a"/>n'
svg += f'<polyline points="{points_str}" class="ln"/>n'

for x,y,d in points:
    date = datetime.fromisoformat(d["date"]).strftime("%b %d")
    label = "contribution" if d["contributionCount"] == 1 else "contributions"
    svg += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.5" class="d"><title>{date}: {d["contributionCount"]} {label}</title></circle>n'

for i, (x,y,d) in enumerate(points):
    if i % 5 == 0 or i == DAYS - 1:
        date = datetime.fromisoformat(d["date"]).strftime("%b %d")
        svg += f'<text x="{x:.1f}" y="162" class="t" text-anchor="middle">{date}</text>n'

svg += '</svg>'

open("github-activity-30days.svg","w").write(svg)
print(f"Generated {total} contributions for {DAYS} days, MAX_Y={MAX_Y}")
