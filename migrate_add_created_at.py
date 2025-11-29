#!/usr/bin/env python3
"""
Small migration helper: add `created_at` column to `task` table if missing.

Usage: run from project root where `app.db` exists:
    python migrate_add_created_at.py

It will create a backup `app.db.bak` before modifying the database.
"""
import shutil
import sqlite3
from pathlib import Path
from config import Config
import sys


def get_sqlite_path(uri: str) -> Path:
    # support URIs like sqlite:///app.db or sqlite:////absolute/path/app.db
    if not uri.startswith('sqlite:'):
        raise ValueError('Only sqlite URIs are supported by this script')
    # strip sqlite:///
    path = uri.split('sqlite:///')[-1]
    return Path(path)


def column_exists(conn, table: str, column: str) -> bool:
    cur = conn.execute(f"PRAGMA table_info('{table}')")
    cols = [row[1] for row in cur.fetchall()]
    return column in cols


def main():
    cfg = Config()
    uri = cfg.SQLALCHEMY_DATABASE_URI
    db_path = get_sqlite_path(uri)

    if not db_path.exists():
        print(f"Database file not found: {db_path}")
        sys.exit(1)

    backup = db_path.with_suffix(db_path.suffix + '.bak')
    print(f"Creating backup: {backup}")
    shutil.copy2(db_path, backup)

    conn = sqlite3.connect(str(db_path))
    try:
        if column_exists(conn, 'task', 'created_at'):
            print('Column `created_at` already exists — nothing to do.')
            return

        print('Adding `created_at` column to `task` table...')
        # Add column (nullable)
        conn.execute("ALTER TABLE task ADD COLUMN created_at DATETIME")
        # Populate created_at: if deadline exists use deadline, else use current timestamp
        conn.execute("UPDATE task SET created_at = COALESCE(deadline, CURRENT_TIMESTAMP) WHERE created_at IS NULL")
        conn.commit()
        print('Migration completed successfully.')
    finally:
        conn.close()


if __name__ == '__main__':
    main()
