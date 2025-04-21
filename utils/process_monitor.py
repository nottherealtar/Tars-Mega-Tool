import psutil
import time
import os
import sys
from datetime import datetime

# Rich imports
from rich.console import Console
from rich.table import Table
from rich.align import Align
from rich.text import Text
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.live import Live
from rich.box import DOUBLE

# Local imports
from utils.logging import log_event
from utils.helpers import (
    clear_screen, print_banner, get_key, format_seconds, console, save_output_to_file,
    MAIN_STYLE, HIGHLIGHT_STYLE, HACKER_GREEN, BORDER_STYLE
)

# --- Global Variables for Process Monitoring ---
monitored_processes = []  # List of dicts: {'pid': int|None, 'name': str, 'monitor_type': str, 'start_time': float, 'last_active': float}
# --- End Global Variables ---


def select_running_process(arrow_menu_func):
    """Select a running process to monitor from a list using the provided arrow_menu."""
    global monitored_processes

    clear_screen()
    print_banner()
    title = Text("Select Running Process", style=f"bold {HACKER_GREEN}")
    console.print(Align.center(title))
    console.print()

    running_processes_info = []
    try:
        with Progress(SpinnerColumn(), TextColumn("Loading processes..."), transient=True, console=console) as progress:
            progress.add_task("", total=None)
            attrs = ['pid', 'name', 'status']
            for proc in psutil.process_iter(attrs=attrs, ad_value=None):
                pinfo = proc.info
                if pinfo['pid'] is not None and pinfo['pid'] > 4 and \
                        pinfo['name'] and pinfo['name'].lower() not in ['system idle process', 'system'] and \
                        pinfo['status'] != psutil.STATUS_ZOMBIE:
                    running_processes_info.append(pinfo)
    except Exception as e:
        console.print(Align.center(Text(f"Error loading processes: {e}", style="bold red")))
        time.sleep(2)
        clear_screen()
        return

    if not running_processes_info:
        console.print(Align.center(Text("No suitable running processes found to select.", style="yellow")))
        time.sleep(2)
        clear_screen()
        return

    running_processes_info.sort(key=lambda p: p['name'].lower())
    process_options = [f"{p['name']} (PID: {p['pid']})" for p in running_processes_info]
    process_options.append("Back")

    selected_index = arrow_menu_func("Select Process to Monitor", process_options)

    if selected_index == -1 or selected_index == len(running_processes_info):
        clear_screen()
        return

    selected_process = running_processes_info[selected_index]

    if any(p['pid'] == selected_process['pid'] for p in monitored_processes):
        console.print(Align.center(Text(f"Process {selected_process['name']} (PID: {selected_process['pid']}) is already being monitored.", style="yellow")))
    else:
        monitored_processes.append({
            'pid': selected_process['pid'],
            'name': selected_process['name'],
            'monitor_type': None,
            'start_time': None,
            'last_active': time.time()
        })
        console.print(Align.center(Text(f"Added {selected_process['name']} (PID: {selected_process['pid']}) to monitoring list.", style=f"bold {HACKER_GREEN}")))
        log_event(f"Added process {selected_process['name']} (PID: {selected_process['pid']}) for monitoring")

    time.sleep(1.5)
    clear_screen()


def enter_process_manually():
    """Enter a process name manually to monitor."""
    global monitored_processes

    clear_screen()
    print_banner()
    title = Text("Enter Process Name", style=f"bold {HACKER_GREEN}")
    console.print(Align.center(title))
    console.print()

    instruction = Text("Enter the process name (e.g., chrome.exe) or type 'back':", style=MAIN_STYLE)
    console.print(Align.center(instruction))
    console.print()

    process_name = Prompt.ask("[bold]Process Name[/bold]")

    if not process_name or process_name.lower() == 'back':
        clear_screen()
        return
    if process_name.lower() == 'exit':
        clear_screen()
        console.print(Align.center(Text("\nGoodbye!", style=f"bold {HACKER_GREEN}")))
        sys.exit()

    if any(p.get('name', '').lower() == process_name.lower() for p in monitored_processes):
        console.print(Align.center(Text(f"Process name '{process_name}' is already in the monitoring list.", style="yellow")))
    else:
        monitored_processes.append({
            'pid': None,
            'name': process_name,
            'monitor_type': None,
            'start_time': None,
            'last_active': time.time()
        })
        console.print(Align.center(Text(f"Added '{process_name}' to monitoring list. Will monitor any process with this name.", style=f"bold {HACKER_GREEN}")))
        log_event(f"Added process name '{process_name}' for monitoring")

    time.sleep(1.5)
    clear_screen()


def view_selected_processes():
    """View the list of processes selected for monitoring."""
    clear_screen()
    print_banner()
    title = Text("Selected Processes for Monitoring", style=f"bold {HACKER_GREEN}")
    console.print(Align.center(title))
    console.print()

    if not monitored_processes:
        console.print(Align.center(Text("No processes selected for monitoring.", style="yellow")))
    else:
        table = Table(box=DOUBLE, border_style=BORDER_STYLE, title=f"[{HACKER_GREEN}]Monitored Processes[/{HACKER_GREEN}]")
        table.add_column("Process Name", style=MAIN_STYLE)
        table.add_column("PID", style=MAIN_STYLE)
        for process in monitored_processes:
            pid_str = str(process['pid']) if process['pid'] is not None else "[dim]By Name[/dim]"
            table.add_row(process['name'], pid_str)
        console.print(Align.center(table))

    console.print()
    instruction = Text("Press any key to return...", style=MAIN_STYLE)
    console.print(Align.center(instruction))
    while get_key() is None:
        time.sleep(0.1)
    clear_screen()


def clear_selected_processes():
    """Clear the list of selected processes."""
    global monitored_processes

    clear_screen()
    print_banner()
    title = Text("Clear Selected Processes", style=f"bold {HACKER_GREEN}")
    console.print(Align.center(title))
    console.print()

    if not monitored_processes:
        console.print(Align.center(Text("No processes are currently selected.", style="yellow")))
    else:
        confirm = Confirm.ask(f"Clear all {len(monitored_processes)} selected processes?", default=False)
        if confirm:
            monitored_processes = []
            console.print(Align.center(Text("All selected processes have been cleared.", style=f"bold {HACKER_GREEN}")))
            log_event("Cleared all monitored processes")
        else:
            console.print(Align.center(Text("Operation cancelled.", style="yellow")))

    time.sleep(1.5)
    clear_screen()


def list_running_processes():
    """List all running processes."""
    processes = []
    try:
        attrs = ['pid', 'name', 'status']
        for proc in psutil.process_iter(attrs=attrs, ad_value=None):
            if proc.info['status'] != psutil.STATUS_ZOMBIE and proc.info['name']:
                processes.append(proc.info)
    except Exception as e:
        console.print(f"[bold red]Error listing processes: {str(e)}[/bold red]")
    return processes


def display_running_processes():
    """Display running processes in a table."""
    clear_screen()
    print_banner()
    title = Text("Running Processes", style=f"bold {HACKER_GREEN}")
    console.print(Align.center(title))
    console.print()

    processes = list_running_processes()
    if not processes:
        console.print(Align.center(Text("[bold yellow]No running processes found or accessible.[/bold yellow]")))
    else:
        table = Table(title="Running Processes", show_header=True, header_style=f"bold {HACKER_GREEN}", box=DOUBLE, border_style=BORDER_STYLE)
        table.add_column("PID", style="dim", justify="right")
        table.add_column("Name", style=MAIN_STYLE)

        processes.sort(key=lambda p: p['name'].lower())

        for proc in processes:
            pid_str = str(proc.get('pid', 'N/A'))
            name_str = proc.get('name', 'Unknown')
            table.add_row(pid_str, name_str)

        console.print(Align.center(table))

    console.print()

    if processes:
        def generate_save_content():
            lines = [f"Running Processes ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})"]
            lines.append("-" * 30)
            lines.append("PID\tName")
            for proc in processes:
                pid_str = str(proc.get('pid', 'N/A'))
                name_str = proc.get('name', 'Unknown')
                lines.append(f"{pid_str}\t{name_str}")
            return "\n".join(lines)
        save_output_to_file(generate_save_content, "running_processes")

    instruction = Text("Press any key to return...", style=MAIN_STYLE)
    console.print(Align.center(instruction))
    while get_key() is None:
        time.sleep(0.1)
    clear_screen()


def terminate_process(pid):
    """Attempts to terminate a process by its PID."""
    try:
        p = psutil.Process(pid)
        process_name = p.name()  # Get name before terminating

        # Attempt graceful termination first
        console.print(f"Attempting to terminate process '{process_name}' (PID: {pid})...", style=MAIN_STYLE)
        p.terminate()

        # Wait a moment to see if it terminated
        try:
            gone, alive = psutil.wait_procs([p], timeout=3)
            if p in gone:
                console.print(f"[bold green]Process '{process_name}' (PID: {pid}) terminated successfully.[/bold green]")
                log_event(f"Terminated process '{process_name}' (PID: {pid})")
                return True
            else:
                # If still alive, offer forceful kill
                console.print(f"[yellow]Process '{process_name}' did not terminate gracefully.[/yellow]")
                if Confirm.ask(f"Force kill process '{process_name}' (PID: {pid})? (May cause data loss)", default=False):
                    p.kill()
                    # Check again
                    gone, alive = psutil.wait_procs([p], timeout=1)
                    if p in gone:
                        console.print(f"[bold green]Process '{process_name}' (PID: {pid}) forcefully killed.[/bold green]")
                        log_event(f"Force killed process '{process_name}' (PID: {pid})")
                        return True
                    else:
                        console.print(f"[bold red]Failed to force kill process '{process_name}' (PID: {pid}).[/bold red]")
                        log_event(f"Failed to force kill process '{process_name}' (PID: {pid})")
                        return False
                else:
                    console.print(f"Force kill cancelled for '{process_name}'.", style="yellow")
                    log_event(f"Force kill cancelled for process '{process_name}' (PID: {pid})")
                    return False
        except psutil.TimeoutExpired:
            console.print(f"[bold red]Timeout waiting for process '{process_name}' (PID: {pid}) to terminate.[/bold red]")
            log_event(f"Timeout waiting for process '{process_name}' (PID: {pid}) termination check")
            return False

    except psutil.NoSuchProcess:
        console.print(f"[bold red]Error: Process with PID {pid} not found.[/bold red]")
        log_event(f"Attempted to terminate non-existent PID {pid}")
        return False
    except psutil.AccessDenied:
        console.print(f"[bold red]Error: Access denied. Cannot terminate process {pid}. Try running as administrator.[/bold red]")
        log_event(f"Access denied trying to terminate PID {pid}")
        return False
    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred while terminating PID {pid}: {e}[/bold red]")
        log_event(f"Unexpected error terminating PID {pid}: {e}")
        return False


def select_process_to_terminate(arrow_menu_func):
    """Displays running processes and prompts user to select one to terminate."""
    clear_screen()
    print_banner()
    title = Text("Terminate Process", style=f"bold {HACKER_GREEN}")
    console.print(Align.center(title))
    console.print()

    running_processes_info = []
    try:
        with Progress(SpinnerColumn(), TextColumn("Loading processes..."), transient=True, console=console) as progress:
            progress.add_task("", total=None)
            attrs = ['pid', 'name', 'status', 'username']  # Add username for context
            for proc in psutil.process_iter(attrs=attrs, ad_value='N/A'):  # Use ad_value for missing attrs
                pinfo = proc.info
                # Filter out low PIDs, system processes, idle, and potentially self
                if pinfo['pid'] is not None and pinfo['pid'] > 4 and \
                        pinfo['name'] and pinfo['name'].lower() not in ['system idle process', 'system'] and \
                        pinfo['status'] != psutil.STATUS_ZOMBIE and \
                        pinfo['pid'] != os.getpid():  # Don't list self
                    running_processes_info.append(pinfo)
    except Exception as e:
        console.print(Align.center(Text(f"Error loading processes: {e}", style="bold red")))
        time.sleep(2)
        return  # Go back to menu

    if not running_processes_info:
        console.print(Align.center(Text("No suitable running processes found to terminate.", style="yellow")))
        time.sleep(2)
        return  # Go back to menu

    # Sort by name
    running_processes_info.sort(key=lambda p: p['name'].lower())

    # Create options for arrow_menu
    process_options = [f"{p['name']} (PID: {p['pid']}, User: {p['username']})" for p in running_processes_info]
    process_options.append("Back")

    # Use the passed arrow_menu function for selection
    selected_index = arrow_menu_func("Select Process to Terminate", process_options)

    if selected_index == -1 or selected_index == len(running_processes_info):  # Back selected or ESC
        return  # Go back to menu

    selected_process = running_processes_info[selected_index]
    pid_to_terminate = selected_process['pid']
    process_name = selected_process['name']

    console.print()  # Spacer
    # Confirmation
    if Confirm.ask(f"Are you sure you want to attempt terminating '{process_name}' (PID: {pid_to_terminate})?", default=False):
        terminate_process(pid_to_terminate)
    else:
        console.print("Termination cancelled.", style="yellow")
        log_event(f"Termination cancelled by user for process '{process_name}' (PID: {pid_to_terminate})")

    # Wait for user to see the result before returning to menu
    console.print()
    instruction = Text("Press any key to return...", style=MAIN_STYLE)
    console.print(Align.center(instruction))
    while get_key() is None:
        time.sleep(0.1)
    # No clear_screen here, let arrow_menu handle it
