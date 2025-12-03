"""
Utility for parsing Bible verse references and extracting Hebrew text from WLCa.json
"""

import re
import json
from pathlib import Path
from typing import List, Tuple, Optional


# Bible book names and abbreviations (case-insensitive, no periods)
# Format: (book_number, [name, abbrev1, abbrev2, ...])
BIBLE_BOOKS = [
    (1, ["genesis", "gen", "ge", "gn"]),
    (2, ["exodus", "ex", "exod", "exo"]),
    (3, ["leviticus", "lev", "le", "lv"]),
    (4, ["numbers", "num", "nu", "nm", "nb"]),
    (5, ["deuteronomy", "deut", "de", "dt"]),
    (6, ["joshua", "josh", "jos", "jsh"]),
    (7, ["judges", "judg", "jdg", "jg", "jdgs"]),
    (8, ["ruth", "rth", "ru"]),
    (9, ["1 samuel", "1 sam", "1 sm", "1 sa", "1 s", "i sam", "i sa", "1sam", "1sa", "1s", "1st samuel", "1st sam", "first samuel", "first sam"]),
    (10, ["2 samuel", "2 sam", "2 sm", "2 sa", "2 s", "ii sam", "ii sa", "2sam", "2sa", "2s", "2nd samuel", "2nd sam", "second samuel", "second sam"]),
    (11, ["1 kings", "1 kgs", "1 ki", "1kgs", "1kin", "1ki", "1k", "i kgs", "i ki", "1st kings", "1st kgs", "first kings", "first kgs"]),
    (12, ["2 kings", "2 kgs", "2 ki", "2kgs", "2kin", "2ki", "2k", "ii kgs", "ii ki", "2nd kings", "2nd kgs", "second kings", "second kgs"]),
    (13, ["1 chronicles", "1 chron", "1 chr", "1 ch", "1chron", "1chr", "1ch", "i chron", "i chr", "i ch", "1st chronicles", "1st chron", "first chronicles", "first chron"]),
    (14, ["2 chronicles", "2 chron", "2 chr", "2 ch", "2chron", "2chr", "2ch", "ii chron", "ii chr", "ii ch", "2nd chronicles", "2nd chron", "second chronicles", "second chron"]),
    (15, ["ezra", "ezr", "ez"]),
    (16, ["nehemiah", "neh", "ne"]),
    (17, ["esther", "est", "esth", "es"]),
    (18, ["job", "jb"]),
    (19, ["psalms", "ps", "psalm", "pslm", "psa", "psm", "pss"]),
    (20, ["proverbs", "prov", "pro", "prv", "pr"]),
    (21, ["ecclesiastes", "eccles", "eccle", "ecc", "ec", "qoh"]),
    (22, ["song of solomon", "song", "song of songs", "sos", "so", "canticle of canticles", "canticles", "cant"]),
    (23, ["isaiah", "isa", "is"]),
    (24, ["jeremiah", "jer", "je", "jr"]),
    (25, ["lamentations", "lam", "la"]),
    (26, ["ezekiel", "ezek", "eze", "ezk"]),
    (27, ["daniel", "dan", "da", "dn"]),
    (28, ["hosea", "hos", "ho"]),
    (29, ["joel", "jl"]),
    (30, ["amos", "am"]),
    (31, ["obadiah", "obad", "ob"]),
    (32, ["jonah", "jnh", "jon"]),
    (33, ["micah", "mic", "mc"]),
    (34, ["nahum", "nah", "na"]),
    (35, ["habakkuk", "hab", "hb"]),
    (36, ["zephaniah", "zeph", "zep", "zp"]),
    (37, ["haggai", "hag", "hg"]),
    (38, ["zechariah", "zech", "zec", "zc"]),
    (39, ["malachi", "mal", "ml"]),
]

# Create lookup: normalized name -> book_number
BOOK_LOOKUP = {}
for book_num, names in BIBLE_BOOKS:
    for name in names:
        # Normalize: lowercase, no periods, no extra spaces
        normalized = re.sub(r'[.\s]+', ' ', name.lower().strip())
        BOOK_LOOKUP[normalized] = book_num


def normalize_book_name(book_str: str) -> Optional[int]:
    """
    Normalize a book name/abbreviation and return the book number.
    Returns None if not found.
    """
    # Remove periods, normalize whitespace, lowercase
    normalized = re.sub(r'[.\s]+', ' ', book_str.lower().strip())
    return BOOK_LOOKUP.get(normalized)


def parse_verse_reference(ref_str: str) -> List[Tuple[int, int, int]]:
    """
    Parse a verse reference string into a list of (book, chapter, verse) tuples.
    
    Supports:
    - Single verse: "Ezra 1:2" or "2 Samuel 11:2"
    - Range: "Ps 119:1 Ps 119:6" (inclusive, RTL order)
    
    Returns list of (book_num, chapter, verse) tuples.
    Raises ValueError if parsing fails.
    """
    # Split by spaces to get tokens
    tokens = ref_str.strip().split()
    if not tokens:
        raise ValueError("Empty verse reference")
    
    def find_book_name(start_idx: int) -> Tuple[Optional[int], int]:
        """
        Try to find a book name starting at start_idx.
        Returns (book_num, end_idx) where end_idx is the index after the book name.
        """
        # Try progressively longer book names (1 token, 2 tokens, 3 tokens, etc.)
        for end_idx in range(start_idx + 1, len(tokens) + 1):
            book_str = ' '.join(tokens[start_idx:end_idx])
            book_num = normalize_book_name(book_str)
            if book_num is not None:
                return (book_num, end_idx)
        return (None, start_idx)
    
    # Try to parse as single verse: "Book Chapter:Verse"
    # Find the book name starting from the beginning
    book_num, book_end_idx = find_book_name(0)
    
    if book_num is not None and book_end_idx < len(tokens):
        # Remaining tokens should be chapter:verse
        chapter_verse = tokens[book_end_idx]
        
        if ':' in chapter_verse:
            try:
                chapter, verse = map(int, chapter_verse.split(':'))
                # Check if there are more tokens (could be a range)
                if book_end_idx + 1 < len(tokens):
                    # Try to parse as range: "Book Chapter:Verse Book Chapter:Verse"
                    book2_num, book2_end_idx = find_book_name(book_end_idx + 1)
                    if book2_num is not None and book2_num == book_num and book2_end_idx < len(tokens):
                        chapter_verse2 = tokens[book2_end_idx]
                        if ':' in chapter_verse2:
                            try:
                                chapter2, verse2 = map(int, chapter_verse2.split(':'))
                                if chapter != chapter2:
                                    raise ValueError(f"Range must be within same chapter: {chapter} != {chapter2}")
                                
                                # Generate all verses in range (inclusive)
                                verses = []
                                for v in range(min(verse, verse2), max(verse, verse2) + 1):
                                    verses.append((book_num, chapter, v))
                                
                                # Return in RTL order (higher verse numbers first)
                                return sorted(verses, key=lambda x: x[2], reverse=True)
                            except ValueError:
                                pass
                # Single verse
                return [(book_num, chapter, verse)]
            except ValueError:
                pass
    
    # Try alternative format: "Book Chapter:Verse-Verse" (e.g., "Ps 119:1-6")
    if book_num is not None and book_end_idx < len(tokens):
        range_str = tokens[book_end_idx]
        if ':' in range_str and '-' in range_str:
            try:
                chapter_part, verse_range = range_str.split(':')
                chapter = int(chapter_part)
                
                if '-' in verse_range:
                    verse1, verse2 = map(int, verse_range.split('-'))
                    verses = []
                    for v in range(min(verse1, verse2), max(verse1, verse2) + 1):
                        verses.append((book_num, chapter, v))
                    return sorted(verses, key=lambda x: x[2], reverse=True)
            except ValueError:
                pass
    
    raise ValueError(f"Could not parse verse reference: {ref_str}")


def extract_hebrew_from_wlca(wlca_path: Path, book: int, chapter: int, verse: int) -> Optional[str]:
    """
    Extract Hebrew text for a specific verse from WLCa.json.
    Returns None if verse not found.
    """
    with open(wlca_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    for entry in data:
        if (entry.get('book') == book and 
            entry.get('chapter') == chapter and 
            entry.get('verse') == verse):
            text = entry.get('text', '')
            
            # Remove Strong's tags
            hebrew_text = re.sub(r'<S>\d+</S>', '', text)
            # Remove ketiv/qere markers
            hebrew_text = re.sub(r'\[k_[^\]]+\]', '', hebrew_text)
            hebrew_text = re.sub(r'\[q_[^\]]+\]', '', hebrew_text)
            # Remove HTML tags
            hebrew_text = hebrew_text.replace('<br/>', '')
            # Clean up whitespace
            hebrew_text = ' '.join(hebrew_text.split())
            
            return hebrew_text
    
    return None


def get_hebrew_for_verses(wlca_path: Path, verse_refs: List[Tuple[int, int, int]]) -> str:
    """
    Extract and concatenate Hebrew text for multiple verses.
    Verses are concatenated in the order provided (RTL order for ranges).
    """
    hebrew_parts = []
    missing_verses = []
    
    for book, chapter, verse in verse_refs:
        hebrew = extract_hebrew_from_wlca(wlca_path, book, chapter, verse)
        if hebrew:
            hebrew_parts.append(hebrew)
        else:
            missing_verses.append(f"{book}:{chapter}:{verse}")
    
    if missing_verses:
        raise ValueError(f"Verses not found in WLCa.json: {', '.join(missing_verses)}")
    
    # Concatenate with spaces (RTL order preserved)
    return ' '.join(hebrew_parts)

