'''
Greenhouse filler. Handles both the new job-boards.greenhouse.io UI and the
older boards.greenhouse.io embedded form. Fills fields only - never submits.
'''

import config
from filler import common


BASIC_FIELDS = {
    "#first_name": lambda: config.first_name,
    "#last_name": lambda: config.last_name,
    "#email": lambda: config.email,
    "#phone": lambda: config.phone,
}


def fill(page, job: dict) -> dict:
    report = common.new_report()
    page.wait_for_load_state("domcontentloaded")
    # Old-style boards pages need the Apply tab opened first; new ones don't.
    try:
        apply_btn = page.get_by_role("link", name="Apply", exact=True)
        if apply_btn.count():
            apply_btn.first.click()
    except Exception:
        pass
    page.wait_for_timeout(1500)

    for selector, value_fn in BASIC_FIELDS.items():
        try:
            field = page.locator(selector)
            if field.count() and not field.first.input_value():
                field.first.fill(value_fn())
                report["filled"].append(selector)
        except Exception:
            report["unanswered"].append(selector)

    common.upload_resume(page, report)
    page.wait_for_timeout(2000)  # let the resume upload/parse settle
    common.fill_by_labels(page, job["country"], report)
    _fill_react_selects(page, job["country"], report)
    return report


def _fill_react_selects(page, job_country: str, report: dict) -> None:
    '''New-UI Greenhouse renders selects as react-select comboboxes: click the
    control, then click the option whose text matches the answer.'''
    controls = page.locator(".select__control")
    for i in range(controls.count()):
        control = controls.nth(i)
        try:
            container = control.locator(
                "xpath=ancestor::*[.//label][1]")
            label_text = container.locator("label").first.inner_text(timeout=2000).strip()
        except Exception:
            continue
        value = common.answer_for(label_text, job_country)
        if value is None:
            continue
        try:
            if control.locator(".select__single-value").count():
                continue  # already has a value
            control.click()
            option = page.locator(".select__option", has_text=value)
            if not option.count():
                # Autocomplete selects (School, Degree, Discipline) only load
                # options after you type into them.
                page.keyboard.type(value)
                page.wait_for_timeout(1200)
                option = page.locator(".select__option", has_text=value)
                if not option.count():
                    option = page.locator(".select__option")  # best remaining match
            if option.count():
                option.first.click()
                report["filled"].append(f"{label_text} -> {value}")
            else:
                page.keyboard.press("Escape")
                report["unanswered"].append(label_text)
        except Exception:
            report["unanswered"].append(label_text)
