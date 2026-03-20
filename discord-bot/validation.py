import re

VALID_EMAIL_DOMAINS = [
    "@columbia.edu",
    "@barnard.edu",
    "@tc.columbia.edu",
    "@cumc.columbia.edu",
    "@ldeo.columbia.edu",
    "@gsb.columbia.edu",
    "@cs.columbia.edu",
    "@caa.columbia.edu",
]


def extract_email_domain(email):
    """Extract the @domain portion from an email string, or None if not found."""
    matches = re.findall(r'@[\w.-]+', email)
    if matches:
        return matches[0].lower()
    return None


def is_valid_email(email):
    """Check if an email has a valid Columbia/Barnard domain."""
    domain = extract_email_domain(email)
    return domain is not None and domain in VALID_EMAIL_DOMAINS


def classify_email_input(email_input, prefix='?'):
    """Classify user input during verification.

    Returns a tuple of (status, detail):
        ("valid", email)        - valid Columbia/Barnard email
        ("invalid_domain", msg) - has @, but wrong domain
        ("cancelled", None)     - user typed a command (starts with prefix)
        ("error", None)         - unrecognizable input
    """
    email_input = email_input.strip()
    domain = extract_email_domain(email_input)

    if domain and domain in VALID_EMAIL_DOMAINS:
        return ("valid", email_input)
    elif '@' in email_input:
        domain_list = '\n'.join(VALID_EMAIL_DOMAINS)
        msg = (
            f"{email_input} is not a valid email address. You must use an email ending in:\n"
            f"```\n{domain_list}\n```\n"
            f"If you think your email should be valid, please contact staff. "
            f"Type {prefix}verify to try again."
        )
        return ("invalid_domain", msg)
    elif email_input.startswith(prefix):
        return ("cancelled", None)
    else:
        return ("error", None)
