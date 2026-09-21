from datetime import datetime, timezone
from pathlib import Path

now = datetime.now(timezone.utc)
date = now.strftime("%Y-%m-%d")
time = now.strftime("%H:%M:%S UTC")

content = f"""Stat update

Date: {date}
Updated at: {time}
Status: Active
"""

Path("stat").write_text(content, encoding="utf-8")

print(f"Stat updated on {date} at {time}")
