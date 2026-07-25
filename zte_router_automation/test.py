import os
from playwright.sync_api import sync_playwright, expect
from pyfiglet import Figlet
from rich import print, box
from rich.panel import Panel
from rich.console import Console
from rich.prompt import Prompt, Confirm
import time
import json

from dotenv import load_dotenv

load_dotenv()

f = Figlet(font="slant", width=200)
console = Console()

passcode = os.getenv("PASSWORD")
router_url = os.getenv("ROUTER_URL")


try:
    with open("zte_router_automation/mac_address.json", "r") as file:
        mac_addr_db = json.load(file)
except FileNotFoundError:
    console.print("[bold red]File not found or file path isn't correct.[/bold red]")
    raise SystemExit(1)
except json.JSONDecodeError:
    console.print("[bold red]Invalid JSON structure detected, (check commas/quotes).[/bold red]")
    raise SystemExit(1)


# time delay
def time_delay():
    time.sleep(2)


# adding mac address
def add_mac_address():
    whitelist_txtbox.fill(mac_addr)
    expect(whitelist_txtbox).to_be_visible(timeout=6000)

    # The Apply button is <input type="submit">, not <button>,
    # so get_by_role("button") won't find it.
    # Scope to the form and target the submit input directly.
    whitelist_form = page.locator("#setWhiteListFrm")
    apply_btn = whitelist_form.locator('input[type="submit"]')
    expect(apply_btn).to_be_visible(timeout=6000)
    apply_btn.click()

    time_delay()
    console.print(f"[bold green]✔ {mac_addr} has been added successfully.[/bold green]")


# deleting mac address
def delete_mac_address():
    whitelist_tbody = page.locator("#whitelist")
    del_mac_addr = whitelist_tbody.locator(
        f'input[type="button"][value="Delete"][id="{mac_addr.strip()}"]'
    )
    expect(del_mac_addr).to_be_visible(timeout=6000)
    del_mac_addr.click()

    time_delay()
    console.print(f"[bold yellow]✔ {mac_addr} has been deleted.[/bold yellow]")


def get_all_macs():
    mac_addr_table = page.locator("#whitelist tr").all()
    all_macs = []
    for row in mac_addr_table:
        cells = row.locator("td").all_inner_texts()
        row_data = [cell.strip() for cell in cells]
        all_macs.extend(row_data)
    return all_macs


def prompt_action_and_host():
    """Ask the user, via rich, whether to add or remove a PC, then which host."""
    console.print(
        Panel.fit(
            "[bold cyan]ZTE Router MAC Whitelist Manager[/bold cyan]",
            box=box.ROUNDED,
        )
    )

    action = Prompt.ask(
        "[bold]What would you like to do?[/bold]",
        choices=["add", "remove"],
        default="add",
    )

    hostnames = list(mac_addr_db.keys())
    console.print(
        Panel(
            "\n".join(f"[cyan]{i+1}.[/cyan] {name}" for i, name in enumerate(hostnames)),
            title="Known Hosts",
            box=box.ROUNDED,
        )
    )

    hostname = Prompt.ask("[bold]Enter PC's hostname[/bold]", choices=hostnames, show_choices=False)
    return action, hostname


with sync_playwright() as p:
    print(f.renderText("ZTE Router Automation"))

    action, hostname = prompt_action_and_host()
    mac_addr = mac_addr_db[hostname]

    console.print(
        Panel.fit(
            f"Action: [bold]{action.upper()}[/bold]\nHostname: [bold]{hostname}[/bold]\nMAC: [bold]{mac_addr}[/bold]",
            title="Summary",
            box=box.ROUNDED,
        )
    )

    if not Confirm.ask("Proceed with this action?", default=True):
        console.print("[yellow]Cancelled by user.[/yellow]")
        raise SystemExit(0)

    browser = p.chromium.launch(headless=False)  # headless=False helps debug visual issues
    page = browser.new_page()

    try:
        with console.status("[bold green]Logging in to router..."):
            page.goto(router_url)  # your router url e.g http://172.168.0.1/login

            password_field = page.locator('#txtPwd')
            expect(password_field).to_be_visible(timeout=60000)
            password_field.fill(passcode)
            page.get_by_text('submit').click()

            page.wait_for_load_state("networkidle", timeout=15000)

            page.evaluate("window.location.hash = '#wifi_main_chip1'")
            page.wait_for_timeout(2000)

        wifi_section = page.locator('#wifi_main_chip1')
        try:
            nav_link = page.locator('a[href="#wifi_mac_filter"]')
            expect(nav_link).to_be_visible(timeout=10000)
            nav_link.click()

            whitelist_switch = page.locator("#mac_filter_switch_white")

            if whitelist_switch.is_checked():
                console.print("[green]Whitelist is enabled.[/green]")
                whitelist_txtbox = page.locator("#texNewMacAddressWhiteList")

                all_macs = get_all_macs()
                mac_exists = mac_addr.strip().lower() in [m.lower() for m in all_macs]

                if action == "add":
                    if mac_exists:
                        console.print(
                            f"[yellow]{mac_addr} already exists in whitelist — removing and re-adding.[/yellow]"
                        )
                        time_delay()
                        delete_mac_address()
                        time_delay()
                        add_mac_address()
                    else:
                        time_delay()
                        add_mac_address()

                elif action == "remove":
                    if mac_exists:
                        time_delay()
                        delete_mac_address()
                    else:
                        console.print(
                            f"[red]{mac_addr} is not in the whitelist — nothing to remove.[/red]"
                        )

            else:
                console.print("[red]Whitelist is not enabled.[/red]")
                if Confirm.ask("Enable whitelist mode now?", default=False):
                    whitelist_switch.check()
                    page.get_by_text("submit").click()

        except Exception as e:
            console.print(f"[bold red]Navigation failed:[/bold red] {e}")

    except Exception as e:
        console.print(f"[bold red]Trouble reaching the router:[/bold red] {e}")

    finally:
        page.wait_for_timeout(3000)
        page.screenshot(path="example.png", full_page=True)
        console.print(f"[dim]{page.title()}[/dim]")
        browser.close() 