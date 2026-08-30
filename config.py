'''
Profile, answers, and filters for the intern application bot.

SAFETY: this bot NEVER submits an application. It fills forms and leaves the
page open for manual review. There is no submit code anywhere in this project;
tests/test_no_submit.py enforces that.
'''

import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# ======================= PROFILE =======================
first_name = "Shrey"
last_name = "Jain"
full_name = "Shrey Jain"
email = "shrey.jain@mail.mcgill.ca"
phone = "4166788828"
city = "Montreal, Quebec, Canada"
country = "Canada"                 # country of residence
current_company = "AI-Intelekt"
gender = "Male"
linkedin = "https://www.linkedin.com/in/shrey-jain-7697b9238/"
website = ""                       # portfolio, optional
school = "McGill University"
degree = "Bachelor's Degree"
discipline = "Computer Engineering"
graduation = "May 2029"            # expected graduation
edu_start_month = "August"         # started McGill Aug 2025
edu_start_year = "2025"
grad_month = "May"
grad_year = "2029"
availability = "May 2027"          # earliest internship start
years_of_experience = "1"
resume_path = os.path.join(PROJECT_ROOT, "resume", "resume.pdf")

# Work authorization: Canadian citizen.
#  - Canada: authorized to work, no sponsorship needed.
#  - USA: NOT currently authorized, needs employer-sponsored authorization (e.g. J-1 intern visa).
# When a question names a country, that country's answer is used; otherwise the
# job posting's country is used.

# ======================= FILTERS =======================
listings_url = "https://raw.githubusercontent.com/SimplifyJobs/Summer2027-Internships/dev/.github/scripts/listings.json"
terms = ["Summer 2027"]
categories = ["Software", "Software Engineering", "AI/ML/Data"]
countries = ["USA", "Canada"]      # keep a job if at least one of its locations is here ("Remote" also kept)
exclude_title_words = ["PhD", "Master's", "MBA", "Quant"]   # grad-only / off-target roles

# ======================= RUN SETTINGS =======================
batch_limit = 3                    # how many applications to fill per run of apply_bot.py
headless = False                   # False = you watch the browser fill the forms
