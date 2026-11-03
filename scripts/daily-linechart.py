import os, requests
from datetime import datetime, timedelta, timezone

USERNAME = "0xbabyalien"
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
DAYS = 30

if not TOKEN:
    raise ValueError("GitHub token not found. Ensure GH_TOKEN or GITHUB_TOKEN is set in environment variables.")

query = """
query($login:String!, $from:DateTime!,$to:DateTime!){
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

variables = {
    "login": USERNAME,
    "from": from_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
    "to": now.strftime("%Y-%m-%dT%H:%M:%SZ")
}

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "User-Agent": USERNAME,
    "Content-Type": "application/json"
}

response = requests.post(
    "https://api.github.com/graphql",
    json={"query": query, "variables": variables},
    headers=headers
)

res = response.json()

if "data" not in res or res["data"] is None:
    print(f"HTTP Status Code: {response.status_code}")
    print(f"GitHub API Error Response: {res}")
    raise KeyError(f"API response missing 'data' key. Response: {res}")

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

points_str = " ".join([f"{x:.1f},{y:.1f}" for x, y, _ in points])
polygon_str = " ".join(poly_points)

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="170" viewBox="0 0 {VIEW_W} 170" role="img" aria-label="Daily GitHub activity line chart - last {DAYS} days">
<style>
.bg{{fill:#fff}} .t{{font:9px -apple-system,Segoe UI,Arial,sans-serif;fill:#57606a}}
.h{{font:600 12px -apple-system,Segoe UI,Arial,sans-serif;fill:#1f2328}}
.g{{stroke:#d8dee4;stroke-width:1}} .a{{fill:#0ad;opacity:.2}}
.ln{{
  fill:none;
  stroke:#a819bb;
  stroke-width:2;
  stroke-linejoin:round;
  stroke-linecap:round;
  stroke-dasharray: 10 10;
  stroke-dashoffset: 0;
  animation: walk 0.8s linear infinite;
}}
.d{{fill:#fff;stroke
