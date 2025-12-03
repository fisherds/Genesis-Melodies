"""
Shared utility functions for the understanding_embeddings package.
"""

import os
import sys
from pathlib import Path


def ensure_correct_working_directory():
    """
    Ensure that scripts are run from the project root (ml_ai_lunch_and_learn).
    This function checks for the presence of the 'understanding_embeddings' folder
    in the current working directory.
    """
    required_folder = "understanding_embeddings"
    cwd = os.getcwd()
    complete_path = os.path.join(cwd, required_folder)
    
    if not os.path.isdir(complete_path):
        print(f"Error: This script must be run from the project root folder (ml_ai_lunch_and_learn),")
        print(f"       which should contain '{required_folder}'.")
        print(f"       Current working directory: {cwd}")
        sys.exit(1)

