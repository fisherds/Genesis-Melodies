"""
Agentic Chunking System

Creates optimized chunks for three different embedding models:
- BERiT (Hebrew, Lmax=128)
- Hebrew ST (Hebrew, Lmax=512)
- English ST (English, Lmax=384)

Uses SpacyTextSplitter to create semantically-aware chunks that can span
partial verses, then maps chunks back to verse references.
"""

import json
from pathlib import Path
from langchain_text_splitters import SpacyTextSplitter
import re

# Model configurations
# Chunk sizes adjusted based on actual tokenization results
# Target: ~75% of max tokens to leave safety margin for variability
MODEL_CONFIGS = {
    "berit": {
        "pipeline": None,  # Hebrew pipeline not available, will use fallback
        "chunk_size": 180,  # Target ~94 tokens (73% of 128), based on ~0.52 tokens/char ratio
        "chunk_overlap": 30,  # ~17% overlap
        "language": "hebrew"
    },
    "hebrew_st": {
        "pipeline": None,  # Hebrew pipeline not available, will use fallback
        "chunk_size": 600,  # Target ~282 tokens (55% of 512), based on ~0.47 tokens/char ratio - Best practice: 200-400 tokens
        "chunk_overlap": 120,  # ~20% overlap
        "language": "hebrew"
    },
    "english_st": {
        "pipeline": "en_core_web_sm",  # English pipeline
        "chunk_size": 800,  # Target ~176 tokens (46% of 384), based on ~0.22 tokens/char ratio - Best practice: 200-400 tokens
        "chunk_overlap": 160,  # ~20% overlap
        "language": "english"
    }
}

# Chapter lengths for Genesis 1-25
CHAPTER_LENGTHS = {
    1: 31, 2: 25, 3: 24, 4: 26, 5: 32, 6: 22, 7: 24, 8: 22, 9: 29, 10: 32,
    11: 32, 12: 20, 13: 18, 14: 24, 15: 21, 16: 16, 17: 27, 18: 33, 19: 38,
    20: 18, 21: 34, 22: 24, 23: 20, 24: 67, 25: 18
}


def load_verse_records(records_dir: Path):
    """Load verse records from JSON file."""
    verse_records_path = records_dir / 'verse_records.json'
    with open(verse_records_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_text_visuals(flask_server_dir: Path):
    """Load text visuals to check for verse dividers."""
    visuals_path = flask_server_dir / 'public' / 'scripts' / 'text_visuals.json'
    if visuals_path.exists():
        with open(visuals_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def create_verse_lookup(verse_records):
    """Create lookup dictionaries for verses."""
    verse_lookup = {}  # (chapter, verse) -> verse_record
    verse_list = []  # Ordered list of (chapter, verse) tuples
    
    for record in verse_records:
        if record['verses']:
            ch = record['verses'][0]['chapter']
            v = record['verses'][0]['verse']
            verse_lookup[(ch, v)] = record
            verse_list.append((ch, v))
    
    return verse_lookup, verse_list


def concatenate_verses_for_chunking(verse_list, verse_lookup, language="hebrew", text_visuals=None):
    """
    Concatenate verses with appropriate separators.
    Uses spaces by default, but checks text_visuals for special dividers.
    Returns full text and verse boundaries with accurate character positions.
    """
    texts = []
    verse_boundaries = []  # List of (chapter, verse, start_pos, end_pos, verse_text, word_count)
    current_pos = 0
    separator = " "
    
    for i, (ch, v) in enumerate(verse_list):
        record = verse_lookup.get((ch, v))
        if not record:
            continue
        
        # Get the appropriate text based on language
        if language == "hebrew":
            text = record.get('hebrew', '')
        else:  # english
            text = record.get('text', '')
        
        if not text:
            continue
        
        # Count words in this verse
        words = text.split()
        word_count = len(words)
        
        # Track verse boundary with accurate position
        verse_start = current_pos
        verse_end = current_pos + len(text)
        verse_boundaries.append((ch, v, verse_start, verse_end, text, word_count))
        
        texts.append(text)
        
        # Update position (text + separator for next verse, except last)
        current_pos = verse_end
        if i < len(verse_list) - 1:
            current_pos += len(separator)
    
    # Join with spaces
    full_text = separator.join(texts)
    
    return full_text, verse_boundaries


def find_verse_references(chunk_text, chunk_start, chunk_end, verse_boundaries, verse_list, verse_lookup, language="hebrew"):
    """
    Map a chunk back to verse references, including partial verses.
    Returns list of verse objects with decimal notation for partial verses.
    Also returns the actual partial text for each verse.
    """
    verse_refs = []
    verse_partial_texts = []  # Store the actual partial text for each verse: (ch, v, partial_text, is_full, word_count)
    
    # Find which verses are covered by this chunk
    for i, (ch, v, v_start, v_end, verse_text, total_words) in enumerate(verse_boundaries):
        # Check if this verse overlaps with the chunk
        if v_end < chunk_start or v_start > chunk_end:
            continue
        
        # Calculate overlap
        overlap_start = max(chunk_start, v_start)
        overlap_end = min(chunk_end, v_end)
        
        # Calculate character offset within the verse
        char_offset_in_verse = overlap_start - v_start
        char_length_in_verse = overlap_end - overlap_start
        
        # Extract the overlapping text from the verse more accurately
        if char_offset_in_verse >= 0 and char_offset_in_verse < len(verse_text):
            # Get the actual overlapping text
            overlap_text = verse_text[char_offset_in_verse:char_offset_in_verse + char_length_in_verse]
            
            # Find which words are in the overlap by checking word boundaries
            verse_words = verse_text.split()
            overlap_words_list = []
            current_char_pos = 0
            
            for word in verse_words:
                # Find word position in verse
                word_start_in_verse = verse_text.find(word, current_char_pos)
                if word_start_in_verse == -1:
                    word_start_in_verse = current_char_pos
                word_end_in_verse = word_start_in_verse + len(word)
                current_char_pos = word_end_in_verse
                
                # Check if word overlaps with our chunk range
                word_start_absolute = v_start + word_start_in_verse
                word_end_absolute = v_start + word_end_in_verse
                
                if word_end_absolute > overlap_start and word_start_absolute < overlap_end:
                    overlap_words_list.append(word)
            
            overlap_words = len(overlap_words_list)
            partial_text = " ".join(overlap_words_list) if overlap_words_list else ""
        else:
            overlap_words = 0
            partial_text = ""
        
        # Determine if this is a partial verse
        is_full_verse = (overlap_start == v_start and overlap_end == v_end)
        is_start_of_verse = (overlap_start == v_start)
        is_end_of_verse = (overlap_end == v_end)
        
        # Check if overlap is actually the full verse
        # Use word count as primary check, with character position as secondary
        tolerance = 2  # Allow 2 character difference for whitespace
        is_actually_full = (abs(overlap_start - v_start) <= tolerance and 
                           abs(overlap_end - v_end) <= tolerance)
        
        # If word count matches or exceeds total, it's a full verse
        if is_actually_full or overlap_words >= total_words:
            # Full verse - use integer, not float
            verse_refs.append({"chapter": ch, "verse": v})
            verse_partial_texts.append((ch, v, verse_text, True, total_words))
        elif is_start_of_verse:
            # Partial at end: e.g., 1:2.4 means 4 words from start of verse 2
            if overlap_words > 0 and overlap_words < total_words:
                verse_refs.append({"chapter": ch, "verse": float(f"{v}.{overlap_words}")})
                # Extract first N words from verse
                words = verse_text.split()
                partial_text = " ".join(words[:overlap_words]) if overlap_words <= len(words) else verse_text
                verse_partial_texts.append((ch, v, partial_text, False, overlap_words))
            elif overlap_words >= total_words:
                # Actually full verse
                verse_refs.append({"chapter": ch, "verse": v})
                verse_partial_texts.append((ch, v, verse_text, True, total_words))
        elif is_end_of_verse:
            # Partial at start: e.g., 1:4.2 means last 2 words of verse 4
            words_from_end = total_words - overlap_words
            if words_from_end > 0 and words_from_end < total_words:
                verse_refs.append({"chapter": ch, "verse": float(f"{v}.{words_from_end}")})
                # Extract last N words from verse
                words = verse_text.split()
                partial_text = " ".join(words[-words_from_end:]) if words_from_end <= len(words) else verse_text
                verse_partial_texts.append((ch, v, partial_text, False, overlap_words))
            elif words_from_end <= 0 or overlap_words >= total_words:
                # Actually full verse
                verse_refs.append({"chapter": ch, "verse": v})
                verse_partial_texts.append((ch, v, verse_text, True, total_words))
        else:
            # Partial in middle (rare) - use words from start
            if overlap_words > 0 and overlap_words < total_words:
                verse_refs.append({"chapter": ch, "verse": float(f"{v}.{overlap_words}")})
                # Extract first N words from verse (approximation)
                words = verse_text.split()
                partial_text = " ".join(words[:overlap_words]) if overlap_words <= len(words) else verse_text
                verse_partial_texts.append((ch, v, partial_text, False, overlap_words))
            elif overlap_words >= total_words:
                # Actually full verse
                verse_refs.append({"chapter": ch, "verse": v})
                verse_partial_texts.append((ch, v, verse_text, True, total_words))
    
    return verse_refs, verse_partial_texts


def create_chunks_for_model(verse_records, model_name, model_config, records_dir: Path, text_visuals=None):
    """
    Create chunks for a specific model using SpacyTextSplitter.
    """
    print(f"\n=== Creating chunks for {model_name} ===")
    
    # Create verse lookup
    verse_lookup, verse_list = create_verse_lookup(verse_records)
    
    # Concatenate all verses
    language = model_config["language"]
    full_text, verse_boundaries = concatenate_verses_for_chunking(
        verse_list, verse_lookup, language=language, text_visuals=text_visuals
    )
    
    print(f"Full text length: {len(full_text)} characters")
    print(f"Number of verses: {len(verse_list)}")
    
    # Create text splitter and get chunks with positions
    chunks_with_positions = []
    
    # Check if pipeline is available
    pipeline = model_config["pipeline"]
    use_spacy = pipeline is not None
    
    if use_spacy:
        try:
            text_splitter = SpacyTextSplitter(
                pipeline=pipeline,
                chunk_size=model_config["chunk_size"],
                chunk_overlap=model_config["chunk_overlap"],
                separator=" ",
            )
            chunks = text_splitter.split_text(full_text)
            print(f"Created {len(chunks)} chunks using SpacyTextSplitter")
            
            # Find positions of each chunk in the full text
            current_pos = 0
            for chunk in chunks:
                # Find where this chunk appears in the full text
                chunk_start = full_text.find(chunk, current_pos)
                if chunk_start == -1:
                    # If exact match not found (due to whitespace differences), use current_pos
                    chunk_start = current_pos
                chunk_end = chunk_start + len(chunk)
                chunks_with_positions.append((chunk, chunk_start, chunk_end))
                current_pos = chunk_end - model_config["chunk_overlap"]
        except Exception as e:
            print(f"Error creating chunks with Spacy: {e}")
            print("Falling back to simple character-based splitting...")
            use_spacy = False
    
    if not use_spacy:
        # Fallback: simple character-based splitting
        print("Using character-based splitting (Spacy model not available)")
        chunk_size = model_config["chunk_size"]
        chunk_overlap = model_config["chunk_overlap"]
        start = 0
        while start < len(full_text):
            end = start + chunk_size
            chunk = full_text[start:end]
            chunks_with_positions.append((chunk, start, end))
            start = end - chunk_overlap
            if start >= len(full_text):
                break
    
    # Map chunks back to verse references
    records = []
    
    for i, (chunk, chunk_start, chunk_end) in enumerate(chunks_with_positions):
        
        # Find verse references for this chunk
        verse_refs, verse_partial_texts = find_verse_references(
            chunk, chunk_start, chunk_end, verse_boundaries,
            verse_list, verse_lookup, language=language
        )
        
        if not verse_refs:
            current_pos = chunk_end
            continue
        
        # Clean up verse refs: remove .0 and convert full verses to integers
        cleaned_verse_refs = []
        for vref in verse_refs:
            ch = vref["chapter"]
            v = vref["verse"]
            if isinstance(v, float):
                # Check if it's effectively a whole verse (.0 or equals total words)
                if v == int(v):  # e.g., 1.0
                    cleaned_verse_refs.append({"chapter": ch, "verse": int(v)})
                else:
                    cleaned_verse_refs.append({"chapter": ch, "verse": v})
            else:
                cleaned_verse_refs.append({"chapter": ch, "verse": v})
        
        # Build title (clean up .0 in display)
        title_parts = []
        for vref in cleaned_verse_refs:
            ch = vref["chapter"]
            v = vref["verse"]
            if isinstance(v, float) and v == int(v):
                title_parts.append(f"{ch}:{int(v)}")
            elif isinstance(v, float):
                title_parts.append(f"{ch}:{v}")
            else:
                title_parts.append(f"{ch}:{v}")
        title = ", ".join(title_parts)
        
        # Get all verses used (for full verse lookups)
        verses_used = set()
        for vref in cleaned_verse_refs:
            ch = vref["chapter"]
            v = vref["verse"]
            if isinstance(v, float):
                v = int(v)  # Get base verse number
            verses_used.add((ch, v))
        
        # Build text based on chunking language
        if language == "hebrew":
            # Hebrew-chunked: extract partial Hebrew/Strongs, but full English
            hebrew_parts = []
            strongs_parts = []
            for vref, (ch_part, v_part, partial_text, is_full, word_count) in zip(cleaned_verse_refs, verse_partial_texts):
                record = verse_lookup.get((ch_part, v_part))
                if not record:
                    continue
                
                if is_full:
                    # Full verse - get from lookup
                    hebrew_parts.append(record.get('hebrew', ''))
                    strongs_parts.append(record.get('strongs', ''))
                else:
                    # Partial verse - extract first N words from Hebrew/Strongs
                    hebrew_full = record.get('hebrew', '')
                    strongs_full = record.get('strongs', '')
                    hebrew_words = hebrew_full.split()
                    strongs_words = strongs_full.split()
                    
                    # Extract first word_count words (use the partial_text word count, not the decimal)
                    # The decimal notation tells us how many words: e.g., 2.7 means 7 words
                    v = vref["verse"]
                    if isinstance(v, float):
                        # Extract the decimal part to get word count
                        decimal_str = str(v).split('.')[1]
                        word_count_from_decimal = int(decimal_str)
                    else:
                        word_count_from_decimal = word_count
                    
                    if word_count_from_decimal > 0 and word_count_from_decimal <= len(hebrew_words):
                        hebrew_parts.append(" ".join(hebrew_words[:word_count_from_decimal]))
                        if word_count_from_decimal <= len(strongs_words):
                            strongs_parts.append(" ".join(strongs_words[:word_count_from_decimal]))
                        else:
                            strongs_parts.append(strongs_full)
                    else:
                        # Fallback to full if count doesn't match
                        hebrew_parts.append(hebrew_full)
                        strongs_parts.append(strongs_full)
            
            # English: always full verses
            english_parts = []
            for ch, v in sorted(verses_used):
                record = verse_lookup.get((ch, v))
                if record:
                    english_parts.append(record.get('text', ''))
            
            hebrew_text = " ".join(hebrew_parts)
            strongs_text = " ".join(strongs_parts)
            english_text = " ".join(english_parts)
        else:
            # English-chunked: extract partial English, but full Hebrew/Strongs
            english_parts = []
            for vref, (ch_part, v_part, partial_text, is_full, word_count) in zip(cleaned_verse_refs, verse_partial_texts):
                if is_full:
                    # Full verse - get from lookup
                    record = verse_lookup.get((ch_part, v_part))
                    if record:
                        english_parts.append(record.get('text', ''))
                else:
                    # Partial verse - use the partial text (already extracted from chunk)
                    english_parts.append(partial_text)
            
            # Hebrew/Strongs: always full verses
            hebrew_parts = []
            strongs_parts = []
            for ch, v in sorted(verses_used):
                record = verse_lookup.get((ch, v))
                if record:
                    hebrew_parts.append(record.get('hebrew', ''))
                    strongs_parts.append(record.get('strongs', ''))
            
            hebrew_text = " ".join(hebrew_parts)
            strongs_text = " ".join(strongs_parts)
            english_text = " ".join(english_parts)
        
        # Create record
        record_id = f"agentic_{model_name}_{i+1:03d}"
        record = {
            "id": record_id,
            "title": f"Genesis {title}",
            "text": english_text,  # Always English for text field
            "verses": cleaned_verse_refs,
            "hebrew": hebrew_text,
            "strongs": strongs_text
        }
        
        records.append(record)
        
        # Update position (accounting for overlap)
        current_pos = chunk_end - model_config["chunk_overlap"]
    
    # Write output
    output_file = records_dir / f'agentic_{model_name}_records.json'
    print(f"Writing {len(records)} records to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
    
    return records


def main():
    """Main function to create all agentic chunking records."""
    # Get paths
    # Script is in functions/data/, so data_dir is the parent directory
    data_dir = Path(__file__).parent  # functions/data/
    records_dir = data_dir / 'records'
    # text_visuals.json is in public/scripts/ (if it exists)
    project_root = Path(__file__).parent.parent.parent
    flask_server_dir = project_root / 'public' / 'scripts'  # For text_visuals.json
    
    # Load data
    print("Loading verse records...")
    verse_records = load_verse_records(records_dir)
    print(f"Loaded {len(verse_records)} verse records")
    
    print("Loading text visuals...")
    text_visuals = load_text_visuals(flask_server_dir)
    print(f"Loaded {len(text_visuals)} text visuals")
    
    # Create chunks for each model
    for model_name, model_config in MODEL_CONFIGS.items():
        try:
            create_chunks_for_model(
                verse_records, model_name, model_config, records_dir, text_visuals
            )
        except Exception as e:
            print(f"Error processing {model_name}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n=== Agentic chunking complete ===")


if __name__ == "__main__":
    main()

