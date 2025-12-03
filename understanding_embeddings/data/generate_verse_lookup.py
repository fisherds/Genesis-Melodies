#!/usr/bin/env python3
"""
Generate verse_lookup.json file for Genesis 1:1 to 25:18.
This file contains English and Hebrew text for each verse, used by the backend for verse lookup.

This script is NOT part of the backend - it's a one-time generation script.
"""

import json
import re
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from understanding_embeddings.shared.utils import ensure_correct_working_directory

def load_bibleproject_translation(file_path: Path):
    """
    Load BP translation from .txt file and create a lookup dict: (chapter, verse) -> text
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    lookup = {}
    current_chapter = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Check for chapter header
        if line.startswith('Chapter '):
            current_chapter = int(line.split()[1])
            continue
        
        # Parse verse line: "28 - text here"
        match = re.match(r'(\d+)\s*-\s*(.+)', line)
        if match:
            verse_num = int(match.group(1))
            verse_text = match.group(2).strip()
            
            if current_chapter:
                lookup[(current_chapter, verse_num)] = verse_text
    
    return lookup


def load_wlca(file_path: Path):
    """
    Load WLCa.json and extract Hebrew text for Genesis (book=1).
    Returns dict: (chapter, verse) -> cleaned_hebrew_text
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    lookup = {}
    
    for entry in data:
        if entry.get('book') == 1:  # Genesis only
            chapter = entry.get('chapter')
            verse = entry.get('verse')
            text = entry.get('text', '')
            
            # Clean Hebrew text
            hebrew = text
            # Remove Strong's tags
            hebrew = re.sub(r'<S>\d+</S>', '', hebrew)
            # Remove ketiv/qere markers
            hebrew = re.sub(r'\[k_[^\]]+\]', '', hebrew)
            hebrew = re.sub(r'\[q_[^\]]+\]', '', hebrew)
            # Remove HTML tags
            hebrew = hebrew.replace('<br/>', '')
            # Clean up whitespace
            hebrew = ' '.join(hebrew.split())
            
            lookup[(chapter, verse)] = hebrew
    
    return lookup


def main():
    ensure_correct_working_directory()
    
    # Get paths
    data_dir = project_root / 'understanding_embeddings' / 'data'
    bp_translation_path = data_dir / 'raw' / 'bp_translation_gen_1_25.txt'
    wlca_path = data_dir / 'raw' / 'WLCa.json'
    output_path = data_dir / 'records' / 'verse_lookup.json'
    
    print(f"Loading BibleProject translation from: {bp_translation_path}")
    bp_lookup = load_bibleproject_translation(bp_translation_path)
    print(f"Loaded {len(bp_lookup)} English verses")
    
    print(f"\nLoading WLCa Hebrew from: {wlca_path}")
    hebrew_lookup = load_wlca(wlca_path)
    print(f"Loaded {len(hebrew_lookup)} Hebrew verses")
    
    # Generate verse records for Genesis 1:1 to 25:18
    # Chapter lengths (last verse of each chapter):
    chapter_lengths = {
        1: 31, 2: 25, 3: 24, 4: 26, 5: 32, 6: 22, 7: 24, 8: 22, 9: 29,
        10: 32, 11: 32, 12: 20, 13: 18, 14: 24, 15: 21, 16: 16, 17: 27,
        18: 33, 19: 38, 20: 18, 21: 34, 22: 24, 23: 20, 24: 67, 25: 18
    }
    
    verse_records = []
    
    for chapter in range(1, 26):  # Chapters 1-25
        last_verse = chapter_lengths[chapter]
        for verse in range(1, last_verse + 1):
            # Get English text
            english_text = bp_lookup.get((chapter, verse), '')
            
            # Get Hebrew text
            hebrew_text = hebrew_lookup.get((chapter, verse), '')
            
            verse_records.append({
                "chapter": chapter,
                "verse": verse,
                "text": english_text,
                "hebrew": hebrew_text
            })
    
    # Write output
    print(f"\nWriting {len(verse_records)} verse records to: {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(verse_records, f, ensure_ascii=False, indent=2)
    
    print(f"✓ Successfully created verse_lookup.json with {len(verse_records)} verses")
    
    # Verify we have data for all verses
    missing_english = [f"{r['chapter']}:{r['verse']}" for r in verse_records if not r['text']]
    missing_hebrew = [f"{r['chapter']}:{r['verse']}" for r in verse_records if not r['hebrew']]
    
    if missing_english:
        print(f"\n⚠ Warning: {len(missing_english)} verses missing English text")
        if len(missing_english) <= 10:
            print(f"  Missing: {', '.join(missing_english)}")
    
    if missing_hebrew:
        print(f"\n⚠ Warning: {len(missing_hebrew)} verses missing Hebrew text")
        if len(missing_hebrew) <= 10:
            print(f"  Missing: {', '.join(missing_hebrew)}")


if __name__ == "__main__":
    main()

