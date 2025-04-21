import os
import platform
import time
import sys
from datetime import datetime

# Rich imports
from rich.console import Console
from rich.text import Text
from rich.align import Align
from rich.prompt import Prompt

# Local imports
from utils.helpers import (
    clear_screen, print_banner, get_key, console,
    MAIN_STYLE, HIGHLIGHT_STYLE, HACKER_GREEN, BORDER_STYLE
)
from utils.logging import log_event # Import logging

# --- Existing Scheduling Logic (Keep as is for now) ---
def parse_datetime(input_str):
    """Parse a date and time string into a datetime object."""
    # Add more formats as needed
    formats = [
        "%d/%m/%Y %I:%M%p", "%d/%m/%Y %H:%M", # With minutes
        "%d/%m/%Y %I%p", "%d/%m/%Y %I %p", # Without minutes (assume :00)
        "%d/%m/%y %I:%M%p", "%d/%m/%y %H:%M", # 2-digit year
        "%d/%m/%y %I%p", "%d/%m/%y %I %p",
        "%Y-%m-%d %H:%M", # ISO-like
        "%m/%d/%Y %I:%M%p", "%m/%d/%Y %H:%M", # US format
        "%m/%d/%y %I:%M%p", "%m/%d/%y %H:%M",
    ]
    for fmt in formats:
        try:
            # Handle AM/PM formats where hour might be implied as :00
            dt = datetime.strptime(input_str, fmt)
            # If format includes %p but not %M, strptime might default to 00 minutes.
            # This seems acceptable for scheduling.
            return dt
        except ValueError:
            continue
    # If no format matches
    raise ValueError("Invalid date and time format. Use formats like DD/MM/YYYY HH:MM(AM/PM) or YYYY-MM-DD HH:MM.")


def schedule_shutdown(date_time):
    """Schedule a shutdown task at a specific date and time."""
    now = datetime.now()
    if date_time <= now:
        console.print(Align.center(Text("The specified time is in the past. Please enter a future time.", style="bold red")))
        return False # Indicate failure

    shutdown_time_str = date_time.strftime("%H:%M")
    shutdown_date_str = date_time.strftime("%d/%m/%Y") # Format for schtasks
    system = platform.system()

    try:
        if system == "Windows":
            # Task names cannot contain / or \. Replace with _ or similar if needed.
            task_name = f"TarsUtil_ScheduledShutdown_{date_time.strftime('%Y%m%d_%H%M')}"
            # Use full path to shutdown.exe for reliability? Usually not needed.
            # Ensure the command is properly quoted if path contains spaces.
            # /F forces closing applications. Remove if not desired.
            command = f'schtasks /create /tn "{task_name}" /tr "shutdown /s /f /t 0" /sc once /st {shutdown_time_str} /sd {shutdown_date_str} /f'
            # Use subprocess for better error handling? os.system is simpler here.
            result = os.system(command)
            if result != 0:
                 raise OSError(f"schtasks command failed with exit code {result}")
            log_event(f"Scheduled shutdown via Task Scheduler for {date_time.strftime('%Y-%m-%d %H:%M')}")
            console.print(Align.center(Text(f"Shutdown scheduled on {shutdown_date_str} at {shutdown_time_str} using Task Scheduler.", style=f"bold {HACKER_GREEN}")))
            return True

        elif system == "Linux" or system == "Darwin": # MacOS uses launchd, cron might not be default
            # Using 'at' command is generally better for one-off tasks than cron
            at_time_str = date_time.strftime("%H:%M %m/%d/%Y") # Format for 'at'
            # Ensure 'at' command exists?
            # Use echo and pipe to at command
            command = f'echo "shutdown -h now" | at {at_time_str}'
            result = os.system(command)
            if result != 0:
                 # Try cron as fallback? Or just report error.
                 # Cron requires careful handling of existing crontab.
                 # For simplicity, stick to 'at' or report failure.
                 raise OSError(f"'at' command failed with exit code {result}. Ensure 'atd' service is running.")
            log_event(f"Scheduled shutdown via 'at' for {date_time.strftime('%Y-%m-%d %H:%M')}")
            console.print(Align.center(Text(f"Shutdown scheduled on {shutdown_date_str} at {shutdown_time_str} using 'at'.", style=f"bold {HACKER_GREEN}")))
            return True
        else:
            console.print(Align.center(Text("Unsupported operating system for scheduling shutdowns.", style="bold red")))
            return False
    except FileNotFoundError:
         console.print(Align.center(Text(f"Required command not found (e.g., schtasks, at). Cannot schedule.", style="bold red")))
         return False
    except OSError as e:
         console.print(Align.center(Text(f"Error scheduling shutdown: {e}", style="bold red")))
         log_event(f"Error scheduling shutdown: {e}")
         return False
    except Exception as e:
         console.print(Align.center(Text(f"An unexpected error occurred: {e}", style="bold red")))
         log_event(f"Unexpected error scheduling shutdown: {e}")
         return False


def calendar_scheduling():
    """Prompt the user to schedule a shutdown task."""
    clear_screen()
    print_banner()
    title = Text("Schedule Shutdown/Restart", style=f"bold {HACKER_GREEN}")
    console.print(Align.center(title))
    console.print()

    while True:
        prompt_text = Text("Enter date & time (e.g., 21/04/2025 8:30PM, tomorrow 14:00) or 'back':", style=MAIN_STYLE)
        console.print(Align.center(prompt_text))
        console.print()
        user_input = Prompt.ask("[bold]Date and Time[/bold]")

        if user_input.lower() == "back":
            clear_screen()
            return
        if user_input.lower() == "exit":
             clear_screen(); console.print(Align.center(Text("\nGoodbye!", style=f"bold {HACKER_GREEN}"))); sys.exit()

        # Add basic relative time parsing (optional enhancement)
        # E.g., "tomorrow 14:00", "in 2 hours", etc. - Requires more complex parsing logic

        try:
            date_time = parse_datetime(user_input)
            if schedule_shutdown(date_time):
                 # Success message printed by schedule_shutdown
                 time.sleep(2.5)
                 clear_screen()
                 return # Exit after successful scheduling
            else:
                 # Error message printed by schedule_shutdown
                 time.sleep(2.5)
                 # Loop again to re-prompt
                 clear_screen(); print_banner(); console.print(Align.center(title)); console.print()
                 continue

        except ValueError as e:
            console.print(Align.center(Text(f"[bold red]Error: {str(e)}[/bold red]")))
            time.sleep(2.5)
            # Loop again to re-prompt
            clear_screen(); print_banner(); console.print(Align.center(title)); console.print()
            continue

# --- Placeholder for Google Calendar ---
def google_calendar_placeholder():
    """Placeholder for Google Calendar integration."""
    clear_screen(); print_banner()
    title = Text("Google Calendar Integration", style=f"bold {HACKER_GREEN}")
    console.print(Align.center(title)); console.print()
    console.print(Align.center(Text("Feature under development.", style=MAIN_STYLE)))
    console.print(Align.center(Text("This will allow syncing shutdown schedules with Google Calendar.", style=MAIN_STYLE)))
    console.print()
    instruction = Text("Press any key to return...", style=MAIN_STYLE)
    console.print(Align.center(instruction))
    while get_key() is None: time.sleep(0.1)
    clear_screen()
