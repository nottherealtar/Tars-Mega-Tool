import socket
import urllib.request
import json
import re
import time
import sys
import os
import platform
import subprocess
from datetime import datetime

# Rich imports
from rich.console import Console
from rich.table import Table
from rich.align import Align
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt
from rich.box import DOUBLE
from rich.panel import Panel

# WHOIS import
try:
    import whois
except ImportError:
    whois = None

# Local imports
from utils.helpers import (
    clear_screen, print_banner, get_key, console, save_output_to_file,
    MAIN_STYLE, HIGHLIGHT_STYLE, HACKER_GREEN, BORDER_STYLE
)

def show_my_ip():
    """Display the local IP address and computer name."""
    clear_screen(); print_banner()
    title = Text("My IP Address", style=f"bold {HACKER_GREEN}")
    console.print(Align.center(title)); console.print()

    hostname = "N/A"
    local_ip = "N/A"
    external_ip = "N/A"

    with Progress(SpinnerColumn(), TextColumn("Gathering IP information..."), transient=True, console=console) as progress:
        progress.add_task("", total=None)
        try:
            hostname = socket.gethostname()
            try:
                local_ip = socket.gethostbyname(hostname)
            except socket.gaierror:
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    s.settimeout(1.0)
                    s.connect(("8.8.8.8", 80))
                    local_ip = s.getsockname()[0]
                    s.close()
                except Exception:
                    local_ip = "N/A (Fallback failed)"
            try:
                req = urllib.request.Request("https://api.ipify.org", headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=3) as response:
                    external_ip = response.read().decode('utf-8')
            except Exception as ext_e:
                external_ip = f"Error or Timeout ({type(ext_e).__name__})"
        except Exception as e:
            console.print(Align.center(Text(f"Error retrieving host/IP info: {str(e)}", style="bold red")))

    ip_info_data = {
        "Computer Name": hostname,
        "Local IP Address": local_ip,
        "External IP Address": external_ip
    }

    table = Table(box=DOUBLE, border_style=BORDER_STYLE, title=f"[{HACKER_GREEN}]IP Information[/{HACKER_GREEN}]")
    table.add_column("Information", style=MAIN_STYLE)
    table.add_column("Value", style=MAIN_STYLE)
    for key, value in ip_info_data.items():
        table.add_row(key, value)
    console.print(Align.center(table))
    console.print()

    def generate_save_content():
        lines = [f"IP Information ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})"]
        lines.append("-" * 30)
        for key, value in ip_info_data.items():
            lines.append(f"{key}: {value}")
        return "\n".join(lines)

    save_output_to_file(generate_save_content, "my_ip_info")

    instruction = Text("Press any key to return...", style=MAIN_STYLE)
    console.print(Align.center(instruction))
    while get_key() is None: time.sleep(0.1)
    clear_screen()

def lookup_ip_info():
    """Look up information about an IP address or domain using ip-api.com."""
    clear_screen(); print_banner()
    title = Text("IP Address Information Lookup", style=f"bold {HACKER_GREEN}")
    console.print(Align.center(title)); console.print()

    while True:
        prompt_text = Text("Enter an IP address or domain name to lookup, or type 'back':", style=MAIN_STYLE)
        console.print(Align.center(prompt_text))
        console.print()
        ip_input = Prompt.ask("[bold]IP or Domain[/bold]")

        if ip_input.lower() == "back":
            clear_screen(); return
        if ip_input.lower() == "exit":
            clear_screen(); console.print(Align.center(Text("\nGoodbye!", style=f"bold {HACKER_GREEN}"))); sys.exit()

        ip_input = ip_input.strip()
        if not ip_input:
            console.print("[red]Input cannot be empty.[/red]")
            time.sleep(1.5)
            clear_screen(); print_banner(); console.print(Align.center(title)); console.print()
            continue
        else:
            break

    console.print()
    ip_data = None
    error_message = None

    with Progress(SpinnerColumn(), TextColumn(f"Looking up {ip_input}..."), transient=True, console=console) as progress:
        progress.add_task("", total=None)
        try:
            encoded_input = urllib.parse.quote(ip_input)
            url = f"http://ip-api.com/json/{encoded_input}?fields=status,message,country,regionName,city,zip,lat,lon,timezone,isp,org,as,query"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                ip_data = json.load(response)
        except urllib.error.URLError as e:
            error_message = f"Network error: {e}"
        except json.JSONDecodeError:
            error_message = "Error decoding response from API."
        except socket.timeout:
            error_message = "Request timed out."
        except Exception as e:
            error_message = f"An unexpected error occurred: {type(e).__name__} - {e}"

    saved_content = None
    if error_message:
        console.print(Align.center(Text(error_message, style="bold red")))
        saved_content = f"Error looking up '{ip_input}': {error_message}"
    elif ip_data and ip_data.get("status") == "success":
        table = Table(title=f"[bold {HACKER_GREEN}]Information for {ip_data.get('query', ip_input)}[/bold {HACKER_GREEN}]",
                      box=DOUBLE, border_style=BORDER_STYLE)
        table.add_column("Property", style=MAIN_STYLE)
        table.add_column("Value", style=MAIN_STYLE)

        key_order = ['query', 'country', 'regionName', 'city', 'zip', 'lat', 'lon', 'timezone', 'isp', 'org', 'as']
        display_data = {}
        for key in key_order:
            value = ip_data.get(key, 'N/A')
            display_key = ' '.join(word.capitalize() for word in re.findall('[A-Z][^A-Z]*|[a-z][^A-Z]*', key)) or key.capitalize()
            table.add_row(display_key, str(value))
            display_data[display_key] = str(value)

        console.print(Align.center(table))

        lines = [f"IP Lookup Results for '{ip_data.get('query', ip_input)}' ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})"]
        lines.append("-" * 30)
        for key, value in display_data.items():
            lines.append(f"{key}: {value}")
        saved_content = "\n".join(lines)

    elif ip_data and ip_data.get("status") == "fail":
        message = ip_data.get('message', 'Failed to retrieve information.')
        console.print(Align.center(Text(f"API Error for '{ip_input}': {message}", style="bold red")))
        saved_content = f"API Error for '{ip_input}': {message}"
    else:
        console.print(Align.center(Text(f"Could not retrieve valid information for '{ip_input}'.", style="bold red")))
        saved_content = f"Could not retrieve valid information for '{ip_input}'."

    console.print()

    if saved_content:
        def generate_save_content():
            return saved_content
        save_output_to_file(generate_save_content, f"ip_lookup_{ip_input.replace('.', '_')}")

    instruction = Text("Press any key to return...", style=MAIN_STYLE)
    console.print(Align.center(instruction))
    while get_key() is None: time.sleep(0.1)

def scan_open_ports(target, start_port=1, end_port=1024):
    """Scan a target for open ports within a specified range."""
    clear_screen()
    print_banner()
    title = Text(f"Port Scan: {target} ({start_port}-{end_port})", style=f"bold {HACKER_GREEN}")
    console.print(Align.center(title))
    console.print()

    open_ports = []
    open_ports_data = []
    target_ip = None

    try:
        target_ip = socket.gethostbyname(target)
        console.print(Align.center(Text(f"Resolved '{target}' to {target_ip}", style="dim")))
    except socket.gaierror:
        console.print(Align.center(Text(f"Could not resolve hostname '{target}'.", style="bold red")))
        time.sleep(2)
        clear_screen()
        return []
    except Exception as e:
        console.print(Align.center(Text(f"Error resolving hostname: {e}", style="bold red")))
        time.sleep(2)
        clear_screen()
        return []

    console.print()

    with Progress(
        TextColumn("[bold cyan]Scanning Port {task.fields[port]}..."),
        BarColumn(bar_width=40),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console
    ) as progress:
        total_ports = end_port - start_port + 1
        task = progress.add_task("", total=total_ports, port=start_port)

        for port in range(start_port, end_port + 1):
            progress.update(task, advance=1, port=port)
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.settimeout(0.5)
                    result = sock.connect_ex((target_ip, port))
                    if result == 0:
                        service_name = "[dim]Unknown[/dim]"
                        try:
                            if 1 <= port <= 65535:
                                service_name = socket.getservbyport(port, 'tcp')
                        except OSError:
                            pass
                        except OverflowError:
                            service_name = "[dim]Invalid Port[/dim]"
                        open_ports.append(port)
                        open_ports_data.append((port, service_name))
            except socket.timeout:
                continue
            except OSError as e:
                console.print(f"\n[red]OS Error scanning port {port}: {e}[/red]")
                if "Too many open files" in str(e):
                    console.print("[yellow]Too many open files. Stopping scan. Try reducing the port range or check system limits.[/yellow]")
                    break
                continue
            except Exception as e:
                console.print(f"\n[red]Unexpected error scanning port {port}: {e}[/red]")
                continue

    console.print()

    if open_ports_data:
        table = Table(title=f"[bold {HACKER_GREEN}]Open Ports on {target} ({target_ip})[/{HACKER_GREEN}]",
                      show_header=True, header_style=f"bold {HACKER_GREEN}",
                      box=DOUBLE, border_style=BORDER_STYLE)
        table.add_column("Port", style=MAIN_STYLE, justify="right")
        table.add_column("Service (Common)", style=MAIN_STYLE)
        for port_num, service_name in open_ports_data:
            table.add_row(str(port_num), service_name)
        console.print(Align.center(table))
    else:
        console.print(Align.center(Text(f"[bold yellow]No open ports found on {target} ({target_ip}) in the range {start_port}-{end_port}.[/bold yellow]")))

    console.print()

    if open_ports_data:
        def generate_save_content():
            lines = [f"Open Ports Scan Results for {target} ({target_ip}) - Range {start_port}-{end_port} ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})"]
            lines.append("-" * 30)
            lines.append("Port\tService")
            for port_num, service_name in open_ports_data:
                plain_service_name = service_name.replace("[dim]", "").replace("[/dim]", "")
                lines.append(f"{port_num}\t{plain_service_name}")
            return "\n".join(lines)
        save_output_to_file(generate_save_content, f"port_scan_{target.replace('.', '_')}")

    instruction = Text("Press any key to return...", style=MAIN_STYLE)
    console.print(Align.center(instruction))
    while get_key() is None: time.sleep(0.1)

    return [p[0] for p in open_ports_data]

def parse_ping_summary(output):
    """Parses the summary statistics from ping output (Windows/Linux)."""
    summary = {
        "packets_sent": "N/A",
        "packets_received": "N/A",
        "packets_lost": "N/A",
        "loss_percent": "N/A",
        "min_rtt": "N/A",
        "avg_rtt": "N/A",
        "max_rtt": "N/A",
    }
    lines = output.strip().splitlines()

    if platform.system() == "Windows":
        for line in lines:
            line = line.strip()
            if "Packets: Sent =" in line:
                match = re.search(r"Sent = (\d+), Received = (\d+), Lost = (\d+) \((\d+)% loss\)", line)
                if match:
                    summary["packets_sent"] = match.group(1)
                    summary["packets_received"] = match.group(2)
                    summary["packets_lost"] = match.group(3)
                    summary["loss_percent"] = match.group(4) + "%"
            elif "Minimum =" in line:
                match = re.search(r"Minimum = (\d+)ms, Maximum = (\d+)ms, Average = (\d+)ms", line)
                if match:
                    summary["min_rtt"] = match.group(1) + "ms"
                    summary["max_rtt"] = match.group(2) + "ms"
                    summary["avg_rtt"] = match.group(3) + "ms"
    else:  # Linux/macOS style
        for line in lines:
            line = line.strip()
            if "packets transmitted" in line:
                match = re.search(r"(\d+) packets transmitted, (\d+) received", line)
                if match:
                    summary["packets_sent"] = match.group(1)
                    summary["packets_received"] = match.group(2)
                    sent = int(match.group(1))
                    received = int(match.group(2))
                    if sent > 0:
                        lost = sent - received
                        loss_pct = (lost / sent) * 100
                        summary["packets_lost"] = str(lost)
                        summary["loss_percent"] = f"{loss_pct:.1f}%"
            elif "rtt min/avg/max/mdev" in line or "round-trip min/avg/max/stddev" in line:
                parts = line.split('=')
                if len(parts) == 2:
                    times = parts[1].strip().split('/')[0:3]  # Get min, avg, max
                    unit = parts[1].strip().split(' ')[-1]  # Get unit (ms)
                    if len(times) == 3:
                        summary["min_rtt"] = f"{times[0]}{unit}"
                        summary["avg_rtt"] = f"{times[1]}{unit}"
                        summary["max_rtt"] = f"{times[2]}{unit}"

    return summary

def run_ping(target):
    """Runs the OS ping command against a target and displays results."""
    clear_screen()
    print_banner()
    title = Text(f"Pinging {target}", style=f"bold {HACKER_GREEN}")
    console.print(Align.center(title))
    console.print()

    system = platform.system()
    if system == "Windows":
        command = ["ping", target]
    else:
        command = ["ping", "-c", "4", target]  # Send 4 packets

    console.print(f"Executing: [cyan]{' '.join(command)}[/cyan]\n")
    ping_output = ""
    error_output = ""
    try:
        process = subprocess.run(command, capture_output=True, text=True, timeout=30)  # 30s timeout
        ping_output = process.stdout
        error_output = process.stderr

        console.print(Panel(ping_output or "[dim]No standard output.[/dim]", title="Ping Output", border_style="dim", expand=False))

        if process.returncode != 0:
            console.print(f"[yellow]Ping command exited with code {process.returncode}.[/yellow]")
            if error_output:
                console.print(Panel(error_output, title="Error Output", border_style="red", expand=False))

        summary = parse_ping_summary(ping_output)
        if any(v != "N/A" for v in summary.values()):
            summary_table = Table(title="Ping Summary", box=DOUBLE, border_style=BORDER_STYLE, show_header=False)
            summary_table.add_column("Metric", style="dim")
            summary_table.add_column("Value", style=MAIN_STYLE)
            summary_table.add_row("Packets Sent", summary["packets_sent"])
            summary_table.add_row("Packets Received", summary["packets_received"])
            summary_table.add_row("Packets Lost", f"{summary['packets_lost']} ({summary['loss_percent']})")
            summary_table.add_row("Min Round Trip", summary["min_rtt"])
            summary_table.add_row("Avg Round Trip", summary["avg_rtt"])
            summary_table.add_row("Max Round Trip", summary["max_rtt"])
            console.print(Align.center(summary_table))

    except FileNotFoundError:
        console.print(f"[bold red]Error: '{command[0]}' command not found. Is it installed and in your PATH?[/bold red]")
        ping_output = f"Error: '{command[0]}' command not found."
    except subprocess.TimeoutExpired:
        console.print("[bold red]Error: Ping command timed out after 30 seconds.[/bold red]")
        ping_output = "Error: Ping command timed out."
    except Exception as e:
        console.print(f"[bold red]Error executing ping command: {e}[/bold red]")
        ping_output = f"Error executing ping command: {e}"

    console.print()

    if ping_output:
        def generate_save_content():
            return f"Ping results for {target} ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})\nCommand: {' '.join(command)}\n\n{ping_output}\n{error_output if error_output else ''}"
        save_output_to_file(generate_save_content, f"ping_{target.replace('.', '_')}")

    instruction = Text("Press any key to return...", style=MAIN_STYLE)
    console.print(Align.center(instruction))
    while get_key() is None: time.sleep(0.1)

def parse_traceroute_hop(line):
    """Parses a single line of traceroute output to find IP and hostname."""
    line = line.strip()
    hop_match = re.match(r'^\s*(\d+)', line)
    hop_num = hop_match.group(1) if hop_match else None
    if not hop_num:
        return None

    if "Request timed out" in line or line.count('*') >= 3:
        return {"hop": hop_num, "ip": "* * *", "hostname": "Request timed out", "latency": None}

    ip_match = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', line)
    ip = ip_match.group(1) if ip_match else None
    if not ip:
        return None

    hostname = None
    host_ip_pattern = r'([\w\.\-]+)\s*[\(\[]\s*' + re.escape(ip) + r'\s*[\)\]]'
    hostname_match = re.search(host_ip_pattern, line)
    if hostname_match:
        hostname = hostname_match.group(1)

    latency_match = re.findall(r'(\d+)\s*ms', line)
    latency = "/".join(latency_match) + " ms" if latency_match else None

    return {"hop": hop_num, "ip": ip, "hostname": hostname, "latency": latency}

def get_whois_info(ip):
    """Performs a WHOIS lookup and extracts key info, falling back to raw text."""
    if not whois:
        return "[dim]python-whois not installed[/dim]"

    if not isinstance(ip, str) or not ip or ip == '* * *':
        return "[dim]Invalid IP for WHOIS[/dim]"

    try:
        import ipaddress
        ip_obj = ipaddress.ip_address(ip)
        if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_multicast or ip_obj.is_unspecified:
            return "[dim]Private/Reserved IP[/dim]"
    except ValueError:
        return "[dim]Invalid IP Format[/dim]"
    except ImportError:
        if ip.startswith('192.168.') or ip.startswith('10.') or \
           (ip.startswith('172.') and 16 <= int(ip.split('.')[1]) <= 31) or \
           ip.startswith('127.'):
            return "[dim]Private/Loopback IP[/dim]"
    except Exception:
        return "[dim]IP Check Error[/dim]"

    default_timeout = socket.getdefaulttimeout()
    w = None
    raw_whois_text = None
    try:
        try:
            socket.setdefaulttimeout(5.0)
            w = whois.whois(ip)
        except Exception as e_lookup:
            socket.setdefaulttimeout(default_timeout)
            return f"[dim]WHOIS Lookup Failed ({type(e_lookup).__name__})[/dim]"
        finally:
            socket.setdefaulttimeout(default_timeout)

        try:
            raw_whois_text = getattr(w, 'text', None)
        except Exception:
            pass

        if w is None:
            if raw_whois_text:
                first_lines = raw_whois_text.strip().splitlines()[:3]
                summary = " ".join(line.strip() for line in first_lines)
                return f"[dim]WHOIS Raw (Obj=None): {summary[:100]}...[/dim]"
            else:
                return "[dim]No WHOIS data (None)[/dim]"

        is_empty_or_error = False
        try:
            if hasattr(w, '__dict__') and not w.__dict__:
                is_empty_or_error = True
            elif getattr(w, 'status', None) == 'error' or \
                 (getattr(w, 'domain_name', None) is None and getattr(w, 'org', None) is None and getattr(w, 'nets', None) is None):
                is_empty_or_error = True
        except Exception:
            is_empty_or_error = True

        if is_empty_or_error:
            if raw_whois_text:
                first_lines = raw_whois_text.strip().splitlines()[:3]
                summary = " ".join(line.strip() for line in first_lines)
                return f"[dim]WHOIS Raw: {summary[:100]}...[/dim]"
            else:
                return "[dim]No WHOIS data[/dim]"

        org_name = None
        try:
            org_name = getattr(w, 'org', None)
            if not org_name:
                nets = getattr(w, 'nets', None)
                if nets and isinstance(nets, list) and len(nets) > 0 and isinstance(nets[0], dict):
                    org_name = nets[0].get('name')
            if not org_name:
                org_name = getattr(w, 'name', None)
        except Exception:
            if raw_whois_text:
                first_lines = raw_whois_text.strip().splitlines()[:3]
                summary = " ".join(line.strip() for line in first_lines)
                return f"[dim]WHOIS Raw: {summary[:100]}...[/dim]"
            else:
                return "[dim]WHOIS Parse Error[/dim]"

        if org_name:
            return str(org_name)
        else:
            if raw_whois_text:
                first_lines = raw_whois_text.strip().splitlines()[:3]
                summary = " ".join(line.strip() for line in first_lines)
                return f"[dim]WHOIS Raw: {summary[:100]}...[/dim]"
            else:
                return "[dim]N/A[/dim]"

    except AttributeError as e_attr:
        if raw_whois_text:
            first_lines = raw_whois_text.strip().splitlines()[:3]
            summary = " ".join(line.strip() for line in first_lines)
            return f"[dim]WHOIS Raw (Outer AttrErr): {summary[:100]}...[/dim]"
        else:
            return f"[dim]WHOIS Lib Error (Outer Attr)[/dim]"
    except Exception as e:
        error_type = type(e).__name__
        if raw_whois_text:
            first_lines = raw_whois_text.strip().splitlines()[:3]
            summary = " ".join(line.strip() for line in first_lines)
            return f"[dim]WHOIS Raw (Outer Err: {error_type}): {summary[:100]}...[/dim]"
        else:
            return f"[dim]WHOIS Error (Outer {error_type})[/dim]"

def run_traceroute(target):
    """Runs the OS traceroute command, parses hops, and adds WHOIS info."""
    clear_screen()
    print_banner()
    title = Text(f"Traceroute to {target}", style=f"bold {HACKER_GREEN}")
    console.print(Align.center(title))
    console.print()

    system = platform.system()
    if system == "Windows":
        command = ["tracert", "-d", target]
    else:
        command = ["traceroute", "-n", target]

    console.print(f"Executing: [cyan]{' '.join(command)}[/cyan]\n")
    console.print("[yellow]Traceroute running... (WHOIS lookups will add time)[/yellow]\n")

    traceroute_output = ""
    error_output = ""
    parsed_hops = []
    process_error = None

    try:
        process = subprocess.run(command, capture_output=True, text=True, timeout=120)
        traceroute_output = process.stdout
        error_output = process.stderr

        if process.returncode != 0:
            console.print(f"[yellow]Traceroute command exited with code {process.returncode}.[/yellow]")
            if error_output:
                console.print(Panel(error_output, title="Error Output", border_style="red", expand=False))

        lines = traceroute_output.strip().splitlines()
        start_line = 0
        if system == "Windows":
            for i, line in enumerate(lines):
                if not line.strip() or line.strip().startswith("Tracing route to"):
                    start_line = i + 1
                elif re.match(r'^\s*\d+', line):
                    break
            if start_line < len(lines) and "maximum of 30 hops" in lines[start_line]:
                start_line += 1

        with Progress(TextColumn("Processing hop {task.fields[hop_num]} - WHOIS lookup..."), transient=True, console=console) as progress:
            num_lines_to_process = len(lines) - start_line
            task = progress.add_task("", total=num_lines_to_process if num_lines_to_process > 0 else 1, hop_num=0)

            for i, line in enumerate(lines[start_line:]):
                hop_data = parse_traceroute_hop(line)

                if hop_data:
                    current_hop_num = hop_data.get("hop", str(i + 1))
                    progress.update(task, advance=1, hop_num=current_hop_num)

                    if hop_data["ip"] != "* * *":
                        hop_data["whois"] = get_whois_info(hop_data["ip"])
                        if not hop_data["hostname"]:
                            try:
                                hostname, _, _ = socket.gethostbyaddr(hop_data["ip"])
                                hop_data["hostname"] = hostname
                            except (socket.herror, socket.gaierror, socket.timeout, OSError):
                                pass
                    else:
                        hop_data["whois"] = ""

                    parsed_hops.append(hop_data)
                else:
                    progress.update(task, advance=1)

    except FileNotFoundError:
        process_error = f"Error: '{command[0]}' command not found. Is it installed and in your PATH?"
        traceroute_output = process_error
    except subprocess.TimeoutExpired:
        process_error = "Error: Traceroute command timed out after 120 seconds."
        traceroute_output = (traceroute_output + f"\n\n{process_error}").strip()
    except Exception as e:
        process_error = f"Error executing traceroute command: {e}"
        traceroute_output = process_error

    console.print()

    if parsed_hops:
        table = Table(title=f"Traceroute Path to {target}", box=DOUBLE, border_style=BORDER_STYLE)
        table.add_column("Hop", style="dim", justify="right")
        table.add_column("IP Address", style=MAIN_STYLE)
        table.add_column("Hostname", style=MAIN_STYLE)
        table.add_column("WHOIS Org/NetName", style="cyan")

        for hop in parsed_hops:
            hop_num_str = str(hop.get("hop", ""))
            ip_str = str(hop.get("ip", ""))
            hostname_str = str(hop.get("hostname") or "[dim]Resolving...[/dim]" if ip_str != "* * *" else hop.get("hostname", ""))
            if hostname_str == "[dim]Resolving...[/dim]" and ip_str != "* * *":
                hostname_str = ip_str
            whois_str = str(hop.get("whois", ""))

            table.add_row(hop_num_str, ip_str, hostname_str, whois_str)
        console.print(Align.center(table))
    elif process_error:
        console.print(f"[bold red]{process_error}[/bold red]")
    else:
        console.print("[yellow]Could not parse traceroute output.[/yellow]")
        if traceroute_output:
            console.print(Panel(traceroute_output, title="Raw Output", border_style="dim", expand=False))

    console.print()

    if traceroute_output:
        def generate_save_content():
            return f"Traceroute results for {target} ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})\nCommand: {' '.join(command)}\n\n{traceroute_output}\n{error_output if error_output else ''}"
        save_output_to_file(generate_save_content, f"traceroute_{target.replace('.', '_')}")

    instruction = Text("Press any key to return...", style=MAIN_STYLE)
    console.print(Align.center(instruction))
    while get_key() is None: time.sleep(0.1)

