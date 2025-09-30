# Data Reconciliation Guide

This guide explains how to achieve 100% data integrity for player salary and skill data using the enhanced reconciliation tool.

## Overview

The reconciliation process addresses the ~30% missing player coverage by handling both:
1. **Name Mapping**: Players that exist in the database but with slightly different names in the CSV files
2. **Player Creation**: Players that exist in the CSV files but are missing from the database entirely

## Prerequisites

Before running the reconciliation tool, ensure you have:

1. **Database populated with players**: Run the player population scripts first
2. **CSV files available**: 
   - `data/player_salaries_2024-25.csv`
   - `data/darko_dpm_2024-25.csv`
3. **Required Python packages**:
   ```bash
   pip install rapidfuzz
   ```

## Running the Reconciliation Tool

### Basic Usage

```bash
python src/nba_stats/scripts/fix_player_names.py
```

### Advanced Usage

```bash
python src/nba_stats/scripts/fix_player_names.py \
    --db-path src/nba_stats/db/nba_stats.db \
    --mapping-file mappings/player_name_map.csv \
    --salaries-csv data/player_salaries_2024-25.csv \
    --skills-csv data/darko_dpm_2024-25.csv
```

## How It Works

### 1. Interactive Reconciliation Process

For each unmatched player name, the tool will:

1. **Check for exact matches** in the database
2. **Find fuzzy matches** using string similarity (if rapidfuzz is available)
3. **Present options** to the user:
   - Select from suggested matches
   - Create a new player via NBA API search
   - Skip the player
   - Quit the tool

### 2. Player Creation

When creating a new player:
- The tool searches the NBA API for the player by name
- If found, it creates a new entry in the `Players` table
- The mapping is automatically saved to the mapping file

### 3. Mapping File

The tool creates/updates `mappings/player_name_map.csv` with the format:
```csv
csv_name,db_name
"dario saric","Dario Šarić"
"luka doncic","Luka Dončić"
```

## Example Session

```
============================================================
Unmatched: 'dario saric'
============================================================
Suggestions:
  1. Dario Šarić (ID: 203967) - 92.3% match
  2. Dennis Schröder (ID: 203471) - 35.2% match

Options:
  (1-2) Select a suggestion above
  (c)reate - Create a new player for this name
  (s)kip - Skip this player
  (q)uit - Exit the tool

Your choice: 1
Selected: Dario Šarić (ID: 203967) - 92.3% match
Confirm this mapping? (y/n): y
✓ Saved mapping: 'dario saric' -> 'Dario Šarić'
```

## After Reconciliation

Once the reconciliation is complete:

1. **Re-run the population scripts** to use the new mappings:
   ```bash
   python src/nba_stats/scripts/populate_salaries.py
   python src/nba_stats/scripts/populate_player_skill.py
   ```

2. **Verify 100% coverage**:
   ```bash
   python src/nba_stats/scripts/verify_data_integrity.py
   ```

## Troubleshooting

### Common Issues

1. **NBA API Timeouts**: The tool includes retry logic, but if you encounter persistent timeouts, try running the tool during off-peak hours.

2. **Fuzzy Matching Not Available**: If `rapidfuzz` is not installed, the tool will still work but won't provide fuzzy match suggestions.

3. **Database Locked**: Ensure no other processes are using the database when running the reconciliation tool.

### Manual Mapping

If you need to manually add mappings, edit `mappings/player_name_map.csv` directly:

```csv
csv_name,db_name
"custom name","Canonical Name"
```

## Best Practices

1. **Run reconciliation in batches**: Don't try to reconcile all players at once. Take breaks between sessions.

2. **Verify mappings**: Double-check that the suggested matches are correct before confirming.

3. **Backup your database**: Always backup your database before running reconciliation.

4. **Document decisions**: Keep notes on any unusual cases or manual decisions made during reconciliation.

## Expected Results

After successful reconciliation, you should see:
- **100% coverage** for both salary and skill data
- **Comprehensive mapping file** that can be reused for future seasons
- **Clean, consistent data** ready for analysis

The reconciliation tool transforms the data pipeline from a fragile, manual process into a robust, automated system that can handle the complete spectrum of real-world data integrity challenges.
