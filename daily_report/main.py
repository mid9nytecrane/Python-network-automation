from playwright.sync_api import sync_playwright, expect,Page

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    try:
        page.goto("https://forms.cloud.microsoft/pages/responsepage.aspx?id=yhSrr2CrpkKKKf8QFCTzGG5I3GM8yb9CtKmMJNFSqupUOEo5SzBGSzNMSUlKMTVHOEIzVzg0SDhMVy4u&route=shorturl")


        page.get_by_role("button", name="Start now").click()

        page.wait_for_load_state("networkidle", timeout=15000)

        #selecting a region
        page.get_by_role("button", name="1. Select your Region").click()
        region_option = page.get_by_role("option", name="Savannah")
        expect(region_option).to_be_visible(timeout=3000)
        region_option.click()

        # filling coordinator name
        coordinator_name_input = page.get_by_label('Name of Coordinator')
        coordinator_name_input.clear()
        coordinator_name_input.fill("John Doe")

        expect(coordinator_name_input).to_be_visible(timeout=10000)


    except Exception as e:
        print(f'having troubles visiting the link!!! - {e}')

    finally:
        page.wait_for_timeout(3000)
        page.screenshot(path="example.png", full_page=True)
        print(page.title())
        browser.close()