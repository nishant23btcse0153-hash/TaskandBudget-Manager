#!/usr/bin/env python3
"""
Migration helper: add `priority` and `tags` columns to `task` table if missing.

Usage: python migrate_add_task_priority_tags.py
"""
import shutil
import sqlite3
from pathlib import Path
from config import Config
import sys


def get_sqlite_path(uri: str) -> Path:
    if not uri.startswith('sqlite:'):
        raise ValueError('Only sqlite URIs are supported by this script')
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
        if column_exists(conn, 'task', 'priority'):
            print('Column `priority` already exists — nothing to do for priority.')
        else:
            print('Adding `priority` column to `task` table...')
            conn.execute("ALTER TABLE task ADD COLUMN priority TEXT")
            conn.execute("UPDATE task SET priority = 'Medium' WHERE priority IS NULL")
            conn.commit()

        if column_exists(conn, 'task', 'tags'):
            print('Column `tags` already exists — nothing to do for tags.')
        else:
            print('Adding `tags` column to `task` table...')
            conn.execute("ALTER TABLE task ADD COLUMN tags TEXT")
            conn.execute("UPDATE task SET tags = '' WHERE tags IS NULL")
            conn.commit()

        print('Migration finished successfully.')
    finally:
        conn.close()


if __name__ == '__main__':
    main()
