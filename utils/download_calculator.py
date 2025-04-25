import re
import time
import sys
from datetime import datetime, timedelta

from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich.prompt import Prompt

from utils.helpers import (
    clear_screen, print_banner, get_key, console, format_duration,
    MAIN_STYLE, HIGHLIGHT_STYLE, HACKER_GREEN, BORDER_STYLE
)
from utils import shutdown_timer

KB = 1024
MB = 1024 * KB
GB = 1024 * MB
TB = 1024 * GB

def parse_size(size_str):
    size_str = size_str.strip().upper()
    match = re.match(r"^([\d.]+)\s*(KB|MB|GB|TB)$", size_str)
    if not match:
        raise ValueError("Invalid size format. Use KB, MB, GB, TB (e.g., '500MB', '1.5GB').")
    value = float(match.group(1))
    unit = match.group(2)
    if unit == "KB":
        return int(value * KB)
    elif unit == "MB":
        return int(value * MB)
    elif unit == "GB":
        return int(value * GB)
    elif unit == "TB":
        return int(value * TB)
    raise ValueError("Unknown size unit.")

def parse_speed(speed_str):
    speed_str = speed_str.strip().upper()
    match = re.match(r"^([\d.]+)\s*(KB|MB|GB)/S$", speed_str)
    if not match:
        raise ValueError("Invalid speed format. Use KB/s, MB/s, GB/s (e.g., '10MB/s').")
    value = float(match.group(1))
    unit = match.group(2)
    if unit == "KB":
        return value * KB
    elif unit == "MB":
        return value * MB
    elif unit == "GB":
        return value * GB
    raise ValueError("Unknown speed unit.")

def calculate_download_time(file_size_bytes, speed_bytes_per_sec):
    if speed_bytes_per_sec <= 0:
        raise ValueError("Download speed must be positive.")
    if file_size_bytes < 0:
        raise ValueError("File size cannot be negative.")
    if file_size_bytes == 0:
        return 0
    return file_size_bytes / speed_bytes_per_sec

def display_download_time_calculator():
    clear_screen()
    print_banner()
    title = Text("Download Time Calculator", style=f"bold {HACKER_GREEN}")
    console.print(Align.center(title))
    console.print()
    while True:
        size_prompt = Text("Enter file size (e.g., 500MB, 2GB) or 'back':", style=MAIN_STYLE)
        console.print(Align.center(size_prompt))
        console.print()
        size_input = Prompt.ask("[bold]File Size[/bold]")
        if size_input.lower() == "back":
            clear_screen(); return
        if size_input.lower() == "exit":
            clear_screen(); console.print(Align.center(Text("\nGoodbye!", style=f"bold {HACKER_GREEN}"))); sys.exit()
        try:
            file_size_bytes = parse_size(size_input)
            break
        except ValueError as e:
            error_msg = Text(f"\nError: {str(e)}", style="bold red")
            console.print(Align.center(error_msg))
            time.sleep(2)
            clear_screen(); print_banner(); console.print(Align.center(title)); console.print()
            continue
    while True:
        speed_prompt = Text("Enter download speed (e.g., 10MB/s, 500KB/s, 1GB/s) or 'back':", style=MAIN_STYLE)
        console.print(Align.center(speed_prompt))
        console.print()
        speed_input = Prompt.ask("[bold]Download Speed[/bold]")
        if speed_input.lower() == "back":
            clear_screen(); return
        if speed_input.lower() == "exit":
            clear_screen(); console.print(Align.center(Text("\nGoodbye!", style=f"bold {HACKER_GREEN}"))); sys.exit()
        try:
            speed_bytes_per_sec = parse_speed(speed_input)
            if speed_bytes_per_sec <= 0:
                raise ValueError("Download speed must be greater than zero.")
            break
        except ValueError as e:
            error_msg = Text(f"\nError: {str(e)}", style="bold red")
            console.print(Align.center(error_msg))
            time.sleep(2)
            clear_screen(); print_banner(); console.print(Align.center(title)); console.print()
            console.print(Align.center(size_prompt))
            console.print(f"   File Size: [bold]{size_input}[/bold]")
            console.print()
            continue
    console.print()
    try:
        total_seconds = calculate_download_time(file_size_bytes, speed_bytes_per_sec)
        readable_time = format_duration(total_seconds)
        finish_time = datetime.now() + timedelta(seconds=total_seconds)
        finish_time_str = finish_time.strftime("%Y-%m-%d %H:%M:%S")
        result_text = Text.assemble(
            ("Estimated download time for a ", MAIN_STYLE),
            (f"{size_input}", HIGHLIGHT_STYLE),
            (" file at ", MAIN_STYLE),
            (f"{speed_input}", HIGHLIGHT_STYLE),
            (" is:\n\n", MAIN_STYLE),
            (f"{readable_time}", f"bold {HACKER_GREEN}"),
            ("\n\n", MAIN_STYLE),
            ("Estimated completion time: ", MAIN_STYLE),
            (f"{finish_time_str}", HIGHLIGHT_STYLE)
        )
        console.print(Align.center(Panel(result_text, title="Calculation Result", border_style=BORDER_STYLE, padding=(1, 2))))
        instruction = Text("Press ENTER to continue...", style=MAIN_STYLE)
        console.print(Align.center(instruction))
        while True:
            key = get_key()
            if key == "ENTER":
                break
            time.sleep(0.05)
        clear_screen()
        print_banner()
    except Exception as e:
        error_msg = Text(f"Calculation Error: {str(e)}", style="bold red")
        console.print(Align.center(error_msg))
        console.print()
        instruction = Text("Press any key to return...", style=MAIN_STYLE)
        console.print(Align.center(instruction))
        while get_key() is None:
            time.sleep(0.50)
        clear_screen()
        return

    # --- Arrow menu for post-download action ---
    console.print()
    from ui.menus import arrow_menu
    timer_seconds = int(total_seconds) + 1200
    buffer_time = format_duration(1200)
    total_time_str = format_duration(timer_seconds)
    # Show download time and buffer in the menu panel
    menu_panel = Panel(
        Text(
            f"Download time: {readable_time}\n"
            f"Buffer (grace period): {buffer_time}\n"
            f"Total time until action: {total_time_str}\n\n"
            "Choose what to do after the download completes:",
            style=MAIN_STYLE
        ),
        border_style=BORDER_STYLE
    )
    console.print(Align.center(menu_panel))
    options = [
        "Shutdown after download (adds 20 min buffer)",
        "Restart after download (adds 20 min buffer)",
        "Do Nothing",
        "Back"
    ]
    choice = arrow_menu("After Download Action", options)
    if choice == 0 or choice == 1:
        action = "shutdown" if choice == 0 else "restart"
        # Show the download time and buffer in confirmation
        confirm_panel = Panel(
            Text(
                f"Download time: {readable_time}\n"
                f"Buffer (grace period): {buffer_time}\n"
                f"Total time until {action}: {total_time_str}\n\n"
                f"Schedule a {action} after this time?",
                style=MAIN_STYLE
            ),
            border_style=BORDER_STYLE
        )
        console.print(Align.center(confirm_panel))
        confirm_options = ["Yes", "No"]
        confirm_choice = arrow_menu("Confirm Action", confirm_options)
        if confirm_choice == 0:
            # Call set_timer_rich with the calculated time, bypassing user input
            shutdown_timer.set_timer_rich(action, preset_seconds=timer_seconds)
            return

    # --- End Arrow menu ---

    console.print()
    instruction = Text("Press any key to return...", style=MAIN_STYLE)
    console.print(Align.center(instruction))
    while get_key() is None:
        time.sleep(0.1)
    clear_screen()

__all__ = ['display_download_time_calculator']
