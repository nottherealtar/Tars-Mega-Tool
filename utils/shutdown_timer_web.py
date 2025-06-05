import os
import platform
import threading
import time
from datetime import datetime, timedelta
import subprocess

# Timer state
active_timer = None
timer_action = None
timer_end_time = None

def _perform_action(action):
    """Perform the specified action (shutdown, restart, or BIOS)."""
    if platform.system() == "Windows":
        if action == "shutdown":
            os.system("shutdown /s /t 0")
        elif action == "restart":
            os.system("shutdown /r /t 0")
        elif action == "bios":
            os.system("shutdown /r /fw /t 0")
    else:
        if action == "shutdown":
            os.system("shutdown now")
        elif action == "restart":
            os.system("reboot")

def _timer_thread(action, duration):
    """Thread to handle the timer countdown and execute the action."""
    global active_timer, timer_action, timer_end_time
    timer_end_time = datetime.now() + timedelta(seconds=duration)
    time.sleep(duration)
    _perform_action(action)
    active_timer = None
    timer_action = None
    timer_end_time = None

def set_timer(action, duration):
    """Set a timer for shutdown, restart, or BIOS restart."""
    try:
        system = platform.system()
        if system == "Windows":
            if action == "shutdown":
                command = f"shutdown -s -t {duration}"
            elif action == "restart":
                command = f"shutdown -r -t {duration}"
            elif action == "bios":
                command = f"shutdown /r /fw /t {duration}"
            else:
                return {"error": f"Unsupported action: {action}"}
        elif system == "Linux":
            if action == "shutdown":
                command = f"shutdown -h +{int(duration) // 60}"
            elif action == "restart":
                command = f"shutdown -r +{int(duration) // 60}"
            elif action == "bios":
                return {"error": "BIOS restart is not supported on Linux."}
            else:
                return {"error": f"Unsupported action: {action}"}
        else:
            return {"error": f"Unsupported operating system: {system}"}

        # Execute the command
        subprocess.run(command, shell=True, check=True)
        return {"message": f"{action.capitalize()} timer set for {duration} seconds."}
    except subprocess.CalledProcessError as e:
        return {"error": f"Failed to execute command: {e}"}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {str(e)}"}

def cancel_timer():
    """Cancel the active timer."""
    global active_timer, timer_action, timer_end_time
    if not active_timer:
        print("[DEBUG] No active timer to cancel.")
        return {"error": "No active timer to cancel."}

    print("[DEBUG] Canceling active timer...")
    active_timer = None
    timer_action = None
    timer_end_time = None
    print("[DEBUG] Timer canceled successfully.")
    return {"message": "Active timer has been canceled."}

def get_timer_status():
    """Get the status of the active timer."""
    if not active_timer:
        return {"active": False, "message": "No active timer."}

    remaining_time = (timer_end_time - datetime.now()).total_seconds()
    if remaining_time <= 0:
        return {"active": False, "message": "No active timer."}

    return {
        "active": True,
        "action": timer_action,
        "remaining": _format_duration(remaining_time),
    }

def _parse_duration(duration):
    """Parse a duration string into seconds."""
    try:
        if duration.isdigit():
            return int(duration)
        elif "s" in duration:
            return int(duration.replace("s", ""))
        elif "m" in duration:
            return int(duration.replace("m", "")) * 60
        elif "h" in duration:
            return int(duration.replace("h", "")) * 3600
        elif ":" in duration:
            parts = list(map(int, duration.split(":")))
            if len(parts) == 2:
                return parts[0] * 60 + parts[1]
            elif len(parts) == 3:
                return parts[0] * 3600 + parts[1] * 60 + parts[2]
        raise ValueError("Invalid duration format. Use s, m, h, or HH:MM:SS.")
    except Exception:
        raise ValueError("Invalid duration format. Use s, m, h, or HH:MM:SS.")

def _format_duration(seconds):
    """Format seconds into a human-readable string."""
    seconds = int(seconds)
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if seconds > 0:
        parts.append(f"{seconds}s")
    return " ".join(parts)
