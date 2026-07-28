import os
from playwright.sync_api import sync_playwright, expect
from InquirerPy import inquirer
from pyfiglet import Figlet
from rich import print, box
from rich.panel import Panel
from rich.table import Table
from rich.console import Console
from rich.prompt import Prompt, Confirm
import time
import json
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()
SCRIPT_DIR = Path(__file__).parent
json_file_path = SCRIPT_DIR / "mac_address.json"


f = Figlet(font="slant", justify="left", width=200)
console = Console()

passcode = os.getenv("PASSWORD")
router_url = os.getenv("ROUTER_URL")


try:
    with open(json_file_path, "r") as file:
        mac_addr_db = json.load(file)
except FileNotFoundError:
    print("File not found or file path isn't correct.")
except json.JSONDecodeError:
    print("Invalid JSON strucute detected, (check commas/qoutes).")


# time delay
def time_delay():
    time.sleep(2)


# adding mac address
def add_mac_address():
    whitelist_txtbox.fill(mac_addr)
    expect(whitelist_txtbox).to_be_visible(timeout=6000)

    whitelist_form = page.locator("#setWhiteListFrm")
    apply_btn = whitelist_form.locator('input[type="submit"]')
    expect(apply_btn).to_be_visible(timeout=6000)
    apply_btn.click()

    time_delay()
    console.log(f"{mac_addr} - has been added successfully...")


# deleting mac address
def delete_mac_address():
    whitelist_tbody = page.locator("#whitelist")
    del_mac_addr = whitelist_tbody.locator(
        f'input[type="button"][value="Delete"][id="{mac_addr.strip()}"]'
    )
    expect(del_mac_addr).to_be_visible(timeout=6000)
    del_mac_addr.click()

    time_delay()
    console.log(f"{mac_addr} - has been deleted!!!")


# NEW: pulled the raw "read every cell out of #whitelist" step into its
# own function. Both the status table AND mac_exists_in_whitelist() need
# this same raw list, so it's read once per call site instead of having
# two separate near-identical row-parsing loops drift apart over time.
def get_whitelist_cells():
    mac_addr_table = page.locator("#whitelist tr").all()
    all_cells = []

    for row in mac_addr_table:
        cells = row.locator("td").all_inner_texts()
        row_data = [cell.strip() for cell in cells]
        all_cells.extend(row_data)

    return all_cells


def mac_exists_in_whitelist():
    all_cells = get_whitelist_cells()
    return mac_addr.strip().lower() in [m.lower() for m in all_cells]


def sync_mac_address():
    if mac_exists_in_whitelist():
        time_delay()
        console.log("Deleting mac address...")
        delete_mac_address()

        time_delay()
        console.log(f"then adding mac address - {mac_addr} back to whitelist...")
        add_mac_address()
    else:
        console.log("adding mac address ...")
        add_mac_address()


def remove_mac_address_flow():
    if mac_exists_in_whitelist():
        delete_mac_address()
    else:
        console.log(f"[yellow]{mac_addr} is not in the whitelist - nothing to delete.[/yellow]")


def run_action():
    if action == "1":
        sync_mac_address()
    elif action == "2":
        remove_mac_address_flow()


# NEW: builds and prints a table of every known host from mac_address.json
# next to whether its mac is currently sitting in the router's whitelist.
# `current_whitelist_cells` is the raw cell dump from get_whitelist_cells(),
# passed in once so this doesn't have to re-query the page for every host.
def display_known_hosts_table(current_whitelist_cells):
    lowered_cells = [c.lower() for c in current_whitelist_cells]

    table = Table(title="Known Hosts", box=box.ROUNDED)
    table.add_column("#", justify="right", style="cyan")
    table.add_column("Hostname", style="bold")
    table.add_column("MAC Address")
    table.add_column("Whitelisted", justify="center")

    for i, (hostname, mac) in enumerate(mac_addr_db.items(), start=1):
        is_whitelisted = mac.strip().lower() in lowered_cells
        status = "[green]Yes[/green]" if is_whitelisted else "[dim]No[/dim]"
        table.add_row(str(i), hostname, mac, status)

    console.print(table)


def prompt_action_and_host():
    console.print(
        Panel.fit(
            "[bold cyan][ + ] ZTE Router MAC Whitelist Manager [ + ] [/bold cyan]",
            box=box.ROUNDED,
        )
    )

    console.print(
        "[bold][ 1 ] Add a PC to the whitelist\n[ 2 ] Remove a PC from the whitelist[/bold]"
    )

    action = Prompt.ask(
        "\n  [bold][ + ] Select Option :[/bold]",
        choices=["1", "2"],
    )

    hostnames = list(mac_addr_db.keys())
    hostname = Prompt.ask("  [bold][ + ] Enter PC's hostname [/bold]", choices=hostnames, show_choices=False)
    return action, hostname


with sync_playwright() as p:
    print(f.renderText("  ZTE Router Automation"))

    browser = p.chromium.launch()
    page = browser.new_page()

    try:
        page.goto(router_url)

        password_field = page.locator('#txtPwd')
        expect(password_field).to_be_visible(timeout=60000)
        password_field.fill(passcode)
        page.get_by_text('submit').click()

        page.wait_for_load_state("networkidle", timeout=15000)

        page.evaluate("window.location.hash = '#wifi_main_chip1'")
        page.wait_for_timeout(2000)

        try:
            nav_link = page.locator('a[href="#wifi_mac_filter"]')
            expect(nav_link).to_be_visible(timeout=10000)
            nav_link.click()

            whitelist_switch = page.locator("#mac_filter_switch_white")
            whitelist_txtbox = page.locator("#texNewMacAddressWhiteList")

            # MOVED UP: read the live whitelist table BEFORE prompting, so
            # the "Known Hosts" table can show each host's current status
            # instead of just listing names blind.
            current_whitelist_cells = get_whitelist_cells()
            display_known_hosts_table(current_whitelist_cells)

            action, hostname = prompt_action_and_host()
            mac_addr = mac_addr_db[hostname]

            if mac_addr is None:
                console.log("[red]No mac address found for the given hostname. Please check the hostname and try again.[/red]")

            elif whitelist_switch.is_checked():
                print("whitelist is checked.")
                run_action()

            else:
                print("whitelist is not checked...")

                if action == "2":
                    console.log(f"[yellow]Whitelist isn't enabled - {mac_addr} can't be in it, nothing to delete.[/yellow]")
                else:
                    whitelist_switch.check()
                    mac_filter_form = page.locator("#macFilterForm")
                    apply_btn = mac_filter_form.locator('input[type="submit"][value="Apply"]')
                    expect(apply_btn).to_be_visible(timeout=6000)
                    apply_btn.click()

                    time_delay()
                    page.wait_for_load_state("networkidle", timeout=15000)
                    run_action()

        except Exception as e:
            print(f"Direct hash navigation failed, trying nav link... {e}")

    except Exception as e:
        print(f"having troubles visiting the link!!! - {e}")

    finally:
        page.wait_for_timeout(3000)
        page.screenshot(path="example.png", full_page=True)
        print(page.title())
        browser.close()