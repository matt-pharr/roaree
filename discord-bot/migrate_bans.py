#!/usr/bin/env python3
"""One-time migration: bans.txt -> SQLite bans.db"""

from pathlib import Path
from bans_db import BotDB

BANS_TXT = Path(__file__).resolve().parent.parent / "bans.txt"

db = BotDB()
count = db.import_from_text(BANS_TXT)
print(f"Imported {count} new email(s) into bans.db")

print("\nCurrent bans:")
for email in db.list_all():
    print(f"  {email}")

db.close()
