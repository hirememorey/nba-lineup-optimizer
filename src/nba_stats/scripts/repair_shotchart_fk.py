import sqlite3
from .common_utils import get_db_connection, logger


def delete_invalid_shotchart_rows(conn: sqlite3.Connection) -> int:
    """Delete PlayerShotChart rows whose foreign keys do not exist in parent tables."""
    cursor = conn.cursor()

    # Delete rows with invalid team_id
    cursor.execute(
        """
        DELETE FROM PlayerShotChart
        WHERE team_id NOT IN (SELECT team_id FROM Teams)
        """
    )
    deleted_teams = cursor.rowcount

    # Delete rows with invalid game_id
    cursor.execute(
        """
        DELETE FROM PlayerShotChart
        WHERE game_id NOT IN (SELECT game_id FROM Games)
        """
    )
    deleted_games = cursor.rowcount

    conn.commit()
    return (deleted_teams or 0) + (deleted_games or 0)


def main() -> None:
    conn = get_db_connection()
    if conn is None:
        logger.error("Could not connect to database.")
        return
    try:
        conn.execute("PRAGMA foreign_keys = ON;")
        deleted = delete_invalid_shotchart_rows(conn)

        # Re-check integrity limited to PlayerShotChart
        violations = list(
            conn.execute("PRAGMA foreign_key_check('PlayerShotChart')").fetchall()
        )
        if violations:
            logger.warning(
                f"PlayerShotChart FK violations remain after repair: sample {violations[:5]}"
            )
        logger.info(f"PlayerShotChart repair complete. Deleted: {deleted}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()


