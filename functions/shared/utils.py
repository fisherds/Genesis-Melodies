"""
Shared utility functions for the Cloud Functions package.
"""

import os
import sys
from pathlib import Path


def ensure_correct_working_directory_for_local_data_generation():
    """
    Ensure that local data generation scripts are run from the project root.
    
    Scripts like reindex_all.py should be run from the project root:
    - python functions/data/reindex_all.py
    
    This ensures that relative paths work correctly.
    """
    cwd = Path(os.getcwd())
    
    # Check if we're in the project root (should have functions/ subdirectory)
    if (cwd / "functions").exists() and (cwd / "functions" / "data").exists():
        return  # We're in the right place (project root)
    
    # Check if we're in the functions directory (also acceptable for some scripts)
    if cwd.name == "functions" and (cwd / "data").exists():
        return  # We're in functions directory
    
    # If not, exit with error message
    print(f"Error: Script must be run from project root or functions directory", flush=True)
    print(f"Current directory: {cwd}", flush=True)
    print(f"Expected: Project root (with functions/ subdirectory)", flush=True)
    print(f"Or: functions/ directory", flush=True)
    print(f"\nRun from project root: python functions/data/reindex_all.py", flush=True)
    sys.exit(1)
