#!/usr/bin/env python3
"""
Comprehensive Data Audit for NBA Lineup Optimizer
Phase 0: Complete assessment of data quality issues

This script performs a thorough audit of the PlayerArchetypeFeatures table
to identify exactly which features are missing, incomplete, or unreliable.
"""

import sqlite3
import pandas as pd
import json
from pathlib import Path
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_audit.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DataAuditor:
    def __init__(self, db_path="src/nba_stats/db/nba_stats.db"):
        self.db_path = db_path
        self.conn = None
        self.audit_results = {}
        
    def connect_database(self):
        """Connect to the database and verify it exists."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            logger.info(f"Connected to database: {self.db_path}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    def get_table_schema(self, table_name):
        """Get the schema for a given table."""
        cursor = self.conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        return [col[1] for col in columns]  # Column names
    
    def audit_player_archetype_features(self):
        """Comprehensive audit of the PlayerArchetypeFeatures table."""
        logger.info("Starting comprehensive audit of PlayerArchetypeFeatures table...")
        
        # Get all columns in the table
        columns = self.get_table_schema("PlayerArchetypeFeatures")
        logger.info(f"Found {len(columns)} columns in PlayerArchetypeFeatures")
        
        # Get total count of players
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM PlayerArchetypeFeatures WHERE season = '2024-25'")
        total_players = cursor.fetchone()[0]
        logger.info(f"Total players in 2024-25 season: {total_players}")
        
        # Define the 48 canonical metrics from the research paper
        canonical_metrics = [
            'FTPCT', 'TSPCT', 'THPAr', 'FTr', 'TRBPCT', 'ASTPCT', 'AVGDIST',
            'Zto3r', 'THto10r', 'TENto16r', 'SIXTto3PTr', 'HEIGHT', 'WINGSPAN',
            'FRNTCTTCH', 'TOP', 'AVGSECPERTCH', 'AVGDRIBPERTCH', 'ELBWTCH',
            'POSTUPS', 'PNTTOUCH', 'DRIVES', 'DRFGA', 'DRPTSPCT', 'DRPASSPCT',
            'DRASTPCT', 'DRTOVPCT', 'DRPFPCT', 'DRIMFGPCT', 'CSFGA', 'CS3PA',
            'PASSESMADE', 'SECAST', 'POTAST', 'PUFGA', 'PU3PA', 'PSTUPFGA',
            'PSTUPPTSPCT', 'PSTUPPASSPCT', 'PSTUPASTPCT', 'PSTUPTOVPCT',
            'PNTTCHS', 'PNTFGA', 'PNTPTSPCT', 'PNTPASSPCT', 'PNTASTPCT',
            'PNTTVPCT', 'AVGFGATTEMPTEDAGAINSTPERGAME'
        ]
        
        # Check which canonical metrics exist in the table
        missing_columns = []
        existing_columns = []
        
        for metric in canonical_metrics:
            if metric in columns:
                existing_columns.append(metric)
            else:
                missing_columns.append(metric)
        
        logger.info(f"Canonical metrics found in table: {len(existing_columns)}/{len(canonical_metrics)}")
        logger.info(f"Missing canonical metrics: {missing_columns}")
        
        # Audit each existing metric
        feature_audit = {}
        
        for metric in existing_columns:
            logger.info(f"Auditing metric: {metric}")
            
            # Get basic statistics
            cursor.execute(f"""
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN {metric} IS NOT NULL THEN 1 END) as non_null,
                    COUNT(CASE WHEN {metric} > 0 THEN 1 END) as positive,
                    COUNT(CASE WHEN {metric} = 0 THEN 1 END) as zero,
                    AVG({metric}) as avg_value,
                    MIN({metric}) as min_value,
                    MAX({metric}) as max_value
                FROM PlayerArchetypeFeatures 
                WHERE season = '2024-25'
            """)
            
            stats = cursor.fetchone()
            
            # Calculate coverage percentages
            total = stats[0]
            non_null_count = stats[1]
            positive_count = stats[2]
            zero_count = stats[3]
            
            non_null_coverage = (non_null_count / total) * 100 if total > 0 else 0
            positive_coverage = (positive_count / total) * 100 if total > 0 else 0
            zero_percentage = (zero_count / total) * 100 if total > 0 else 0
            
            feature_audit[metric] = {
                'total_players': total,
                'non_null_count': non_null_count,
                'positive_count': positive_count,
                'zero_count': zero_count,
                'non_null_coverage': round(non_null_coverage, 2),
                'positive_coverage': round(positive_coverage, 2),
                'zero_percentage': round(zero_percentage, 2),
                'avg_value': round(stats[4], 4) if stats[4] is not None else None,
                'min_value': round(stats[5], 4) if stats[5] is not None else None,
                'max_value': round(stats[6], 4) if stats[6] is not None else None,
                'status': self._classify_feature_status(positive_coverage, zero_percentage)
            }
            
            logger.info(f"  {metric}: {positive_coverage:.1f}% populated, {zero_percentage:.1f}% zeros")
        
        # Store results
        self.audit_results = {
            'timestamp': datetime.now().isoformat(),
            'total_players': total_players,
            'canonical_metrics': {
                'total': len(canonical_metrics),
                'found': len(existing_columns),
                'missing': len(missing_columns),
                'missing_list': missing_columns
            },
            'feature_audit': feature_audit,
            'summary': self._generate_summary(feature_audit)
        }
        
        return self.audit_results
    
    def _classify_feature_status(self, positive_coverage, zero_percentage):
        """Classify the status of a feature based on coverage and zero percentage."""
        if positive_coverage == 0:
            return "MISSING"
        elif positive_coverage < 20:
            return "CRITICAL"
        elif positive_coverage < 50:
            return "POOR"
        elif positive_coverage < 80:
            return "FAIR"
        elif zero_percentage > 50:
            return "SPARSE"
        else:
            return "GOOD"
    
    def _generate_summary(self, feature_audit):
        """Generate a summary of the audit results."""
        status_counts = {}
        for metric, data in feature_audit.items():
            status = data['status']
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Identify critical issues
        critical_issues = []
        for metric, data in feature_audit.items():
            if data['status'] in ['MISSING', 'CRITICAL']:
                critical_issues.append({
                    'metric': metric,
                    'status': data['status'],
                    'coverage': data['positive_coverage']
                })
        
        return {
            'status_distribution': status_counts,
            'critical_issues': critical_issues,
            'total_critical': len(critical_issues)
        }
    
    def audit_related_tables(self):
        """Audit related tables to understand data flow."""
        logger.info("Auditing related tables...")
        
        related_tables = [
            'Players',
            'PlayerSeasonArchetypes', 
            'PlayerSeasonSkill',
            'PlayerShotChart',
            'PlayerSeasonRawStats',
            'PlayerSeasonAdvancedStats'
        ]
        
        table_audit = {}
        
        for table in related_tables:
            try:
                cursor = self.conn.cursor()
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                
                # Get sample data
                cursor.execute(f"SELECT * FROM {table} LIMIT 3")
                sample_data = cursor.fetchall()
                
                table_audit[table] = {
                    'exists': True,
                    'row_count': count,
                    'sample_data': sample_data
                }
                
                logger.info(f"  {table}: {count} rows")
                
            except sqlite3.Error as e:
                table_audit[table] = {
                    'exists': False,
                    'error': str(e)
                }
                logger.warning(f"  {table}: Table not found or error - {e}")
        
        return table_audit
    
    def generate_report(self):
        """Generate a comprehensive audit report."""
        logger.info("Generating comprehensive audit report...")
        
        # Create report directory
        report_dir = Path("audit_reports")
        report_dir.mkdir(exist_ok=True)
        
        # Generate timestamped report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = report_dir / f"comprehensive_data_audit_{timestamp}.json"
        
        # Include related table audit
        related_tables_audit = self.audit_related_tables()
        
        full_report = {
            'audit_metadata': {
                'timestamp': datetime.now().isoformat(),
                'database_path': self.db_path,
                'auditor_version': '1.0.0'
            },
            'player_archetype_features_audit': self.audit_results,
            'related_tables_audit': related_tables_audit
        }
        
        # Save JSON report
        with open(report_file, 'w') as f:
            json.dump(full_report, f, indent=2)
        
        logger.info(f"Audit report saved to: {report_file}")
        
        # Generate human-readable summary
        self._generate_human_readable_summary(report_file)
        
        return report_file
    
    def _generate_human_readable_summary(self, report_file):
        """Generate a human-readable summary of the audit results."""
        summary_file = report_file.with_suffix('.md')
        
        with open(summary_file, 'w') as f:
            f.write("# Comprehensive Data Audit Report\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Executive Summary
            f.write("## Executive Summary\n\n")
            summary = self.audit_results['summary']
            f.write(f"- **Total Players:** {self.audit_results['total_players']}\n")
            f.write(f"- **Canonical Metrics Found:** {self.audit_results['canonical_metrics']['found']}/{self.audit_results['canonical_metrics']['total']}\n")
            f.write(f"- **Critical Issues:** {summary['total_critical']}\n\n")
            
            # Status Distribution
            f.write("## Feature Status Distribution\n\n")
            for status, count in summary['status_distribution'].items():
                f.write(f"- **{status}:** {count} features\n")
            f.write("\n")
            
            # Critical Issues
            if summary['critical_issues']:
                f.write("## Critical Issues\n\n")
                f.write("| Metric | Status | Coverage |\n")
                f.write("|--------|--------|----------|\n")
                for issue in summary['critical_issues']:
                    f.write(f"| {issue['metric']} | {issue['status']} | {issue['coverage']:.1f}% |\n")
                f.write("\n")
            
            # Detailed Feature Analysis
            f.write("## Detailed Feature Analysis\n\n")
            f.write("| Metric | Status | Coverage | Zeros | Avg Value |\n")
            f.write("|--------|--------|----------|-------|----------|\n")
            
            for metric, data in self.audit_results['feature_audit'].items():
                avg_val = data['avg_value'] if data['avg_value'] is not None else 'N/A'
                f.write(f"| {metric} | {data['status']} | {data['positive_coverage']:.1f}% | {data['zero_percentage']:.1f}% | {avg_val} |\n")
        
        logger.info(f"Human-readable summary saved to: {summary_file}")

def main():
    """Main execution function."""
    logger.info("Starting comprehensive data audit...")
    
    auditor = DataAuditor()
    
    if not auditor.connect_database():
        logger.error("Failed to connect to database. Exiting.")
        return
    
    try:
        # Run the audit
        auditor.audit_player_archetype_features()
        
        # Generate report
        report_file = auditor.generate_report()
        
        logger.info("Data audit completed successfully!")
        logger.info(f"Report saved to: {report_file}")
        
    except Exception as e:
        logger.error(f"Audit failed with error: {e}")
        raise
    finally:
        if auditor.conn:
            auditor.conn.close()

if __name__ == "__main__":
    main()
