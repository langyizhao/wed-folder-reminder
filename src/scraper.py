import asyncio
import logging
import re
from dataclasses import dataclass
from datetime import date, datetime

from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)


@dataclass
class VolunteerSlot:
    date_str: str
    parsed_date: date
    volunteer_name: str


async def scrape_signupgenius(url: str, target_date: date, debug_screenshot: bool = False) -> list[VolunteerSlot]:
    """Scrape a SignUpGenius page and return volunteer slots matching target_date."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        page = await context.new_page()

        logger.info(f"Loading SignUpGenius page: {url}")
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)

        # The page is a SPA — wait for the actual signup content to render.
        # Look for date-like text or volunteer-related content in the body.
        rendered = False
        for attempt in range(12):
            await asyncio.sleep(3)
            text = await page.evaluate("() => document.body.innerText")
            # Check if date patterns or signup keywords appear — indicates data loaded
            has_dates = re.search(r"\d{1,2}/\d{1,2}/\d{4}", text)
            months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
            has_months = any(m in text for m in months)
            if has_dates or has_months:
                logger.info(f"Signup content detected after ~{(attempt + 1) * 3}s")
                rendered = True
                break
            logger.debug(f"Waiting for content... attempt {attempt + 1}")

        if not rendered:
            logger.warning("Signup content did not appear after 36s, proceeding with current page state")

        if debug_screenshot:
            await page.screenshot(path="debug_screenshot.png", full_page=True)
            logger.info("Debug screenshot saved to debug_screenshot.png")

        # Dump rendered HTML for extraction
        content = await page.content()
        text_content = await page.evaluate("() => document.body.innerText")

        if debug_screenshot:
            with open("debug_text.txt", "w") as f:
                f.write(text_content)
            logger.info("Debug text dump saved to debug_text.txt")

        await browser.close()

    logger.info(f"Page loaded, extracting volunteer data for {target_date}")
    return _extract_slots(text_content, content, target_date)


def _extract_slots(text_content: str, html_content: str, target_date: date) -> list[VolunteerSlot]:
    """Extract volunteer slots from page text content.

    The SignUpGenius page text follows this repeating pattern per date:
        MM/DD/YYYY
        HH:MMam/pm-
        HH:MMam/pm
        Wednesday
        Full / Sign Up
        Wednesday Folder
        Sort Papers by student name into Bin
        All slots filled / 0 of 1 slots filled
        <blank>
        Volunteer Name  (only present if slot is filled)
        <blank>
        Optional comment
        Initials (e.g., YL)
    """
    date_pattern = re.compile(r"^(\d{1,2}/\d{1,2}/\d{4})$")
    lines = text_content.split("\n")
    slots = []

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        match = date_pattern.match(line)
        if not match:
            i += 1
            continue

        # Parse the date
        try:
            slot_date = datetime.strptime(match.group(1), "%m/%d/%Y").date()
        except ValueError:
            i += 1
            continue

        date_str = match.group(1)

        # If this date doesn't match our target, skip ahead
        if slot_date != target_date:
            i += 1
            continue

        # Scan ahead through this date's block to find if slot is filled
        # and extract the volunteer name
        is_filled = False
        volunteer_name = None
        j = i + 1
        while j < len(lines):
            block_line = lines[j].strip()
            # Stop if we hit the next date block
            if date_pattern.match(block_line):
                break
            if block_line.lower() == "all slots filled":
                is_filled = True
            j += 1

        if is_filled:
            # Volunteer name appears after "All slots filled" + blank line
            k = i + 1
            while k < len(lines):
                bl = lines[k].strip()
                if bl.lower() == "all slots filled":
                    # Name is after next non-empty line
                    k += 1
                    while k < len(lines) and not lines[k].strip():
                        k += 1
                    if k < len(lines):
                        name = lines[k].strip()
                        if name and not date_pattern.match(name):
                            volunteer_name = name
                    break
                k += 1

        if volunteer_name:
            slots.append(VolunteerSlot(
                date_str=date_str,
                parsed_date=slot_date,
                volunteer_name=volunteer_name,
            ))
            logger.info(f"Found volunteer: {volunteer_name} for {slot_date}")
        else:
            logger.info(f"No volunteer signed up for {slot_date}")

        # Move past this block
        i = j if j > i else i + 1

    return slots
