'''
Ashby filler. Application pages (jobs.ashbyhq.com/<company>/<id>/application)
are React forms with labeled inputs. Fills fields only - never submits.
'''

from filler import common


def fill(page, job: dict) -> dict:
    report = common.new_report()
    page.wait_for_load_state("domcontentloaded")
    if "/application" not in page.url:
        try:
            page.get_by_role("link", name="Application").first.click()
        except Exception:
            try:
                page.get_by_role("button", name="Apply").first.click()
            except Exception:
                pass
    page.wait_for_timeout(1500)
    common.upload_resume(page, report)
    page.wait_for_timeout(2500)  # Ashby autofills fields from the parsed resume
    common.fill_by_labels(page, job["country"], report)
    _fill_yes_no_buttons(page, job["country"], report)
    return report


def _fill_yes_no_buttons(page, job_country: str, report: dict) -> None:
    '''Ashby renders Yes/No questions as a labeled hidden checkbox plus a
    visible Yes/No button pair. Click the right button inside the nearest
    container that holds both the label and the buttons.'''
    labels = page.locator("label")
    for i in range(labels.count()):
        lab = labels.nth(i)
        try:
            label_text = lab.inner_text(timeout=1500).strip()
        except Exception:
            continue
        value = common.answer_for(label_text, job_country)
        if value not in ("Yes", "No"):
            continue
        try:
            container = lab.locator(
                'xpath=ancestor::div[.//button[normalize-space()="Yes"]][1]')
            if not container.count():
                continue
            button = container.first.get_by_role("button", name=value, exact=True)
            if button.count():
                button.first.click()
                report["filled"].append(f"{label_text} -> {value}")
            else:
                report["unanswered"].append(label_text)
        except Exception:
            report["unanswered"].append(label_text)
