import logging
import smtplib
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from src.scraper import VolunteerSlot

logger = logging.getLogger(__name__)


def format_email(slots: list[VolunteerSlot], target_date: date, signup_url: str, teacher_name: str) -> tuple[str, str, str]:
    """Format the reminder email. Returns (subject, body_html, body_text)."""
    date_str = target_date.strftime("%A, %B %-d, %Y")
    disclaimer = (
        "This is an automated email generated from the SignUpGenius page. "
        "If there are any discrepancies, please check the page directly."
    )

    if slots:
        names = ", ".join(slot.volunteer_name for slot in slots)
        subject = f"Wed Folder Update for {date_str}: Volunteer Signed Up"
        body_text = (
            f"Hi {teacher_name},\n\n"
            f"A parent volunteer ({names}) has signed up for Wednesday folders "
            f"on {date_str}. You do not need to prepare the folders yourself.\n\n"
            f"SignUpGenius page: {signup_url}\n\n"
            f"{disclaimer}"
        )
        body_html = (
            f"<p>Hi {teacher_name},</p>"
            f"<p>A parent volunteer (<strong>{names}</strong>) has signed up for "
            f"Wednesday folders on {date_str}. You do not need to prepare the folders yourself.</p>"
            f'<p>SignUpGenius page: <a href="{signup_url}">{signup_url}</a></p>'
            f"<p><em>{disclaimer}</em></p>"
        )
    else:
        subject = f"Wed Folder Update for {date_str}: No Volunteer"
        body_text = (
            f"Hi {teacher_name},\n\n"
            f"No parent volunteer has signed up for Wednesday folders on {date_str}. "
            f"You may need to prepare the folders yourself.\n\n"
            f"SignUpGenius page: {signup_url}\n\n"
            f"{disclaimer}"
        )
        body_html = (
            f"<p>Hi {teacher_name},</p>"
            f"<p>No parent volunteer has signed up for Wednesday folders on {date_str}. "
            f"You may need to prepare the folders yourself.</p>"
            f'<p>SignUpGenius page: <a href="{signup_url}">{signup_url}</a></p>'
            f"<p><em>{disclaimer}</em></p>"
        )

    return subject, body_html, body_text


def send_reminder_email(
    gmail_user: str,
    gmail_app_password: str,
    recipients: list[str],
    subject: str,
    body_html: str,
    body_text: str,
) -> None:
    """Send the reminder email via Gmail SMTP."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = gmail_user
    msg["To"] = ", ".join(recipients)

    msg.attach(MIMEText(body_text, "plain"))
    msg.attach(MIMEText(body_html, "html"))

    logger.info(f"Sending email to {len(recipients)} recipients via Gmail SMTP")
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(gmail_user, gmail_app_password)
        server.sendmail(gmail_user, recipients, msg.as_string())
    logger.info("Email sent successfully")
