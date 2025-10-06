#!/usr/bin/env python3
"""
Production Runner for NBA Lineup Optimizer

This script launches the complete production system with all features:
- Authentication
- User onboarding
- Model evaluation
- Admin panel
- Monitoring
- Error handling
"""

import subprocess
import sys
import os
from pathlib import Path
import logging
import time

def setup_logging():
    """Setup logging for the production runner."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/production.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def check_requirements():
    """Check if all requirements are met."""
    logger = logging.getLogger(__name__)
    
    # Check if we're in the right directory
    if not Path("production_dashboard.py").exists():
        logger.error("production_dashboard.py not found in current directory")
        return False
    
    # Check if database exists
    db_path = "src/nba_stats/db/nba_stats.db"
    if not Path(db_path).exists():
        logger.error(f"Database not found at {db_path}")
        logger.error("Please run the data pipeline first to populate the database")
        return False
    
    # Check if required directories exist
    required_dirs = ["logs", "data", "models", "backups"]
    for dir_name in required_dirs:
        Path(dir_name).mkdir(exist_ok=True)
    
    # Check if model coefficients exist
    coeff_path = "model_coefficients.csv"
    if not Path(coeff_path).exists():
        logger.warning(f"Model coefficients not found at {coeff_path}")
        logger.warning("Data-driven model evaluator not yet implemented")
        logger.warning("This will be available in Phase 1 of the data-driven approach")
    
    return True

def set_environment_variables():
    """Set production environment variables."""
    os.environ["ENVIRONMENT"] = "production"
    os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"
    os.environ["STREAMLIT_SERVER_PORT"] = "8502"
    os.environ["STREAMLIT_SERVER_ADDRESS"] = "0.0.0.0"
    os.environ["PYTHONPATH"] = str(Path.cwd() / "src")
    
    # Set default values if not already set
    if "SECRET_KEY" not in os.environ:
        os.environ["SECRET_KEY"] = "production-secret-key-change-this"
    
    if "ENABLE_AUTH" not in os.environ:
        os.environ["ENABLE_AUTH"] = "true"
    
    if "ADMIN_PASSWORD" not in os.environ:
        os.environ["ADMIN_PASSWORD"] = "admin123"
    
    if "USER_PASSWORD" not in os.environ:
        os.environ["USER_PASSWORD"] = "user123"

def main():
    """Main function."""
    logger = setup_logging()
    
    print("🏀 Starting NBA Lineup Optimizer - Production System")
    print("=" * 60)
    
    # Check requirements
    if not check_requirements():
        print("❌ Requirements check failed. Please fix the issues above.")
        sys.exit(1)
    
    print("✅ Requirements check passed")
    
    # Set environment variables
    set_environment_variables()
    
    print("✅ Environment configured")
    print("✅ Starting production system...")
    print()
    print("The dashboard will be available at: http://localhost:8502")
    print("Default credentials:")
    print("  Admin: admin / admin123")
    print("  User:  user / user123")
    print()
    print("Press Ctrl+C to stop the server")
    print()
    
    try:
        # Launch Streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "production_dashboard.py",
            "--server.port", "8502",
            "--server.headless", "true",
            "--server.address", "0.0.0.0"
        ])
    except KeyboardInterrupt:
        print("\n👋 Production system stopped")
        logger.info("Production system stopped by user")
    except Exception as e:
        print(f"❌ Error launching production system: {e}")
        logger.error(f"Error launching production system: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
