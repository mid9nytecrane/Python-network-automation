import re
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

        # adding comment
        comment_sec = page.get_by_role("textbox", name="8. Observations/Comments")
        comment_sec.fill("no comment")

        # checking courses
        course_select = ["UX Designer","Cyber Security", "Data Analyst", "IT Support", \
                        "Project Management", "AI Essentials", "AI Professional",
                        "Introduction To Programming", "Frontend Development"
                         ]
        #course_check = page.get_by_role("checkbox", name="UX Designer").check()
        for course in course_select:
            page.get_by_role("checkbox", name=course).check()

        #specifying course and their number of attendees
        course_taken = page.get_by_role(
            "textbox",
            name="Specify The Course(s) Taken Today and Indicate the Number of Participants for Each Course (e.g., IT Support – 10, UX Designer – 15, Data Analytics – 8 etc...)"
        )

        courses = []
        while True:
            course = input("Enter course with number of participants (or 'done' to finish): ")
        
            if course.lower() == 'done':
                break
            if course:
                courses.append(course)
        
        print(courses)
        formatted_text = ", ".join(courses)
        print(formatted_text)
        course_taken.fill(formatted_text)

        # Number of attendees per day
        attendees = input('Enter the number of Attendees Today: ')
        attendees_no = page.get_by_label("What is the Total Number of Attendees Today?")
        attendees_no.fill(attendees)

        # Number of males and females
        females_count = input("Enter number of Female(s): ")
        male_count = input("Enter number of Male(s): ")

        formatted_gender_text = f"Male(s) - {male_count}, Female(s) - {females_count}"

        gender_count = page.get_by_role('textbox', name="What Is the Total Number of Male/Female Participants as of Today? (e.g. Male(s) -15, Female(s) 10)")
        gender_count.fill(formatted_gender_text)



    except Exception as e:
        print(f'having troubles visiting the link!!! - {e}')

    finally:
        page.wait_for_timeout(3000)
        page.screenshot(path="example.png", full_page=True)
        print(page.title())
        browser.close()