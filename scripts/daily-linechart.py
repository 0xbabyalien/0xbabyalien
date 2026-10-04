import os, requests
from datetime import datetime, timedelta, timezone

USERNAME = "0xbabyalien"
TOKEN = os.environ["GH_TOKEN"]
MAX_Y = 15

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
seven_days_ago = now - timedelta(days=7)
variables = {"login": USERNAME, "from": seven_days_ago.isoformat(), "to": now.isoformat()}

res = requests.post("https://api.github.com/graphql",
  json={"query": query, "variables": variables},
  headers={"Authorization": f"Bearer {TOKEN}"}).json()

days = []
for week in res["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]:
    for d in week["contributionDays"]:
        days.append(d)

days = days[-7:]
counts = [d["contributionCount"] for d in days]
total = sum(counts)

def y_for(count):
    # y 144 = 0, y 40 = 15
    return 144 - (count / MAX_Y * 104)

points = []
poly_points = ["32,144"]
for i, d in enumerate(days):
    x = 32 + i * (356 / 6) 
    y = y_for(d["contributionCount"])
    points.append((x, y, d))
    poly_points.append(f"{x:.1f},{y:.1f}")
poly_points.append("388.0,144")

points_str = " ".join([f"{x:.1f},{y:.1f}" for x,y,_ in points])
polygon_str = " ".join(poly_points)

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="170" viewBox="0 0 400 170" role="img" aria-label="Daily GitHub activity line chart - last 7 days">
<style>
.bg{{fill:#fff}} .t{{font:9px -apple-system,Segoe UI,Arial,sans-serif;fill:#57606a}}
.h{{font:600 12px -apple-system,Segoe UI,Arial,sans-serif;fill:#1f2328}}
.g{{stroke:#d8dee4;stroke-width:1}} .a{{fill:#0ad;opacity:.2}} .ln{{fill:none;stroke:#888;stroke-width:2;stroke-linejoin:round;stroke-linecap:round}} .d{{fill:#fff;stroke:#216e39;stroke-width:1.5}}
@media (prefers-color-scheme: dark){{.bg{{fill:#0d1117}} .t{{fill:#8b949e}} .h{{fill:#e6edf3}} .g{{stroke:#30363d}} .a{{fill:#0ad}} .ln{{stroke:#0ad}} .d{{fill:#0d1117;stroke:#888}}}}
</style>
<rect class="bg" width="100%" height="100%" rx="8"/>
<text x="32" y="20" class="h">GitHub Activity</text>
<text x="388" y="20" class="t" text-anchor="end">{total} contributions / 7 days</text>
<line x1="32" x2="388" y1="144.0" y2="144.0" class="g"/><text x="26" y="147.0" class="t" text-anchor="end">0</text>
<line x1="32" x2="388" y1="109.3" y2="109.3" class="g"/><text x="26" y="112.3" class="t" text-anchor="end">5</text>
<line x1="32" x2="388" y1="74.7" y2="74.7" class="g"/><text x="26" y="77.7" class="t" text-anchor="end">10</text>
<line x1="32" x2="388" y1="40.0" y2="40.0" class="g"/><text x="26" y="43.0" class="t" text-anchor="end">15</text>
<polygon points="{polygon_str}" class="a"/>
<polyline points="{points_str}" class="ln"/>
'''

for x,y,d in points:
    date = datetime.fromisoformat(d["date"]).strftime("%b %d")
    label = "contribution" if d["contributionCount"] == 1 else "contributions"
    svg += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.5" class="d"><title>{date}: {d["contributionCount"]} {label}</title></circle>n'

for x,y,d in points:
    date = datetime.fromisoformat(d["date"]).strftime("%b %d")
    svg += f'<text x="{x:.1f}" y="162" class="t" text-anchor="middle">{date}</text>n'

svg += '</svg>'

open("github-activity-7days.svg","w").write(svg)
print(f"Generated {total} contributions")
