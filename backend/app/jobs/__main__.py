"""CLI entrypoint for scheduled jobs. Run from backend/:

    python -m app.jobs ingest --csv /path/to/gym_crowd.csv
    python -m app.jobs forecast [--date YYYY-MM-DD]   # default: today in SGT
"""

import argparse
import logging
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

load_dotenv()

from app.db.client import get_supabase  # noqa: E402
from app.jobs.forecast import run_daily_forecast  # noqa: E402
from app.jobs.ingest import ingest_csv  # noqa: E402


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)

    parser = argparse.ArgumentParser(prog="python -m app.jobs")
    sub = parser.add_subparsers(dest="command", required=True)

    ingest = sub.add_parser("ingest", help="Load gym_crowd.csv into crowd_readings")
    ingest.add_argument("--csv", type=Path, required=True)

    forecast = sub.add_parser("forecast", help="Precompute one day of predictions")
    forecast.add_argument("--date", type=date.fromisoformat, default=None)

    args = parser.parse_args()
    supabase = get_supabase()

    if args.command == "ingest":
        ingest_csv(supabase, args.csv)
    else:
        day = args.date or datetime.now(ZoneInfo("Asia/Singapore")).date()
        run_daily_forecast(supabase, day)


if __name__ == "__main__":
    main()
