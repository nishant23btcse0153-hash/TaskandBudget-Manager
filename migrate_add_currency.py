#!/usr/bin/env python3
"""
Migration helper: add `currency` column to `user` and `budget` tables if missing.

Usage: python migrate_add_currency.py
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
        # user.currency
        if column_exists(conn, 'user', 'currency'):
            print('Column `user.currency` already exists.')
        else:
            print('Adding `currency` column to `user` table...')
            conn.execute("ALTER TABLE user ADD COLUMN currency TEXT")
            conn.execute("UPDATE user SET currency = 'USD' WHERE currency IS NULL")
            conn.commit()
            print('Added user.currency and set default USD for existing users.')

        # budget.currency
        if column_exists(conn, 'budget', 'currency'):
            print('Column `budget.currency` already exists.')
        else:
            print('Adding `currency` column to `budget` table...')
            conn.execute("ALTER TABLE budget ADD COLUMN currency TEXT")
            conn.execute("UPDATE budget SET currency = 'USD' WHERE currency IS NULL")
            conn.commit()
            print('Added budget.currency and set default USD for existing transactions.')

        print('Migration finished successfully.')
    finally:
        conn.close()


if __name__ == '__main__':
    main()
