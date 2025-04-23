import sys
import time
import platform  # Needed for OS checks in menus

# Rich imports
from rich.text import Text
from rich.align import Align
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.prompt import Prompt  # Ensure Prompt is imported

# Import helpers
from utils.helpers import (
    clear_screen, print_banner, get_key, console,
    MAIN_STYLE, HIGHLIGHT_STYLE, HACKER_GREEN, BORDER_STYLE
)

# Import feature functions from their respective modules
from utils import shutdown_timer
from utils import network_tools
from utils import process_monitor
from utils import update_checker
from utils import logging as logging_utils  # Use alias to avoid name clash
from utils import calendar_scheduling
from utils import ip_lookup  # Import the new module
from utils import download_calculator

def arrow_menu(title, options):
    """Display a menu with arrow key and WASD navigation"""
    current_option = 0
    while True:
        clear_screen()
        print_banner()
        panel_title = Text(title, style=f"bold {HACKER_GREEN}")
        console.print(Align.center(panel_title))
        console.print()

        # Create menu items as Text objects for consistent alignment
        menu_items = []
        for i, option in enumerate(options):
            if i == current_option:
                item = Text(f" ➤ {option} ", style=HIGHLIGHT_STYLE)  # Add spaces for padding
            else:
                item = Text(f"   {option} ", style=MAIN_STYLE)  # Add spaces for alignment
            menu_items.append(Align.center(item))

        # Print all items at once (might reduce flicker slightly)
        for item in menu_items:
            console.print(item)
        console.print()  # Spacer

        key = None
        while key is None:  # Wait for a valid key press
            key = get_key()
            time.sleep(0.05)  # Small sleep to prevent high CPU usage

        if key == 'UP' and current_option > 0:
            current_option -= 1
        elif key == 'DOWN' and current_option < len(options) - 1:
            current_option += 1
        elif key == 'ENTER' or key == 'RIGHT':  # Allow Right arrow for selection
            return current_option
        elif key == 'ESC' or key == 'LEFT':  # Allow Left arrow for back
            return -1  # Indicate back/cancel

# --- Menu Functions ---

def shutdown_settings_menu():
    """Display the shutdown settings submenu."""
    while True:
        options = [
            "Set Shutdown Timer",
            "Set Restart Timer",
            "Set Boot to BIOS Timer",
            "Cancel Active Timer",
            "View Timer Status",  # Added View here
            "Advanced Shutdown Options",
            "Back to Features Menu"
        ]
        # Add OS-specific info
        if platform.system() != 'Windows':
            options[2] += " (Windows Only)"

        choice = arrow_menu("Shutdown Settings", options)

        if choice == 0:
            shutdown_timer.set_timer_rich("shutdown")
        elif choice == 1:
            shutdown_timer.set_timer_rich("restart")
        elif choice == 2:
            if platform.system() == 'Windows':
                shutdown_timer.set_timer_rich("bios")
            else:
                clear_screen()
                print_banner()
                console.print(Align.center(Text("Restart to BIOS is only supported on Windows.", style="yellow")))
                time.sleep(2)
        elif choice == 3:
            shutdown_timer.cancel_shutdown()
        elif choice == 4:
            shutdown_timer.show_timer_status_rich()  # Call status view
        elif choice == 5:
            advanced_shutdown_menu()
        elif choice == 6 or choice == -1:
            return

def advanced_shutdown_menu():
    """Advanced shutdown options menu"""
    while True:
        options = [
            "Process Completion Action",  # Renamed for clarity
            "Schedule Action (Calendar)",
            "Restart to BIOS/Firmware",  # Moved here as advanced action
            "Back to Shutdown Settings"
        ]
        choice = arrow_menu("Advanced Shutdown Options", options)

        if choice == 0:
            process_completion_menu()  # Go to sub-menu
        elif choice == 1:
            calendar_scheduling.calendar_scheduling()  # Call actual scheduling function
        elif choice == 2:
            shutdown_timer.restart_to_bios()  # Call BIOS restart function
        elif choice == 3 or choice == -1:
            return

def process_completion_menu():
    """Menu for setting up actions based on process completion."""
    while True:
        options = [
            "Select Process from List",
            "Enter Process Name Manually",
            "View Monitored Processes",
            "Clear Monitored Processes",
            "Start Monitoring & Set Action",  # Combined start/config
            "Back to Advanced Settings"
        ]
        choice = arrow_menu("Process Completion Action", options)

        if choice == 0:
            process_monitor.select_running_process(arrow_menu)
        elif choice == 1:
            process_monitor.enter_process_manually()
        elif choice == 2:
            process_monitor.view_selected_processes()
        elif choice == 3:
            process_monitor.clear_selected_processes()
        elif choice == 4:
            process_monitor.start_process_monitoring(arrow_menu)
        elif choice == 5 or choice == -1:
            return

def features_menu(current_version):  # Accept current_version
    """Display the main features menu."""
    while True:
        options = [
            "Shutdown / Restart / Timer",  # Combined related items
            "Network Tools",
            "Process Utilities",  # Added Process menu
            "Download Time Calculator",  # Added option
            "View Logs",
            "Check for Updates",
            "Back to Main Menu"
        ]
        choice = arrow_menu("Main Features", options)

        if choice == 0:
            shutdown_settings_menu()
        elif choice == 1:
            network_tools_menu()
        elif choice == 2:
            process_utilities_menu()  # Call new process menu
        elif choice == 3:  # Download Time Calculator
            download_calculator.display_download_time_calculator()
        elif choice == 4:
            logging_utils.view_logs()  # Use the imported view_logs
        elif choice == 5:
            # --- Update Check Display ---
            clear_screen()
            print_banner()
            title = Text("Update Check", style=f"bold {HACKER_GREEN}")
            console.print(Align.center(title))
            console.print()
            update_info = None
            with Progress(SpinnerColumn(), TextColumn("Checking for updates..."), transient=True, console=console) as progress:
                progress.add_task("", total=None)
                update_info = update_checker.check_for_updates(current_version)

            if update_info.get('error'):
                console.print(Align.center(Text(f"Error checking for updates: {update_info['error']}", style="bold red")))
            elif update_info.get('update_available'):
                console.print(Align.center(Text("Update Available!", style="bold green")))
                console.print(Align.center(Text(f"Current Version: {update_info['current_version']}", style="yellow")))
                console.print(Align.center(Text(f"Latest Version: {update_info['latest_version']}", style="yellow")))
                if update_info.get('release_notes'):
                    console.print(Align.center(Text("Release Notes:", style="dim")))
                    console.print(Align.center(Panel(Text(update_info['release_notes'], style="dim"), border_style="dim", width=60)))
                if update_info.get('download_url'):
                    console.print(Align.center(Text(f"Download: {update_info['download_url']}", style="bold blue")))
                elif update_info.get('release_page_url'):
                    console.print(Align.center(Text(f"Visit Release Page: {update_info['release_page_url']}", style="bold blue")))
                else:
                    console.print(Align.center(Text("No download URL available for .exe asset.", style="bold red")))
            else:
                console.print(Align.center(Text("You are using the latest version.", style=f"bold {HACKER_GREEN}")))

            console.print()
            instruction = Text("Press any key to return...", style=MAIN_STYLE)
            console.print(Align.center(instruction))
            while get_key() is None:
                time.sleep(0.1)
            clear_screen()
            # --- End Update Check Display ---

        elif choice == 6 or choice == -1:
            return

def network_tools_menu():
    """Display the network tools submenu."""
    while True:
        options = [
            "Show My IP Addresses",
            "IP/Domain Info Lookup (ip-api.com)",  # Clarify source
            "Detailed IP Lookup (ipquery.io)",    # Added option
            "Scan Open Ports",
            "Ping Host",
            "Traceroute Host (with WHOIS)",       # Clarify feature
            "Back to Features Menu"
        ]
        choice = arrow_menu("Network Tools", options)

        if choice == 0:
            network_tools.show_my_ip()
        elif choice == 1:
            network_tools.lookup_ip_info()
        elif choice == 2:  # Detailed IP Lookup
            ip_lookup.display_detailed_ip_info()  # Call the new function
        elif choice == 3:  # Scan Ports
            clear_screen()
            print_banner()
            target = Prompt.ask("[bold]Enter target IP or Hostname for Scan[/bold]")
            if target:
                start_port_str = Prompt.ask("[bold]Start Port[/bold]", default="1")
                end_port_str = Prompt.ask("[bold]End Port[/bold]", default="1024")
                try:
                    start_port = int(start_port_str)
                    end_port = int(end_port_str)
                    if 1 <= start_port <= end_port <= 65535:
                        network_tools.scan_open_ports(target, start_port, end_port)
                    else:
                        console.print("[red]Invalid port range (1-65535).[/red]")
                        time.sleep(1.5)
                except ValueError:
                    console.print("[red]Invalid port number entered.[/red]")
                    time.sleep(1.5)
        elif choice == 4:  # Ping Host
            clear_screen()
            print_banner()
            target = Prompt.ask("[bold]Enter target IP or Hostname to Ping[/bold]")
            if target:
                network_tools.run_ping(target)
        elif choice == 5:  # Traceroute Host
            clear_screen()
            print_banner()
            target = Prompt.ask("[bold]Enter target IP or Hostname for Traceroute[/bold]")
            if target:
                network_tools.run_traceroute(target)
        elif choice == 6 or choice == -1:  # Back
            return

def process_utilities_menu():
    """Display the process utilities submenu."""
    while True:
        options = [
            "List Running Processes",
            "Terminate Process",  # Added option
            "Back to Features Menu"
        ]
        choice = arrow_menu("Process Utilities", options)

        if choice == 0:
            process_monitor.display_running_processes()
        elif choice == 1:
            # Pass arrow_menu for the selection list within terminate function
            process_monitor.select_process_to_terminate(arrow_menu)
        elif choice == 2 or choice == -1:
            return

def main_menu(current_version):  # Accept current_version
    """Display the main menu."""
    while True:
        options = ["Main Features", "Exit"]
        choice = arrow_menu("Main Menu", options)

        if choice == 0:
            features_menu(current_version)  # Pass version down
        elif choice == 1 or choice == -1:  # Exit or ESC
            clear_screen()
            console.print(Align.center(Text("\nGoodbye!", style=f"bold {HACKER_GREEN}")))
            time.sleep(1)
            sys.exit(0)  # Clean exit

__all__ = ['main_menu']  # Export only the main entry menu
