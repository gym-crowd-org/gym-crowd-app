"""Scheduled jobs (hourly ingest + daily forecast).

Invoked by GitHub Actions cron via `python -m app.jobs <command>`, not by
request handlers. See .github/workflows/.
"""
