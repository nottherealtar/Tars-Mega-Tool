import os
import time
import threading
import platform
import re
import sys
from datetime import datetime, timedelta

# Rich imports
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt
from rich.align import Align
from rich.box import DOUBLE

# Local imports
from utils.logging import log_event
from utils.helpers import (
    clear_screen, print_banner, get_key, format_time_display, format_seconds,
    console, MAIN_STYLE, HIGHLIGHT_STYLE, HACKER_GREEN, BORDER_STYLE
)

# --- Global Variables for Timer State ---
timer_active = False
end_time = None
timer_type = None # 'shutdown', 'restart', 'bios'
timer_thread = None
# --- End Global Variables ---

def countdown_timer():
    """Background thread to update the countdown timer status."""
    global timer_active, end_time
    while timer_active and end_time is not None:
        if time.time() >= end_time:
            timer_active = False
            # Optionally: Log automatic completion or trigger action here if needed
            break
        time.sleep(0.5) # Check every half second

def parse_timer_input(timer_input):
    """Parse a timer input string like '1h 30m 15s' or '600' into seconds."""
    try:
        # Check for simple integer input first (interpreted as seconds)
        if timer_input.isdigit():
            total_seconds = int(timer_input)
            if total_seconds <= 0:
                raise ValueError("Timer duration must be positive.")
            return total_seconds

        # If not a simple integer, try parsing the h/m/s format
        pattern = r"(?:(\d+)\s*h)?\s*(?:(\d+)\s*m)?\s*(?:(\d+)\s*s)?"
        match = re.match(pattern, timer_input.lower().strip())
        if not match or not match.group(0): # Ensure something was matched
            raise ValueError("Invalid timer format.")

        hours = int(match.group(1)) if match.group(1) else 0
        minutes = int(match.group(2)) if match.group(2) else 0
        seconds = int(match.group(3)) if match.group(3) else 0

        total_seconds = hours * 3600 + minutes * 60 + seconds
        if total_seconds <= 0:
            raise ValueError("Timer duration cannot be zero.")
        return total_seconds
    except ValueError as e:
        # Re-raise with a more specific message if needed, or just let the original message propagate
        raise ValueError(f"Invalid timer input: {e}")
    except Exception as e:
        # Catch other potential errors during parsing
        raise ValueError(f"Error parsing timer input: {str(e)}")


def set_timer_rich(action):
    """Set a timer using Rich UI, including input validation and 'back' option."""
    global timer_active, end_time, timer_type, timer_thread

    clear_screen()
    print_banner()
    title = Text(f"Setting {action.capitalize()} Timer", style=f"bold {HACKER_GREEN}")
    console.print(Align.center(title))
    console.print()

    while True: # Loop for input validation
        prompt_text = Text("Enter time (e.g., 30m, 2h, 1h 30m 15s, 90) or type 'back':", style=MAIN_STYLE)
        console.print(Align.center(prompt_text))
        console.print()
        time_input = Prompt.ask("[bold]Time[/bold]")

        if time_input.lower() == "back":
            clear_screen()
            return
        if time_input.lower() == "exit":
             clear_screen()
             console.print(Align.center(Text("\nGoodbye!", style=f"bold {HACKER_GREEN}")))
             sys.exit()

        try:
            total_seconds = parse_timer_input(time_input)
            break # Valid input, exit loop

        except ValueError as e:
            error_msg = Text(f"\n{str(e)}. Please use formats like 10s, 5m, 1h 30m, 90 or type 'back'.", style="bold red")
            console.print(Align.center(error_msg))
            time.sleep(2.5)
            # Clear the error and prompt again
            clear_screen()
            print_banner()
            console.print(Align.center(title))
            console.print()
            continue # Re-prompt the user

    # Cancel any existing timer *before* setting the new one
    if timer_active:
        # Call cancel_shutdown but suppress its messages for a smoother transition
        original_print = console.print
        console.print = lambda *args, **kwargs: None # Temporarily disable printing
        cancel_shutdown()
        console.print = original_print # Restore printing
        # Need to redraw the screen after cancellation
        clear_screen()
        print_banner()
        console.print(Align.center(title))
        console.print()


    console.print() # Add space before progress bar

    # Show progress bar while setting up timer
    with Progress(
        SpinnerColumn(spinner_name="dots2", style=HACKER_GREEN),
        TextColumn(f"[bold green]Setting {action} timer..."),
        BarColumn(bar_width=40, style=HACKER_GREEN, complete_style=HIGHLIGHT_STYLE),
        expand=True,
        console=console # Ensure progress uses the main console
    ) as progress:
        task = progress.add_task("", total=100)

        # Simulate progress
        for i in range(50):
            progress.update(task, completed=i)
            time.sleep(0.01)

        # Actually set the timer
        try:
            if action == "shutdown":
                os.system(f"shutdown -s -t {total_seconds}")
            elif action == "restart":
                os.system(f"shutdown -r -t {total_seconds}")
            elif action == "bios":
                 if platform.system() == 'Windows':
                     os.system(f"shutdown /r /fw /t {total_seconds}")
                 else:
                     # BIOS restart not standard on Linux/Mac via simple command
                     progress.stop() # Stop progress before printing error
                     console.print(Align.center(Text("\nRestart to BIOS is only supported on Windows.", style="yellow")))
                     time.sleep(2)
                     clear_screen()
                     return # Abort setting timer

            # Continue progress simulation
            for i in range(50, 101):
                progress.update(task, completed=i)
                time.sleep(0.01)

        except Exception as e:
             progress.stop() # Stop progress before printing error
             console.print(f"\n[bold red]Error executing shutdown command: {e}[/bold red]")
             time.sleep(2)
             clear_screen()
             return # Abort if command fails

    # Set timer tracking variables
    timer_active = True
    end_time = time.time() + total_seconds
    timer_type = action

    # Log the event
    log_event(f"Set {action} timer", total_seconds)

    # Start background timer thread
    if timer_thread is None or not timer_thread.is_alive():
        timer_thread = threading.Thread(target=countdown_timer, daemon=True)
        timer_thread.start()

    console.print() # Add space before success message

    # Center the success message
    time_str = format_time_display(total_seconds)
    success_msg = Text(f"Your PC will {action} in {time_str}.", style=f"bold {HACKER_GREEN}")
    console.print(Align.center(success_msg))
    console.print()

    return_msg = Text("Press any key to return to menu...", style=MAIN_STYLE)
    console.print(Align.center(return_msg))
    while get_key() is None: time.sleep(0.1) # Wait for key

    clear_screen()


def cancel_shutdown():
    """Cancel any scheduled shutdown or restart"""
    global timer_active, end_time, timer_type, timer_thread

    clear_screen()
    print_banner()

    if timer_active:
        # Cancel the Windows shutdown command first
        os.system("shutdown -a")
        log_event(f"Cancelled {timer_type or 'timer'}") # Log cancellation

        # Signal the timer thread to stop
        timer_active = False
        end_time = None
        timer_type = None

        # Wait briefly for the thread to potentially exit
        if timer_thread and timer_thread.is_alive():
            # No need to join forcefully, just clear the reference
            pass

        timer_thread = None # Clear the thread variable

        console.print()
        with Progress(
            SpinnerColumn(spinner_name="dots2", style=HACKER_GREEN),
            TextColumn("[bold green]Cancelling timer..."),
            BarColumn(bar_width=40, style=HACKER_GREEN, complete_style=HIGHLIGHT_STYLE),
            expand=True,
            console=console
        ) as progress:
            task = progress.add_task("", total=100)
            for i in range(101):
                progress.update(task, completed=i)
                time.sleep(0.01)

        console.print()
        success_msg = Text("Timer cancelled successfully!", style=f"bold {HACKER_GREEN}")
        console.print(Align.center(success_msg))
        time.sleep(1.5)
        clear_screen()
        return True
    else:
        console.print()
        error_msg = Text("No active timer to cancel.", style="yellow")
        console.print(Align.center(error_msg))
        time.sleep(1.5)
        clear_screen()
        return False

def display_timer_status():
    """Create the Rich renderable for the current timer status."""
    global timer_active, end_time, timer_type

    if timer_active and end_time:
        remaining = end_time - time.time()
        if remaining <= 0:
            # Timer expired but thread might not have updated state yet
            timer_active = False # Ensure state is correct
            return Panel("Timer expired", border_style=BORDER_STYLE, style=MAIN_STYLE)

        hours, remainder = divmod(int(remaining), 3600)
        minutes, seconds = divmod(remainder, 60)
        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        end_time_dt = datetime.fromtimestamp(end_time)
        end_time_str = end_time_dt.strftime("%Y-%m-%d %H:%M:%S") # Show date too

        table = Table(title=f"[bold {HACKER_GREEN}]Active Timer[/bold {HACKER_GREEN}]",
                     show_header=True, header_style=f"bold {HACKER_GREEN}",
                     box=DOUBLE, border_style=BORDER_STYLE)
        table.add_column("Type", style=MAIN_STYLE)
        table.add_column("Time Remaining", style=MAIN_STYLE)
        table.add_column("Scheduled End Time", style=MAIN_STYLE)
        table.add_row(timer_type.capitalize() if timer_type else "Unknown", time_str, end_time_str)
        return Align.center(table)
    else:
        return Panel("No active timer", border_style=BORDER_STYLE, style=MAIN_STYLE)

def show_timer_status_rich():
    """Show the current timer status with live updates and cancellation."""
    global timer_active # Need to check this

    clear_screen()
    print_banner()
    title = Text("Timer Status", style=f"bold {HACKER_GREEN}")
    console.print(Align.center(title))
    console.print()

    if not timer_active:
        console.print(Align.center(display_timer_status())) # Show "No active timer" panel
        console.print()
        instruction = Text("Press any key to return to menu...", style=MAIN_STYLE)
        console.print(Align.center(instruction))
        while get_key() is None: time.sleep(0.1) # Wait for key
        clear_screen()
        return

    # Timer is active, show live status
    instruction = Text("Press 'c' to cancel the timer or ESC/any other key to return", style=f"{HACKER_GREEN}")
    console.print(Align.center(instruction))
    console.print()

    try:
        with Live(display_timer_status(), refresh_per_second=2, console=console, transient=True, vertical_overflow="visible") as live:
            while timer_active: # Loop while the timer is supposed to be active
                current_status_renderable = display_timer_status()
                live.update(current_status_renderable)

                # Check if timer expired *during* the loop iteration
                if isinstance(current_status_renderable, Panel) and "expired" in str(current_status_renderable.renderable).lower():
                    break # Exit loop if timer expired

                key = get_key()
                if key is not None: # Check if *any* key was pressed
                    if key.lower() == 'c':
                        live.stop() # Stop live display *before* cancelling
                        if cancel_shutdown(): # cancel_shutdown handles clearing and messages
                            return # Return after successful cancellation
                        else:
                            # If cancellation failed (e.g., timer expired just now),
                            # redraw the status briefly before returning.
                            clear_screen(); print_banner()
                            console.print(Align.center(title)); console.print()
                            console.print(Align.center(display_timer_status()))
                            time.sleep(1.5); clear_screen()
                            return
                    else: # Any other key (including ESC)
                        live.stop()
                        clear_screen()
                        return

                time.sleep(0.1) # Small sleep to prevent high CPU usage

            # If loop exits because timer_active became false (timer expired or cancelled outside 'c')
            live.update(display_timer_status()) # Show final status (Expired or No Timer)
            time.sleep(1.5) # Pause to show final status

    except Exception as e:
        console.print(f"\n[bold red]Error during live display: {e}[/bold red]")
        time.sleep(2)
    finally:
        clear_screen() # Ensure screen is clear on exit

def restart_to_bios():
    """Restart the system into BIOS/firmware settings."""
    clear_screen()
    print_banner()
    title = Text("Restart to BIOS/Firmware", style=f"bold {HACKER_GREEN}")
    console.print(Align.center(title))
    console.print()

    system = platform.system()
    supported = False
    command = None

    if system == "Windows":
        supported = True
        command = "shutdown /r /fw /t 0"
        log_event("Restart to BIOS initiated (Windows)")
    elif system == "Linux":
        # Check if systemctl is available
        if os.path.exists("/bin/systemctl") or os.path.exists("/usr/bin/systemctl"):
            supported = True
            command = "systemctl reboot --firmware-setup"
            log_event("Restart to BIOS initiated (Linux/systemd)")
        else:
            console.print(Align.center(Text("Systemd not detected. Cannot automatically restart to firmware on this Linux system.", style="yellow")))
    elif system == "Darwin":  # MacOS
        console.print(Align.center(Text("Restarting to Startup Manager on macOS requires holding Option key during boot.", style="yellow")))
        console.print(Align.center(Text("Automatic restart to firmware is not directly supported via command.", style="yellow")))
        log_event("Restart to BIOS attempted (macOS - Not directly supported)")
    else:
        console.print(Align.center(Text(f"Unsupported operating system ({system}) for restarting to BIOS.", style="bold red")))
        log_event(f"Restart to BIOS attempted (Unsupported OS: {system})")

    if supported and command:
        confirm = Prompt.ask(f"[bold yellow]This will immediately restart your computer into the BIOS/firmware settings. Are you sure?[/bold yellow]", choices=["y", "n"], default="n")
        if confirm.lower() == 'y':
            try:
                console.print(Align.center(Text("Attempting to restart to BIOS...", style=f"bold {HACKER_GREEN}")))
                os.system(command)
                # If the command fails to initiate restart immediately, the script might continue
                time.sleep(5) # Give it time
                console.print(Align.center(Text("If the system hasn't restarted, the command may have failed or requires manual confirmation.", style="yellow")))
            except Exception as e:
                console.print(Align.center(Text(f"An error occurred: {str(e)}", style="bold red")))
                log_event(f"Error executing restart to BIOS command: {e}")
        else:
            console.print(Align.center(Text("Operation cancelled.", style="yellow")))
    elif not supported and system not in ["Darwin"]: # Only show return message if not handled above
        console.print()
        instruction = Text("Press any key to return...", style=MAIN_STYLE)
        console.print(Align.center(instruction))
        while get_key() is None: time.sleep(0.1)

    clear_screen()


# Keep original functions if they are simple wrappers or placeholders
# Remove view_timer as show_timer_status_rich replaces it.
# Remove cancel_timer as cancel_shutdown replaces it.
# Remove set_timer as set_timer_rich replaces it.
