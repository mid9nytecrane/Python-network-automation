import os
import re
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, expect

SCRIPT_DIR = Path(__file__).parent  # renamed: this is a directory, not a script path
load_dotenv(SCRIPT_DIR / ".env")
def require_env(key: str) -> str:
    """Return a .env value as a guaranteed str, or exit with a clear message."""
    value = os.getenv(key)
    if not value:  # covers both None and an empty string
        sys.exit(f"Missing value in .env: {key}")
    return value  # Pylance now sees a plain str, so the error disappears


region = require_env("REGION")
district = require_env("DISTRICT")
center = require_env("CENTER")
coordinator = require_env("COORDINATOR")
phone = require_env("PHONE")
form_url = require_env("WEB_URL")
disability_count = "0"


def ask_int(prompt: str) -> int:
    """FIX 7: keep asking until the user enters a valid whole number."""
    while True:
        value = input(prompt).strip()
        if value.isdigit():
            return int(value)
        print("Please enter a whole number.")


# --- FIX 5: gather ALL input BEFORE opening the browser ---
courses = []
while True:
    entry = input("Enter course with number of participants, e.g. 'IT Support - 10' (or 'done'): ").strip()
    if entry.lower() == "done":
        break
    if entry:
        courses.append(entry)

if not courses:
    sys.exit("No courses entered. Nothing to report.")

# FIX 2: derive the checkbox names from what was actually typed.
# "IT Support - 10" or "IT Support – 10" -> "IT Support"
course_names = [re.split(r"\s*[–—-]\s*", c, maxsplit=1)[0].strip() for c in courses]
formatted_courses = ", ".join(courses)

attendees = ask_int("Enter the number of Attendees Today: ")
females_count = ask_int("Enter number of Female(s): ")
male_count = ask_int("Enter number of Male(s): ")

# FIX 7: sanity check so the report doesn't contradict itself
if males_and_females := (males_total := male_count + females_count) != attendees:
    print(f"Warning: Male + Female = {males_total}, but attendees = {attendees}.")
    if input("Continue anyway? (y/n): ").strip().lower() != "y":
        sys.exit("Aborted.")

# FIX 1: use the comment variable instead of a hardcoded string
comment = input(f"Observations/Comments : ").strip()
formatted_gender_text = f"Male(s) - {male_count}, Female(s) - {females_count}"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    try:
        page.goto(form_url)
        page.get_by_role("button", name="Start now").click()
        page.wait_for_load_state("networkidle", timeout=15000)

        # FIX 6: exact=True so "Northern" can't also match "North East", etc.
        page.get_by_role("button", name="1. Select your Region").click()
        region_option = page.get_by_role("option", name=region).first
        expect(region_option).to_be_visible(timeout=3000)
        region_option.click()

        page.get_by_role("button", name="2. Select Your District/Constituency").click()
        district_option = page.get_by_role("option", name=district).first
        expect(district_option).to_be_visible(timeout=3000)
        district_option.click()

        page.get_by_role("button", name="3. Select your Training Center").click()
        training_center = page.get_by_role("option", name=center, exact=True)
        expect(training_center).to_be_visible(timeout=3000)
        training_center.click()

        # FIX 8: assert visibility first; .fill() already clears, so .clear() is redundant
        coordinator_input = page.get_by_label("Name of Coordinator")
        expect(coordinator_input).to_be_visible(timeout=10000)
        coordinator_input.fill(coordinator)

        page.get_by_label("Telephone Number").fill(phone)

        page.get_by_label("How Many Persons with Disability Attended The Training?").fill(disability_count)

        # FIX 3: exact, case-insensitive match so only the "Yes" radio is targeted
        page.get_by_role("radio", name=re.compile(r"^yes$", re.I)).check()

        page.get_by_role("textbox", name="8. Observations/Comments").fill(comment)

        # FIX 2: tick only the courses actually taught today
        for name in course_names:
            page.get_by_role("checkbox", name=name).check()

        # FIX 9: a short prefix is enough, since name matching is substring-based
        page.get_by_role(
            "textbox", name="Specify The Course(s) Taken Today"
        ).fill(formatted_courses)

        page.get_by_label("What is the Total Number of Attendees Today?").fill(str(attendees))

        page.get_by_role(
            "textbox", name="What Is the Total Number of Male/Female Participants"
        ).fill(formatted_gender_text)

        # FIX 12: let yourself review the form before anything is sent
        if input("Review the form. Submit now? (y/n): ").strip().lower() == "y":
            page.get_by_role("button", name="Submit").click()
            page.wait_for_load_state("networkidle")
            print("Submitted.")
        else:
            print("Not submitted.")

    except Exception as e:
        # FIX 4: accurate message, since the failure could be at any step
        print(f"Form automation failed: {e}")

    finally:
        # FIX 11: timestamped screenshot saved next to the script
        shot = SCRIPT_DIR / f"report_{datetime.now():%Y%m%d_%H%M%S}.png"
        page.screenshot(path=shot, full_page=True)
        print(f"Page title: {page.title()} | Screenshot: {shot}")
        browser.close()