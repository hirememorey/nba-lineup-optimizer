import sqlite3
from src.nba_stats.scripts.common_utils import get_db_connection


def test_foreign_keys_enforced():
    conn = get_db_connection()
    try:
        conn.execute("PRAGMA foreign_keys = ON;")
        cursor = conn.cursor()

        cursor.execute("CREATE TABLE IF NOT EXISTS Parent (id INTEGER PRIMARY KEY)")
        cursor.execute("CREATE TABLE IF NOT EXISTS Child (id INTEGER PRIMARY KEY, parent_id INTEGER, FOREIGN KEY(parent_id) REFERENCES Parent(id))")

        cursor.execute("DELETE FROM Child")
        cursor.execute("DELETE FROM Parent")
        conn.commit()

        # Insert a child referencing non-existent parent should fail
        try:
            cursor.execute("INSERT INTO Child(id, parent_id) VALUES (1, 999999)")
            conn.commit()
            assert False, "Expected IntegrityError due to FK violation, but insert succeeded"
        except sqlite3.IntegrityError:
            pass
    finally:
        conn.close()


