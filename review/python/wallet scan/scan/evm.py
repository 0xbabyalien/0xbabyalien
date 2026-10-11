import argparse
import csv
import time
from datetime import datetime
from rich.console import Console
from rich.table import Table
import requests

console = Console()

STABLE_SYMBOLS = ["USDT", "USDC", "DAI", "BUSD", "TUSD", "USDD", "FRAX", "GUSD", "USDP", "LUSD", "FDUSD", "PYUSD"]
CHAINS = {
    "eth": 1, "bsc": 56, "pol": 137, "arb": 42161, "opbnb":204, "mantle":5000, "sonic":146, "hyper":999, "abs":2741, "monad":143, "blast":81457,"bera":80094,
    "op": 10, "base": 8453, "avax": 43114, "linea": 59144, "taiko":167000, "robin":4663, "arc":5042,"stable":988,"sei":1329,"celo":42220,"plasma":9745
}
NATIVE_SYMBOL = {
    "eth":"ETH","bsc":"BNB","pol":"POL","arb":"ETH", "opbnb":"BNB", "mantle":"MNT", "sonic":"S", "hyper":"HYPE","abs":"ETH","monad":"MON","blast":"ETH","bera":"BERA",
    "op":"ETH","base":"ETH","avax":"AVAX","linea":"ETH","taiko":"ETH","robin":"ETH","arc":"USDC","stable":"USDT","sei":"SEI","celo":"CELO","plasma":"XPL"
}
API_URL = "https://api.etherscan.io/v2/api"

def get_all_transactions(address, chain_id, api_key, action="tokentx"):
    all_result = []
    page = 1
    while True:
        params = {
            "chainid": chain_id, "module": "account", "action": action,
            "address": address, "startblock": 0, "endblock": 99999999,
            "page": page, "offset": 100, "sort": "desc", "apikey": api_key
        }
        try:
            res = requests.get(API_URL, params=params, timeout=15).json()
            if res["status"] == "1":
                all_result.extend(res["result"])
                if len(res["result"]) < 100:
                    break
                page += 1
                time.sleep(0.2)
            else:
                if "No transactions found" in res.get("message", ""):
                    break
                else:
                    console.print(f"[yellow]API Info {action}: {res.get('message')} - {res.get('result')}[/yellow]")
                    break
        except Exception as e:
            console.print(f"