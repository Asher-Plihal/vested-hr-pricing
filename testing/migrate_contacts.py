"""
One-time migration: rename clients -> contacts and client_id -> contact_id.
Safe to re-run — skips if already migrated.

Usage:
    python testing/migrate_contacts.py
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from database import engine

STEPS = [
    ("Rename table clients -> contacts",
     "ALTER TABLE clients RENAME TO contacts"),
    ("Rename wc_lines.client_id -> contact_id",
     "ALTER TABLE wc_lines RENAME COLUMN client_id TO contact_id"),
    ("Rename wc_losses.client_id -> contact_id",
     "ALTER TABLE wc_losses RENAME COLUMN client_id TO contact_id"),
    ("Rename suta_lines.client_id -> contact_id",
     "ALTER TABLE suta_lines RENAME COLUMN client_id TO contact_id"),
]

def table_exists(conn, name):
    row = conn.execute(
        text("SELECT name FROM sqlite_master WHERE type='table' AND name=:n"),
        {"n": name}
    ).fetchone()
    return row is not None

def column_exists(conn, table, column):
    rows = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
    return any(r[1] == column for r in rows)

with engine.connect() as conn:
    already_contacts = not table_exists(conn, "clients") and table_exists(conn, "contacts")
    already_columns  = already_contacts and not column_exists(conn, "wc_lines", "client_id")
    if already_contacts and already_columns:
        print("Migration already applied. Nothing to do.")
        sys.exit(0)

    for label, sql in STEPS:
        try:
            conn.execute(text(sql))
            print(f"  OK  {label}")
        except Exception as e:
            print(f"  SKIP {label}: {e}")

    conn.commit()
    print("Migration complete.")
