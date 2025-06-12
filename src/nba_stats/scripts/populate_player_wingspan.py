"""
Populates the wingspan for players from the draft combine data for a given season.
"""
import sqlite3
import time

from .common_utils import get_db_connection, get_nba_stats_client, logger, settings

def _parse_wingspan_to_inches(wingspan_val) -> float:
    """Converts wingspan value, which can be a string (e.g., "6' 5.5\\"") or float, to inches."""
    if isinstance(wingspan_val, (int, float)):
        return float(wingspan_val)
    
    if not isinstance(wingspan_val, str) or not wingspan_val:
        return 0.0

    wingspan_str = str(wingspan_val).replace('"', '').strip()
    try:
        if "'" in wingspan_str:
            feet, inches = wingspan_str.split("'")
            return float(feet.strip()) * 12 + float(inches.strip())
        return float(wingspan_str)
    except (ValueError, IndexError):
        logger.warning(f"Could not parse wingspan value: {wingspan_str}")
        return 0.0

def populate_player_wingspan(season_to_load: str):
    """
    Fetches draft combine stats for a specific season and updates player wingspans in the database.
    """
    logger.info(f"Starting to populate player wingspans for season: {season_to_load}")
    conn = get_db_connection()
    if conn is None:
        logger.error("Could not get database connection. Aborting wingspan population.")
        return

    client = get_nba_stats_client()

    try:
        combine_data = client.get_draft_combine_stats(season_year=season_to_load)
        time.sleep(settings.MIN_SLEEP)

        if not combine_data or 'resultSets' not in combine_data or not combine_data['resultSets']:
            logger.warning(f"No draft combine data found for season {season_to_load}.")
            return

        # Find the correct dataset in the response
        data = next((rs for rs in combine_data['resultSets'] if rs.get('name') == 'DraftCombineStats'), None)
        
        if data is None:
            logger.warning(f"Could not find 'DraftCombineStats' in API response for {season_to_load}")
            return

        headers = data.get('headers', [])
        rows = data.get('rowSet', [])

        if not headers or not rows:
            logger.info(f"No player data to process in draft combine stats for {season_to_load}")
            return

        player_id_idx = headers.index('PLAYER_ID')
        wingspan_idx = headers.index('WINGSPAN')

        cursor = conn.cursor()
        update_count = 0
        for row in rows:
            player_id = row[player_id_idx]
            wingspan_val = row[wingspan_idx]

            if wingspan_val is not None:
                wingspan_in_inches = _parse_wingspan_to_inches(wingspan_val)
                if wingspan_in_inches > 0:
                    # Only update if wingspan is not already set
                    cursor.execute(
                        """
                        UPDATE Players 
                        SET wingspan = ? 
                        WHERE player_id = ? AND (wingspan IS NULL OR wingspan = 0.0 OR wingspan = '')
                        """,
                        (wingspan_in_inches, player_id)
                    )
                    if cursor.rowcount > 0:
                        update_count += 1
        
        if update_count > 0:
            conn.commit()
            logger.info(f"Committed {update_count} wingspan updates for season {season_to_load}.")
        else:
            logger.info(f"No new wingspans to update for season {season_to_load}.")

    except ValueError as e:
        logger.error(f"Missing required column in combine data for {season_to_load}: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred during wingspan population: {e}", exc_info=True)
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Populate player wingspans for a specific season.")
    parser.add_argument("--season", type=str, required=True, help="The season to fetch data for (e.g., '2023-24').")
    args = parser.parse_args()

    populate_player_wingspan(season_to_load=args.season) 