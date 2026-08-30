'''
Unit tests for the answer rules - especially work authorization, which must be
truthful per country: Canadian citizen, so Canada = authorized / no
sponsorship, USA = not yet authorized / needs sponsorship (J-1).
'''

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config  # noqa: E402
from filler.common import answer_for, question_country  # noqa: E402


def test_question_country_detection():
    assert question_country("Are you authorized to work in the United States?") == "USA"
    assert question_country("Do you require sponsorship to work in the U.S.?") == "USA"
    assert question_country("Are you legally entitled to work in Canada?") == "Canada"
    assert question_country("Will you require visa sponsorship?") is None


def test_sponsorship_answers_follow_job_country():
    q = "Will you now or in the future require visa sponsorship?"
    assert answer_for(q, "USA") == "Yes"
    assert answer_for(q, "Canada") == "No"


def test_question_named_country_overrides_job_country():
    q = "Are you legally authorized to work in the United States?"
    assert answer_for(q, "Canada") == "No"   # US question on a Canadian-tagged job
    q2 = "Are you eligible to work in Canada?"
    assert answer_for(q2, "USA") == "Yes"    # Canada question: citizen, always yes


def test_authorization_answers():
    q = "Are you legally authorized to work for any employer?"
    assert answer_for(q, "USA") == "No"
    assert answer_for(q, "Canada") == "Yes"


def test_require_authorization_is_a_sponsorship_question():
    '''"Will you REQUIRE authorization?" is the opposite of "ARE you
    authorized?" - both mention authorization; the answers must differ.'''
    q = "Will you in the future require authorization to legally work in the United States?"
    assert answer_for(q, "USA") == "Yes"
    assert answer_for(q, "Canada") == "Yes"  # question names the US, job country irrelevant
    q2 = "Are you legally eligible to work for any employer in the United States?"
    assert answer_for(q2, "USA") == "No"
    q3 = "Do you require a work permit to work in Canada?"
    assert answer_for(q3, "USA") == "No"


def test_profile_field_answers():
    assert answer_for("First Name *", "USA") == config.first_name
    assert answer_for("Email", "USA") == config.email
    assert answer_for("Phone number", "USA") == config.phone
    assert answer_for("LinkedIn Profile", "USA") == config.linkedin
    assert answer_for("School", "USA") == config.school
    assert answer_for("Expected graduation date", "USA") == config.graduation


def test_unknown_questions_stay_blank():
    assert answer_for("Describe a project you are proud of", "USA") is None
    assert answer_for("Tell us about yourself", "USA") is None


def test_education_details_fill():
    assert answer_for("School*", "USA") == config.school
    assert answer_for("Degree*", "USA") == config.degree
    assert answer_for("Discipline*", "USA") == config.discipline
    assert answer_for("Program", "USA") == config.discipline
    assert answer_for("Start date month*", "USA") == config.edu_start_month
    assert answer_for("Start date year*", "USA") == config.edu_start_year
    assert answer_for("End date month*", "USA") == config.grad_month
    assert answer_for("End date year*", "USA") == config.grad_year
    assert answer_for("What year are you expected to graduate?*", "USA") == config.grad_year
    assert answer_for("Expected graduation date", "USA") == config.graduation


def test_availability_and_experience():
    assert answer_for("When are you available to start?", "USA") == config.availability
    assert answer_for("How many years of relevant work experience do you have?", "USA") == config.years_of_experience


def test_gpa_question_is_not_a_degree_question():
    q = "For your most recent degree, what is/was your GPA (normalized to a 4.0 scale)?"
    assert answer_for(q, "USA") is None


def test_gender_fills_per_user_instruction():
    assert answer_for("Gender", "USA") == config.gender
    assert answer_for("Gender identity", "USA") == config.gender
    assert answer_for("Preferred pronouns", "USA") is None


def test_country_of_residence():
    assert answer_for("Country*", "USA") == config.country
    assert answer_for("Country of residence", "USA") == config.country


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
