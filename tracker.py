'''
CSV-backed tracker of every discovered job and where it stands.

Statuses:
  queued    - supported ATS, waiting to be auto-filled
  manual    - unsupported ATS (Workday etc.): apply by hand via the url
  filled    - form was auto-filled, awaiting your review + manual submit
  submitted - you confirmed you submitted it
  skipped   - you chose to skip it
'''

import csv
import os

import config

TRACKER_PATH = os.path.join(config.PROJECT_ROOT, "data", "tracker.csv")
FIELDS = ["id", "company", "title", "url", "ats", "country", "locations", "status", "notes"]


def load() -> list[dict]:
    if not os.path.exists(TRACKER_PATH):
        return []
    with open(TRACKER_PATH, "r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def save(rows: list[dict]) -> None:
    os.makedirs(os.path.dirname(TRACKER_PATH), exist_ok=True)
    with open(TRACKER_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r.get(k, "") for k in FIELDS})


def set_status(rows: list[dict], job_id: str, status: str, note: str = "") -> None:
    for r in rows:
        if r["id"] == job_id:
            r["status"] = status
            if note:
                r["notes"] = note
            return
