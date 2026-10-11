import argparse
import csv
import time
import requests
from datetime import datetime
from rich.console import Console
from rich.table import Table

console = Console()

STABLE_SYMBOLS = ["USDT", "USDC", "DAI", "BUSD", "USDP", "PYUSD", "FDUSD"]

def load_rpc_url(args):
    try:
        with open(args.api_file, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if content:
                if content.startswith("http"):
                    return content
                else:
                    return f"https://mainnet.helius-rpc.com/?api-key={content}"
    except FileNotFoundError:
        console.print(f"[yellow]File {args.api_file} not found, falling back to public RPC[/yellow]")
    except Exception as e:
        console.print(f"[yellow]Failed to read {args.api_file}: {e}[/yellow]")
    
    return "https://api.mainnet-beta.solana.com"

def load_wallet(args):
    if args.address:
        return args.address.strip()
    try:
        with open(args.wallet_file, 'r', encoding='utf-8') as f:
            for line in f:
                w = line.strip()
                if w:
                    if w.startswith("0x"):
                        console.print(f"[red]SOL address cannot start with 0x, enter a valid Solana base58 address in {args.wallet_file}[/red]")
                        exit()
                    return w
            console.print(f"[red]File {args.wallet_file} is empty![/red]")
            exit()
    except FileNotFoundError:
        console.print(f"[red]File {args.wallet_file} not found![/red]")
        exit()

def rpc_call(method, params, rpc_url):
    payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    try:
        res = requests.post(rpc_url, json=payload, timeout=15).json()
        return res.get("result")
    except Exception as e:
        console.print(f"[red]RPC Error {method}: {e}[/red]")
        return None

def get_signatures(address, rpc_url, limit=100):
    all_sigs = []
    before = None
    while len(all_sigs) < 500:
        params = [address, {"limit": limit, "before": before}] if before else [address, {"limit": limit}]
        result = rpc_call("getSignaturesForAddress", params, rpc_url)
        if not result:
            break
        all_sigs.extend(result)
        if len(result) < limit:
            break
        before = result[-1]["signature"]
        time.sleep(0.2)
    return all_sigs

def scan_wallet(address, rpc_url):
    console.print(f"\n[bold cyan]>> Scanning {address} on SOLANA network...[/bold cyan]")
    console.print(f"[dim]RPC: {rpc_url[:45]}...[/dim]")
    sigs = get_signatures(address, rpc_url)
    if not sigs:
        return []
    receives = []
    for sig_info in sigs:
        sig = sig_info["signature"]
        tx = rpc_call("getTransaction", [sig, {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}], rpc_url)
        if not tx or tx.get("meta", {}).get("err") is not None:
            continue
        block_time = tx.get("blockTime")
        if not block_time:
            continue
        t_str = datetime.fromtimestamp(block_time).strftime('%Y-%m-%d %H:%M:%S')
        meta = tx.get("meta", {})
        try:
            keys = [k["pubkey"] if isinstance(k, dict) else k for k in tx["transaction"]["message"]["accountKeys"]]
            if address in keys:
                idx = keys.index(address)
                pre = meta["preBalances"][idx]
                post = meta["postBalances"][idx]
                diff = post - pre
                if diff > 0:
                    amount = diff / 10**9
                    if amount > 0.0000005:
                        receives.append({
                            "timestamp": block_time,
                            "time": t_str,
                            "type": "NATIVE",
                            "symbol": "SOL",
                            "amount": amount,
                            "from": tx["transaction"]["message"]["accountKeys"][0]["pubkey"] if isinstance(tx["transaction"]["message"]["accountKeys"][0], dict) else str(tx["transaction"]["message"]["accountKeys"][0]),
                            "hash": sig,
                            "status": "✅ Native Coin",
                            "contract": ""
                        })
        except:
            pass
        try:
            pre_tokens = meta.get("preTokenBalances", [])
            post_tokens = meta.get("postTokenBalances", [])
            pre_map = {}
            for b in pre_tokens:
                if b.get("owner") == address:
                    pre_map[b["mint"]] = int(b["uiTokenAmount"]["amount"])
            for b in post_tokens:
                if b.get("owner") == address:
                    mint = b["mint"]
                    post_amt = int(b["uiTokenAmount"]["amount"])
                    pre_amt = pre_map.get(mint, 0)
                    diff = post_amt - pre_amt
                    if diff > 0:
                        decimals = b["uiTokenAmount"]["decimals"]
                        amount = diff / (10 ** decimals)
                        symbol = b["uiTokenAmount"].get("symbol") or mint[:4]
                        if symbol.upper() in STABLE_SYMBOLS:
                            status = "💵 Stable Coin"
                        elif len(symbol) <= 10:
                            status = "✅ Official Token"
                        else:
                            status = "⚠️ Unverified/Spam"
                        receives.append({
                            "timestamp": block_time,
                            "time": t_str,
                            "type": "TOKEN",
                            "symbol": symbol,
                            "amount": amount,
                            "from": "SPL Transfer",
                            "hash": sig,
                            "status": status,
                            "contract": mint
                        })
        except:
            pass
        time.sleep(0.1)
    return sorted(receives, key=lambda x: x['timestamp'], reverse=True)

def main():
    parser = argparse.ArgumentParser(description="Solana Wallet Receiver Scanner")
    parser.add_argument("address", nargs="?", default=None, help="Solana address (optional if using WALLET file)")
    parser.add_argument("--wallet-file", default="components/WALLET_solana.txt", help="Wallet file, default: components/WALLET_solana.txt")
    parser.add_argument("--api-file", default="components/API_solana.txt", help="Solana RPC file, default: components/API_solana.txt")
    parser.add_argument("--hide-spam", action="store_true", help="Hide spam tokens")
    parser.add_argument("--export", help="Export to CSV")
    args = parser.parse_args()
    
    wallet = load_wallet(args)
    rpc_url = load_rpc_url(args)
    data = scan_wallet(wallet, rpc_url)

    if args.hide_spam:
        data = [d for d in data if "Spam" not in d["status"]]
    if not data:
        console.print("[yellow]No RECEIVE transactions found on Solana.[/yellow]")
        return
    table = Table(title=f"SOLANA RECEIVE Scan Results - Total: {len(data)}")
    table.add_column("Time", style="dim")
    table.add_column("Type", style="magenta")
    table.add_column("Token", style="bold green")
    table.add_column("Amount", justify="right", style="cyan")
    table.add_column("Status", style="yellow")
    table.add_column("Tx Hash", style="dim")
    for r in data:
        table.add_row(r["time"], r["type"], r["symbol"], f"{r['amount']:,.6f}", r["status"], r["hash"][:16]+"...")
    console.print(table)
    if args.export:
        for r in data: r.pop("timestamp", None)
        fieldnames = ["time", "type", "symbol", "amount", "from", "hash", "status", "contract"]
        with open(args.export, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        console.print(f"[green]Successfully exported to {args.export}[/green]")

if __name__ == "__main__":
    main()