import psutil
import time
import os
from rich.console import Console
from rich.table import Table
from rich.align import Align
from rich.text import Text
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from utils.logging import log_event

console = Console(color_system="auto", highlight=False)

monitored_processes = []

def select_running_process():
    """Select a running process to monitor."""
    global monitored_processes

    processes = []
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            processes.append(proc.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    if not processes:
        console.print("[bold yellow]No running processes found.[/bold yellow]")
        return

    table = Table(title="Running Processes", show_header=True, header_style="bold green")
    table.add_column("PID", style="dim")
    table.add_column("Name", style="bold")

    for proc in processes:
        table.add_row(str(proc['pid']), proc['name'])

    console.print(Align.center(table))
    console.print()
    pid = Prompt.ask("[bold]Enter the PID of the process to monitor[/bold]", default="")

    if pid.isdigit():
        pid = int(pid)
        for proc in processes:
            if proc['pid'] == pid:
                monitored_processes.append(proc)
                console.print(f"[bold green]Added process {proc['name']} (PID: {pid}) to monitoring list.[/bold green]")
                return
    console.print("[bold red]Invalid PID or process not found.[/bold red]")

def view_monitored_processes():
    """View the list of monitored processes."""
    if not monitored_processes:
        console.print("[bold yellow]No processes are being monitored.[/bold yellow]")
        return

    table = Table(title="Monitored Processes", show_header=True, header_style="bold green")
    table.add_column("PID", style="dim")
    table.add_column("Name", style="bold")

    for proc in monitored_processes:
        table.add_row(str(proc['pid']), proc['name'])

    console.print(Align.center(table))

def clear_monitored_processes():
    """Clear the list of monitored processes."""
    global monitored_processes
    monitored_processes = []
    console.print("[bold green]Cleared all monitored processes.[/bold green]")

def start_process_monitoring(action="shutdown"):
    """Start monitoring processes and perform an action when they complete."""
    global monitored_processes

    if not monitored_processes:
        console.print("[bold yellow]No processes selected for monitoring.[/bold yellow]")
        return

    console.print("[bold green]Monitoring processes...[/bold green]")
    while monitored_processes:
        for proc in monitored_processes[:]:
            try:
                psutil.Process(proc['pid'])
            except psutil.NoSuchProcess:
                monitored_processes.remove(proc)
                console.print(f"[bold green]Process {proc['name']} has completed.[/bold green]")

        if not monitored_processes:
            console.print(f"[bold green]All processes have completed. Performing {action} action.[/bold green]")
            if action == "shutdown":
                os.system("shutdown /s /t 0")
            elif action == "restart":
                os.system("shutdown /r /t 0")
            return

        time.sleep(1)
