import sqlite3
import tempfile
from pathlib import Path

import pytest

from bans_db import BansDB
from validation import extract_email_domain, is_valid_email, classify_email_input


# --- BansDB tests ---

@pytest.fixture
def db(tmp_path):
    """Create a temporary BansDB for each test."""
    db = BansDB(db_path=tmp_path / "test_bans.db")
    yield db
    db.close()


class TestBansDB:
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
        assert count == 0  # already imported

    def test_whitespace_handling(self, db):
        db.add("  test@columbia.edu  ")
        assert db.is_banned("test@columbia.edu")
        assert db.is_banned("  test@columbia.edu  ")


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
