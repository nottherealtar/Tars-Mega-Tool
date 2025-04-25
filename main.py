import os
import sys
import signal
import time # Keep for potential sleep calls if needed

# Rich imports (keep console for potential top-level messages)
from rich.console import Console
from rich.text import Text
from rich.align import Align

# Platform specific imports (keep for elevate)
import platform

# Elevation import
try:
    # Only attempt elevate on Windows
    if platform.system() == "Windows":
        from elevate import elevate
    else:
        elevate = lambda graphical=True: None # No-op function for non-Windows
except ImportError:
    # Handle missing elevate module gracefully on Windows too
    if platform.system() == "Windows":
        print("Optional module 'elevate' not found. Install with: pip install elevate")
        print("Attempting to run without elevated privileges...")
    elevate = lambda graphical=True: None # No-op function

# --- Constants ---
# Read version from VERSION.txt
try:
    version_file = os.path.join(os.path.dirname(__file__), 'VERSION.txt')
    with open(version_file, 'r') as f:
        CURRENT_VERSION = f.read().strip()
except FileNotFoundError:
    CURRENT_VERSION = "0.0.0-dev" # Fallback version
except Exception as e:
    CURRENT_VERSION = "0.0.0-error"
    print(f"Warning: Could not read version file: {e}")

HACKER_GREEN = "bright_green" # Keep for potential exit message style

# --- Console ---
# Use console from helpers or define one here for minimal use
# from utils.helpers import console
console = Console(color_system="auto", highlight=False)

# --- Import Main Menu ---
# Import the main menu function from the UI module (system optimization features removed)
from ui.menus import main_menu

# --- Main Execution ---
def main():
    """Main entry point of the application."""
    try:
        # Request elevated privileges if needed (Windows only)
        # Pass graphical=False if you don't want a UAC GUI prompt
        elevate(graphical=False) # Attempt elevation

        # Handle Ctrl+C gracefully
        signal.signal(signal.SIGINT, lambda signum, frame: (
            # Ensure screen is clear before printing exit message
            os.system('cls' if os.name == 'nt' else 'clear'),
            console.print(Align.center(Text("\nCtrl+C detected. Exiting.", style="yellow"))),
            sys.exit(0)
        ))

        # Start the main application menu, passing the current version
        main_menu(CURRENT_VERSION)

    except PermissionError as pe:
         # Specific handling for permission errors, often related to elevation
         os.system('cls' if os.name == 'nt' else 'clear')
         console.print(f"[bold red]Permission Error:[/bold red]")
         console.print(f"[red]{str(pe)}[/red]")
         console.print("\n[yellow]Some features require administrator privileges.")
         console.print("[yellow]Please try running the tool as an administrator.[/yellow]")
         sys.exit(1)
    except ImportError as ie:
         # Handle missing critical dependencies if any were missed
         os.system('cls' if os.name == 'nt' else 'clear')
         console.print(f"[bold red]Import Error:[/bold red]")
         console.print(f"[red]{str(ie)}[/red]")
         # Print missing module name if available
         if hasattr(ie, 'name'):
             console.print(f"[yellow]Missing module: {ie.name}[/yellow]")
         console.print("\n[yellow]A required module is missing.")
         console.print("[yellow]Please ensure all dependencies are installed (check requirements.txt).[/yellow]")
         sys.exit(1)
    except Exception as e:
        # General error handling
        os.system('cls' if os.name == 'nt' else 'clear')
        console.print(f"[bold red]An unexpected error occurred:[/bold red]")
        console.print(f"[red]{type(e).__name__}: {str(e)}[/red]")
        # Optionally print traceback for debugging during development
        # import traceback
        # console.print_exception(show_locals=True) # Rich traceback
        console.print("\n[yellow]Exiting due to error.[/yellow]")
        sys.exit(1)

if __name__ == "__main__":
    # Ensure the script's directory is in the Python path
    # This helps with finding modules when run directly
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)

    main()
