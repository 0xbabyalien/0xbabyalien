import json
import re
import urllib.request
from datetime import datetime, timezone

# Display symbol -> CoinGecko ID
COINS = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "BNB": "binancecoin",
    "HYPE": "hyperliquid",
}

URL = (
    "https://api.coingecko.com/api/v3/simple/price"
    f"?ids={','.join(COINS.values())}&vs_currencies=usd"
)

with urllib.request.urlopen(URL, timeout=20) as r:
    data = json.load(r)


def fmt(price):
    # No decimals for large prices, two decimals for smaller ones
    return f"${price:,.0f}" if price >= 1000 else f"${price:,.2f}"


parts = []
for symbol, coin_id in COINS.items():
    price = data.get(coin_id, {}).get("usd")
    if price is not None:
        parts.append(f"**{symbol}** {fmt(price)}")

if not parts:
    raise SystemExit("Error: no prices returned from CoinGecko")

now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

block = (
    "<!-- MARKER_START -->\n\n"
    + " · ".join(parts)
    + f"\n\n<sub>Updated {now}</sub>\n\n"
    "<!-- MARKER_END -->"
)

with open("README.md", "r", encoding="utf-8") as f:
    content = f.read()

new_content, count = re.subn(
    r"<!-- MARKER_START -->.*?<!-- MARKER_END -->",
    lambda m: block,
    content,
    flags=re.DOTALL,
)

if count == 0:
    raise SystemExit("Error: marker block not found in README.md")

with open("README.md", "w", encoding="utf-8") as f:
    f.write(new_content)
