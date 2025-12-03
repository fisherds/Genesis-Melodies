#!/usr/bin/env python3
"""
Double-check agentic chunking records for correctness.

Checks for:
1. Verses with .0 that should be integers
2. Full verses that have decimal notation
3. Hebrew-chunked records with full Hebrew when should be partial
4. English-chunked records with full English when should be partial
5. Mismatches between verse references and actual text content
"""

import json
from pathlib import Path
from collections import defaultdict

def load_verse_records(records_dir: Path):
    """Load verse records for reference."""
    verse_records_path = records_dir / 'verse_records.json'
    with open(verse_records_path, 'r', encoding='utf-8') as f:
        records = json.load(f)
    # Create lookup
    lookup = {}
    for record in records:
        if record['verses']:
            ch = record['verses'][0]['chapter']
            v = record['verses'][0]['verse']
            lookup[(ch, v)] = record
    return lookup

def count_words(text):
    """Count words in text."""
    if not text:
        return 0
    return len(text.split())

def extract_verse_text_from_record(record_text, verse_refs, verse_lookup, field_name, model_name, is_chunked_language):
    """
    Extract the text for a specific verse from a record's concatenated text.
    
    Args:
        is_chunked_language: True if this is the language that was chunked (Hebrew for berit/hebrew_st, English for english_st)
    """
    verse_texts = {}
    remaining_text = record_text
    
    for vref in verse_refs:
        ch = vref['chapter']
        v = vref['verse']
        base_v = int(v) if isinstance(v, float) else v
        
        if (ch, base_v) not in verse_lookup:
            continue
        
        verse_record = verse_lookup[(ch, base_v)]
        full_verse_text = verse_record.get(field_name, '')
        
        if not full_verse_text:
            continue
        
        # Determine expected text
        if is_chunked_language and isinstance(v, float):
            # Partial verse in chunked language - extract decimal part
            decimal_str = str(v).split('.')[1]
            word_count = int(decimal_str)
            words = full_verse_text.split()
            if word_count <= len(words):
                expected_text = " ".join(words[:word_count])
            else:
                expected_text = full_verse_text
        else:
            # Full verse (either not chunked language, or full verse in chunked language)
            expected_text = full_verse_text
        
        # Try to find this text in the record
        if expected_text in remaining_text:
            start_idx = remaining_text.find(expected_text)
            end_idx = start_idx + len(expected_text)
            verse_texts[(ch, base_v)] = remaining_text[start_idx:end_idx]
            remaining_text = remaining_text[end_idx:].strip()
        elif full_verse_text in remaining_text:
            # Fallback: use full verse text
            start_idx = remaining_text.find(full_verse_text)
            end_idx = start_idx + len(full_verse_text)
            verse_texts[(ch, base_v)] = remaining_text[start_idx:end_idx]
            remaining_text = remaining_text[end_idx:].strip()
        else:
            # Can't find it - return None to indicate we can't verify
            verse_texts[(ch, base_v)] = None
    
    return verse_texts

def check_record(record, verse_lookup, model_name):
    """Check a single record for issues."""
    issues = []
    record_id = record['id']
    
    # Extract individual verse texts from the record
    # For Hebrew-chunked: Hebrew is chunked (partial), English is always full
    # For English-chunked: English is chunked (partial), Hebrew is always full
    if model_name in ['berit', 'hebrew_st']:
        hebrew_verse_texts = extract_verse_text_from_record(
            record.get('hebrew', ''), record['verses'], verse_lookup, 'hebrew', model_name, is_chunked_language=True
        )
        english_verse_texts = extract_verse_text_from_record(
            record.get('text', ''), record['verses'], verse_lookup, 'text', model_name, is_chunked_language=False
        )
    else:  # english_st
        hebrew_verse_texts = extract_verse_text_from_record(
            record.get('hebrew', ''), record['verses'], verse_lookup, 'hebrew', model_name, is_chunked_language=False
        )
        english_verse_texts = extract_verse_text_from_record(
            record.get('text', ''), record['verses'], verse_lookup, 'text', model_name, is_chunked_language=True
        )
    
    # Check each verse reference
    for vref in record['verses']:
        ch = vref['chapter']
        v = vref['verse']
        base_v = int(v) if isinstance(v, float) else v
        
        # Issue 1: .0 should be integer
        if isinstance(v, float) and v == int(v):
            issues.append(f"{record_id}: Verse {ch}:{v} should be integer (has .0)")
            continue
        
        # Check if verse exists
        if (ch, base_v) not in verse_lookup:
            issues.append(f"{record_id}: Verse {ch}:{base_v} not found in verse_records")
            continue
        
        verse_record = verse_lookup[(ch, base_v)]
        hebrew_full = verse_record.get('hebrew', '')
        english_full = verse_record.get('text', '')
        hebrew_words_full = hebrew_full.split()
        english_words_full = english_full.split()
        
        # Get the extracted text for this verse from the record
        verse_hebrew_text = hebrew_verse_texts.get((ch, base_v))
        verse_english_text = english_verse_texts.get((ch, base_v))
        
        if isinstance(v, float):
            # Partial verse - check word count
            decimal_str = str(v).split('.')[1]
            expected_word_count = int(decimal_str)
            
            if model_name in ['berit', 'hebrew_st']:
                # Hebrew should be partial
                if verse_hebrew_text is not None:
                    hebrew_words_in_record = verse_hebrew_text.split()
                    if len(hebrew_words_in_record) > expected_word_count + 2:  # Allow small tolerance
                        issues.append(f"{record_id}: Verse {ch}:{v} Hebrew has {len(hebrew_words_in_record)} words, expected ~{expected_word_count}")
                    elif len(hebrew_words_in_record) >= len(hebrew_words_full):
                        issues.append(f"{record_id}: Verse {ch}:{v} Hebrew appears to be full verse ({len(hebrew_words_in_record)} words, verse has {len(hebrew_words_full)})")
                
                # English should be full
                if verse_english_text is not None:
                    english_words_in_record = verse_english_text.split()
                    if len(english_words_in_record) < len(english_words_full) - 2:  # Allow small tolerance
                        issues.append(f"{record_id}: Verse {ch}:{base_v} English may be missing words ({len(english_words_in_record)} vs {len(english_words_full)})")
            else:  # english_st
                # English should be partial
                if verse_english_text is not None:
                    english_words_in_record = verse_english_text.split()
                    if len(english_words_in_record) > expected_word_count + 2:  # Allow small tolerance
                        issues.append(f"{record_id}: Verse {ch}:{v} English has {len(english_words_in_record)} words, expected ~{expected_word_count}")
                    elif len(english_words_in_record) >= len(english_words_full):
                        issues.append(f"{record_id}: Verse {ch}:{v} English appears to be full verse ({len(english_words_in_record)} words, verse has {len(english_words_full)})")
                
                # Hebrew should be full
                if verse_hebrew_text is not None:
                    hebrew_words_in_record = verse_hebrew_text.split()
                    if len(hebrew_words_in_record) < len(hebrew_words_full) - 2:  # Allow small tolerance
                        issues.append(f"{record_id}: Verse {ch}:{base_v} Hebrew may be missing words ({len(hebrew_words_in_record)} vs {len(hebrew_words_full)})")
        else:
            # Full verse - should be complete
            if model_name in ['berit', 'hebrew_st']:
                if verse_hebrew_text is not None:
                    hebrew_words_in_record = verse_hebrew_text.split()
                    if len(hebrew_words_in_record) < len(hebrew_words_full) - 2:
                        issues.append(f"{record_id}: Verse {ch}:{v} Hebrew may be missing words ({len(hebrew_words_in_record)} vs {len(hebrew_words_full)})")
                
                if verse_english_text is not None:
                    english_words_in_record = verse_english_text.split()
                    if len(english_words_in_record) < len(english_words_full) - 2:
                        issues.append(f"{record_id}: Verse {ch}:{v} English may be missing words ({len(english_words_in_record)} vs {len(english_words_full)})")
            else:  # english_st
                if verse_english_text is not None:
                    english_words_in_record = verse_english_text.split()
                    if len(english_words_in_record) < len(english_words_full) - 2:
                        issues.append(f"{record_id}: Verse {ch}:{v} English may be missing words ({len(english_words_in_record)} vs {len(english_words_full)})")
                
                if verse_hebrew_text is not None:
                    hebrew_words_in_record = verse_hebrew_text.split()
                    if len(hebrew_words_in_record) < len(hebrew_words_full) - 2:
                        issues.append(f"{record_id}: Verse {ch}:{v} Hebrew may be missing words ({len(hebrew_words_in_record)} vs {len(hebrew_words_full)})")
    
    return issues

def main():
    """Main function to check all agentic records."""
    script_dir = Path(__file__).parent
    data_dir = script_dir.parent
    records_dir = data_dir / 'records'
    
    print("=" * 80)
    print("Agentic Chunking Verification")
    print("=" * 80)
    
    # Load verse records for reference
    print("\nLoading verse records...")
    verse_lookup = load_verse_records(records_dir)
    print(f"Loaded {len(verse_lookup)} verse records")
    
    # Check each agentic file
    agentic_files = [
        ('agentic_berit_records.json', 'berit'),
        ('agentic_hebrew_st_records.json', 'hebrew_st'),
        ('agentic_english_st_records.json', 'english_st')
    ]
    
    all_issues = defaultdict(list)
    
    for filename, model_name in agentic_files:
        filepath = records_dir / filename
        if not filepath.exists():
            print(f"\n⚠️  {filename} not found, skipping...")
            continue
        
        print(f"\n{'=' * 80}")
        print(f"Checking {filename} ({model_name})...")
        print('=' * 80)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            records = json.load(f)
        
        issues_found = []
        for record in records:
            issues = check_record(record, verse_lookup, model_name)
            if issues:
                issues_found.extend(issues)
                all_issues[filename].extend(issues)
        
        if issues_found:
            print(f"\n❌ Found {len(issues_found)} issues:")
            for issue in issues_found[:20]:  # Show first 20
                print(f"  - {issue}")
            if len(issues_found) > 20:
                print(f"  ... and {len(issues_found) - 20} more issues")
        else:
            print(f"\n✅ No issues found in {len(records)} records!")
    
    # Summary
    print(f"\n{'=' * 80}")
    print("Summary")
    print('=' * 80)
    total_issues = sum(len(issues) for issues in all_issues.values())
    if total_issues == 0:
        print("✅ All records passed verification!")
    else:
        for filename, issues in all_issues.items():
            print(f"{filename}: {len(issues)} issues")
        print(f"\nTotal issues: {total_issues}")

if __name__ == "__main__":
    main()

