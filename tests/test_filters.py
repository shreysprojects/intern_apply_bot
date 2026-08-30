'''Unit tests for job filtering and classification (no network, no browser).'''

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fetch_jobs import classify_ats, country_of, job_country, wanted  # noqa: E402


def listing(**overrides):
    base = {
        "id": "x", "company_name": "TestCo", "title": "Software Engineer Intern",
        "active": True, "is_visible": True, "terms": ["Summer 2027"],
        "category": "Software", "locations": ["San Jose, CA"],
        "url": "https://boards.greenhouse.io/testco/jobs/1",
    }
    base.update(overrides)
    return base


def test_country_of():
    assert country_of("San Jose, CA") == "USA"
    assert country_of("NYC") == "USA"
    assert country_of("Toronto, ON") == "Canada"
    assert country_of("Remote in Canada") == "Canada"
    assert country_of("London, UK") == "Other"
    assert country_of("Remote") == "Remote"


def test_job_country_us_wins_on_mixed():
    assert job_country(["Toronto, ON", "Seattle, WA"]) == "USA"
    assert job_country(["Montreal, QC"]) == "Canada"
    assert job_country(["Remote"]) == "USA"


def test_classify_ats():
    assert classify_ats("https://job-boards.greenhouse.io/x/jobs/1") == "greenhouse"
    assert classify_ats("https://jobs.lever.co/x/abc/apply") == "lever"
    assert classify_ats("https://jobs.ashbyhq.com/x/abc") == "ashby"
    assert classify_ats("https://x.wd5.myworkdayjobs.com/en-US/x/job/y") == "workday"
    assert classify_ats("https://careers.example.com/j/1") == "other"


def test_wanted_happy_path():
    assert wanted(listing())


def test_wanted_rejects_inactive_and_hidden():
    assert not wanted(listing(active=False))
    assert not wanted(listing(is_visible=False))


def test_wanted_rejects_wrong_term():
    assert not wanted(listing(terms=["Summer 2026"]))


def test_wanted_rejects_wrong_category():
    assert not wanted(listing(category="Hardware"))


def test_wanted_rejects_grad_only_titles():
    assert not wanted(listing(title="Software Engineer Intern (PhD)"))
    assert not wanted(listing(title="MBA Product Intern"))


def test_wanted_rejects_non_north_american_locations():
    assert not wanted(listing(locations=["London, UK"]))
    assert wanted(listing(locations=["London, UK", "Toronto, ON"]))
    assert wanted(listing(locations=["Remote"]))


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
