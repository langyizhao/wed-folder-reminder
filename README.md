# Wednesday Folder Volunteer Reminder

Automated reminder that checks a SignUpGenius page for the next day's volunteer and emails a notification. Runs as a scheduled GitHub Actions workflow.

## Prerequisites

- Python 3.11+
- [Poetry](https://python-poetry.org/docs/#installation)
- A Gmail account with an [App Password](https://support.google.com/accounts/answer/185833)

## Local Development

```bash
# Clone and enter the project
git clone https://github.com/langyizhao/wed-folder-reminder.git
cd wed-folder-reminder

# Install dependencies
poetry install
poetry run playwright install chromium

# Configure environment
cp .env.example .env
# Edit .env with your actual values

# Run
poetry run python -m src.main

# Run with debug screenshot
DEBUG_SCREENSHOT=true poetry run python -m src.main
```

## Configuration

All settings are configured via environment variables (`.env` file locally, GitHub Secrets in CI).

| Variable | Required | Description |
|---|---|---|
| `SIGNUP_GENIUS_URL` | Yes | SignUpGenius page URL to scrape |
| `EMAIL_RECIPIENTS` | Yes | Comma-separated list of recipient emails |
| `GMAIL_USER` | Yes | Gmail address used to send emails |
| `GMAIL_APP_PASSWORD` | Yes | Gmail App Password (16 characters) |
| `TARGET_DATE` | No | Override target date (YYYY-MM-DD). Defaults to tomorrow. |
| `DEBUG_SCREENSHOT` | No | Set to `true` to save a screenshot of the page. Defaults to `false`. |

## GitHub Actions Setup

1. Go to your repo's **Settings > Secrets and variables > Actions**
2. Add these repository secrets:
   - `SIGNUP_GENIUS_URL` - the SignUpGenius page URL
   - `EMAIL_RECIPIENTS` - comma-separated email addresses
   - `GMAIL_USER` - your Gmail sender address
   - `GMAIL_APP_PASSWORD` - your Gmail App Password

The workflow runs every Tuesday at 7 PM UTC (2 PM EST / 3 PM EDT) by default. To change the schedule, edit the `cron` value in `.github/workflows/reminder.yml`.

You can also trigger the workflow manually from the **Actions** tab with optional overrides for `target_date` and `signup_url`.

## How It Works

1. Launches a headless Chromium browser via Playwright
2. Loads the SignUpGenius page and waits for JavaScript to render
3. Extracts volunteer names and dates from the rendered page
4. Sends an email with the volunteer info (or an "[ACTION NEEDED]" alert if no volunteer is signed up)
