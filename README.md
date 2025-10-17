# Job Alert System

Automate job tracking and stay ahead of new postings across your favorite companies. Configure once, and let the system email you whenever something new appears. Built for simplicity and reliability — no coding required.

## Features

- Guided CLI setup that stores credentials securely in `config.json`
- Scheduled monitoring with cron-friendly `monitor_jobs.py`
- Google Sheets integration for storing job snapshots
- Email and optional Slack/Discord notifications
- Keyword filtering, pagination, retries, and diff tracking
- Comprehensive unit tests covering scraping, diffing, notifications, and sheets helpers

## Quick Start

1. Clone the repository and install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Run the setup wizard:

   ```bash
   python setup.py
   ```

   Provide the requested credentials, Google Sheet information, and company list. A test email is sent automatically.

3. Schedule the monitor with cron:

   ```bash
   0 8 * * * /usr/bin/python /path/to/repo/monitor_jobs.py
   ```

## Configuration

A sample `config.json` produced by the wizard:

```json
{
  "user_name": "Alex",
  "notifications": {
    "sender": "alerts@example.com",
    "recipient": "alex@example.com",
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "username": "alerts@example.com",
    "password": "app-password",
    "use_tls": true,
    "slack_webhook": null,
    "discord_webhook": null
  },
  "sheets": {
    "spreadsheet_url": "https://docs.google.com/spreadsheets/d/your-id/edit",
    "credentials_path": "service-account.json",
    "worksheet_name": "Job Monitor"
  },
  "sites": [
    {
      "name": "Mercari",
      "url": "https://careers.mercari.com",
      "keywords": ["machine", "backend"],
      "max_pages": 2
    }
  ]
}
```

## CLI Utilities

- `python manage_sites.py list`
- `python manage_sites.py add Mercari https://careers.mercari.com --keywords machine backend`
- `python manage_sites.py update Mercari --max-pages 3`
- `python manage_sites.py remove Mercari`

## Troubleshooting

- **SMTP authentication errors** – confirm app passwords are enabled for the sender account.
- **Google Sheets access issues** – ensure the service account email is added as an editor to the spreadsheet.
- **No jobs detected** – review keyword filters or run without keywords to validate scraping.
- **Rate limiting** – increase delays or reduce monitored sites within the configuration.

## Testing

Run the automated tests with coverage:

```bash
pytest --cov=job_monitor tests/
```

## Contributing

Contributions are welcome! Please open an issue or submit a pull request describing your improvements.

## License

MIT License. See `LICENSE` for details.

## Contact

Questions? Reach out at `support@example.com`.
