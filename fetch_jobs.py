'''
Fetch the SimplifyJobs Summer 2027 internship feed, filter it to roles that
fit the profile, classify each posting's ATS, and merge into the tracker.

Run:  venv\\Scripts\\python.exe fetch_jobs.py
Then: venv\\Scripts\\python.exe apply_bot.py
'''

import json
import re
import urllib.request

import config
import tracker

# US state codes + common shorthands the feed uses.
US_STATES = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID",
    "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS",
    "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK",
    "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV",
    "WI", "WY", "DC",
}
CA_PROVINCES = {"ON", "QC", "BC", "AB", "MB", "SK", "NS", "NB", "NL", "PE", "YT", "NT", "NU"}
US_SHORTHANDS = {"NYC", "SF", "USA", "United States"}


def country_of(location: str) -> str:
    '''Best-effort country for one feed location string like "San Jose, CA".'''
    loc = location.strip()
    low = loc.lower()
    if "canada" in low:
        return "Canada"
    if "united states" in low or "usa" in low or loc in US_SHORTHANDS:
        return "USA"
    suffix = loc.rsplit(",", 1)[-1].strip().upper() if "," in loc else ""
    if suffix in CA_PROVINCES:
        return "Canada"
    if suffix in US_STATES:
        return "USA"
    if "remote" in low:
        return "Remote"
    return "Other"


def job_country(locations: list[str]) -> str:
    '''Country used for answering questions when the question itself names none.
    US wins over Canada on mixed postings: the stricter answers are the safe ones.'''
    found = {country_of(l) for l in locations}
    if "USA" in found:
        return "USA"
    if "Canada" in found:
        return "Canada"
    return "USA"  # Remote/unknown: assume US, the conservative answer set


def classify_ats(url: str) -> str:
    host = (re.match(r"https?://([^/]+)", url or "") or [None, ""])[1].lower()
    if "greenhouse" in host:
        return "greenhouse"
    if "lever.co" in host:
        return "lever"
    if "ashbyhq" in host:
        return "ashby"
    if "myworkday" in host:
        return "workday"
    return "other"


def wanted(listing: dict) -> bool:
    '''Pure filter so it can be unit tested without network access.'''
    if not listing.get("active") or not listing.get("is_visible"):
        return False
    if not any(t in listing.get("terms", []) for t in config.terms):
        return False
    if listing.get("category") not in config.categories:
        return False
    title_low = listing.get("title", "").lower()
    if any(w.lower() in title_low for w in config.exclude_title_words):
        return False
    loc_countries = {country_of(l) for l in listing.get("locations", [])}
    if not loc_countries & set(config.countries) and "Remote" not in loc_countries:
        return False
    return True


def fetch_listings() -> list[dict]:
    with urllib.request.urlopen(config.listings_url, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> None:
    listings = fetch_listings()
    matches = [l for l in listings if wanted(l)]
    rows = tracker.load()
    known = {r["id"] for r in rows}
    added = 0
    for l in matches:
        if l["id"] in known:
            continue
        ats = classify_ats(l["url"])
        rows.append({
            "id": l["id"],
            "company": l.get("company_name", ""),
            "title": l.get("title", ""),
            "url": l.get("url", ""),
            "ats": ats,
            "country": job_country(l.get("locations", [])),
            "locations": " | ".join(l.get("locations", [])),
            "status": "queued" if ats in ("greenhouse", "lever", "ashby") else "manual",
            "notes": "",
        })
        added += 1
    tracker.save(rows)

    by_status: dict[str, int] = {}
    for r in rows:
        by_status[r["status"]] = by_status.get(r["status"], 0) + 1
    print(f"Feed: {len(listings)} listings, {len(matches)} match your filters, {added} new.")
    print(f"Tracker: {by_status}")
    print(f'Auto-fillable queue ("queued"): {by_status.get("queued", 0)} — run apply_bot.py')
    print(f'Manual links ("manual", Workday/other ATS): {by_status.get("manual", 0)} — see data/tracker.csv')


if __name__ == "__main__":
    main()
