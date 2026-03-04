import asyncio
import logging
import sys
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from src.config import Config
from src.emailer import format_email, send_reminder_email
from src.scraper import scrape_signupgenius

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def get_target_date(override: str | None = None) -> datetime:
    """Determine the target date to check for volunteers.

    If override is provided, parse it as YYYY-MM-DD.
    Otherwise, use tomorrow's date in US/Eastern timezone.
    """
    if override:
        return datetime.strptime(override, "%Y-%m-%d").date()

    eastern = ZoneInfo("America/New_York")
    today = datetime.now(eastern).date()
    return today + timedelta(days=1)


async def run():
    config = Config()
    target = get_target_date(config.TARGET_DATE)
    end_date = date.fromisoformat(config.END_DATE)
    logger.info(f"Target date: {target.strftime('%A, %B %d, %Y')}")

    if target > end_date:
        logger.info(f"Target date is past end date ({config.END_DATE}), skipping.")
        return

    slots = await scrape_signupgenius(
        url=config.SIGNUP_GENIUS_URL,
        target_date=target,
        debug_screenshot=config.DEBUG_SCREENSHOT,
    )

    subject, body_html, body_text = format_email(
        slots=slots,
        target_date=target,
        signup_url=config.SIGNUP_GENIUS_URL,
        teacher_name=config.TEACHER_NAME,
    )

    send_reminder_email(
        gmail_user=config.GMAIL_USER,
        gmail_app_password=config.GMAIL_APP_PASSWORD,
        recipients=config.EMAIL_RECIPIENTS,
        subject=subject,
        body_html=body_html,
        body_text=body_text,
    )

    logger.info(f"Reminder sent to {len(config.EMAIL_RECIPIENTS)} recipients")


def main():
    try:
        asyncio.run(run())
    except Exception as e:
        logger.error(f"Failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
