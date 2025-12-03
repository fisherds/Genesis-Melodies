#!/usr/bin/env python3
"""
Generate three levels of records from Genesis 1-12 divisions:
- quilt_piece_records.json (5 records - highest level)
- pericope_records.json (50 records - medium level, was decoder_ring_records.json)
- verse_records.json (304 records - lowest level, individual verses)
"""

import json
import re
from pathlib import Path


def parse_chapter_and_verse(verse_str):
    """
    Parse a verse string like "1:1" into chapter and verse.
    Raises ValueError if the format is invalid.
    """
    parts = verse_str.strip().split(':')
    if len(parts) != 2:
        raise ValueError(f"Invalid verse format: '{verse_str}'. Expected format: 'chapter:verse' (e.g., '1:1')")
    
    try:
        chapter = int(parts[0])
        verse = int(parts[1])
        return chapter, verse
    except ValueError as e:
        raise ValueError(f"Invalid verse format: '{verse_str}'. Chapter and verse must be integers. Error: {e}")


def parse_verse_list(verse_list_str):
    """
    Parse a verse list string like "[1:1, 1:2, 1:3]" into a list of (chapter, verse) tuples.
    """
    verse_list_str = verse_list_str.strip('[]')
    verse_parts = [v.strip() for v in verse_list_str.split(',')]
    
    verses = []
    
    for verse_part in verse_parts:
        chapter, verse = parse_chapter_and_verse(verse_part)
        verses.append((chapter, verse))
    
    return verses


def parse_divisions_file(file_path):
    """
    Parse a divisions file (quilt_piece_divisions.txt or decoder_ring_divisions.txt)
    to extract titles and verse lists.
    Returns a list of (title, verse_list) tuples.
    """
    records = []
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    i = 0
    while i < len(lines):
        title = lines[i].strip()
        if i + 1 >= len(lines):
            break
        verse_list_str = lines[i + 1].strip()
        if not title or not verse_list_str:
            raise ValueError(f"Line {i+1}: Empty line found. File should contain only title/verse list pairs with no empty lines.")
        if not verse_list_str.startswith('[') or not verse_list_str.endswith(']'):
            raise ValueError(f"Line {i+2}: Expected verse list starting with '[' and ending with ']', but found: '{verse_list_str}'. Title on line {i+1}: '{title}'")
        
        verses = parse_verse_list(verse_list_str)
        records.append((title, verses))
        i += 2
    
    return records


def load_bibleproject_translation(file_path):
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
                # Only include Genesis 1:1 to 12:5
                if current_chapter == 1 or (current_chapter == 12 and verse_num <= 5) or (1 < current_chapter < 12):
                    lookup[(current_chapter, verse_num)] = verse_text
    
    return lookup


def load_wlca(file_path):
    """
    Load WLCa JSON and create lookups for Hebrew text and Strong's numbers.
    Returns (hebrew_lookup, strongs_lookup) where:
    - hebrew_lookup: (chapter, verse) -> hebrew_text (without Strong's tags)
    - strongs_lookup: (chapter, verse) -> list of Strong's numbers
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    hebrew_lookup = {}
    strongs_lookup = {}
    
    for entry in data:
        if entry.get('book') != 1:
            continue
            
        chapter = entry['chapter']
        verse = entry['verse']
        # Only include Genesis 1:1 to 12:5
        if chapter == 1 or (chapter == 12 and verse <= 5) or (1 < chapter < 12):
            text = entry['text']
            
            # Extract Strong's numbers
            strongs_pattern = r'<S>(\d+)</S>'
            strongs_matches = re.findall(strongs_pattern, text)
            strongs_lookup[(chapter, verse)] = [f"h{num}" for num in strongs_matches]
            
            # Remove Strong's tags to get Hebrew text
            hebrew_text = re.sub(r'<S>\d+</S>', '', text)
            # Remove ketiv/qere markers like [k_...] and [q_...]
            hebrew_text = re.sub(r'\[k_[^\]]+\]', '', hebrew_text)
            hebrew_text = re.sub(r'\[q_[^\]]+\]', '', hebrew_text)
            # Remove HTML tags like <br/> (only at end of text)
            hebrew_text = hebrew_text.replace('<br/>', '')
            # Clean up any extra whitespace
            hebrew_text = ' '.join(hebrew_text.split())
            hebrew_lookup[(chapter, verse)] = hebrew_text
    
    return hebrew_lookup, strongs_lookup


def concatenate_verses(verses, lookup):
    """
    Concatenate verse texts with spaces.
    
    Args:
        verses: List of (chapter, verse) tuples
        lookup: Dict mapping (chapter, verse) -> text
    """
    texts = []
    
    for chapter, verse in verses:
        key = (chapter, verse)
        if key not in lookup:
            print(f"Warning: Missing data for {chapter}:{verse}")
            continue
        
        text = lookup[key]
        texts.append(text)
    
    return ' '.join(texts)


def concatenate_strongs(verses, strongs_lookup):
    """
    Concatenate Strong's numbers with spaces.
    """
    strongs_list = []
    
    for chapter, verse in verses:
        key = (chapter, verse)
        if key not in strongs_lookup:
            continue
        
        strongs = strongs_lookup[key]
        strongs_list.extend(strongs)
    
    return ' '.join(strongs_list)


def generate_quilt_piece_records(divisions, bibleproject_lookup, hebrew_lookup, strongs_lookup, records_dir):
    """Generate quilt_piece_records.json (5 records)."""
    print("\n=== Generating Quilt Piece Records ===")
    records = []
    
    for idx, (title, verses) in enumerate(divisions, start=1):
        record_id = f"quilt_piece_{idx:02d}"
        
        # Get texts
        english_text = concatenate_verses(verses, bibleproject_lookup)
        hebrew_text = concatenate_verses(verses, hebrew_lookup)
        strongs_text = concatenate_strongs(verses, strongs_lookup)
        
        # Convert verses to verbose format: [{"chapter": 1, "verse": 1}, ...]
        verse_objects = [{"chapter": ch, "verse": v} for ch, v in verses]
        
        record = {
            "id": record_id,
            "title": title,
            "text": english_text,
            "verses": verse_objects,
            "hebrew": hebrew_text,
            "strongs": strongs_text
        }
        
        records.append(record)
    
    output_file = records_dir / 'quilt_piece_records.json'
    print(f"Writing {len(records)} quilt piece records to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
    
    return records


def generate_pericope_records(divisions, bibleproject_lookup, hebrew_lookup, strongs_lookup, quilt_piece_records, records_dir):
    """Generate pericope_records.json (50 records) with quilt_pieces field."""
    print("\n=== Generating Pericope Records ===")
    records = []
    
    for idx, (title, verses) in enumerate(divisions, start=1):
        record_id = f"pericope_{idx:02d}"
        
        # Get texts
        english_text = concatenate_verses(verses, bibleproject_lookup)
        hebrew_text = concatenate_verses(verses, hebrew_lookup)
        strongs_text = concatenate_strongs(verses, strongs_lookup)
        
        # Determine which quilt pieces this pericope belongs to
        # Rule: If every verse of a pericope is fully contained within a quilt piece, then it's in that quilt piece
        quilt_pieces = []
        pericope_verses_set = set(verses)  # verses is already a list of tuples
        for qp in quilt_piece_records:
            # Convert qp verses from objects to tuples for comparison
            qp_verses_set = {(v['chapter'], v['verse']) for v in qp['verses']}
            if pericope_verses_set.issubset(qp_verses_set):
                quilt_pieces.append(qp['id'])
        
        # Convert verses to verbose format: [{"chapter": 1, "verse": 1}, ...]
        verse_objects = [{"chapter": ch, "verse": v} for ch, v in verses]
        
        record = {
            "id": record_id,
            "title": title,
            "text": english_text,
            "verses": verse_objects,
            "hebrew": hebrew_text,
            "strongs": strongs_text,
            "quilt_pieces": quilt_pieces
        }
        
        records.append(record)
    
    output_file = records_dir / 'pericope_records.json'
    print(f"Writing {len(records)} pericope records to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
    
    return records


def generate_verse_records(bibleproject_lookup, hebrew_lookup, strongs_lookup, quilt_piece_records, pericope_records, records_dir):
    """Generate verse_records.json (304 records) with quilt_pieces and pericopes fields."""
    print("\n=== Generating Verse Records ===")
    
    # Generate all verses from 1:1 to 12:5
    chapter_lengths = {
        1: 31, 2: 25, 3: 24, 4: 26, 5: 32, 6: 22,
        7: 24, 8: 22, 9: 29, 10: 32, 11: 32, 12: 5
    }
    
    all_verses = []
    for ch in range(1, 13):
        max_v = chapter_lengths.get(ch, 0)
        for v in range(1, max_v + 1):
            all_verses.append((ch, v))
    
    records = []
    
    for chapter, verse in all_verses:
        # Generate ID: verse_01_01 to verse_12_05
        record_id = f"verse_{chapter:02d}_{verse:02d}"
        
        # Generate title: "Genesis 1:1" to "Genesis 12:5"
        title = f"Genesis {chapter}:{verse}"
        
        # Get texts for this single verse
        verses_list = [(chapter, verse)]
        english_text = concatenate_verses(verses_list, bibleproject_lookup)
        hebrew_text = concatenate_verses(verses_list, hebrew_lookup)
        strongs_text = concatenate_strongs(verses_list, strongs_lookup)
        
        # Determine which quilt pieces this verse belongs to
        quilt_pieces = []
        for qp in quilt_piece_records:
            # Convert qp verses from objects to tuples for comparison
            qp_verses_tuples = {(v['chapter'], v['verse']) for v in qp['verses']}
            if (chapter, verse) in qp_verses_tuples:
                quilt_pieces.append(qp['id'])
        
        # Determine which pericopes this verse belongs to
        pericopes = []
        for pc in pericope_records:
            # Convert pc verses from objects to tuples for comparison
            pc_verses_tuples = {(v['chapter'], v['verse']) for v in pc['verses']}
            if (chapter, verse) in pc_verses_tuples:
                pericopes.append(pc['id'])
        
        # Convert verses to verbose format: [{"chapter": 1, "verse": 1}]
        verse_objects = [{"chapter": chapter, "verse": verse}]
        
        record = {
            "id": record_id,
            "title": title,
            "text": english_text,
            "verses": verse_objects,  # Always exactly 1 verse
            "hebrew": hebrew_text,
            "strongs": strongs_text,
            "quilt_pieces": quilt_pieces,
            "pericopes": pericopes
        }
        
        records.append(record)
    
    output_file = records_dir / 'verse_records.json'
    print(f"Writing {len(records)} verse records to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
    
    return records


def generate_all_records():
    """
    Main function to generate all three levels of records.
    """
    # Get the script directory and data directory
    script_dir = Path(__file__).parent
    data_dir = script_dir
    
    # File paths - raw data is in raw/ subdirectory
    raw_dir = data_dir / 'raw'
    records_dir = data_dir / 'records'
    records_dir.mkdir(exist_ok=True, parents=True)
    
    quilt_piece_divisions_file = raw_dir / 'quilt_piece_divisions.txt'
    pericope_divisions_file = raw_dir / 'pericope_divisions.txt'
    bibleproject_translation_file = raw_dir / 'bp_translation_gen_1_25.txt'
    wlca_file = raw_dir / 'WLCa.json'
    
    print("Loading data files...")
    quilt_piece_divisions = parse_divisions_file(quilt_piece_divisions_file)
    pericope_divisions = parse_divisions_file(pericope_divisions_file)
    bibleproject_english_lookup = load_bibleproject_translation(bibleproject_translation_file)
    hebrew_lookup, strongs_lookup = load_wlca(wlca_file)
    
    print(f"Found {len(quilt_piece_divisions)} quilt piece divisions")
    print(f"Found {len(pericope_divisions)} pericope divisions")
    
    # Generate in order: quilt_piece -> pericope -> verse
    quilt_piece_records = generate_quilt_piece_records(
        quilt_piece_divisions, bibleproject_english_lookup, hebrew_lookup, strongs_lookup, records_dir
    )
    
    pericope_records = generate_pericope_records(
        pericope_divisions, bibleproject_english_lookup, hebrew_lookup, strongs_lookup, 
        quilt_piece_records, records_dir
    )
    
    verse_records = generate_verse_records(
        bibleproject_english_lookup, hebrew_lookup, strongs_lookup,
        quilt_piece_records, pericope_records, records_dir
    )
    
    print("\n=== Summary ===")
    print(f"✓ Generated {len(quilt_piece_records)} quilt piece records")
    print(f"✓ Generated {len(pericope_records)} pericope records")
    print(f"✓ Generated {len(verse_records)} verse records")
    print("\nDone!")


if __name__ == '__main__':
    generate_all_records()
