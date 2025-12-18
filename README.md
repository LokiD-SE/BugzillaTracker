# Bugzilla Tracker

A Python script that monitors Bugzilla for bug updates and sends notifications to Google Chat.

## Setup

1. **Create and activate virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Linux/Mac
   # or
   venv\Scripts\activate  # On Windows
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Create `.env` file:**
   Create a `.env` file in the project root with the following variables:
   ```
   BUGZILLA_URL=https://bugzilla.bizom.in/rest/bug
   BUGZILLA_API_KEY=your_api_key_here
   GOOGLE_CHAT_WEBHOOK=your_webhook_url_here
   CHECK_INTERVAL_MINUTES=5
   BUG_STATUS=UNCONFIRMED,CONFIRMED,IN_PROGRESS,RESOLVED,RE-OPENED
   PRODUCT=BizomWeb,Mobile App
   EMAIL=your.email@example.com
   ```

## Usage

You can run the script in three ways:

1. **Using the run script (recommended - automatically uses venv):**
   ```bash
   ./run.sh
   ```

2. **Using the virtual environment's python directly:**
   ```bash
   ./venv/bin/python main.py
   ```

3. **After activating the virtual environment:**
   ```bash
   source venv/bin/activate
   python main.py
   ```

## Features

- Monitors Bugzilla for bug updates based on configured filters
- Sends formatted notifications to Google Chat
- Configurable check interval
- Filters by bug status, product, and email

## Cloud Deployment

This script can be deployed to various cloud platforms. See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions.

**Quick Start - GitHub Actions (Recommended):**
1. Push your code to GitHub
2. Add secrets in Settings → Secrets and variables → Actions
3. The workflow will run automatically every 5 minutes

See `.github/workflows/bugzilla-tracker.yml` for the GitHub Actions configuration.

## Project Structure

```
BugzillaTracker/
├── .env                # Local environment variables (API keys, Webhook URLs)
├── .gitignore          # Keeps your .env and __pycache__ out of version control
├── requirements.txt    # List of Python dependencies
├── main.py             # Entry point (the loop that runs the script)
├── config.py           # Configuration loader (reads .env and defines constants)
├── notifier.py         # Logic for querying Bugzilla and formatting Chat messages
├── run.sh              # Convenience script to run with python3
├── DEPLOYMENT.md       # Cloud deployment guide
└── .github/workflows/  # GitHub Actions workflow
```

