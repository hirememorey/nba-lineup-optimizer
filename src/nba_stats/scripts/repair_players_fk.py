import sqlite3
from .common_utils import get_db_connection, logger


def null_invalid_player_team_ids(conn: sqlite3.Connection) -> int:
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE Players
        SET team_id = NULL
        WHERE team_id IS NOT NULL
          AND team_id NOT IN (SELECT team_id FROM Teams)
        """
    )
    changed = cursor.rowcount or 0
    conn.commit()
    return changed


def main() -> None:
    conn = get_db_connection()
    if conn is None:
        logger.error("Could not connect to database.")
        return
    try:
        conn.execute("PRAGMA foreign_keys = ON;")
        changed = null_invalid_player_team_ids(conn)
        logger.info(f"Players repair complete. team_id set to NULL for {changed} rows with invalid FK.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()


