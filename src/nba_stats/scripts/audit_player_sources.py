import os
import csv
import sqlite3
from typing import Set, Tuple

from .common_utils import get_db_connection, logger
from ..config.settings import PROJECT_ROOT, SEASON_ID


def normalize_name(name: str) -> str:
    if not isinstance(name, str):
        return ""
    return name.strip().lower().replace(".", "").replace("'", "")


def load_player_names_from_db(conn: sqlite3.Connection) -> Set[str]:
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT player_name FROM Players")
    rows = cursor.fetchall()
    return {normalize_name(r[0]) for r in rows if r and r[0]}


def load_player_names_from_csv(csv_path: str, name_column: str = "Player") -> Set[str]:
    names: Set[str] = set()
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get(name_column)
            if name:
                names.add(normalize_name(name))
    return names


def write_report(report_path: str, title: str, items: Set[str]) -> None:
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n")
        for item in sorted(items):
            f.write(f"- {item}\n")


def write_mapping_template(template_path: str, unmapped: Set[str]) -> None:
    with open(template_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["source_name", "canonical_name"]) 
        for name in sorted(unmapped):
            writer.writerow([name, ""])  # leave canonical_name blank for developer to fill


def main() -> None:
    conn = get_db_connection()
    if conn is None:
        logger.error("Could not connect to database.")
        return

    try:
        db_names = load_player_names_from_db(conn)

        salaries_csv = os.path.join(PROJECT_ROOT, "data", f"player_salaries_{SEASON_ID}.csv")
        darko_csv = os.path.join(PROJECT_ROOT, "data", f"darko_dpm_{SEASON_ID}.csv")

        csv_names_salaries = load_player_names_from_csv(salaries_csv)
        csv_names_darko = load_player_names_from_csv(darko_csv)

        csv_union = csv_names_salaries.union(csv_names_darko)

        only_in_csv = csv_union.difference(db_names)
        only_in_db = db_names.difference(csv_union)

        reports_dir = os.path.join(PROJECT_ROOT, "reports")
        os.makedirs(reports_dir, exist_ok=True)

        write_report(os.path.join(reports_dir, "player_names_only_in_csv.md"), "Player names present in CSVs but not in DB", only_in_csv)
        write_report(os.path.join(reports_dir, "player_names_only_in_db.md"), "Player names present in DB but not in CSVs", only_in_db)

        # Generate mapping template for unresolved CSV names
        mappings_dir = os.path.join(PROJECT_ROOT, "mappings")
        os.makedirs(mappings_dir, exist_ok=True)
        write_mapping_template(os.path.join(mappings_dir, "player_name_map.csv"), only_in_csv)

        logger.info("Audit complete. Reports written to 'reports/' and mapping template to 'mappings/'.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()


