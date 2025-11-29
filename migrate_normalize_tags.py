#!/usr/bin/env python3
"""
Migration helper: create `tag` and `task_tag` tables and populate mappings
from existing `task.tags` string column (if present).

Usage: python migrate_normalize_tags.py
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
        cur = conn.cursor()

        # Create tag table if not exists
        cur.execute("""
        CREATE TABLE IF NOT EXISTS tag (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
        """)

        # Create association table task_tag
        cur.execute("""
        CREATE TABLE IF NOT EXISTS task_tag (
            task_id INTEGER NOT NULL,
            tag_id INTEGER NOT NULL,
            PRIMARY KEY (task_id, tag_id)
        )
        """)

        conn.commit()

        # If task table has tags column, migrate entries
        try:
            cur.execute("PRAGMA table_info('task')")
            cols = [r[1] for r in cur.fetchall()]
            if 'tags' in cols:
                print('Migrating existing task.tags values into normalized tag tables...')
                cur.execute("SELECT id, tags FROM task WHERE tags IS NOT NULL AND tags != ''")
                rows = cur.fetchall()
                for task_id, tags_str in rows:
                    names = [t.strip() for t in tags_str.split(',') if t.strip()]
                    for name in names:
                        # insert or ignore tag
                        cur.execute("INSERT OR IGNORE INTO tag(name) VALUES(?)", (name,))
                        cur.execute("SELECT id FROM tag WHERE lower(name)=lower(?)", (name,))
                        tag_row = cur.fetchone()
                        if tag_row:
                            tag_id = tag_row[0]
                            # insert mapping
                            cur.execute("INSERT OR IGNORE INTO task_tag(task_id, tag_id) VALUES(?,?)", (task_id, tag_id))

                conn.commit()
                print('Migration of tags completed.')
            else:
                print('No string `tags` column found on task table; nothing to migrate.')
        except Exception as e:
            print('Error while migrating tags:', e)

        print('Normalization migration finished successfully.')
    finally:
        conn.close()


if __name__ == '__main__':
    main()
