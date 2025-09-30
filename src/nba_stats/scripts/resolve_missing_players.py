import os
import csv
import sqlite3
import unicodedata
from typing import Set, Dict

from .common_utils import get_db_connection, logger, get_nba_stats_client
from ..config.settings import PROJECT_ROOT, SEASON_ID


def normalize_name(name: str) -> str:
    if not isinstance(name, str):
        return ""
    # Strip accents, lowercase, trim, remove punctuation like periods and apostrophes
    base = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('utf-8')
    base = base.lower().strip()
    for ch in [".", "'", ",", "-", "  "]:
        base = base.replace(ch, " ")
    base = " ".join(base.split())
    return base


def load_csv_names() -> Set[str]:
    names: Set[str] = set()
    salaries_csv = os.path.join(PROJECT_ROOT, "data", f"player_salaries_{SEASON_ID}.csv")
    darko_csv = os.path.join(PROJECT_ROOT, "data", f"darko_dpm_{SEASON_ID}.csv")
    for path in [salaries_csv, darko_csv]:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    n = row.get('Player')
                    if n:
                        names.add(normalize_name(n))
    return names


def load_db_names(conn: sqlite3.Connection) -> Set[str]:
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT player_name FROM Players")
    return {normalize_name(r[0]) for r in cur.fetchall() if r and r[0]}


def fetch_api_player_name_to_id() -> Dict[str, int]:
    client = get_nba_stats_client()
    # Use leaguedashplayerstats to get PLAYER_ID and PLAYER_NAME for the target season
    resp = client.get_players_with_stats(SEASON_ID)
    name_to_id: Dict[str, int] = {}
    for p in resp:
        pid = p.get('playerId')
        pname = p.get('playerName')
        if pid and pname:
            name_to_id[normalize_name(pname)] = int(pid)
    # As a fallback, include commonallplayers
    alt = client.get_all_players(SEASON_ID)
    try:
        if alt and 'resultSets' in alt and alt['resultSets']:
            headers = alt['resultSets'][0]['headers']
            rows = alt['resultSets'][0]['rowSet']
            name_idx = headers.index('DISPLAY_FIRST_LAST') if 'DISPLAY_FIRST_LAST' in headers else headers.index('PLAYER')
            id_idx = headers.index('PERSON_ID') if 'PERSON_ID' in headers else headers.index('PLAYER_ID')
            for row in rows:
                pname = row[name_idx]
                pid = row[id_idx]
                if pname and pid and normalize_name(pname) not in name_to_id:
                    name_to_id[normalize_name(pname)] = int(pid)
    except Exception:
        pass
    return name_to_id


def insert_missing_players(conn: sqlite3.Connection, missing_names: Set[str], api_map: Dict[str, int]) -> int:
    inserted = 0
    cur = conn.cursor()
    for n in sorted(missing_names):
        pid = api_map.get(n)
        if not pid:
            continue
        try:
            cur.execute(
                "INSERT OR IGNORE INTO Players (player_id, player_name) VALUES (?, ?)",
                (pid, n.title())
            )
            if cur.rowcount:
                inserted += 1
        except sqlite3.Error:
            continue
    conn.commit()
    return inserted


def main() -> None:
    conn = get_db_connection()
    if conn is None:
        logger.error("Could not connect to database.")
        return
    try:
        conn.execute("PRAGMA foreign_keys = ON;")
        csv_names = load_csv_names()
        db_names = load_db_names(conn)
        missing = csv_names.difference(db_names)
        if not missing:
            logger.info("No missing players to insert.")
            return
        api_map = fetch_api_player_name_to_id()
        inserted = insert_missing_players(conn, missing, api_map)
        logger.info(f"Inserted {inserted} missing players into Players table.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()


