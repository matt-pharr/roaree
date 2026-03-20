import datetime
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


# --- Time range parsing ---

_TIME_RANGE_RE = re.compile(
    r'^\s*(\d+)\s*([ymw]|years?|months?|weeks?)?\s*$',
    re.IGNORECASE,
)

_UNIT_MAP = {
    'y': 'years', 'year': 'years', 'years': 'years',
    'm': 'months', 'month': 'months', 'months': 'months',
    'w': 'weeks', 'week': 'weeks', 'weeks': 'weeks',
}


def parse_time_range(text):
    """Parse a time range string into (timedelta, unit_name) or None for all time.

    Accepts formats like: "5" (5 months), "5m", "5 months", "1y", "1 year", "1w", etc.
    Bare number defaults to months.

    Returns:
        (datetime.timedelta, unit_name) where unit_name is 'years', 'months', or 'weeks'.
        None if text is empty/None (meaning all time).

    Raises:
        ValueError if the text can't be parsed.
    """
    if not text or not text.strip():
        return None

    m = _TIME_RANGE_RE.match(text)
    if not m:
        raise ValueError(f"Could not parse time range: {text!r}. Use e.g. 5, 5m, 1y, 2w.")

    amount = int(m.group(1))
    raw_unit = m.group(2)

    if raw_unit is None:
        unit = 'months'
    else:
        unit = _UNIT_MAP.get(raw_unit.lower())
        if unit is None:
            raise ValueError(f"Unknown time unit: {raw_unit!r}. Use y/m/w.")

    if unit == 'years':
        delta = datetime.timedelta(days=amount * 365)
    elif unit == 'months':
        delta = datetime.timedelta(days=amount * 30)
    elif unit == 'weeks':
        delta = datetime.timedelta(weeks=amount)

    return (delta, unit)
