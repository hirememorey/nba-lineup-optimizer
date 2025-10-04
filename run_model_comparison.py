#!/usr/bin/env python3
"""
Run Model Comparison Dashboard

This script launches the Streamlit comparison dashboard for comparing
the original ModelEvaluator with the new SimpleModelEvaluator.
"""

import subprocess
import sys
from pathlib import Path

def main():
    """Launch the model comparison dashboard."""
    print("Starting NBA Model Comparison Dashboard...")
    print("=" * 50)
    
    # Check if streamlit is available
    try:
        import streamlit
        print(f"✅ Streamlit version: {streamlit.__version__}")
    except ImportError:
        print("❌ Streamlit not found. Please install it with:")
        print("pip install streamlit")
        sys.exit(1)
    
    # Check if the dashboard file exists
    dashboard_path = Path("model_comparison_dashboard.py")
    if not dashboard_path.exists():
        print(f"❌ Dashboard file not found: {dashboard_path}")
        sys.exit(1)
    
    print("✅ Dashboard file found")
    print("\n🚀 Launching dashboard...")
    print("The dashboard will open in your browser at http://localhost:8501")
    print("Press Ctrl+C to stop the dashboard")
    print("=" * 50)
    
    try:
        # Launch streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            str(dashboard_path),
            "--server.port", "8503",  # Use different port to avoid conflicts
            "--server.headless", "false"
        ])
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped by user")
    except Exception as e:
        print(f"❌ Error launching dashboard: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
