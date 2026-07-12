"""Scheduled jobs (scrape + precompute).

Intended to be invoked by GitHub Actions / cron, not by request handlers.
"""


def scrape_occupancy() -> None:
    raise NotImplementedError("Occupancy scraper not implemented yet.")


def precompute_predictions(hours: int = 24) -> None:
    raise NotImplementedError("Prediction precompute job not implemented yet.")
