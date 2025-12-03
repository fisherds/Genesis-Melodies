"""
Shared utility functions for the Cloud Functions package.
"""

import os
import sys
from pathlib import Path


def ensure_correct_working_directory():
    """
    Ensure that scripts are run from the correct directory.
    For Cloud Functions, this is a no-op since the working directory is fixed.
    For local development, it checks for the presence of required folders.
    """
    # In Cloud Functions, the working directory is always the functions directory
    # This check is mainly for local development/testing
    cwd = Path(os.getcwd())
    
    # Check if we're in the functions directory or if dense/data folders exist
    if (cwd.name == "functions" or 
        (cwd / "dense").exists() or 
        (cwd / "data").exists()):
        return  # We're in the right place
    
    # If not, just warn but don't exit (Cloud Functions will handle it)
    print(f"Warning: Current working directory may not be correct: {cwd}", flush=True)
