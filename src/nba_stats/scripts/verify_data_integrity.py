import sqlite3
from .common_utils import get_db_connection, logger
from ..config.settings import SEASON_ID


def assert_row_count(conn: sqlite3.Connection, query: str, expected_min: int = None, expected_exact: int = None, label: str = "") -> None:
    cursor = conn.cursor()
    cursor.execute(query)
    value = cursor.fetchone()[0]
    if expected_exact is not None:
        assert value == expected_exact, f"{label} expected exactly {expected_exact}, found {value}"
    elif expected_min is not None:
        assert value >= expected_min, f"{label} expected at least {expected_min}, found {value}"
    logger.info(f"PASS {label}: {value}")


def main() -> None:
    conn = get_db_connection()
    if conn is None:
        logger.error("Could not connect to database.")
        return
    try:
        # Enforce FK and verify no violations
        conn.execute("PRAGMA foreign_keys = ON;")
        fk_violations = list(conn.execute("PRAGMA foreign_key_check;").fetchall())
        assert len(fk_violations) == 0, f"Foreign key violations found: {fk_violations[:5]} ..."
        logger.info("PASS: No foreign key violations")

        # Quantitative checks
        assert_row_count(conn, "SELECT COUNT(*) FROM Teams", expected_exact=30, label="Teams count")
        assert_row_count(conn, f"SELECT COUNT(*) FROM Games WHERE season = '{SEASON_ID}'", expected_exact=1230, label="Games for target season")
        assert_row_count(conn, "SELECT COUNT(DISTINCT game_id) FROM Possessions", expected_exact=1230, label="Possessions game coverage")
        assert_row_count(conn, f"SELECT COUNT(*) FROM PlayerSalaries WHERE season_id = '{SEASON_ID}'", expected_min=700, label="Player salaries for season")
        assert_row_count(conn, f"SELECT COUNT(*) FROM PlayerSkills WHERE season_id = '{SEASON_ID}'", expected_min=700, label="Player skills for season")

        # Sanity: ensure archetype features exist
        try:
            assert_row_count(conn, f"SELECT COUNT(*) FROM PlayerArchetypeFeatures WHERE season = '{SEASON_ID}'", expected_min=400, label="Archetype features present")
        except sqlite3.Error:
            logger.warning("PlayerArchetypeFeatures table missing or not populated; skipping check.")

        logger.info("All verification checks passed.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()


