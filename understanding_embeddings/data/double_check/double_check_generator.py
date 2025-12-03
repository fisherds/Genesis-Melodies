#!/usr/bin/env python3
"""
Generate double-check fields for decoder ring records using genesis_concordance.json.

This script adds double-check fields by reconstructing text, Hebrew, and Strong's
from word-level concordance data.
"""

import json
from pathlib import Path
from collections import defaultdict


def load_concordance(file_path):
    """
    Load genesis_concordance.json and create lookups by verse.
    Returns dict: (chapter, verse) -> list of word entries
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    concordance_by_verse = defaultdict(list)
    
    for entry in data:
        chapter = entry['chapter']
        verse = entry['verse']
        concordance_by_verse[(chapter, verse)].append(entry)
    
    # Sort each verse's words by word_index
    for key in concordance_by_verse:
        concordance_by_verse[key].sort(key=lambda x: x.get('word_index', 0))
    
    return concordance_by_verse


def validate_verse(chapter, verse):
    """
    Check if a verse is valid for Genesis 1-12.
    Returns (is_valid, reason)
    """
    # Genesis chapter verse counts (approximate - Genesis 4 has 26 verses, etc.)
    max_verses = {
        1: 31,
        2: 25,
        3: 24,
        4: 26,
        5: 32,
        6: 22,
        7: 24,
        8: 22,
        9: 29,
        10: 32,
        11: 32,
        12: 20  # We only need up to 12:5
    }
    
    if chapter < 1 or chapter > 12:
        return False, f"Chapter {chapter} is outside Genesis 1-12"
    
    if chapter == 12 and verse > 5:
        return False, f"Verse {chapter}:{verse} is beyond 12:5"
    
    if chapter in max_verses and verse > max_verses[chapter]:
        return False, f"Verse {chapter}:{verse} exceeds maximum for chapter {chapter} (max: {max_verses[chapter]})"
    
    return True, None


def reconstruct_from_concordance(verses, concordance_by_verse):
    """
    Reconstruct text, Hebrew, and Strong's from concordance for given verses.
    Returns (english_text, hebrew_text, strongs_text, warnings)
    """
    english_parts = []
    hebrew_parts = []
    strongs_parts = []
    warnings = []
    
    for chapter, verse in verses:
        key = (chapter, verse)
        
        # Validate verse
        is_valid, reason = validate_verse(chapter, verse)
        if not is_valid:
            warnings.append(f"Invalid verse {chapter}:{verse} - {reason}")
            continue
        
        # Get words for this verse
        if key in concordance_by_verse:
            words = concordance_by_verse[key]
            verse_english = []
            verse_hebrew = []
            verse_strongs = []
            
            for word_entry in words:
                if 'english_text' in word_entry and word_entry['english_text']:
                    verse_english.append(word_entry['english_text'])
                if 'hebrew_word' in word_entry and word_entry['hebrew_word']:
                    verse_hebrew.append(word_entry['hebrew_word'])
                if 'strongs_number' in word_entry and word_entry['strongs_number']:
                    verse_strongs.append(word_entry['strongs_number'])
            
            if verse_english:
                english_parts.append(' '.join(verse_english))
            if verse_hebrew:
                hebrew_parts.append(' '.join(verse_hebrew))
            if verse_strongs:
                strongs_parts.append(' '.join(verse_strongs))
        else:
            warnings.append(f"No concordance data found for {chapter}:{verse} (verse may not exist in Genesis or data may be missing)")
    
    english_text = ' '.join(english_parts)
    hebrew_text = ' '.join(hebrew_parts)
    strongs_text = ' '.join(strongs_parts)
    
    return english_text, hebrew_text, strongs_text, warnings


def generate_double_check_records():
    """
    Main function to generate double-check fields for decoder ring records.
    """
    # Get the script directory and data directory
    # Script is in data/double_check/, so parent is data/
    script_dir = Path(__file__).parent
    data_dir = script_dir.parent  # Go up one level to data/
    
    # File paths
    records_file = data_dir / 'records' / 'pericope_records.json'
    concordance_file = data_dir / 'double_check' / 'genesis_concordance.json'
    output_file = data_dir / 'double_check' / 'decoder_ring_records_double_check.json'
    
    print("Loading files...")
    with open(records_file, 'r', encoding='utf-8') as f:
        records = json.load(f)
    
    concordance_by_verse = load_concordance(concordance_file)
    print(f"Loaded {len(concordance_by_verse)} verses from concordance")
    
    print(f"\nProcessing {len(records)} records...")
    
    all_warnings = []
    
    for i, record in enumerate(records, 1):
        # Handle both old format (objects) and new format (tuples/arrays)
        if record['verses'] and isinstance(record['verses'][0], dict):
            verses = [(v['chapter'], v['verse']) for v in record['verses']]
        else:
            # New format: tuples stored as arrays in JSON
            verses = [tuple(v) if isinstance(v, list) else v for v in record['verses']]
        
        # Reconstruct from concordance
        double_check_text, double_check_hebrew, double_check_strongs, warnings = \
            reconstruct_from_concordance(verses, concordance_by_verse)
        
        # Collect warnings
        if warnings:
            all_warnings.append({
                'record': i,
                'title': record['title'],
                'warnings': warnings
            })
        
        # Rename original fields and add double-check fields
        # Put matching fields next to each other
        new_record = {
            'title': record['title'],
            'verses': record['verses'],
            'origin_field_text': record['text'],
            'double_check_text': double_check_text,
            'origin_field_hebrew': record['hebrew'],
            'double_check_hebrew': double_check_hebrew,
            'origin_field_strongs': record['strongs'],
            'double_check_strongs': double_check_strongs
        }
        
        records[i - 1] = new_record
    
    # Print warnings summary
    if all_warnings:
        print(f"\n⚠️  Warnings found in {len(all_warnings)} records:")
        for warning_info in all_warnings:
            print(f"\n  Record {warning_info['record']}: {warning_info['title']}")
            for warning in warning_info['warnings']:
                print(f"    - {warning}")
    else:
        print("\n✓ No warnings found")
    
    # Write output
    print(f"\nWriting {len(records)} records to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
    
    print("Done!")


if __name__ == '__main__':
    generate_double_check_records()

