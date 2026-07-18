

from playwright.sync_api import sync_playwright, expect
from InquirerPy import inquirer
from pyfiglet import Figlet
from rich import print,box
from rich.panel import Panel

from InquirerPy import inquirer


f = Figlet(font="slant", width=200)


passcode = "Sh8448saqqara@99"
MAC_ADDRESS= "14:B5:CD:28:B8:CB"

mac_addr_db = {
    "OMCP-DMG-001": "14:B5:CD:2E:26:01",
    "OMCP-DMG-002": "20:BD:1D:8C:C1:DE",
    "OMCP-DMG-003": "20:BD:1D:11:D5:69",
    "OMCP-DMG-004": "14:B5:CD:24:C5:51"
}

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
    print(f"{mac_addr} - has been added successfully...") 


# deleting mac address
def delete_mac_address():
    whitelist_tbody = page.locator("#whitelist")
    del_mac_addr = whitelist_tbody.locator(
        f'input[type="button"][value="Delete"][id="{mac_addr.strip()}"]'
        )
    expect(del_mac_addr).to_be_visible(timeout=6000)
    del_mac_addr.click()

    print(del_mac_addr.count())
    print(f"{mac_addr} - has been deleted!!!")



with sync_playwright() as p:
    print(Panel.fit(f.renderText("ZTE Router Automation"),box=box.HEAVY, border_style="cyan"))
    #print(Panel.fit("hello world", title="hello cruel"))
    

    browser = p.chromium.launch(headless=False)  # headless=False helps debug visual issues
    page = browser.new_page()

    # Navigate to login page
    try:
        page.goto("http://192.168.0.1/index.html#login")

        # Wait for password field and fill it
        password_field = page.locator('#txtPwd')
        expect(password_field).to_be_visible(timeout=60000)
        password_field.fill(passcode)
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

            #expect(wifi_section).to_be_visible(timeout=10000)
            # print("\n=========== Debugging =================")
            # print('check debug for if statement')

            #whitelist_switch = page.get_by_role("radio", name="mac_filter_switch")
            #whitelist_switch = page.get_by_test_id("mac_filter_switch_white")
            whitelist_switch = page.locator("#mac_filter_switch_white")
            #print(whitelist_switch)

            if whitelist_switch.is_checked():
                print("whitelist is checked.")
                whitelist_txtbox = page.locator("#texNewMacAddressWhiteList")
                hostname = ""

                try:
                    hostname = input("[+]Enter PC's MAC Adress: ").strip()
                    mac_addr = mac_addr_db[hostname]
                except Exception as e:
                    print(f"{hostname} has no mac address or invalid hostname= {hostname}")

                #Adding mac address
                

                #checking if mac address exist in whitelist
                mac_addr_table = page.locator("#whitelist tr").all()
                print("\nMac Address List")
                # print(mac_addr_table)
                all_macs = []

                for row in mac_addr_table:
                    cells = row.locator("td").all_inner_texts()
                    row_data = [cell.strip() for cell in cells]
                    #print(row_data)
                    all_macs.extend(row_data)
                    
                #print(all_macs)

                if mac_addr.strip().lower() in [m.lower() for m in all_macs]:
                    print('mac address exist')
                    # okay_btn = page.get_by_role("button", name="OK")
                    # expect(okay_btn).to_be_visible(timeout=6000)
                    # okay_btn.click()

                    #DELETING MAC ADDRESS
                    print('deleting mac address...')
                    delete_mac_address()

                    print("then adding mac address back")
                    add_mac_address()
                else:
                    print('mac addres does not exist')
                    print('adding mac address ...')

                    add_mac_address()


            else:
                print("whitelist is not checked...")
                whitelist_switch.check()

                page.get_by_text("submit").click()

          
            
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
