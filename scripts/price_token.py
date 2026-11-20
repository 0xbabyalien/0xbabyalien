import json
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone

NL = chr(10)  # newline, avoids backslash escapes that can break when pasting

# Display symbol -> (CoinGecko ID, badge color in hex)
COINS = {
    "BTC": ("bitcoin", "F7931A"),
    "ETH": ("ethereum", "627EEA"),
    "SOL": ("solana", "9945FF"),
    "BNB": ("binancecoin", "F3BA2F"),
    "HYPE": ("hyperliquid", "14B8A6"),
}

ids = ",".join(coin_id for coin_id, _ in COINS.values())
URL = "https://api.coingecko.com/api/v3/simple/price?ids=" + ids + "&vs_currencies=usd"

with urllib.request.urlopen(URL, timeout=20) as r:
    data = json.load(r)


def fmt(price):
    # No decimals for large prices, two decimals for smaller ones
    if price >= 1000:
        return "$" + format(price, ",.0f")
    return "$" + format(price, ",.2f")


def badge(symbol, price, color):
    # Static shields.io badge rendered with an HTML img tag
    label = urllib.parse.quote(symbol, safe="")
    message = urllib.parse.quote(fmt(price), safe="")
    src = (
        "https://img.shields.io/badge/"
        + label + "-" + message + "-" + color
        + "?style=plastic&labelColor=1F2937"
    )
    return '<img src="' + src + '" alt="' + symbol + '">'


parts = []
for symbol, (coin_id, color) in COINS.items():
    price = data.get(coin_id, {}).get("usd")
    if price is not None:
        parts.append(badge(symbol, price, color))

if not parts:
    raise SystemExit("Error: no prices returned from CoinGecko")

now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

block = NL.join(
    [
        "<!-- MARKER_START -->",
        "",
        " ".join(parts),
        "",
        r'$\color{#594236}{\textsf{Updated ' + now + r'}}$',
        "<!-- MARKER_END -->",
    ]
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
