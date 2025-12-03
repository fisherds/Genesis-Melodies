#!/usr/bin/env python3
"""
Reindex all vector stores with the new structure.
This will:
1. Remove old chroma_db directories
2. Create new vector stores for:
   - hebrew_st_pericope
   - hebrew_st_verse
   - english_st_pericope
   - english_st_verse
   - berit_verse
   - berit_agentic_berit
   - hebrew_st_agentic_berit
   - english_st_agentic_berit
   - hebrew_st_agentic_hebrew_st
   - english_st_agentic_hebrew_st
   - hebrew_st_agentic_english_st
   - english_st_agentic_english_st

Run from project root: python functions/data/reindex_all.py
"""

import sys
import shutil
from pathlib import Path

# Add functions directory to path for imports
# This script runs from project root, so functions/ is the parent of data/
FUNCTIONS_DIR = Path(__file__).parent.parent
if str(FUNCTIONS_DIR) not in sys.path:
    sys.path.insert(0, str(FUNCTIONS_DIR))

from dense.vector_store import create_vector_store
from dense.models import get_persist_directory
from shared.utils import ensure_correct_working_directory_for_local_data_generation

# Get directories
# Script is in functions/data/, so:
DATA_DIR = Path(__file__).parent  # functions/data/
DENSE_DIR = FUNCTIONS_DIR / 'dense'  # functions/dense/

# Old chroma_db locations to remove (legacy locations)
CHROMA_DB_DIR = DENSE_DIR / 'chroma_db'
OLD_CHROMA_DBS = [
    DATA_DIR / 'chroma_db_berit',
    DATA_DIR / 'chroma_db_hebrew_st',
    # Dead databases replaced by english_st_* versions
    CHROMA_DB_DIR / 'english_pericope',  # Replaced by english_st_pericope
    CHROMA_DB_DIR / 'english_verse',     # Replaced by english_st_verse
    CHROMA_DB_DIR / 'english_agentic_berit',      # Replaced by english_st_agentic_berit
    CHROMA_DB_DIR / 'english_agentic_hebrew_st', # Replaced by english_st_agentic_hebrew_st
    CHROMA_DB_DIR / 'english_agentic_english_st', # Replaced by english_st_agentic_english_st
]

# Also remove any other unexpected databases (keep only the 12 correct ones)
EXPECTED_DB_NAMES = {
    'berit_agentic_berit', 'berit_verse',
    'english_st_agentic_berit', 'english_st_agentic_english_st', 'english_st_agentic_hebrew_st',
    'english_st_pericope', 'english_st_verse',
    'hebrew_st_agentic_berit', 'hebrew_st_agentic_english_st', 'hebrew_st_agentic_hebrew_st',
    'hebrew_st_pericope', 'hebrew_st_verse'
}

# Vector store configurations (5 original + 7 agentic = 12 total)
VECTOR_STORES = [
    # Original 5
    {'model_key': 'hebrew_st', 'record_level': 'pericope'},
    {'model_key': 'hebrew_st', 'record_level': 'verse'},
    {'model_key': 'english_st', 'record_level': 'pericope'},
    {'model_key': 'english_st', 'record_level': 'verse'},
    {'model_key': 'berit', 'record_level': 'verse'},
    # Agentic BERiT (3 models)
    {'model_key': 'berit', 'record_level': 'agentic_berit'},
    {'model_key': 'hebrew_st', 'record_level': 'agentic_berit'},
    {'model_key': 'english_st', 'record_level': 'agentic_berit'},
    # Agentic Hebrew ST (2 models)
    {'model_key': 'hebrew_st', 'record_level': 'agentic_hebrew_st'},
    {'model_key': 'english_st', 'record_level': 'agentic_hebrew_st'},
    # Agentic English ST (2 models)
    {'model_key': 'hebrew_st', 'record_level': 'agentic_english_st'},
    {'model_key': 'english_st', 'record_level': 'agentic_english_st'},
]

# Ensure we're running from the correct directory
ensure_correct_working_directory_for_local_data_generation()

print("=" * 60)
print("Reindexing All Vector Stores")
print("=" * 60)
print()

# Step 1: Remove old chroma_db directories
print("Step 1: Removing old/dead chroma_db directories...")
for old_db in OLD_CHROMA_DBS:
    if old_db.exists():
        print(f"  Removing {old_db}...")
        shutil.rmtree(old_db)
        print(f"  ✓ Removed {old_db}")
    else:
        print(f"  {old_db} does not exist, skipping")

# Also check for any unexpected databases in chroma_db directory
if CHROMA_DB_DIR.exists():
    print("\n  Checking for unexpected databases...")
    for db_path in CHROMA_DB_DIR.iterdir():
        if db_path.is_dir() and db_path.name not in EXPECTED_DB_NAMES:
            print(f"  Removing unexpected database: {db_path.name}...")
            shutil.rmtree(db_path)
            print(f"  ✓ Removed {db_path.name}")
print()

# Step 2: Create new vector stores
print("Step 2: Creating new vector stores...")
print()

for i, config in enumerate(VECTOR_STORES, 1):
    model_key = config['model_key']
    record_level = config['record_level']
    
    print(f"[{i}/{len(VECTOR_STORES)}] Creating {model_key}_{record_level}...")
    print(f"  Model: {model_key}")
    print(f"  Record Level: {record_level}")
    
    try:
        create_vector_store(
            data_dir=DATA_DIR,
            model_key=model_key,
            record_level=record_level,
            force=True
        )
        print(f"  ✓ {model_key}_{record_level} created successfully")
    except Exception as e:
        print(f"  ✗ Error creating {model_key}_{record_level}: {e}")
        raise
    
    print()

print("=" * 60)
print("✓ All vector stores reindexed successfully!")
print("=" * 60)
print()
print("Created vector stores:")
for config in VECTOR_STORES:
    persist_dir = get_persist_directory(DENSE_DIR, config['model_key'], config['record_level'])
    print(f"  - {persist_dir.name}")

