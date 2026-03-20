import sqlite3
import tempfile
from pathlib import Path

import pytest

from bans_db import BotDB, parse_verif_message
from charts import generate_verification_chart
from validation import extract_email_domain, is_valid_email, classify_email_input, parse_time_range


# --- Fixtures ---

@pytest.fixture
def db(tmp_path):
    """Create a temporary BotDB for each test."""
    db = BotDB(db_path=tmp_path / "test.db")
    yield db
    db.close()


# --- BansDB tests ---

class TestBans:
    def test_add_and_is_banned(self, db):
        assert not db.is_banned("test@columbia.edu")
        assert db.add("test@columbia.edu", banned_by="admin")
        assert db.is_banned("test@columbia.edu")

    def test_add_duplicate_returns_false(self, db):
        assert db.add("test@columbia.edu")
        assert not db.add("test@columbia.edu")

    def test_case_insensitive(self, db):
        db.add("Test@Columbia.EDU")
        assert db.is_banned("test@columbia.edu")
        assert db.is_banned("TEST@COLUMBIA.EDU")

    def test_exact_match_no_substring(self, db):
        db.add("foo@columbia.edu")
        assert not db.is_banned("foo@columbia.education")
        assert not db.is_banned("afoo@columbia.edu")
        assert db.is_banned("foo@columbia.edu")

    def test_remove(self, db):
        db.add("test@columbia.edu")
        assert db.remove("test@columbia.edu")
        assert not db.is_banned("test@columbia.edu")

    def test_remove_nonexistent_returns_false(self, db):
        assert not db.remove("nobody@columbia.edu")

    def test_list_all(self, db):
        db.add("b@columbia.edu")
        db.add("a@barnard.edu")
        result = db.list_all()
        assert len(result) == 2
        assert "b@columbia.edu" in result
        assert "a@barnard.edu" in result

    def test_list_all_empty(self, db):
        assert db.list_all() == []

    def test_import_from_text(self, db, tmp_path):
        txt = tmp_path / "bans.txt"
        txt.write_text("alice@columbia.edu\nbob@barnard.edu\n\n")
        count = db.import_from_text(txt)
        assert count == 2
        assert db.is_banned("alice@columbia.edu")
        assert db.is_banned("bob@barnard.edu")

    def test_import_from_text_no_file(self, db, tmp_path):
        count = db.import_from_text(tmp_path / "nonexistent.txt")
        assert count == 0

    def test_import_idempotent(self, db, tmp_path):
        txt = tmp_path / "bans.txt"
        txt.write_text("alice@columbia.edu\n")
        db.import_from_text(txt)
        count = db.import_from_text(txt)
        assert count == 0

    def test_whitespace_handling(self, db):
        db.add("  test@columbia.edu  ")
        assert db.is_banned("test@columbia.edu")
        assert db.is_banned("  test@columbia.edu  ")


# --- Verification DB tests ---

class TestVerifications:
    def test_add_and_lookup_by_discord_id(self, db):
        assert db.add_verification("user@columbia.edu", 12345)
        records = db.lookup_by_discord_id(12345)
        assert len(records) == 1
        assert records[0][0] == "user@columbia.edu"
        assert records[0][1] is not None  # has timestamp

    def test_add_duplicate_returns_false(self, db):
        assert db.add_verification("user@columbia.edu", 12345)
        assert not db.add_verification("user@columbia.edu", 12345)

    def test_same_email_different_users(self, db):
        assert db.add_verification("user@columbia.edu", 111)
        assert db.add_verification("user@columbia.edu", 222)
        records = db.lookup_by_email("user@columbia.edu")
        assert len(records) == 2

    def test_same_user_different_emails(self, db):
        assert db.add_verification("a@columbia.edu", 111)
        assert db.add_verification("b@columbia.edu", 111)
        records = db.lookup_by_discord_id(111)
        assert len(records) == 2

    def test_lookup_by_email(self, db):
        db.add_verification("user@columbia.edu", 12345)
        records = db.lookup_by_email("user@columbia.edu")
        assert len(records) == 1
        assert records[0][0] == 12345

    def test_lookup_by_email_case_insensitive(self, db):
        db.add_verification("User@Columbia.EDU", 12345)
        records = db.lookup_by_email("user@columbia.edu")
        assert len(records) == 1

    def test_lookup_empty(self, db):
        assert db.lookup_by_discord_id(99999) == []
        assert db.lookup_by_email("nobody@columbia.edu") == []

    def test_verification_count(self, db):
        assert db.verification_count() == 0
        db.add_verification("a@columbia.edu", 111)
        db.add_verification("b@columbia.edu", 222)
        assert db.verification_count() == 2

    def test_verification_count_deduplicates_users(self, db):
        db.add_verification("a@columbia.edu", 111)
        db.add_verification("b@columbia.edu", 111)
        assert db.verification_count() == 1

    def test_verifications_since(self, db):
        db.add_verification("a@columbia.edu", 111)
        # All verifications are "now", so counting since epoch should get them all
        assert db.verifications_since("2000-01-01 00:00:00") == 1
        # Counting since far future should get none
        assert db.verifications_since("2099-01-01 00:00:00") == 0

    def test_monthly_verification_counts(self, db):
        messages = [
            ("a@columbia.edu = <@1> (1)", "2024-01-15 10:00:00"),
            ("b@columbia.edu = <@2> (2)", "2024-01-20 12:00:00"),
            ("c@columbia.edu = <@3> (3)", "2024-03-05 08:00:00"),
        ]
        db.import_verif_messages(messages)
        counts = db.monthly_verification_counts()
        assert len(counts) == 2
        assert counts[0] == (2024, 1, 2)  # Jan: 2 verifications
        assert counts[1] == (2024, 3, 1)  # Mar: 1 verification

    def test_monthly_verification_counts_empty(self, db):
        assert db.monthly_verification_counts() == []

    def test_monthly_verification_counts_with_since(self, db):
        messages = [
            ("a@columbia.edu = <@1> (1)", "2023-06-15 10:00:00"),
            ("b@columbia.edu = <@2> (2)", "2024-01-20 12:00:00"),
            ("c@columbia.edu = <@3> (3)", "2024-03-05 08:00:00"),
        ]
        db.import_verif_messages(messages)
        counts = db.monthly_verification_counts(since="2024-01-01 00:00:00")
        assert len(counts) == 2
        assert counts[0] == (2024, 1, 1)
        assert counts[1] == (2024, 3, 1)

    def test_weekly_verification_counts(self, db):
        messages = [
            ("a@columbia.edu = <@1> (1)", "2024-01-15 10:00:00"),  # Mon
            ("b@columbia.edu = <@2> (2)", "2024-01-16 12:00:00"),  # Tue same week
            ("c@columbia.edu = <@3> (3)", "2024-01-22 08:00:00"),  # next Mon
        ]
        db.import_verif_messages(messages)
        counts = db.weekly_verification_counts()
        assert len(counts) == 2
        assert counts[0][1] == 2  # first week: 2
        assert counts[1][1] == 1  # second week: 1

    def test_weekly_verification_counts_with_since(self, db):
        messages = [
            ("a@columbia.edu = <@1> (1)", "2023-06-15 10:00:00"),
            ("b@columbia.edu = <@2> (2)", "2024-01-15 12:00:00"),
        ]
        db.import_verif_messages(messages)
        counts = db.weekly_verification_counts(since="2024-01-01 00:00:00")
        assert len(counts) == 1
        assert counts[0][1] == 1

    def test_weekly_verification_counts_empty(self, db):
        assert db.weekly_verification_counts() == []


# --- Chart generation tests ---

class TestGenerateVerificationChart:
    def test_returns_none_for_empty(self):
        assert generate_verification_chart([]) is None

    def test_returns_png_bytes(self):
        data = [(2024, 1, 5), (2024, 2, 3), (2024, 3, 7)]
        buf = generate_verification_chart(data)
        assert buf is not None
        header = buf.read(8)
        # PNG magic bytes
        assert header[:4] == b'\x89PNG'

    def test_single_month(self):
        buf = generate_verification_chart([(2024, 6, 10)])
        assert buf is not None
        assert buf.read(4) == b'\x89PNG'

    def test_multi_year(self):
        data = [(2022, 9, 5), (2023, 1, 10), (2024, 6, 3)]
        buf = generate_verification_chart(data)
        assert buf is not None
        assert buf.read(4) == b'\x89PNG'

    def test_weekly_granularity(self):
        data = [("2024-01-01", 3), ("2024-01-08", 5), ("2024-01-15", 2)]
        buf = generate_verification_chart(data, granularity='weekly')
        assert buf is not None
        assert buf.read(4) == b'\x89PNG'

    def test_weekly_single_week(self):
        buf = generate_verification_chart([("2024-06-03", 7)], granularity='weekly')
        assert buf is not None
        assert buf.read(4) == b'\x89PNG'


# --- parse_verif_message tests ---

class TestParseVerifMessage:
    def test_standard_format(self):
        result = parse_verif_message("mcp2198@columbia.edu = <@140951260323905537> (140951260323905537)")
        assert result == ("mcp2198@columbia.edu", 140951260323905537)

    def test_subdomain_email(self):
        result = parse_verif_message("user@tc.columbia.edu = <@12345> (12345)")
        assert result == ("user@tc.columbia.edu", 12345)

    def test_extra_whitespace(self):
        result = parse_verif_message("  user@columbia.edu  =  <@12345>  (12345)  ")
        assert result == ("user@columbia.edu", 12345)

    def test_non_matching_message(self):
        assert parse_verif_message("some random message") is None
        assert parse_verif_message("user@columbia.edu banned by admin") is None

    def test_empty_string(self):
        assert parse_verif_message("") is None

    def test_email_lowercased(self):
        result = parse_verif_message("User@Columbia.EDU = <@12345> (12345)")
        assert result[0] == "user@columbia.edu"


class TestImportVerifMessages:
    def test_import_messages(self, db):
        messages = [
            ("mcp2198@columbia.edu = <@140951260323905537> (140951260323905537)", "2024-01-15 10:30:00"),
            ("yz4219@columbia.edu = <@987654321> (987654321)", "2024-02-20 14:00:00"),
        ]
        count = db.import_verif_messages(messages)
        assert count == 2
        assert db.verification_count() == 2

    def test_import_skips_non_matching(self, db):
        messages = [
            ("mcp2198@columbia.edu = <@12345> (12345)", "2024-01-15 10:30:00"),
            ("some random log message", "2024-01-15 10:31:00"),
            ("email@columbia.edu banned by admin", "2024-01-15 10:32:00"),
        ]
        count = db.import_verif_messages(messages)
        assert count == 1

    def test_import_idempotent(self, db):
        messages = [
            ("user@columbia.edu = <@12345> (12345)", "2024-01-15 10:30:00"),
        ]
        assert db.import_verif_messages(messages) == 1
        assert db.import_verif_messages(messages) == 0

    def test_import_preserves_timestamp(self, db):
        messages = [
            ("user@columbia.edu = <@12345> (12345)", "2024-06-15 09:00:00"),
        ]
        db.import_verif_messages(messages)
        records = db.lookup_by_discord_id(12345)
        assert records[0][1] == "2024-06-15 09:00:00"

    def test_import_no_timestamp(self, db):
        messages = [
            ("user@columbia.edu = <@12345> (12345)", None),
        ]
        count = db.import_verif_messages(messages)
        assert count == 1
        records = db.lookup_by_discord_id(12345)
        assert records[0][1] is not None  # gets default CURRENT_TIMESTAMP


# --- Validation tests ---

class TestExtractEmailDomain:
    def test_standard_email(self):
        assert extract_email_domain("user@columbia.edu") == "@columbia.edu"

    def test_subdomain_email(self):
        assert extract_email_domain("user@tc.columbia.edu") == "@tc.columbia.edu"

    def test_no_at_sign(self):
        assert extract_email_domain("noemail") is None

    def test_empty_string(self):
        assert extract_email_domain("") is None

    def test_case_insensitive(self):
        assert extract_email_domain("User@Columbia.EDU") == "@columbia.edu"

    def test_with_whitespace(self):
        assert extract_email_domain("  user@barnard.edu  ") == "@barnard.edu"


class TestIsValidEmail:
    def test_valid_columbia(self):
        assert is_valid_email("user@columbia.edu")

    def test_valid_barnard(self):
        assert is_valid_email("user@barnard.edu")

    def test_valid_subdomain(self):
        assert is_valid_email("user@tc.columbia.edu")
        assert is_valid_email("user@cs.columbia.edu")
        assert is_valid_email("user@gsb.columbia.edu")

    def test_invalid_domain(self):
        assert not is_valid_email("user@gmail.com")
        assert not is_valid_email("user@columbia.education")

    def test_no_domain(self):
        assert not is_valid_email("nodomain")

    def test_empty(self):
        assert not is_valid_email("")


class TestClassifyEmailInput:
    def test_valid_email(self):
        status, detail = classify_email_input("user@columbia.edu")
        assert status == "valid"
        assert detail == "user@columbia.edu"

    def test_invalid_domain(self):
        status, detail = classify_email_input("user@gmail.com")
        assert status == "invalid_domain"
        assert "not a valid email" in detail

    def test_cancelled_with_prefix(self):
        status, detail = classify_email_input("?help")
        assert status == "cancelled"
        assert detail is None

    def test_cancelled_custom_prefix(self):
        status, detail = classify_email_input("!help", prefix="!")
        assert status == "cancelled"

    def test_garbage_input(self):
        status, detail = classify_email_input("asdfghjkl")
        assert status == "error"

    def test_whitespace_stripped(self):
        status, detail = classify_email_input("  user@columbia.edu  ")
        assert status == "valid"
        assert detail == "user@columbia.edu"

    def test_empty_string(self):
        status, detail = classify_email_input("")
        assert status == "error"


class TestParseTimeRange:
    def test_none_returns_none(self):
        assert parse_time_range(None) is None

    def test_empty_returns_none(self):
        assert parse_time_range("") is None
        assert parse_time_range("   ") is None

    def test_bare_number_defaults_to_months(self):
        delta, unit = parse_time_range("5")
        assert unit == "months"
        assert delta.days == 150

    def test_months_short(self):
        delta, unit = parse_time_range("3m")
        assert unit == "months"
        assert delta.days == 90

    def test_months_with_space(self):
        delta, unit = parse_time_range("3 m")
        assert unit == "months"

    def test_months_with_extra_spaces(self):
        delta, unit = parse_time_range("  3   m  ")
        assert unit == "months"

    def test_months_long(self):
        delta, unit = parse_time_range("2 months")
        assert unit == "months"
        assert delta.days == 60

    def test_month_singular(self):
        delta, unit = parse_time_range("1 month")
        assert unit == "months"

    def test_years_short(self):
        delta, unit = parse_time_range("1y")
        assert unit == "years"
        assert delta.days == 365

    def test_years_with_space(self):
        delta, unit = parse_time_range("2 y")
        assert unit == "years"
        assert delta.days == 730

    def test_years_long(self):
        delta, unit = parse_time_range("1 year")
        assert unit == "years"

    def test_years_plural(self):
        delta, unit = parse_time_range("3 years")
        assert unit == "years"

    def test_weeks_short(self):
        delta, unit = parse_time_range("2w")
        assert unit == "weeks"
        assert delta.days == 14

    def test_weeks_with_space(self):
        delta, unit = parse_time_range("1 w")
        assert unit == "weeks"
        assert delta.days == 7

    def test_weeks_long(self):
        delta, unit = parse_time_range("4 weeks")
        assert unit == "weeks"

    def test_case_insensitive(self):
        delta, unit = parse_time_range("2Y")
        assert unit == "years"
        delta, unit = parse_time_range("3M")
        assert unit == "months"
        delta, unit = parse_time_range("1W")
        assert unit == "weeks"

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            parse_time_range("abc")
        with pytest.raises(ValueError):
            parse_time_range("5d")
        with pytest.raises(ValueError):
            parse_time_range("five months")
