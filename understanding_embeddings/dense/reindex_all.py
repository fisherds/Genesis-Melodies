#!/usr/bin/env python3
"""
Reindex all vector stores with the new structure.
This will:
1. Remove old chroma_db directories
2. Create new vector stores for:
   - hebrew_st_pericope
   - hebrew_st_verse
   - english_pericope
   - english_verse
   - berit_verse
   - berit_agentic_berit
   - hebrew_st_agentic_berit
   - english_agentic_berit
   - hebrew_st_agentic_hebrew_st
   - english_agentic_hebrew_st
   - hebrew_st_agentic_english_st
   - english_agentic_english_st
"""

import sys
import shutil
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from understanding_embeddings.dense.vector_store import create_vector_store
from understanding_embeddings.dense.models import get_persist_directory
from understanding_embeddings.shared.utils import ensure_correct_working_directory

# Ensure we're running from the project root
ensure_correct_working_directory()

# Get directories
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR.parent / 'data'

# Old chroma_db locations to remove
OLD_CHROMA_DBS = [
    DATA_DIR / 'chroma_db_berit',
    DATA_DIR / 'chroma_db_hebrew_st',
]

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

print("=" * 60)
print("Reindexing All Vector Stores")
print("=" * 60)
print()

# Step 1: Remove old chroma_db directories
print("Step 1: Removing old chroma_db directories...")
for old_db in OLD_CHROMA_DBS:
    if old_db.exists():
        print(f"  Removing {old_db}...")
        shutil.rmtree(old_db)
        print(f"  ✓ Removed {old_db}")
    else:
        print(f"  {old_db} does not exist, skipping")
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
    persist_dir = get_persist_directory(BASE_DIR, config['model_key'], config['record_level'])
    print(f"  - {persist_dir.name}")

