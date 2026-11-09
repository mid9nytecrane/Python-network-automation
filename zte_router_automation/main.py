import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, expect
from pyfiglet import Figlet

# FIX: removed `from rich import print` (it shadowed the built-in print and crashed with
# MarkupError when text such as an exception message contained "[...]").
# FIX: removed unused import `Confirm`.
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

SCRIPT_DIR = Path(__file__).parent

# FIX: load_dotenv() with no path only finds .env in the terminal's working directory.
load_dotenv(SCRIPT_DIR / ".env")

json_file_path = SCRIPT_DIR / "mac_address.json"

fig = Figlet(font="slant", justify="left", width=200)
console = Console()

passcode = os.getenv("PASSWORD")
router_url = os.getenv("ROUTER_URL")

# FIX: nothing validated these, so page.goto(None) / fill(None) crashed later.
missing = [n for n, v in (("ROUTER_URL", router_url), ("PASSWORD", passcode)) if not v]
if missing:
    raise SystemExit(f"Missing {', '.join(missing)} in your .env file.")

# FIX: the old except blocks only printed a message, so the script carried on and later
# died with NameError: mac_addr_db is not defined. Exit instead.
try:
    with open(json_file_path, "r") as file:
        mac_addr_db = json.load(file)
except FileNotFoundError:
    raise SystemExit("mac_address.json not found or file path isn't correct.")
except json.JSONDecodeError:
    raise SystemExit("Invalid JSON structure detected (check commas/quotes).")

if not mac_addr_db:
    raise SystemExit("mac_address.json is empty, add at least one hostname.")


def log(msg: str, markup: bool = False) -> None:
    """console.log wrapper. markup=False prints text literally (safe for exceptions/hostnames)."""
    console.log(msg, markup=markup)


# time delay
def time_delay(seconds: float = 1) -> None:
    time.sleep(seconds)


def click_submit(page) -> None:
    """
    FIX: page.get_by_text('submit') can match several elements and raise a strict-mode
    error. Restrict to visible ones and take the first. If it clicks the wrong thing,
    replace with the button's real id.
    """
    page.get_by_text("submit").locator("visible=true").first.click()


# ---------------------------------------------------------------------------
# Whitelist table helpers
# FIX (biggest bug): page, whitelist_txtbox, mac_addr and action are now LOCAL variables
# inside main(), but the functions below read them as globals -> NameError on every action.
# Everything they need is now passed in as a parameter.
# ---------------------------------------------------------------------------

def get_whitelist_cells(page) -> list:
    """Return the text of every cell in the whitelist table."""
    all_cells = []
    for row in page.locator("#whitelist tr").all():
        cells = row.locator("td").all_inner_texts()
        all_cells.extend(cell.strip() for cell in cells)
    return all_cells


def find_in_whitelist(page, mac: str):
    """
    Case-insensitive search. Returns the MAC exactly as the ROUTER spells it
    (needed for the Delete button id), or None if it isn't whitelisted.
    """
    target = mac.strip().lower()
    for cell in get_whitelist_cells(page):
        if cell.lower() == target:
            return cell
    return None


# adding mac address
def add_mac_address(page, mac: str) -> None:
    whitelist_txtbox = page.locator("#texNewMacAddressWhiteList")

    # FIX: wait until the box is visible BEFORE filling it (was fill() then expect()).
    expect(whitelist_txtbox).to_be_visible(timeout=6000)
    whitelist_txtbox.fill(mac)

    whitelist_form = page.locator("#setWhiteListFrm")
    apply_btn = whitelist_form.locator('input[type="submit"]')
    expect(apply_btn).to_be_visible(timeout=6000)
    apply_btn.click()

    time_delay()

    # FIX: confirm it really landed instead of always claiming success.
    if find_in_whitelist(page, mac):
        log(f"[green]{mac} - has been added successfully...[/green]", markup=True)
    else:
        log(f"[yellow]WARNING: {mac} was submitted but is not in the whitelist table.[/yellow]", markup=True)


# deleting mac address
def delete_mac_address(page, router_mac: str) -> None:
    """`router_mac` must be the MAC as the router shows it (the Delete button id uses it)."""
    whitelist_tbody = page.locator("#whitelist")
    del_mac_addr = whitelist_tbody.locator(
        f'input[type="button"][value="Delete"][id="{router_mac.strip()}"]'
    )
    expect(del_mac_addr).to_be_visible(timeout=6000)
    del_mac_addr.click()

    # FIX: wait for the row to actually disappear instead of a blind sleep.
    # (Any JS confirm popup is auto-accepted by the dialog handler set in main().)
    expect(del_mac_addr).to_have_count(0, timeout=10000)
    log(f"[green]{router_mac} - has been deleted!!![/green]", markup=True)


def sync_mac_address(page, mac: str) -> None:
    """Add the MAC; if it's already whitelisted, delete it first then add it back."""
    existing = find_in_whitelist(page, mac)
    if existing:
        time_delay()
        log("Deleting mac address...")
        delete_mac_address(page, existing)

        time_delay()
        log(f"then adding mac address - {mac} back to whitelist...")
        add_mac_address(page, mac)
    else:
        log("adding mac address...")
        add_mac_address(page, mac)


def remove_mac_address_flow(page, mac: str) -> None:
    existing = find_in_whitelist(page, mac)
    if existing:
        delete_mac_address(page, existing)
    else:
        log(f"[yellow]{mac} is not in the whitelist - nothing to delete.[/yellow]", markup=True)


def enable_whitelist(page, whitelist_switch) -> None:
    """Turn on whitelist mode and apply it."""
    whitelist_switch.check()
    mac_filter_form = page.locator("#macFilterForm")
    apply_btn = mac_filter_form.locator('input[type="submit"][value="Apply"]')
    expect(apply_btn).to_be_visible(timeout=6000)
    apply_btn.click()

    time_delay()
    page.wait_for_load_state("networkidle", timeout=15000)
    # FIX: verify the switch really stuck before continuing.
    expect(whitelist_switch).to_be_checked(timeout=10000)


def run_action(page, action: str, mac: str) -> None:
    """
    FIX: this used to read a global `action`, and the whitelist-enabled check lived in
    main() duplicated for both branches. It now lives here, once.
    """
    whitelist_switch = page.locator("#mac_filter_switch_white")

    if whitelist_switch.is_checked():
        log("whitelist is checked.")
    else:
        log("whitelist is not checked...")
        if action == "2":
            log(f"[yellow]Whitelist isn't enabled - {mac} can't be in it, nothing to delete.[/yellow]", markup=True)
            return
        enable_whitelist(page, whitelist_switch)

    if action == "1":
        sync_mac_address(page, mac)
    elif action == "2":
        remove_mac_address_flow(page, mac)


# ---------------------------------------------------------------------------
# Connected devices
# ---------------------------------------------------------------------------

# getting connected devices
def get_connected_devices(page) -> list:
    all_devices = []
    for row in page.locator("#deviceInfoWhite tr").all():
        cells = row.locator("td").all_inner_texts()
        row_data = [cell.strip() for cell in cells]
        # FIX: was `len(row_data) >= 2`, but the callers read row_data[2] -> IndexError
        # on a 2-cell row. Require 3 cells so index 2 always exists.
        if len(row_data) >= 3:
            all_devices.append(row_data)
    return all_devices


def mac_exists_in_connected_devices(page, mac: str) -> bool:
    # NOTE: currently unused; handy if you later want "is this PC online?" checks.
    connected_macs = [row[2].lower() for row in get_connected_devices(page)]
    return mac.strip().lower() in connected_macs


# table showing connected devices
def display_connected_devices_table(page) -> None:
    table = Table(title="\nConnected Devices", box=box.ROUNDED)
    table.add_column("#", justify="right", style="cyan")
    table.add_column("Hostname", style="bold purple")
    table.add_column("MAC Address")

    for i, row_data in enumerate(get_connected_devices(page), start=1):
        hostname = row_data[1].replace("\xa0", " ")
        mac = row_data[2]
        # markup safety: a hostname like "[x]" must not be parsed as rich markup
        table.add_row(str(i), rich_escape(hostname), rich_escape(mac))

    console.print(table)


def rich_escape(text: str) -> str:
    from rich.markup import escape
    return escape(text)


def display_known_hosts_table(page) -> None:
    # FIX: this used to be built ONCE before the loop, so after an add/delete the
    # "Whitelisted" column was stale. It now re-reads the router table each time.
    lowered_cells = [c.lower() for c in get_whitelist_cells(page)]

    table = Table(title="Known Hosts", box=box.ROUNDED)
    table.add_column("#", justify="right", style="cyan")
    table.add_column("Hostname", style="bold")
    table.add_column("MAC Address")
    table.add_column("Whitelisted", justify="center")

    for i, (hostname, mac) in enumerate(mac_addr_db.items(), start=1):
        is_whitelisted = mac.strip().lower() in lowered_cells
        status = "[green]Yes[/green]" if is_whitelisted else "[dim]No[/dim]"
        table.add_row(str(i), rich_escape(hostname), rich_escape(mac), status)

    console.print(table)


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

# Prompts once per call; the continuous loop lives in main().
def prompt_action() -> str:
    console.print(
        Panel.fit(
            "[bold cyan][ + ] ZTE Router MAC Whitelist Manager [ + ] [/bold cyan]",
            box=box.DOUBLE_EDGE,
        )
    )

    console.print(
        "[bold][ 1 ] Add a PC to the whitelist\n"
        "[ 2 ] Remove a PC from the whitelist\n"
        "[ 3 ] Show connected devices\n"
        "[ done ] Exit[/bold]"
    )

    return Prompt.ask(
        "\n  [bold][ + ] Select Option :[/bold]",
        choices=["1", "2", "3", "done"],
    )


def prompt_hostname() -> str:
    hostnames = list(mac_addr_db.keys())
    return Prompt.ask(
        "  [bold][ + ] Enter PC's hostname [/bold]",
        choices=hostnames,
        show_choices=False,
    )


# ---------------------------------------------------------------------------
# Browser steps
# ---------------------------------------------------------------------------

def login(page) -> None:
    page.goto(router_url)

    password_field = page.locator("#txtPwd")
    expect(password_field).to_be_visible(timeout=60000)
    password_field.fill(passcode)
    click_submit(page)

    page.wait_for_load_state("networkidle", timeout=15000)


def open_mac_filter_page(page) -> None:
    page.evaluate("window.location.hash = '#wifi_main_chip1'")
    page.wait_for_timeout(2000)

    nav_link = page.locator('a[href="#wifi_mac_filter"]')
    expect(nav_link).to_be_visible(timeout=10000)
    nav_link.click()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    console.print(fig.renderText("  ZTE Router Automation"), markup=False)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # headless=False shows the automation visually
        page = browser.new_page()

        # Auto-accept router JS confirm()/alert() popups (e.g. on Delete).
        page.on("dialog", lambda dialog: dialog.accept())

        try:
            # Login + navigation run ONCE; every menu action reuses this session.
            login(page)
            open_mac_filter_page(page)

            while True:
                display_known_hosts_table(page)
                action = prompt_action()

                if action == "done":
                    console.print("[bold green]Session ended.[/bold green]")
                    break

                # FIX: each action has its own try/except, so one failed action
                # (timeout, missing element...) no longer kills the whole session.
                try:
                    if action == "3":
                        display_connected_devices_table(page)
                        continue

                    # actions "1" and "2" need a target PC first
                    hostname = prompt_hostname()
                    # FIX: mac_addr_db[hostname] raises KeyError and never returns None,
                    # so the old `is None` check was unreachable. .get() makes it work.
                    mac_addr = mac_addr_db.get(hostname)
                    if not mac_addr:
                        log("[red]No mac address found for that hostname. Check it and try again.[/red]", markup=True)
                        continue

                    run_action(page, action, mac_addr.strip())

                except Exception as e:
                    # FIX: the old handler said "Direct hash navigation failed" for ANY error.
                    log(f"[red]Action failed: {type(e).__name__}: {rich_escape(str(e))}[/red]", markup=True)

        except Exception as e:
            log(f"[red]Could not log in / open the MAC filter page: {rich_escape(str(e))}[/red]", markup=True)

        finally:
            # FIX: guarded so a failing screenshot can't skip browser.close().
            try:
                page.wait_for_timeout(3000)
                page.screenshot(path=str(SCRIPT_DIR / "example.png"), full_page=True)
                log(f"Page title: {page.title()}")
            except Exception:
                pass
            finally:
                browser.close()

    input("\nAll done, Press Enter to close...")


# FIX: main() was defined but never called, so running the file did nothing at all.
if __name__ == "__main__":
    main()