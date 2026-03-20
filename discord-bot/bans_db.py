import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "bans.db"


class BansDB:
    """SQLite-backed email ban storage with exact-match lookups."""

    def __init__(self, db_path=None):
        self.db_path = str(db_path or DEFAULT_DB_PATH)
        self._conn = sqlite3.connect(self.db_path)
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS bans ("
            "  email TEXT PRIMARY KEY COLLATE NOCASE,"
            "  banned_by TEXT,"
            "  banned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            ")"
        )
        self._conn.commit()

    def close(self):
        self._conn.close()

    def add(self, email, banned_by="unknown"):
        """Ban an email. Returns True if newly banned, False if already banned."""
        email = email.strip().lower()
        try:
            self._conn.execute(
                "INSERT INTO bans (email, banned_by) VALUES (?, ?)",
                (email, str(banned_by)),
            )
            self._conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def remove(self, email):
        """Unban an email. Returns True if it was banned, False if not found."""
        email = email.strip().lower()
        cursor = self._conn.execute("DELETE FROM bans WHERE email = ?", (email,))
        self._conn.commit()
        return cursor.rowcount > 0

    def is_banned(self, email):
        """Check if an email is banned (exact match, case-insensitive)."""
        email = email.strip().lower()
        row = self._conn.execute(
            "SELECT 1 FROM bans WHERE email = ?", (email,)
        ).fetchone()
        return row is not None

    def list_all(self):
        """Return a list of all banned emails."""
        rows = self._conn.execute(
            "SELECT email FROM bans ORDER BY banned_at"
        ).fetchall()
        return [row[0] for row in rows]

    def import_from_text(self, text_path):
        """One-time migration helper: import emails from a bans.txt file."""
        path = Path(text_path)
        if not path.exists():
            return 0
        count = 0
        with open(path) as f:
            for line in f:
                email = line.strip()
                if email and self.add(email, banned_by="migrated_from_txt"):
                    count += 1
        return count
