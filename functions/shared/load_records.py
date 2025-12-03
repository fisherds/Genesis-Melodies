"""
Load decoder ring records from JSON file.
"""

import json
from pathlib import Path
from typing import List, Dict


def load_records(data_dir: Path, record_level: str = 'pericope') -> List[Dict]:
    """
    Load decoder ring records from JSON file.
    
    Args:
        data_dir: Path to the data directory containing records
        record_level: 'pericope', 'verse', 'agentic_berit', 'agentic_hebrew_st', or 'agentic_english_st'
        
    Returns:
        List of record dictionaries, each containing:
        - id: Unique identifier (e.g., "pericope_01" or "verse_01_01")
        - title: Thematic title
        - verses: List of {"chapter": number, "verse": number} objects
        - text: English text
        - hebrew: Hebrew text
        - strongs: Strong's numbers
    """
    if record_level == 'pericope':
        records_file = data_dir / 'records' / 'pericope_records.json'
    elif record_level == 'verse':
        records_file = data_dir / 'records' / 'verse_records.json'
    elif record_level == 'agentic_berit':
        records_file = data_dir / 'records' / 'agentic_berit_records.json'
    elif record_level == 'agentic_hebrew_st':
        records_file = data_dir / 'records' / 'agentic_hebrew_st_records.json'
    elif record_level == 'agentic_english_st':
        records_file = data_dir / 'records' / 'agentic_english_st_records.json'
    else:
        raise ValueError(
            f"Invalid record_level: {record_level}. "
            f"Must be 'pericope', 'verse', 'agentic_berit', 'agentic_hebrew_st', or 'agentic_english_st'"
        )
    
    if not records_file.exists():
        raise FileNotFoundError(f"Records file not found: {records_file}")
    
    with open(records_file, 'r', encoding='utf-8') as f:
        records = json.load(f)
    
    return records

