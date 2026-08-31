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

        # selecting district / constituency
        page.get_by_role("button", name="2. Select Your District/Constituency").click()
        district_option = page.get_by_role("option", name="DAMONGO").first
        expect(district_option).to_be_visible(timeout=3000)
        district_option.click()

        # selecting training center
        page.get_by_role("button", name='3. Select your Training Center').click()
        training_center = page.get_by_role("option", name="DAMONGO CIC")
        expect(training_center).to_be_visible(timeout=3000)
        training_center.click()

        # filling coordinator name
        coordinator_name_input = page.get_by_label('Name of Coordinator')
        coordinator_name_input.clear()
        coordinator_name_input.fill("John Doe")
        expect(coordinator_name_input).to_be_visible(timeout=10000)

        # filling phone number
        phone_no = page.get_by_label("Telephone Number")
        phone_no.clear()
        phone_no.fill("0556060306")

        # filling number of disable people
        disable_no = page.get_by_label("How Many Persons with Disability Attended The Training?")
        disable_no.clear()
        disable_no.fill("0")

        #checking radio button if center is ready
        center_ready = page.get_by_role("radio", name="yes")
        center_ready.check()
        


    except Exception as e:
        print(f'having troubles visiting the link!!! - {e}')

    finally:
        page.wait_for_timeout(3000)
        page.screenshot(path="example.png", full_page=True)
        print(page.title())
        browser.close()