'''
Generic best-effort filler for companies that host their own application form
(Jane Street, D.E. Shaw, embedded Greenhouse boards, ...). Clicks through to
the form if needed, then runs only the shared label-driven pass - fills what
it can, reports everything else for the human. Never submits.
'''

from filler import common


def fill(page, job: dict) -> dict:
    report = common.new_report()
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(1500)
    # Many career pages show the form only after an "Apply" link/button.
    if not page.locator('input[type="file"]').count():
        for name in ("Apply now", "Apply Now", "Apply"):
            try:
                target = page.get_by_role("link", name=name, exact=True)
                if not target.count():
                    target = page.get_by_role("button", name=name, exact=True)
                if target.count():
                    target.first.click()
                    page.wait_for_timeout(2000)
                    break
            except Exception:
                continue
    common.upload_resume(page, report)
    page.wait_for_timeout(2000)
    common.fill_by_labels(page, job["country"], report)
    if not report["filled"]:
        report["unanswered"].append(
            "nothing auto-filled - this site's form may need an account or "
            "live in an embedded frame; complete it by hand in the open tab")
    return report
