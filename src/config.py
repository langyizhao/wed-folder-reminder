import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    def __init__(self):
        self.SIGNUP_GENIUS_URL = self._require("SIGNUP_GENIUS_URL")
        self.EMAIL_RECIPIENTS = self._parse_recipients(self._require("EMAIL_RECIPIENTS"))
        self.GMAIL_USER = self._require("GMAIL_USER")
        self.GMAIL_APP_PASSWORD = self._require("GMAIL_APP_PASSWORD")
        self.TEACHER_NAME = os.getenv("TEACHER_NAME", "Mr Smalley")
        self.TARGET_DATE = os.getenv("TARGET_DATE") or None
        self.END_DATE = os.getenv("END_DATE", "2026-06-10")
        self.DEBUG_SCREENSHOT = os.getenv("DEBUG_SCREENSHOT", "false").lower() == "true"

    def _require(self, key: str) -> str:
        value = os.getenv(key)
        if not value:
            raise ValueError(f"Missing required environment variable: {key}")
        return value

    def _parse_recipients(self, raw: str) -> list[str]:
        recipients = [addr.strip() for addr in raw.split(",") if addr.strip()]
        if not recipients:
            raise ValueError("EMAIL_RECIPIENTS must contain at least one email address")
        return recipients
