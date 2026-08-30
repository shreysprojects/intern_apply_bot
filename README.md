# Intern Apply Bot — fill, never submit

Finds **Summer 2027 tech internships** from the [SimplifyJobs Summer2027-Internships](https://github.com/SimplifyJobs/Summer2027-Internships) list (big tech postings on company career sites, outside LinkedIn), filters them to Shrey's profile, and **auto-fills** the application forms with Playwright.

> **It never submits.** There is no submit code anywhere in this project — the bot fills the form, leaves the tab open, and you review + click Submit yourself. `tests/test_no_submit.py` fails the suite if anyone adds code that clicks anything named "submit", calls `.submit()`, or presses Enter in a form.

## Usage

```powershell
cd C:\Users\shrey\intern_apply_bot
venv\Scripts\python.exe fetch_jobs.py    # refresh the job queue (run this every day or two)
venv\Scripts\python.exe apply_bot.py     # fill the next 3 queued applications
```

Or double-click `START_INTERN_BOT.bat` which does both.

`apply_bot.py` opens each job in its own tab, fills what it can, and prints a report: `filled:` lines are done, `YOUR TURN:` lines are questions it left blank for you (free-text questions, unusual dropdowns). Review every tab, finish the blanks, submit the ones you want, then answer the console prompts (`y`/`n`/`s`) so `data\tracker.csv` stays accurate.

## What it can and can't fill

| ATS | Coverage |
|---|---|
| Greenhouse, Lever, Ashby | Auto-filled (basics, resume upload, work-auth questions, common dropdowns) |
| Workday, everything else | Marked `manual` in `data\tracker.csv` — apply by hand via the link (Workday requires a per-company account; no tool fills it reliably) |

## Answers it gives (config.py)

- Profile: Shrey Jain, McGill B.Eng Computer Engineering, Montreal. **Expected graduation is set to "May 2029" — VERIFY.**
- Work authorization (Canadian citizen): Canada → authorized, no sponsorship. **USA → not authorized, needs sponsorship (J-1)** — the truthful answers. A question that names a country uses that country; otherwise the posting's country is used.
- Filters: Summer 2027 · Software / AI/ML/Data categories · US + Canada + Remote locations · grad-only titles (PhD/Master's/MBA) excluded.

## Files

- `config.py` — profile, answers, filters, batch size
- `fetch_jobs.py` — feed download + filtering → `data\tracker.csv`
- `apply_bot.py` — the filling loop (`--limit N`, `--smoke`)
- `filler/` — per-ATS form fillers + shared label-matching logic
- `data\tracker.csv` — every job and its status (`queued` / `manual` / `submitted` / `skipped`)

## Tests

```powershell
venv\Scripts\python.exe -m pytest tests -q
```
