#!/usr/bin/env python3
"""
Database Sanity Verification Script

This script performs deep, domain-specific sanity checks directly on the SQLite
database to verify its structural integrity, statistical reasonableness, and
logical consistency.

It is designed to catch issues that basic data quality checks might miss, such as:
- Logically impossible statistical values (e.g., more shots made than attempted).
- Violations of relational integrity (e.g., orphan records in stats tables).
- Inconsistencies with the fundamental rules of basketball.
"""

import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('database_sanity.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DatabaseSanityVerifier:
    def __init__(self, db_path: str = "src/nba_stats/db/nba_stats.db"):
        self.db_path = db_path
        self.report_path = Path("database_sanity_report.md")
        self.results: Dict[str, Any] = {
            "checks": [],
            "summary": {
                "passed": 0,
                "failed": 0,
                "total": 0,
            }
        }

    def run_all_checks(self):
        logger.info(f"Starting database sanity check for: {self.db_path}")
        if not Path(self.db_path).exists():
            logger.error(f"Database file not found at {self.db_path}")
            return

        with sqlite3.connect(self.db_path) as conn:
            # Table Presence Checks
            self._run_check(
                conn,
                name="Check for PlayerSeasonRawStats table",
                query="SELECT name FROM sqlite_master WHERE type='table' AND name='PlayerSeasonRawStats';",
                test_func=lambda result: len(result) > 0,
                description="Verifies that the essential `PlayerSeasonRawStats` table exists."
            )
            self._run_check(
                conn,
                name="Check for PlayerSeasonAdvancedStats table",
                query="SELECT name FROM sqlite_master WHERE type='table' AND name='PlayerSeasonAdvancedStats';",
                test_func=lambda result: len(result) > 0,
                description="Verifies that the essential `PlayerSeasonAdvancedStats` table exists."
            )
            
            # Data Content Checks
            self._run_check(
                conn,
                name="Check for data in PlayerSeasonRawStats",
                query="SELECT COUNT(*) FROM PlayerSeasonRawStats WHERE season = '2024-25';",
                test_func=lambda result: result[0][0] > 500,
                description="Verifies that `PlayerSeasonRawStats` has a reasonable amount of data for the season ( > 500 players)."
            )
            self._run_check(
                conn,
                name="Check for logical shooting stats (FGM <= FGA)",
                query="SELECT player_id, season, field_goals_made, field_goals_attempted FROM PlayerSeasonRawStats WHERE field_goals_made > field_goals_attempted;",
                test_func=lambda result: len(result) == 0,
                description="Checks for any records where field goals made are greater than field goals attempted."
            )
            self._run_check(
                conn,
                name="Check for logical three-point stats (FG3M <= FG3A)",
                query="SELECT player_id, season, three_pointers_made, three_pointers_attempted FROM PlayerSeasonRawStats WHERE three_pointers_made > three_pointers_attempted;",
                test_func=lambda result: len(result) == 0,
                description="Checks for any records where three-pointers made are greater than three-pointers attempted."
            )
            self._run_check(
                conn,
                name="Check for logical free throw stats (FTM <= FTA)",
                query="SELECT player_id, season, free_throws_made, free_throws_attempted FROM PlayerSeasonRawStats WHERE free_throws_made > free_throws_attempted;",
                test_func=lambda result: len(result) == 0,
                description="Checks for any records where free throws made are greater than free throws attempted."
            )
            self._run_check(
                conn,
                name="Check for negative stats",
                query="SELECT player_id, season, MIN(games_played, minutes_played, points, offensive_rebounds, defensive_rebounds, assists, steals, blocks, turnovers, personal_fouls)"
                      "FROM PlayerSeasonRawStats WHERE games_played < 0 OR minutes_played < 0 OR points < 0 OR offensive_rebounds < 0 OR defensive_rebounds < 0 OR assists < 0 OR steals < 0 OR blocks < 0 OR turnovers < 0 OR personal_fouls < 0;",
                test_func=lambda result: len(result) == 0,
                description="Checks for any negative values in core statistical columns."
            )
            
            # Relational Integrity Checks
            self._run_check(
                conn,
                name="Check for orphan players in PlayerSeasonRawStats",
                query="""
                    SELECT psr.player_id
                    FROM PlayerSeasonRawStats psr
                    LEFT JOIN Players p ON psr.player_id = p.player_id
                    WHERE p.player_id IS NULL;
                """,
                test_func=lambda result: len(result) == 0,
                description="Checks for records in `PlayerSeasonRawStats` that don't have a corresponding player in the `Players` table."
            )
            self._run_check(
                conn,
                name="Check for orphan players in PlayerSalaries",
                query="""
                    SELECT ps.player_id
                    FROM PlayerSalaries ps
                    LEFT JOIN Players p ON ps.player_id = p.player_id
                    WHERE p.player_id IS NULL;
                """,
                test_func=lambda result: len(result) == 0,
                description="Checks for records in `PlayerSalaries` that don't have a corresponding player in the `Players` table."
            )

        self._generate_report()
        logger.info(f"Database sanity check complete. Report generated at: {self.report_path}")

    def _run_check(self, conn: sqlite3.Connection, name: str, query: str, test_func: callable, description: str, params: tuple = ()):
        self.results["summary"]["total"] += 1
        status = "PASS"
        violating_rows = []
        error_message = None
        
        try:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            if not test_func(rows):
                status = "FAIL"
                violating_rows = [dict(zip([d[0] for d in cursor.description], row)) for row in rows]
        except Exception as e:
            status = "ERROR"
            error_message = str(e)

        if status in ["FAIL", "ERROR"]:
            self.results["summary"]["failed"] += 1
            logger.error(f"✗ Check FAILED: {name} | Reason: {error_message or 'Test condition not met'}")
        else:
            self.results["summary"]["passed"] += 1
            logger.info(f"✓ Check PASSED: {name}")

        self.results["checks"].append({
            "name": name,
            "description": description,
            "status": status,
            "query": query,
            "violating_rows": violating_rows[:5], # Sample first 5
            "error_message": error_message,
        })

    def _generate_report(self):
        with open(self.report_path, "w") as f:
            f.write("# Database Sanity Report\n\n")
            f.write(f"**Database:** `{self.db_path}`\n")
            f.write(f"**Timestamp:** {datetime.now().isoformat()}\n\n")

            summary = self.results['summary']
            f.write("## Summary\n\n")
            f.write(f"- ✅ **Passed:** {summary['passed']}/{summary['total']}\n")
            f.write(f"- ❌ **Failed:** {summary['failed']}/{summary['total']}\n\n")

            f.write("## Detailed Check Results\n\n")

            for check in self.results["checks"]:
                f.write(f"### {'✅' if check['status'] == 'PASS' else '❌'} {check['name']}\n\n")
                f.write(f"**Status:** `{check['status']}`\n\n")
                f.write(f"**Description:** {check['description']}\n\n")
                
                if check['status'] != 'PASS':
                    if check['error_message']:
                        f.write(f"**Error:**\n```\n{check['error_message']}\n```\n\n")
                    
                    if check['violating_rows']:
                        f.write("**Sample Violating Rows:**\n\n")
                        f.write("```json\n")
                        f.write(json.dumps(check['violating_rows'], indent=2))
                        f.write("\n```\n\n")
                
                f.write("---\n\n")


if __name__ == "__main__":
    import argparse
    from datetime import datetime
    import json

    parser = argparse.ArgumentParser(description="Run deep sanity checks on the NBA stats database.")
    parser.add_argument("--db-path", default="src/nba_stats/db/nba_stats.db", help="Path to the SQLite database file.")
    args = parser.parse_args()

    verifier = DatabaseSanityVerifier(db_path=args.db_path)
    verifier.run_all_checks()
