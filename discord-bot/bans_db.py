import re
import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "bans.db"

# Matches: "email = <@discord_id> (discord_id)"
VERIF_MSG_PATTERN = re.compile(
    r'^(.+?@[\w.-]+)\s*=\s*<@(\d+)>\s*\((\d+)\)$'
)


def parse_verif_message(text):
    """Parse a verification channel message.

    Returns (email, discord_id) or None if the message doesn't match.
    """
    m = VERIF_MSG_PATTERN.match(text.strip())
    if m:
        return (m.group(1).strip().lower(), int(m.group(2)))
    return None


class BotDB:
    """SQLite-backed storage for bans and verifications."""

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
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS verifications ("
            "  email TEXT NOT NULL COLLATE NOCASE,"
            "  discord_id INTEGER NOT NULL,"
            "  verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,"
            "  PRIMARY KEY (email, discord_id)"
            ")"
        )
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_verif_discord_id "
            "ON verifications (discord_id)"
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

    # --- Verification methods ---

    def add_verification(self, email, discord_id):
        """Record a verification. Returns True if new, False if duplicate."""
        email = email.strip().lower()
        try:
            self._conn.execute(
                "INSERT INTO verifications (email, discord_id) VALUES (?, ?)",
                (email, int(discord_id)),
            )
            self._conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def lookup_by_discord_id(self, discord_id):
        """Return list of emails associated with a Discord user ID."""
        rows = self._conn.execute(
            "SELECT email, verified_at FROM verifications "
            "WHERE discord_id = ? ORDER BY verified_at",
            (int(discord_id),),
        ).fetchall()
        return [(row[0], row[1]) for row in rows]

    def lookup_by_email(self, email):
        """Return list of (discord_id, verified_at) for an email."""
        email = email.strip().lower()
        rows = self._conn.execute(
            "SELECT discord_id, verified_at FROM verifications "
            "WHERE email = ? ORDER BY verified_at",
            (email,),
        ).fetchall()
        return [(row[0], row[1]) for row in rows]

    def verification_count(self):
        """Return total number of unique verified users."""
        row = self._conn.execute(
            "SELECT COUNT(DISTINCT discord_id) FROM verifications"
        ).fetchone()
        return row[0]

    def verifications_since(self, since_timestamp):
        """Return count of verifications since a given ISO timestamp."""
        row = self._conn.execute(
            "SELECT COUNT(*) FROM verifications WHERE verified_at >= ?",
            (since_timestamp,),
        ).fetchone()
        return row[0]

    def monthly_verification_counts(self, since=None):
        """Return list of (year, month, count) tuples for verifications per month."""
        if since:
            rows = self._conn.execute(
                "SELECT CAST(strftime('%Y', verified_at) AS INTEGER),"
                "       CAST(strftime('%m', verified_at) AS INTEGER),"
                "       COUNT(*)"
                "  FROM verifications"
                " WHERE verified_at >= ?"
                " GROUP BY strftime('%Y-%m', verified_at)"
                " ORDER BY strftime('%Y-%m', verified_at)",
                (since,),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT CAST(strftime('%Y', verified_at) AS INTEGER),"
                "       CAST(strftime('%m', verified_at) AS INTEGER),"
                "       COUNT(*)"
                "  FROM verifications"
                " GROUP BY strftime('%Y-%m', verified_at)"
                " ORDER BY strftime('%Y-%m', verified_at)"
            ).fetchall()
        return [(row[0], row[1], row[2]) for row in rows]

    def weekly_verification_counts(self, since=None):
        """Return list of (iso_date_string, count) tuples grouped by ISO week start (Monday)."""
        if since:
            rows = self._conn.execute(
                "SELECT date(verified_at, 'weekday 0', '-6 days') AS week_start,"
                "       COUNT(*)"
                "  FROM verifications"
                " WHERE verified_at >= ?"
                " GROUP BY week_start"
                " ORDER BY week_start",
                (since,),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT date(verified_at, 'weekday 0', '-6 days') AS week_start,"
                "       COUNT(*)"
                "  FROM verifications"
                " GROUP BY week_start"
                " ORDER BY week_start"
            ).fetchall()
        return [(row[0], row[1]) for row in rows]

    def import_verif_messages(self, messages):
        """Import parsed verification messages. Returns count of new records.

        Args:
            messages: iterable of (text, timestamp) tuples where text is the
                      raw message content and timestamp is an ISO string or None.
        """
        count = 0
        for text, timestamp in messages:
            parsed = parse_verif_message(text)
            if not parsed:
                continue
            email, discord_id = parsed
            try:
                if timestamp:
                    self._conn.execute(
                        "INSERT INTO verifications (email, discord_id, verified_at) "
                        "VALUES (?, ?, ?)",
                        (email, discord_id, timestamp),
                    )
                else:
                    self._conn.execute(
                        "INSERT INTO verifications (email, discord_id) VALUES (?, ?)",
                        (email, discord_id),
                    )
                count += 1
            except sqlite3.IntegrityError:
                pass
        self._conn.commit()
        return count


# Backwards-compatible alias
BansDB = BotDB
