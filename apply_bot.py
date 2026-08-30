'''
Fill internship applications for review - NEVER submit.

Takes the next batch of "queued" jobs from data/tracker.csv, opens each in its
own browser tab, auto-fills the form, then hands control to you: review every
tab, complete anything listed as unanswered, and click Submit YOURSELF if you
want to send it. Afterwards, tell the console what you did so the tracker
stays accurate.

Usage:
  venv\\Scripts\\python.exe apply_bot.py            # fill config.batch_limit jobs
  venv\\Scripts\\python.exe apply_bot.py --limit 5
  venv\\Scripts\\python.exe apply_bot.py --smoke    # headless single-job fill test, no resume upload, no tracker update
'''

import argparse
import sys

from playwright.sync_api import sync_playwright

import config
import tracker
from filler import ashby, common, generic, greenhouse, lever

FILLERS = {
    "greenhouse": greenhouse.fill,
    "lever": lever.fill,
    "ashby": ashby.fill,
    "generic": generic.fill,
}


def fill_job(page, job: dict) -> dict:
    page.goto(job["url"], timeout=60000)
    return FILLERS[job["ats"]](page, job)


def print_report(job: dict, report: dict) -> None:
    print(f'\n=== {job["company"]} — {job["title"]} [{job["ats"]}, {job["country"]}] ===')
    print(f'    {job["url"]}')
    filled_labels = {line.split(" -> ")[0] for line in report["filled"]}
    unanswered = [u for u in dict.fromkeys(report["unanswered"]) if u not in filled_labels]
    for line in report["filled"]:
        print(f"    filled:     {line}")
    for line in unanswered:
        print(f"    YOUR TURN:  {line}")
    if not unanswered:
        print("    Everything matched — still review before submitting.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=config.batch_limit)
    parser.add_argument("--smoke", action="store_true",
                        help="headless single-job fill test: no resume upload, no tracker update")
    parser.add_argument("--ats", choices=sorted(FILLERS), help="only fill jobs on this ATS")
    args = parser.parse_args()

    rows = tracker.load()
    queue = [r for r in rows if r["status"] == "queued" and r["ats"] in FILLERS]
    if args.ats:
        queue = [r for r in queue if r["ats"] == args.ats]
    if not queue:
        print("Nothing queued. Run fetch_jobs.py first, or check data/tracker.csv.")
        sys.exit(0)
    batch = queue[:1] if args.smoke else queue[:args.limit]

    if args.smoke:
        # Smoke mode verifies filling works without sending anything anywhere:
        # skip the resume upload (a real upload transfers the file to the ATS).
        common.upload_resume = lambda page, report: report["unanswered"].append(
            "resume upload (skipped in smoke mode)")

    # Standard-ATS forms come out near-complete; company-hosted "generic" forms
    # need more hand-finishing. Give each kind its own browser WINDOW so the
    # quick reviews and the longer ones stay separated.
    QUICK_ATS = ("greenhouse", "lever", "ashby")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=args.smoke or config.headless)
        contexts = {}

        def context_for(job):
            kind = "QUICK REVIEW" if job["ats"] in QUICK_ATS else "NEEDS HAND-FINISHING"
            if kind not in contexts:
                contexts[kind] = browser.new_context()
            return kind, contexts[kind]

        results = []
        for job in batch:
            kind, context = context_for(job)
            page = context.new_page()
            try:
                report = fill_job(page, job)
            except Exception as e:
                report = common.new_report()
                report["unanswered"].append(f"page failed to fill: {e}")
            if report.get("asks_gpa") and not args.smoke:
                # User rule: never apply anywhere that asks for GPA.
                print(f'\nSKIPPED (asks for GPA): {job["company"]} — {job["title"]}')
                tracker.set_status(rows, job["id"], "skipped", "asks for GPA - per user rule")
                page.close()
                continue
            print(f"\n[window: {kind}]", end="")
            print_report(job, report)
            results.append((job, page, report))
        tracker.save(rows)  # persist GPA-skips even if the review below is abandoned

        if args.smoke:
            job, page, report = results[0]
            page.screenshot(path="data/smoke_screenshot.png", full_page=True)
            print("\nSmoke test done — screenshot at data/smoke_screenshot.png. "
                  "Nothing was uploaded or recorded.")
            browser.close()
            return

        print("\n----------------------------------------------------------------")
        print("All tabs are filled and OPEN. Review each one, complete anything")
        print('marked "YOUR TURN", and click Submit yourself if you want to send')
        print("it. This tool will not submit for you.")
        print("----------------------------------------------------------------")
        for job, page, report in results:
            while True:
                answer = input(
                    f'{job["company"]} — {job["title"]}: did you submit it? '
                    "[y]es / [n]ot yet (keep queued) / [s]kip forever: ").strip().lower()
                if answer in ("y", "n", "s"):
                    break
            if answer == "y":
                tracker.set_status(rows, job["id"], "submitted")
            elif answer == "s":
                tracker.set_status(rows, job["id"], "skipped")
            else:
                tracker.set_status(rows, job["id"], "queued", "filled once, not submitted")
        tracker.save(rows)
        input("Tracker saved. Press Enter to close the browser... ")
        browser.close()


if __name__ == "__main__":
    main()
