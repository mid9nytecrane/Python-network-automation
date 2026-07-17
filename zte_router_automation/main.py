from playwright.sync_api import sync_playwright, expect

passcode = "Sh8448saqqara@99"
mac_addr = "14:B5:CD:2C:8F:2D"

with sync_playwright() as p:
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
            print("\n=========== Debugging =================")
            print('check debug for if statement')

            #whitelist_switch = page.get_by_role("radio", name="mac_filter_switch")
            #whitelist_switch = page.get_by_test_id("mac_filter_switch_white")
            whitelist_switch = page.locator("#mac_filter_switch_white")
            print(whitelist_switch)

            if whitelist_switch.is_checked():
                print("whitelist is checked.")
                whitelist_txtbox = page.locator("#texNewMacAddressWhiteList")
                whitelist_txtbox.fill(mac_addr)
                expect(whitelist_txtbox).to_be_visible(timeout=6000)
                print(page.locator("input[type=submit]").all_inner_texts())
                page.locator("input[value=Apply]").click()
            else:
                print("whitelist is not checked...")
                whitelist_switch.check()
                page.get_by_text("submit").click()

            # whitelist_switch = page.get_by_role("checkbox", name="White List")
            # expect(whitelist_switch).to_be_visible(timeout=10000)
            # is_active = whitelist_switch.is_checked()
            # if is_active:
            #     print("whitelist is checked")
            # else:
            #     print("whitelist is not checked")
            
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
