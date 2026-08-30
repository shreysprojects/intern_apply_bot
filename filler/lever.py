'''
Lever filler. Lever application pages (jobs.lever.co/<company>/<id>/apply)
are plain HTML forms. Fills fields only - never submits.
'''

import config
from filler import common

BASIC_FIELDS = {
    'input[name="name"]': lambda: config.full_name,
    'input[name="email"]': lambda: config.email,
    'input[name="phone"]': lambda: config.phone,
    'input[name="urls[LinkedIn]"]': lambda: config.linkedin,
    'input[name="location"]': lambda: config.city,
}


def fill(page, job: dict) -> dict:
    report = common.new_report()
    page.wait_for_load_state("domcontentloaded")
    if not page.url.rstrip("/").endswith("/apply"):
        try:
            page.get_by_role("link", name="Apply for this job").first.click()
            page.wait_for_load_state("domcontentloaded")
        except Exception:
            pass
    page.wait_for_timeout(1000)

    for selector, value_fn in BASIC_FIELDS.items():
        value = value_fn()
        if not value:
            continue
        try:
            field = page.locator(selector)
            if field.count() and not field.first.input_value():
                field.first.fill(value)
                report["filled"].append(selector)
        except Exception:
            report["unanswered"].append(selector)

    common.upload_resume(page, report)
    page.wait_for_timeout(2000)  # Lever parses the resume on upload
    common.fill_by_labels(page, job["country"], report)
    return report
