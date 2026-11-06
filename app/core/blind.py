# Blind Review Mode: the AI (and HR, until approval) judges the skills, not the person.
# The full CV stays in the database. Only a cleaned copy goes to the AI
import re

EMAIL = r"[\w.+-]+@[\w-]+\.[\w.-]+"
LINK = r"(https?://|www\.)\S+|\b(linkedin|github)\.com/\S*"
PHONE = r"\+?\d[\d\s().-]{8,}\d"


# A phone number has 10 or more digits. "2019 - 2023" has 8, so dates stay
def hide_phone(match):
    return "[PHONE]" if sum(c.isdigit() for c in match.group()) >= 10 else match.group()


# Gives back the CV text without the candidate's name, email, phone and links
def clean_cv(text, name=""):
    # Emails, links and phones first, so a name inside an email doesn't break it
    text = re.sub(EMAIL, "[EMAIL]", text)
    text = re.sub(LINK, "[LINK]", text, flags=re.IGNORECASE)
    text = re.sub(PHONE, hide_phone, text)
    for word in name.split():
        if len(word) > 2:   # skip tiny words like "Al"
            text = re.sub(rf"\b{re.escape(word)}\b", "[NAME]", text, flags=re.IGNORECASE)
    return text
