#!/usr/bin/env python3
"""
Analyze double-check decoder ring records.

This script analyzes the records and outputs detailed analysis to a text file.
"""

import json
import re
from pathlib import Path


def analyze_hebrew_differences(origin, double_check):
    """
    Analyze Hebrew text differences, looking for junk characters and specific issues.
    Returns detailed analysis dictionary.
    """
    analysis = {
        'origin_length': len(origin) if origin else 0,
        'double_check_length': len(double_check) if double_check else 0,
        'exact_match': origin == double_check,
        'junk_chars_origin': [],
        'junk_chars_double_check': [],
        'character_differences': [],
        'non_hebrew_chars_origin': [],
        'non_hebrew_chars_double_check': []
    }
    
    if not origin or not double_check:
        return analysis
    
    # Hebrew Unicode range: U+0590 to U+05FF (Hebrew block)
    # Also includes U+FB1D to U+FB4F (Hebrew Presentation Forms)
    hebrew_pattern = re.compile(r'[\u0590-\u05FF\uFB1D-\uFB4F\s\t]')
    
    # Find junk characters (non-Hebrew, non-whitespace)
    seen_chars_origin = set()
    for i, char in enumerate(origin):
        if not hebrew_pattern.match(char) and char not in [' ', '\t', '\n']:
            if char not in seen_chars_origin:
                seen_chars_origin.add(char)
                analysis['junk_chars_origin'].append((char, ord(char), i))
    
    seen_chars_double_check = set()
    for i, char in enumerate(double_check):
        if not hebrew_pattern.match(char) and char not in [' ', '\t', '\n']:
            if char not in seen_chars_double_check:
                seen_chars_double_check.add(char)
                analysis['junk_chars_double_check'].append((char, ord(char), i))
    
    # Find non-Hebrew characters (excluding whitespace and punctuation that might be valid)
    # Valid punctuation in Hebrew texts: ׃ (U+05C3), ״ (U+05F4), etc.
    valid_punctuation = ['׃', '״', '־', '׀', '׆']
    
    for char in set(origin):
        if not hebrew_pattern.match(char) and char not in [' ', '\t', '\n'] + valid_punctuation:
            if char not in [c[0] for c in analysis['non_hebrew_chars_origin']]:
                count = origin.count(char)
                analysis['non_hebrew_chars_origin'].append((char, ord(char), count))
    
    for char in set(double_check):
        if not hebrew_pattern.match(char) and char not in [' ', '\t', '\n'] + valid_punctuation:
            if char not in [c[0] for c in analysis['non_hebrew_chars_double_check']]:
                count = double_check.count(char)
                analysis['non_hebrew_chars_double_check'].append((char, ord(char), count))
    
    # Character-by-character comparison for first 200 chars
    min_len = min(len(origin), len(double_check), 200)
    differences = []
    for i in range(min_len):
        if origin[i] != double_check[i]:
            differences.append((i, origin[i], double_check[i], ord(origin[i]), ord(double_check[i])))
    
    analysis['character_differences'] = differences[:50]  # Limit to first 50 differences
    
    return analysis


def compare_texts(original, double_check, field_name):
    """
    Compare original and double-check texts and return analysis.
    """
    if not original or not double_check:
        return {
            'match': False,
            'original_length': len(original) if original else 0,
            'double_check_length': len(double_check) if double_check else 0,
            'similarity': 0.0,
            'notes': 'One or both fields are empty'
        }
    
    # Exact match
    if original == double_check:
        return {
            'match': True,
            'original_length': len(original),
            'double_check_length': len(double_check),
            'similarity': 1.0,
            'notes': 'Exact match'
        }
    
    # Calculate simple similarity (word overlap)
    original_words = set(original.lower().split())
    double_check_words = set(double_check.lower().split())
    
    if not original_words and not double_check_words:
        similarity = 1.0
    elif not original_words or not double_check_words:
        similarity = 0.0
    else:
        intersection = original_words & double_check_words
        union = original_words | double_check_words
        similarity = len(intersection) / len(union) if union else 0.0
    
    # Check if they're similar (high similarity but not exact)
    notes = []
    if similarity > 0.8:
        notes.append('Very similar (likely same content, different formatting/translation)')
    elif similarity > 0.5:
        notes.append('Moderately similar (some differences)')
    else:
        notes.append('Significantly different')
    
    # Check length differences
    length_diff = abs(len(original) - len(double_check))
    percent_diff = 0.0
    if len(original) != len(double_check):
        notes.append(f'Length difference: {length_diff} chars')
        
        # Flag if > 15% difference (for English text) or > 10% (for Hebrew/Strong's)
        max_len = max(len(original), len(double_check))
        if max_len > 0:
            percent_diff = (length_diff / max_len) * 100
            threshold = 15 if field_name == 'text' else 10
            if percent_diff > threshold:
                notes.append(f'⚠️ WARNING: Length difference > {threshold}% ({percent_diff:.1f}%)')
    
    return {
        'match': False,
        'original_length': len(original),
        'double_check_length': len(double_check),
        'similarity': similarity,
        'notes': '; '.join(notes),
        'percent_diff': percent_diff,
        'original_text': original if field_name == 'text' and percent_diff > 15 else None,
        'double_check_text': double_check if field_name == 'text' and percent_diff > 15 else None
    }


def analyze_records(records, output_file):
    """
    Analyze all records and write detailed analysis to file.
    """
    text_matches = 0
    hebrew_matches = 0
    strongs_matches = 0
    
    text_similarities = []
    hebrew_similarities = []
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("DOUBLE-CHECK ANALYSIS REPORT\n")
        f.write("="*80 + "\n\n")
        
        f.write(f"Total records analyzed: {len(records)}\n\n")
        
        # Analyze each record
        f.write("="*80 + "\n")
        f.write("DETAILED RECORD ANALYSIS\n")
        f.write("="*80 + "\n\n")
        
        for i, record in enumerate(records, 1):
            f.write(f"Record {i}: {record['title']}\n")
            f.write("-" * 80 + "\n")
            
            verses = record.get('verses', [])
            f.write(f"Verses: {len(verses)}\n")
            # Handle both old format (objects) and new format (tuples/arrays)
            if verses and isinstance(verses[0], dict):
                verse_list = [(v['chapter'], v['verse']) for v in verses]
            else:
                verse_list = [tuple(v) if isinstance(v, list) else v for v in verses]
            f.write(f"Verse list: {verse_list}\n\n")
            
            # Text analysis
            origin_text = record.get('origin_field_text', '')
            double_check_text = record.get('double_check_text', '')
            text_analysis = compare_texts(origin_text, double_check_text, 'text')
            
            f.write("English Text:\n")
            f.write(f"  Origin text length: {text_analysis['original_length']}\n")
            f.write(f"  Double-check text length: {text_analysis['double_check_length']}\n")
            f.write(f"  Similarity: {text_analysis['similarity']:.3f}\n")
            f.write(f"  Notes: {text_analysis['notes']}\n")
            
            # Print both texts if difference > 15%
            if text_analysis.get('percent_diff', 0) > 15:
                f.write(f"\n  ⚠️ FULL TEXT COMPARISON (>15% difference):\n")
                f.write(f"  Origin text:\n")
                f.write(f"    {text_analysis.get('original_text', origin_text)}\n")
                f.write(f"  Double-check text:\n")
                f.write(f"    {text_analysis.get('double_check_text', double_check_text)}\n")
            
            if text_analysis['match']:
                text_matches += 1
            text_similarities.append(text_analysis['similarity'])
            f.write("\n")
            
            # Hebrew analysis - detailed character analysis
            origin_hebrew = record.get('origin_field_hebrew', '')
            double_check_hebrew = record.get('double_check_hebrew', '')
            hebrew_analysis = compare_texts(origin_hebrew, double_check_hebrew, 'hebrew')
            hebrew_diff_analysis = analyze_hebrew_differences(origin_hebrew, double_check_hebrew)
            
            f.write("Hebrew Text:\n")
            f.write(f"  Origin Hebrew length: {hebrew_analysis['original_length']}\n")
            f.write(f"  Double-check Hebrew length: {hebrew_analysis['double_check_length']}\n")
            f.write(f"  Similarity: {hebrew_analysis['similarity']:.3f}\n")
            f.write(f"  Notes: {hebrew_analysis['notes']}\n")
            
            # Detailed Hebrew character analysis
            if not hebrew_diff_analysis['exact_match']:
                f.write(f"\n  Hebrew Character Analysis:\n")
                
                # Junk characters in origin
                if hebrew_diff_analysis['junk_chars_origin']:
                    f.write(f"    ⚠️  Junk characters in ORIGIN ({len(hebrew_diff_analysis['junk_chars_origin'])} unique):\n")
                    for char, code, pos in hebrew_diff_analysis['junk_chars_origin'][:10]:
                        f.write(f"      - '{char}' (U+{code:04X}) at position {pos}\n")
                
                # Junk characters in double-check
                if hebrew_diff_analysis['junk_chars_double_check']:
                    f.write(f"    ⚠️  Junk characters in DOUBLE-CHECK ({len(hebrew_diff_analysis['junk_chars_double_check'])} unique):\n")
                    for char, code, pos in hebrew_diff_analysis['junk_chars_double_check'][:10]:
                        f.write(f"      - '{char}' (U+{code:04X}) at position {pos}\n")
                
                # Non-Hebrew characters
                if hebrew_diff_analysis['non_hebrew_chars_origin']:
                    f.write(f"    Non-Hebrew chars in ORIGIN ({len(hebrew_diff_analysis['non_hebrew_chars_origin'])} unique):\n")
                    for char, code, count in hebrew_diff_analysis['non_hebrew_chars_origin'][:10]:
                        f.write(f"      - '{char}' (U+{code:04X}) appears {count} times\n")
                
                if hebrew_diff_analysis['non_hebrew_chars_double_check']:
                    f.write(f"    Non-Hebrew chars in DOUBLE-CHECK ({len(hebrew_diff_analysis['non_hebrew_chars_double_check'])} unique):\n")
                    for char, code, count in hebrew_diff_analysis['non_hebrew_chars_double_check'][:10]:
                        f.write(f"      - '{char}' (U+{code:04X}) appears {count} times\n")
                
                # Character differences (first few)
                if hebrew_diff_analysis['character_differences']:
                    f.write(f"    First {min(10, len(hebrew_diff_analysis['character_differences']))} character differences:\n")
                    for pos, orig_char, dcheck_char, orig_code, dcheck_code in hebrew_diff_analysis['character_differences'][:10]:
                        f.write(f"      Position {pos}: origin='{orig_char}' (U+{orig_code:04X}) vs double-check='{dcheck_char}' (U+{dcheck_code:04X})\n")
            
            if hebrew_analysis['match']:
                hebrew_matches += 1
            hebrew_similarities.append(hebrew_analysis['similarity'])
            f.write("\n")
            
            # Strong's analysis
            origin_strongs = record.get('origin_field_strongs', '')
            double_check_strongs = record.get('double_check_strongs', '')
            
            f.write("Strong's Numbers:\n")
            origin_count = len(origin_strongs.split()) if origin_strongs else 0
            double_check_count = len(double_check_strongs.split()) if double_check_strongs else 0
            f.write(f"  Origin Strong's count: {origin_count}\n")
            f.write(f"  Double-check Strong's count: {double_check_count}\n")
            
            if origin_strongs == double_check_strongs:
                f.write(f"  Status: EXACT MATCH ✓\n")
                strongs_matches += 1
            else:
                f.write(f"  Status: DIFFERENT\n")
                if origin_count != double_check_count:
                    f.write(f"  Warning: Count mismatch ({origin_count} vs {double_check_count})\n")
            
            f.write("\n" + "="*80 + "\n\n")
        
        # Summary statistics
        f.write("\n" + "="*80 + "\n")
        f.write("SUMMARY STATISTICS\n")
        f.write("="*80 + "\n\n")
        
        f.write("--- English Text (origin_field_text vs double_check_text) ---\n")
        f.write(f"Exact matches: {text_matches}/{len(records)} ({100*text_matches/len(records):.1f}%)\n")
        if text_similarities:
            avg_sim = sum(text_similarities) / len(text_similarities)
            f.write(f"Average similarity: {avg_sim:.3f}\n")
            f.write(f"Note: These are different translations, so exact match not expected\n")
        f.write("\n")
        
        f.write("--- Hebrew Text (origin_field_hebrew vs double_check_hebrew) ---\n")
        f.write(f"Exact matches: {hebrew_matches}/{len(records)} ({100*hebrew_matches/len(records):.1f}%)\n")
        if hebrew_similarities:
            avg_sim = sum(hebrew_similarities) / len(hebrew_similarities)
            f.write(f"Average similarity: {avg_sim:.3f}\n")
            f.write(f"Note: May differ due to textual variations between sources\n")
        f.write("\n")
        
        f.write("--- Strong's Numbers (origin_field_strongs vs double_check_strongs) ---\n")
        f.write(f"Exact matches: {strongs_matches}/{len(records)} ({100*strongs_matches/len(records):.1f}%)\n")
        f.write(f"Note: These should match exactly if both sources use same Strong's mapping\n")
        f.write("\n")
        
        f.write("="*80 + "\n")


def analyze_double_check_records():
    """
    Main function to analyze double-check decoder ring records.
    """
    # Get the script directory and data directory
    # Script is in data/double_check/, so parent is data/
    script_dir = Path(__file__).parent
    data_dir = script_dir.parent  # Go up one level to data/
    
    # File paths
    records_file = data_dir / 'double_check' / 'decoder_ring_records_double_check.json'
    output_file = data_dir / 'double_check' / 'decoder_ring_records_analysis.txt'
    
    print("Loading double-check records...")
    with open(records_file, 'r', encoding='utf-8') as f:
        records = json.load(f)
    
    print(f"Analyzing {len(records)} records...")
    
    analyze_records(records, output_file)
    
    print(f"\nAnalysis complete! Results written to {output_file}")
    print("Done!")


if __name__ == '__main__':
    analyze_double_check_records()

