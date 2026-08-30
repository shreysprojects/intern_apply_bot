'''
Label-driven form filling shared by every ATS filler.

The model: walk the labels of a form, match each label's text against the
answer rules below, and fill the matching control. Anything with no rule is
left blank and reported, so it shows up in the console for you to complete
during review. Nothing here submits anything.
'''

import re

import config


def question_country(label_text: str) -> str | None:
    '''Country a question names, if any ("...authorized to work in the US?").'''
    low = " " + label_text.lower() + " "
    if re.search(r"united states|u\.s\.|\bus[a.]?\b|\bu\.s\b", low):
        return "USA"
    if "canada" in low or "canadian" in low:
        return "Canada"
    return None


def needs_sponsorship(country: str) -> str:
    return "Yes" if country == "USA" else "No"


def authorized_to_work(country: str) -> str:
    return "No" if country == "USA" else "Yes"


def answer_for(label_text: str, job_country: str) -> str | None:
    '''The answer for one question label, or None to leave it blank.'''
    low = label_text.lower().strip()
    if not low:
        return None
    country = question_country(label_text) or job_country

    # "Do you REQUIRE sponsorship/authorization?" must be checked before
    # "ARE you authorized?" - both mention authorization, opposite answers.
    if re.search(r"sponsor|visa|work\s+permit|require\w*\s+(?:\w+\s+){0,4}authoriz", low):
        return needs_sponsorship(country)
    if re.search(r"authoriz|legally\s+(?:able|permitted|allowed|eligible|entitled)|eligib\w*\s+to\s+work", low):
        return authorized_to_work(country)

    if re.search(r"first\s*name|given\s*name", low):
        return config.first_name
    if re.search(r"last\s*name|family\s*name|surname", low):
        return config.last_name
    if re.search(r"full\s*name|your\s*name|^name\s*[*✱]?$", low):
        return config.full_name
    if "email" in low:
        return config.email
    if "phone" in low or "mobile" in low:
        return config.phone
    if re.search(r"linkedin", low):
        return config.linkedin
    if re.search(r"website|portfolio|personal\s+site", low):
        return config.website or None
    if re.search(r"school|university|college|education", low):
        return config.school
    if re.search(r"\bgpa\b|grade\s*point", low):
        return None  # even when the label also mentions "degree"
    if re.search(r"degree", low):
        return config.degree
    if re.search(r"major|discipline|field\s+of\s+study|program\s+of\s+study|^program\s*[*✱]?$", low):
        return config.discipline
    # Split education-date fields (Greenhouse education section and similar).
    if re.search(r"start\s*date\s*month", low):
        return config.edu_start_month
    if re.search(r"start\s*date\s*year", low):
        return config.edu_start_year
    if re.search(r"end\s*date\s*month|graduation\s*month", low):
        return config.grad_month
    if re.search(r"end\s*date\s*year|graduat\w*\s*year|year\s+(?:do\s+you|are\s+you)\s+expect\w*\s+to\s+graduate|year\s+of\s+graduation", low):
        return config.grad_year
    if re.search(r"graduat", low):
        return config.graduation
    if re.search(r"available\s+to\s+(?:start|begin)|earliest\s+start|availability\s+date|when\s+(?:can|could)\s+you\s+start|start\s+date\s+for\s+(?:the\s+)?internship", low):
        return config.availability
    if re.search(r"years?\s+of\s+(?:\w+\s+){0,3}experience|how\s+many\s+years", low):
        return config.years_of_experience
    if re.search(r"current\s+(?:location|city)|where\s+are\s+you\s+(?:located|based)|^location\s*[*✱]?$|^city\b", low):
        return config.city
    if re.search(r"^country\s*(?:of\s+residence)?\s*[*✱]?$", low):
        return config.country
    if re.search(r"current\s+(?:company|employer)|most\s+recent\s+(?:company|employer)|^(?:company|employer|organization)\s*[*✱]?$", low):
        return config.current_company
    if re.search(r"^gender\s*[*✱]?$|gender\s*identity", low):
        return config.gender
    if re.search(r"how\s+did\s+you\s+hear|hear\s+about\s+us", low):
        return "University resources"
    if re.search(r"pronouns", low):
        return None
    return None


def _fill_control(page, control, value: str, report: dict, label_text: str) -> None:
    tag = control.evaluate("el => el.tagName.toLowerCase()")
    ctype = (control.get_attribute("type") or "").lower()
    try:
        if tag == "select":
            try:
                control.select_option(label=value)
            except Exception:
                # fall back to the first option whose text contains the answer
                options = control.evaluate(
                    "el => Array.from(el.options).map(o => o.text)")
                match = next((o for o in options if value.lower() in o.lower()), None)
                if match is None:
                    report["unanswered"].append(label_text)
                    return
                control.select_option(label=match)
        elif ctype in ("checkbox", "radio", "file"):
            return  # handled by ATS-specific passes (Yes/No buttons, uploads)
        elif tag in ("input", "textarea"):
            if control.input_value():
                return  # already filled (autofill or a previous pass)
            control.fill(value)
        else:
            report["unanswered"].append(label_text)
            return
        report["filled"].append(f"{label_text} -> {value}")
    except Exception as e:
        report["unanswered"].append(f"{label_text} ({e.__class__.__name__})")


def fill_by_labels(page, job_country: str, report: dict) -> None:
    '''Generic pass over every <label> on the page. Not scoped to <form>:
    some ATSes (Ashby) render the application without a form element.'''
    labels = page.locator("label")
    for i in range(labels.count()):
        lab = labels.nth(i)
        try:
            text = lab.inner_text(timeout=2000).strip()
        except Exception:
            continue
        if not text or len(text) > 400:
            continue
        if re.search(r"\bgpa\b|grade\s*point", text.lower()):
            # The user does not apply anywhere that asks for GPA.
            report["asks_gpa"] = True
            report["unanswered"].append(text)
            continue
        value = answer_for(text, job_country)
        if value is None:
            if _looks_like_question(text):
                report["unanswered"].append(text)
            continue
        control = _control_for_label(page, lab)
        if control is None:
            report["unanswered"].append(text)
            continue
        _fill_control(page, control, value, report, text)


def _control_for_label(page, label):
    for_id = label.get_attribute("for")
    if for_id:
        target = page.locator(f'[id="{for_id}"]')
        if target.count():
            return target.first
    nested = label.locator("input, textarea, select")
    if nested.count():
        return nested.first
    return None


def _looks_like_question(text: str) -> bool:
    '''Only report substantive-looking labels, not UI chrome.'''
    return len(text) > 12 or text.endswith("?") or "*" in text


def upload_resume(page, report: dict) -> None:
    '''Attach the resume, preferring a file input named/labeled "resume"
    (Ashby also has a separate "autofill from resume" input first).'''
    file_inputs = page.locator('input[type="file"]')
    if not file_inputs.count():
        report["unanswered"].append("resume upload (no file input found)")
        return
    target = file_inputs.first
    for i in range(file_inputs.count()):
        candidate = file_inputs.nth(i)
        ident = " ".join(filter(None, (
            candidate.get_attribute("id"), candidate.get_attribute("name"),
            candidate.get_attribute("aria-label")))).lower()
        if "resume" in ident or "cv" in ident:
            target = candidate
            break
    try:
        target.set_input_files(config.resume_path)
        report["filled"].append("resume upload")
    except Exception as e:
        report["unanswered"].append(f"resume upload ({e.__class__.__name__})")


def new_report() -> dict:
    return {"filled": [], "unanswered": [], "asks_gpa": False}
