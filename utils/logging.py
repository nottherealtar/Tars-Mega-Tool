import os
from datetime import datetime

# Rich imports
from rich.console import Console
from rich.table import Table
from rich.align import Align
from rich.text import Text
from rich.box import DOUBLE

# Local imports from helpers
from utils.helpers import (
    clear_screen, print_banner, get_key, console, save_output_to_file, # Import save helper
    MAIN_STYLE, HIGHLIGHT_STYLE, HACKER_GREEN, BORDER_STYLE
)

LOG_FILE = os.path.join(os.path.expanduser("~"), "TarsUtilitiesTool", "logs.txt")

# Ensure the log directory exists
log_dir = os.path.dirname(LOG_FILE)
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

def log_event(action, duration_seconds=None):
    """Log shutdown or other events to a file"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"{timestamp} | {action}"
    if duration_seconds is not None:
        log_entry += f" | Duration: {duration_seconds} seconds"
    log_entry += "\n"
    with open(LOG_FILE, "a") as f:
        f.write(log_entry)

def read_logs():
    """Read and return the shutdown logs"""
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            return f.readlines()
    return []

def view_logs():
    """View shutdown logs in rich UI"""
    logs = read_logs()

    clear_screen()
    print_banner()

    title = Text("Activity Logs", style=f"bold {HACKER_GREEN}")
    console.print(Align.center(title))
    console.print()

    log_data_for_save = [] # Initialize outside the conditional
    if not logs:
        console.print(Align.center(Text("No logs found", style="yellow")))
    else:
        table = Table(box=DOUBLE, border_style=BORDER_STYLE, title=f"[{HACKER_GREEN}]Log Entries[/{HACKER_GREEN}]")
        table.add_column("Timestamp", style=MAIN_STYLE, no_wrap=True)
        table.add_column("Action", style=MAIN_STYLE)
        table.add_column("Details", style=MAIN_STYLE)

        # Display logs in reverse chronological order (newest first)
        for log in reversed(logs):
            parts = log.strip().split(" | ")
            timestamp = parts[0] if len(parts) > 0 else "N/A"
            action = parts[1] if len(parts) > 1 else "N/A"
            details = parts[2] if len(parts) > 2 else ""
            table.add_row(timestamp, action, details)
            log_data_for_save.append((timestamp, action, details)) # Add tuple for saving

        console.print(Align.center(table))

    console.print()

    # --- Wait for dismissal or Save action ---
    instruction = Text("Press 's' to save logs, ESC or any other key to return...", style=MAIN_STYLE)
    console.print(Align.center(instruction))

    while True: # Loop until a valid action is taken
        key = get_key()
        if key is not None:
            if key.lower() == 's':
                if logs: # Only offer save if there are logs
                    def generate_save_content():
                        lines = [f"Activity Logs ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})"]
                        lines.append("-" * 60)
                        lines.append("Timestamp\t\tAction\t\tDetails")
                        # Use the saved data which is already reversed
                        for timestamp, action, details in log_data_for_save:
                            lines.append(f"{timestamp}\t{action}\t{details}")
                        return "\n".join(lines)
                    save_output_to_file(generate_save_content, "activity_logs")
                    # After saving, wait for another key press to return
                    console.print(Align.center(Text("Press any key to return...", style=MAIN_STYLE)))
                    while get_key() is None: time.sleep(0.1)
                    break # Exit outer loop after saving and second key press
                else:
                    # If 's' is pressed but no logs, just wait for another key
                    console.print(Align.center(Text("No logs to save. Press any key to return...", style="yellow")))
                    while get_key() is None: time.sleep(0.1)
                    break # Exit outer loop
            else: # Any other key (including ESC) means go back
                break # Exit outer loop immediately

        time.sleep(0.05) # Prevent high CPU usage while waiting

# Add this line to make view_logs directly callable
__all__ = ['log_event', 'view_logs', 'read_logs', 'LOG_FILE']
