import sqlite3
from .common_utils import get_db_connection, logger


TABLES_WITH_TEAM_ID = [
    "PlayerSeasonRawStats",
    "PlayerSeasonAdvancedStats",
    "PlayerSeasonDriveStats",
    "PlayerSeasonHustleStats",
    "PlayerSeasonOpponentShootingStats",
    "PlayerSeasonTrackingTouchesStats",
    "PlayerSeasonPassingStats",
    "PlayerSeasonCatchAndShootStats",
    "PlayerSeasonPullUpStats",
    "PlayerLineupStats",
    "PlayerSeasonReboundingStats",
    "PlayerSeasonPostUpStats",
    "PlayerSeasonPaintTouchStats",
    "PlayerSeasonElbowTouchStats",
]


def delete_invalid_team_rows(conn: sqlite3.Connection) -> dict[str, int]:
    counts: dict[str, int] = {}
    cursor = conn.cursor()
    for table in TABLES_WITH_TEAM_ID:
        try:
            cursor.execute(
                f"DELETE FROM {table} WHERE team_id NOT IN (SELECT team_id FROM Teams)"
            )
            deleted = cursor.rowcount or 0
            counts[table] = deleted
            logger.info(f"{table}: deleted {deleted} rows with invalid team_id")
        except sqlite3.Error as e:
            logger.error(f"Error repairing {table}: {e}")
    conn.commit()
    return counts


def main() -> None:
    conn = get_db_connection()
    if conn is None:
        logger.error("Could not connect to database.")
        return
    try:
        conn.execute("PRAGMA foreign_keys = ON;")
        results = delete_invalid_team_rows(conn)
        # Summarize remaining FK violations quickly
        violations = list(conn.execute("PRAGMA foreign_key_check;").fetchall())
        if violations:
            logger.warning(f"FK violations remain after team repair: sample {violations[:5]}")
        logger.info(f"Team FK repair complete: {results}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()


