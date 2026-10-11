from datetime import datetime, timezone
from pathlib import Path

readme_path = Path("README.md")

now = datetime.now(timezone.utc)
date = now.strftime("%Y-%m-%d")
time = now.strftime("%H:%M:%S UTC")

readme = readme_path.read_text(encoding="utf-8")

start_marker = "<!-- STAT_START -->"
end_marker = "<!-- STAT_END -->"

start_index = readme.find(start_marker)
end_index = readme.find(end_marker)

if start_index == -1 or end_index == -1:
    raise ValueError("STAT_START or STAT_END marker was not found in README.md")

if end_index <= start_index:
    raise ValueError("STAT_END appears before STAT_START")

new_content = (
    readme[:start_index + len(start_marker)]
    + f"""
📅 Daily commits: 1
🖥 Last update: {date} {time}
"""
    + readme[end_index:]
)

readme_path.write_text(new_content, encoding="utf-8")

print(f"README.md updated successfully on {date} at {time}")
