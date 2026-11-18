"""Hourly ingest: cumulative gym_crowd.csv (from S3) -> crowd_readings.

CSV format (fixed, produced by the scraper):
    timestamp,name,current,capacity
    2026-10-20T19:18:16.699336+08:00,University Sports Centre - Gym,89,110

- `name` must equal gyms.name exactly; unknown names are logged and skipped.
- Timestamps without an offset are Asia/Singapore local time.
- Only rows newer than the latest stored reading per gym are sent, and the
  upsert ignores (gym_id, observed_at) duplicates, so re-runs are safe.
"""

from __future__ import annotations

import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from app.api.services import _as_singapore, latest_reading, list_gyms

from supabase import Client

log = logging.getLogger(__name__)

SG_TZ = ZoneInfo("Asia/Singapore")
CHUNK_SIZE = 500


def parse_timestamp(value: str) -> datetime:
    ts = datetime.fromisoformat(value.strip())
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=SG_TZ)
    return ts


def parse_csv(path: Path, gyms_by_name: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    unknown: dict[str, int] = {}
    invalid = 0

    with path.open(newline="", encoding="utf-8") as f:
        for line_no, raw in enumerate(csv.DictReader(f), start=2):
            name = (raw.get("name") or "").strip()
            gym = gyms_by_name.get(name)
            if gym is None:
                unknown[name] = unknown.get(name, 0) + 1
                continue
            try:
                observed_at = parse_timestamp(raw["timestamp"])
                occupancy = int(raw["current"])
                capacity = int(raw["capacity"])
            except (KeyError, TypeError, ValueError):
                invalid += 1
                log.warning("line %d: unparseable row %r", line_no, raw)
                continue
            if capacity <= 0 or not 0 <= occupancy <= capacity:
                invalid += 1
                log.warning("line %d: occupancy/capacity out of range %r", line_no, raw)
                continue
            rows.append(
                {
                    "gym_id": gym["id"],
                    "observed_at": observed_at,
                    "occupancy": occupancy,
                    "capacity": capacity,
                }
            )

    for name, count in unknown.items():
        log.warning("skipped %d rows for unknown gym name %r", count, name)
    if invalid:
        log.warning("skipped %d invalid rows", invalid)
    return rows


def ingest_csv(supabase: Client, path: Path) -> dict[str, int]:
    gyms = list_gyms(supabase)
    gyms_by_name = {g["name"]: g for g in gyms}
    rows = parse_csv(path, gyms_by_name)

    # Keep only rows newer than what each gym already has.
    latest: dict[str, datetime | None] = {}
    for gym in gyms:
        reading = latest_reading(supabase, gym["id"])
        latest[gym["id"]] = _as_singapore(reading["observed_at"]) if reading else None

    new_rows = [
        {**r, "observed_at": r["observed_at"].isoformat()}
        for r in rows
        if latest[r["gym_id"]] is None or r["observed_at"] > latest[r["gym_id"]]
    ]

    for i in range(0, len(new_rows), CHUNK_SIZE):
        supabase.table("crowd_readings").upsert(
            new_rows[i : i + CHUNK_SIZE],
            on_conflict="gym_id,observed_at",
            ignore_duplicates=True,
        ).execute()

    stats = {"parsed": len(rows), "inserted": len(new_rows)}
    log.info("ingest done: %s", stats)
    return stats
