import subprocess
import sys
import os
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

console = Console()

MENU = {
    "1": {"name": "EVM Network", "file": "scan/evm.py"},
    "2": {"name": "Solana Network", "file": "scan/solana.py"},
    "3": {"name": "Tron Network", "file": "scan/tron.py"},
    "4": {"name": "Stellar Network", "file": "scan/stellar.py"},
}

def run_file(filename):
    if not os.path.exists(filename):
        console.print(f"[red]File {filename} does not exist / has not been created![/red]")
        return
    
    try:
        subprocess.run([sys.executable, filename])
    except KeyboardInterrupt:
        console.print("\n[yellow]Canceled by user[/yellow]")
    except Exception as e:
        console.print(f"[red]Failed to run {filename}: {e}[/red]")

def main():
    while True:
        console.clear()
        console.print(Panel.fit("[bold cyan]🔍 WALLET SCANNER - SELECT NETWORK[/bold cyan]", border_style="cyan"))
        console.print("[bold white]1.[/bold white] EVM Network [dim](eth, bsc, base, arb, etc. - uses evm.py)[/dim]")
        console.print("[bold white]2.[/bold white] Solana Network")
        console.print("[bold white]3.[/bold white] Tron Network")
        console.print("[bold white]4.[/bold white] Stellar Network [dim](L1)[/dim]")
        console.print("[bold white]0.[/bold white] Exit\n")

        choice = Prompt.ask("[bold yellow]Select option[/bold yellow]", choices=["1","2","3","4","0"], default="1")

        if choice == "0":
            console.print("[green]Bye![/green]")
            break
        
        target = MENU[choice]
        console.print(f"\n[bold green]>> Running {target['name']} ({target['file']})...[/bold green]\n")
        
        if choice == "1" and os.path.exists("scan/evm.py"):
            console.print("[dim]EVM Chains: eth, bsc, pol, arb, op, base, avax, etc.[/dim]")
            chain = Prompt.ask("Enter chain", default="bsc")
            hide = Prompt.ask("Hide spam? (y/n)", choices=["y","n"], default="n")
            cmd = [sys.executable, "scan/evm.py", "--chain", chain]
            if hide == "y":
                cmd.append("--hide-spam")
            try:
                subprocess.run(cmd)
            except KeyboardInterrupt:
                pass
            Prompt.ask("\n[dim]Press ENTER to return to menu[/dim]")
        else:
            run_file(target["file"])
            Prompt.ask("\n[dim]Press ENTER to return to menu[/dim]")

if __name__ == "__main__":
    main()# review
