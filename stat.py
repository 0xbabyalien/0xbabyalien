from datetime import datetime, timezone
from pathlib import Path

now = datetime.now(timezone.utc)
date = now.strftime("%Y-%m-%d")
time = now.strftime("%H:%M:%S UTC")

readme = Path("README.md")
content = readme.read_text(encoding="utf-8")

marker = "<!-- STAT -->"

new_stat = f"""<!-- STAT -->
Last updated: {date} {time}
"""

if marker in content:
    before = content.split(marker)[0]
    content = before + new_stat
else:
    content += f"\n\n{new_stat}"

readme.write_text(content, encoding="utf-8")

print(f"README.md updated on {date} at {time}")
