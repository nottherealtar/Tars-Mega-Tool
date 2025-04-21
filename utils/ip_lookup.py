import requests
import json
import time
import sys
import re

# Rich imports
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.align import Align
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt
from rich.box import DOUBLE

# Local imports
from utils.helpers import (
    clear_screen, print_banner, get_key, console, save_output_to_file,
    MAIN_STYLE, HIGHLIGHT_STYLE, HACKER_GREEN, BORDER_STYLE
)
from datetime import datetime

API_URL_BASE = "https://api.ipquery.io/"  # Base URL without IP

def lookup_ip_detailed(ip_address):
    """Looks up detailed IP information using ipquery.io (JSON format).
       Returns a dict: {"data": parsed_dict|None, "error": str|None, "raw_text": str|None}
    """
    url = f"{API_URL_BASE}{ip_address}"
    headers = {'User-Agent': 'TarsUtilitiesTool/1.0'}
    result = {"data": None, "error": None, "raw_text": None}
    raw_response_text = None
    response = None

    try:
        response = requests.get(url, headers=headers, timeout=10)
        try:
            raw_response_text = response.text
        except Exception as e_read:
            result["error"] = f"Error reading response body: {e_read}"
            return result

        result["raw_text"] = raw_response_text

        if not raw_response_text:
            if response.status_code == 200:
                result["error"] = "API returned empty response body."
                return result

        response.raise_for_status()

        parsed_data = response.json()

        if isinstance(parsed_data, dict):
            result["data"] = parsed_data
        else:
            result["error"] = "Invalid API response format (unexpected JSON structure)."

    except requests.exceptions.Timeout:
        result["error"] = "Request timed out."
        result["raw_text"] = raw_response_text
    except requests.exceptions.HTTPError as http_err:
        error_msg = str(http_err)
        status_code = response.status_code if response else 'N/A'
        if raw_response_text:
            try:
                err_details = json.loads(raw_response_text)
                msg = err_details.get('message', error_msg)
                error_msg = f"HTTP Error {status_code}: {msg}"
            except json.JSONDecodeError:
                error_msg = f"HTTP Error {status_code}: {raw_response_text[:100]}"
        else:
            error_msg = f"HTTP Error {status_code}: (No response body)"
        result["error"] = error_msg
        result["raw_text"] = raw_response_text
    except requests.exceptions.RequestException as req_err:
        result["error"] = f"Network Error: {req_err}"
    except json.JSONDecodeError:
        result["error"] = "Error decoding API response (invalid JSON)."
        result["raw_text"] = raw_response_text
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        result["error"] = f"An unexpected error occurred: {type(e).__name__}"
        result["raw_text"] = raw_response_text

    return result

def display_detailed_ip_info():
    """Prompts for IP and displays detailed info from ipquery.io (parsed from JSON)."""
    clear_screen(); print_banner()
    title = Text("Detailed IP Information Lookup (ipquery.io)", style=f"bold {HACKER_GREEN}")
    console.print(Align.center(title)); console.print()

    while True:
        prompt_text = Text("Enter an IP address to lookup, or type 'back':", style=MAIN_STYLE)
        console.print(Align.center(prompt_text))
        console.print()
        ip_input = Prompt.ask("[bold]IP Address[/bold]")

        if ip_input.lower() == "back":
            clear_screen(); return
        if ip_input.lower() == "exit":
            clear_screen(); console.print(Align.center(Text("\nGoodbye!", style=f"bold {HACKER_GREEN}"))); sys.exit()

        ip_input = ip_input.strip()
        if not re.match(r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$", ip_input):
            console.print("[red]Invalid IPv4 format. Please try again.[/red]")
            time.sleep(1.5)
            clear_screen(); print_banner(); console.print(Align.center(title)); console.print()
            continue
        else:
            break

    console.print()
    lookup_result = None
    with Progress(SpinnerColumn(), TextColumn(f"Looking up {ip_input}..."), transient=True, console=console) as progress:
        progress.add_task("", total=None)
        lookup_result = lookup_ip_detailed(ip_input)

    raw_text_to_save = lookup_result.get("raw_text")

    if lookup_result["error"]:
        console.print(Align.center(Text(lookup_result["error"], style="bold red")))
    elif lookup_result["data"]:
        data = lookup_result["data"]
        ip = data.get("ip", ip_input)

        isp_table = Table(title=f"ISP Information", box=DOUBLE, border_style=BORDER_STYLE, show_header=False)
        isp_table.add_column("Property", style="dim")
        isp_table.add_column("Value", style=MAIN_STYLE)
        isp_info = data.get("isp", {})
        isp_table.add_row("ASN", str(isp_info.get("asn", "N/A")))
        isp_table.add_row("Organization", str(isp_info.get("org", "N/A")))
        isp_table.add_row("ISP Name", str(isp_info.get("isp", "N/A")))
        console.print(Align.center(isp_table))
        console.print()

        loc_table = Table(title=f"Location Information", box=DOUBLE, border_style=BORDER_STYLE, show_header=False)
        loc_table.add_column("Property", style="dim")
        loc_table.add_column("Value", style=MAIN_STYLE)
        loc_info = data.get("location", {})
        country = str(loc_info.get('country', 'N/A'))
        country_code = str(loc_info.get('country_code', 'N/A'))
        loc_table.add_row("Country", f"{country} ({country_code})" if country != 'N/A' else 'N/A')
        loc_table.add_row("State/Region", str(loc_info.get('state', 'N/A')))
        loc_table.add_row("City", str(loc_info.get('city', 'N/A')))
        loc_table.add_row("Zipcode", str(loc_info.get('zipcode', 'N/A')))
        lat = loc_info.get('latitude', 'N/A')
        lon = loc_info.get('longitude', 'N/A')
        loc_table.add_row("Coordinates", f"Lat: {lat}, Lon: {lon}" if lat != 'N/A' else 'N/A')
        loc_table.add_row("Timezone", str(loc_info.get('timezone', 'N/A')))
        loc_table.add_row("Local Time", str(loc_info.get('localtime', 'N/A')))
        console.print(Align.center(loc_table))
        console.print()

        risk_table = Table(title=f"Risk Assessment", box=DOUBLE, border_style=BORDER_STYLE, show_header=False)
        risk_table.add_column("Property", style="dim")
        risk_table.add_column("Value", style=MAIN_STYLE)
        risk_info = data.get("risk", {})
        risk_table.add_row("Is Mobile?", str(risk_info.get('is_mobile', 'N/A')))
        risk_table.add_row("Is VPN?", str(risk_info.get('is_vpn', 'N/A')))
        risk_table.add_row("Is Tor?", str(risk_info.get('is_tor', 'N/A')))
        risk_table.add_row("Is Proxy?", str(risk_info.get('is_proxy', 'N/A')))
        risk_table.add_row("Is Datacenter?", str(risk_info.get('is_datacenter', 'N/A')))
        risk_table.add_row("Risk Score", str(risk_info.get('risk_score', 'N/A')))
        console.print(Align.center(risk_table))

        def generate_save_content():
            import json
            try:
                return json.dumps(data, indent=4)
            except TypeError as e:
                return f"Error serializing data: {e}\n\nRaw data structure:\n{data}"
        save_output_to_file(generate_save_content, f"ip_details_{ip_input.replace('.', '_')}")

    else:
        console.print(Align.center(Text(f"Could not retrieve valid information for '{ip_input}'.", style="bold red")))

    console.print()

    if raw_text_to_save:
        def generate_save_content():
            return raw_text_to_save
        save_output_to_file(generate_save_content, f"ip_details_{ip_input.replace('.', '_')}_response")

    instruction = Text("Press any key to return...", style=MAIN_STYLE)
    console.print(Align.center(instruction))
    while get_key() is None: time.sleep(0.1)
