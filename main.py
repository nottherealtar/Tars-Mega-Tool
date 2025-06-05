import os
import sys
import eel
import platform
from rich.console import Console
from utils import shutdown_timer_web

# --- Constants ---
CURRENT_VERSION = "1.0.0"  # Replace with dynamic version reading if needed
WEB_FOLDER = "web"
MAIN_HTML = "main.html"

# Console instance for logging
console = Console(color_system="auto", highlight=False)

# --- Eel Setup ---
eel.init(WEB_FOLDER)

# --- Expose Functions to JavaScript ---
@eel.expose
def get_version():
    """Return the current version of the application."""
    console.print("[DEBUG] get_version called.")
    return CURRENT_VERSION

@eel.expose
def get_platform():
    """Return the platform information."""
    console.print("[DEBUG] get_platform called.")
    return platform.system()

@eel.expose
def set_timer_js(action, duration):
    try:
        console.print(f"[DEBUG] set_timer_js called with action: {action}, duration: {duration}")
        # Call the correct function from shutdown_timer_web
        result = shutdown_timer_web.set_timer(action, duration)
        return {"message": "Timer set successfully!"} if result else {"error": "Failed to set timer."}
    except AttributeError as e:
        console.print(f"[red]Function not found in shutdown_timer_web: {e}[/red]")
        return {"error": "The requested function is not implemented in the backend."}
    except Exception as e:
        console.print(f"[red]Error in set_timer_js: {e}[/red]")
        return {"error": f"An unexpected error occurred: {str(e)}"}

@eel.expose
def cancel_timer_js():
    try:
        console.print("[DEBUG] cancel_timer_js called.")
        result = shutdown_timer_web.cancel_shutdown()
        return {"message": "Timer canceled successfully!"} if result else {"error": "No active timer to cancel."}
    except Exception as e:
        console.print(f"[red]Error in cancel_timer_js: {e}[/red]")
        return {"error": f"An unexpected error occurred: {str(e)}"}

@eel.expose
def get_timer_status_js():
    try:
        console.print("[DEBUG] get_timer_status_js called.")
        return shutdown_timer_web.get_timer_status()
    except Exception as e:
        console.print(f"[red]Error in get_timer_status_js: {e}[/red]")
        return {"error": f"An unexpected error occurred: {str(e)}"}

# Placeholder for other features
@eel.expose
def placeholder_function():
    console.print("[DEBUG] placeholder_function called.")
    return {"message": "This feature is not yet implemented."}

# --- Integration Verification ---
def verify_integration():
    """Verify that all exposed functions are working correctly."""
    console.print("[INFO] Verifying integration with exposed functions...")
    try:
        # Test each exposed function
        version = get_version()
        console.print(f"[INFO] get_version() returned: {version}")

        platform_info = get_platform()
        console.print(f"[INFO] get_platform() returned: {platform_info}")

        timer_status = get_timer_status_js()
        console.print(f"[INFO] get_timer_status_js() returned: {timer_status}")

        console.print("[INFO] Integration verification completed successfully.")
    except Exception as e:
        console.print(f"[red][ERROR] Integration verification failed: {e}[/red]")

# --- Main Execution ---
def main():
    try:
        console.print(f"[INFO] Starting Tars Utilities Tool v{CURRENT_VERSION}...")
        verify_integration()  # Run integration verification
        eel.start(MAIN_HTML, size=(1200, 800), port=0)  # Use random port
    except Exception as e:
        console.print(f"[bold red]An error occurred: {e}[/bold red]")
        sys.exit(1)

if __name__ == "__main__":
    main()
