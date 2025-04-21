import os
import sys
import time
from datetime import datetime # Import datetime for filenames

# Rich imports
from rich.console import Console
from rich.text import Text
from rich.align import Align
from rich.prompt import Prompt, Confirm # Import Confirm

# Platform specific imports for get_key
try:
    import msvcrt  # Windows
except ImportError:
    msvcrt = None # Define as None if import fails
try:
    import tty
    import termios # Unix/Linux/MacOS
    import select # For non-blocking read on Unix
except ImportError:
    # Fallback if Unix specific modules are not available
    termios = None
    tty = None
    select = None

# Define styles here or import from a central config if preferred
HACKER_GREEN = "bright_green"
HACKER_BG = "black"
MAIN_STYLE = f"{HACKER_GREEN} on {HACKER_BG}"
HIGHLIGHT_STYLE = f"black on {HACKER_GREEN}"
BORDER_STYLE = HACKER_GREEN # Added border style constant

# Console instance (can be shared or created per module)
console = Console(color_system="auto", highlight=False)

def clear_screen():
    """Clear the screen completely."""
    if os.name == 'nt':  # Windows
        os.system('cls')
    else:  # Unix/Linux/MacOS
        os.system('clear')
    # Use Rich's clear as well for better compatibility
    console.clear()

def print_banner():
    """Prints the application banner."""
    # Define the banner text using a raw multi-line string
    # Ensure no leading/trailing spaces on each line unless intended for the art
    banner_text = r"""
 ███████████                                ███████████                   ████
░█░░░███░░░█                               ░█░░░███░░░█                  ░░███
░   ░███  ░   ██████   ████████   █████    ░   ░███  ░   ██████   ██████  ░███   █████
    ░███     ░░░░░███ ░░███░░███ ███░░         ░███     ███░░███ ███░░███ ░███  ███░░
    ░███      ███████  ░███ ░░░ ░░█████        ░███    ░███ ░███░███ ░███ ░███ ░░█████
    ░███     ███░░███  ░███      ░░░░███       ░███    ░███ ░███░███ ░███ ░███  ░░░░███
    █████   ░░████████ █████     ██████        █████   ░░██████ ░░██████  █████ ██████
   ░░░░░     ░░░░░░░░ ░░░░░     ░░░░░░        ░░░░░     ░░░░░░   ░░░░░░  ░░░░░ ░░░░░░

"""
    # Create a Text object with the banner text and style, NO justify here
    banner = Text(banner_text, style=f"bold {HACKER_GREEN}")
    # Print the banner centered using Align.center
    console.print(Align.center(banner))
    console.print() # Add a blank line after the banner

def get_key():
    """Get a keypress from the user, cross-platform, non-blocking."""
    if os.name == 'nt' and msvcrt:  # Windows
        if msvcrt.kbhit(): # Check if a key is pressed before blocking
            key = msvcrt.getch()
            if key == b'\xe0':  # Special key prefix
                key = msvcrt.getch()
                if key == b'H': return 'UP'
                elif key == b'P': return 'DOWN'
                elif key == b'K': return 'LEFT'
                elif key == b'M': return 'RIGHT'
            elif key == b'\r': return 'ENTER'
            elif key == b'\x1b': return 'ESC'
            # WASD for navigation
            elif key in [b'w', b'W']: return 'UP'
            elif key in [b's', b'S']: return 'DOWN'
            elif key in [b'a', b'A']: return 'LEFT'
            elif key in [b'd', b'D']: return 'RIGHT'
            try:
                return key.decode('utf-8', errors='ignore')
            except UnicodeDecodeError:
                return None # Ignore undecodable keys
        else:
            return None # No key pressed
    elif termios and tty and select:  # Unix-like
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            # Use select to check for input without blocking
            if select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
                ch = sys.stdin.read(1)
                if ch == '\x1b':
                    # Check for ANSI escape sequences (arrows)
                    # Read potentially following characters for arrow keys non-blockingly
                    next1 = None
                    if select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
                        next1 = sys.stdin.read(1)
                    if next1 == '[':
                        next2 = None
                        if select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
                            next2 = sys.stdin.read(1)
                        if next2 == 'A': return 'UP'
                        elif next2 == 'B': return 'DOWN'
                        elif next2 == 'C': return 'RIGHT'
                        elif next2 == 'D': return 'LEFT'
                    return 'ESC' # Treat lone escape or unknown sequence as ESC
                elif ch == '\r': return 'ENTER'
                # WASD for navigation
                elif ch in ['w', 'W']: return 'UP'
                elif ch in ['s', 'S']: return 'DOWN'
                elif ch in ['a', 'A']: return 'LEFT'
                elif ch in ['d', 'D']: return 'RIGHT'
                return ch
            else:
                return None # No key pressed
        except Exception:
             # Fallback or ignore if termios/tty setup fails
             return None
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    else: # Fallback if no specific implementation works
        # This fallback is blocking, consider alternatives if needed
        # For non-blocking, returning None is better than input()
        return None
    return None # Default return if no key detected or error


def format_time_display(total_seconds):
    """Format seconds into a human-readable string"""
    total_seconds = int(total_seconds) # Ensure integer
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    time_str = ""
    if hours: time_str += f"{hours} hour{'s' if hours > 1 else ''} "
    if minutes: time_str += f"{minutes} minute{'s' if minutes > 1 else ''} "
    if seconds or not time_str: # Show seconds if non-zero or if hours/minutes are zero
        time_str += f"{seconds} second{'s' if seconds != 1 else ''}"
    return time_str.strip()

def format_seconds(seconds):
    """Format seconds into mm:ss format"""
    seconds = int(seconds) # Ensure integer
    minutes, secs = divmod(seconds, 60)
    return f"{minutes:02d}:{secs:02d}"

def generate_default_filename(base_name="output"):
    """Generates a default filename with a timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{base_name}_{timestamp}.txt"

def save_output_to_file(content_generator, default_filename_base="output"):
    """Asks the user if they want to save output and handles saving."""
    console.print() # Add a blank line before asking
    if Confirm.ask(f"Save this output to a file?", default=False):
        default_filename = generate_default_filename(default_filename_base)
        filename = Prompt.ask("Enter filename to save", default=default_filename)
        filename = filename.strip()

        if not filename:
            console.print("[yellow]Invalid filename. Save cancelled.[/yellow]")
            return

        try:
            # Generate the content *when needed* for saving
            content_to_save = content_generator()
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content_to_save)
            console.print(f"[bold green]Output saved successfully to '{filename}'[/bold green]")
        except IOError as e:
            console.print(f"[bold red]Error saving file '{filename}': {e}[/bold red]")
        except Exception as e:
            console.print(f"[bold red]An unexpected error occurred during saving: {e}[/bold red]")
        time.sleep(1.5) # Give user time to read save status message


__all__ = [
    'clear_screen', 'print_banner', 'get_key', 'format_time_display',
    'format_seconds', 'console', 'MAIN_STYLE', 'HIGHLIGHT_STYLE',
    'HACKER_GREEN', 'HACKER_BG', 'BORDER_STYLE', 'save_output_to_file' # Add save function
]
