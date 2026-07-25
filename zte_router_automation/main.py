
import os
from playwright.sync_api import sync_playwright, expect
from InquirerPy import inquirer
from pyfiglet import Figlet
from rich import print,box
from rich.panel import Panel
from rich.console import Console
import time
import json
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()
SCRIPT_DIR = Path(__file__).parent
json_file_path = SCRIPT_DIR / "mac_address.json"


f = Figlet(font="slant",justify="left", width=200)
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

#print(mac_addr_db)

#time delay
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
    console.log(f"{mac_addr} - has been added successfully...") 


# deleting mac address
def delete_mac_address():
    whitelist_tbody = page.locator("#whitelist")
    del_mac_addr = whitelist_tbody.locator(
        f'input[type="button"][value="Delete"][id="{mac_addr.strip()}"]'
        )
    expect(del_mac_addr).to_be_visible(timeout=6000)
    del_mac_addr.click()

    #print(del_mac_addr.count())
    #print(f"{mac_addr} - has been deleted!!!")
    time_delay()
    console.log(f"{mac_addr} - has been deleted!!!")


def sync_mac_address():
    mac_addr_table = page.locator("#whitelist tr").all()
    #print("\nMac Address List")
    all_macs = []
    
    for row in mac_addr_table:
        cells = row.locator("td").all_inner_texts()
        row_data = [cell.strip() for cell in cells]
        all_macs.extend(row_data)

    if mac_addr.strip().lower() in [m.lower() for m in all_macs]:
        time_delay()
        console.log("Deleting mac address...")
        delete_mac_address()

        time_delay()
        console.log(f"then adding mac address - {mac_addr} back to whitelist...")
        add_mac_address()

    else:
        console.log('adding mac address ...')

        add_mac_address()
    


with sync_playwright() as p:
    print(f.renderText("  ZTE Router Automation"))
   
    browser = p.chromium.launch()  # headless=False helps debug visual issues
    page = browser.new_page()

    # Navigate to login page
    try:
        page.goto(router_url) # your router url e.g http://172.168.0.1/login

        # Wait for password field and fill it
        password_field = page.locator('#txtPwd')
        expect(password_field).to_be_visible(timeout=60000)
        password_field.fill(passcode) #your router web UI password
        page.get_by_text('submit').click()

        # Wait for login to complete — wait for a post-login element or a timeout
        page.wait_for_load_state("networkidle", timeout=15000)

        # Navigate to wifi section using hash change via JS
        # page.goto() on same-origin hash may not trigger SPA routing reliably
        page.evaluate("window.location.hash = '#wifi_main_chip1'")

        # Give the SPA time to render the target section
        page.wait_for_timeout(2000)

        # Try waiting for the wifi section to actually appear in the DOM
        wifi_section = page.locator('#wifi_main_chip1')
        try:
            # expect(wifi_section).to_be_visible(timeout=10000)
            # expect(wifi_section).click()
            # print("Wi-Fi section is visible.")

            nav_link = page.locator('a[href="#wifi_mac_filter"]')
            expect(nav_link).to_be_visible(timeout=10000)
            nav_link.click()

            whitelist_switch = page.locator("#mac_filter_switch_white")
            
            hostname = ""
            mac_addr = None

            
            try:
                hostname = input("[+]Enter PC's Hostname : ").strip()
                mac_addr = mac_addr_db[hostname]
            except Exception as e:
                print(f"{hostname} has no mac address or invalid hostname= {hostname}")


            whitelist_txtbox = page.locator("#texNewMacAddressWhiteList")
            if mac_addr is None:
                console.log("[red]No mac address found for the given hostname. Please check the hostname and try again.[/red]")

            elif whitelist_switch.is_checked():
                print("whitelist is checked.")

                sync_mac_address()

            else:
                print("whitelist is not checked...")
                whitelist_switch.check()
                mac_filter_form = page.locator("#macFilterForm")
                apply_btn = mac_filter_form.locator('input[type="submit"][value="Apply"]')
                expect(apply_btn).to_be_visible(timeout=6000)
                apply_btn.click()

                time_delay()
                page.wait_for_load_state("networkidle", timeout=15000)
                sync_mac_address()
                


        
            
        except Exception as e:
            # Fallback: try clicking the sidebar/nav link if direct hash didn't work
            print(f"Direct hash navigation failed, trying nav link... {e}")
            #nav_link = page.locator('a[href="#wifi_main_chip1"]')
            
    except Exception as e:
        print(f"having troubles visiting the link!!! - {e}")

    finally:
        page.wait_for_timeout(3000)
        page.screenshot(path="example.png", full_page=True)
        print(page.title())
        browser.close()
