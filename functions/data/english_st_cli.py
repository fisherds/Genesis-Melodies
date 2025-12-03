#!/usr/bin/env python3
"""
Command-line interface for English Sentence Transformer embedding search.
"""

import argparse
import json
import re
import sys
from pathlib import Path

# Add functions directory to path
# english_st_cli.py is in functions/data/, so functions/ is the parent
FUNCTIONS_DIR = Path(__file__).parent.parent
if str(FUNCTIONS_DIR) not in sys.path:
    sys.path.insert(0, str(FUNCTIONS_DIR))

from dense.vector_store import create_vector_store, load_vector_store
from dense.search import dense_search
from shared.verse_parser import parse_verse_reference
from dense.models import get_persist_directory, get_outputs_directory
from data.decoder_ring_record_generator import concatenate_verses
from shared.utils import ensure_correct_working_directory_for_local_data_generation

# Model configuration
MODEL_KEY = 'english_st'

# Constants
DATA_DIR = Path(__file__).parent  # functions/data/
OUTPUTS_DIR = get_outputs_directory(DATA_DIR / 'outputs', MODEL_KEY)


def generate_filename_from_reference(reference: str) -> str:
    """
    Generate a filename from a verse reference.
    Examples:
    - "GENESIS 1:1" -> "genesis_1_1.json"
    - "Ps 119:1 Ps 119:6" -> "ps_119_1_ps_119_6.json"
    """
    # Convert to lowercase
    filename = reference.lower()
    # Replace spaces and colons with underscores
    filename = re.sub(r'[\s:]+', '_', filename)
    # Remove any trailing underscores
    filename = filename.strip('_')
    # Add .json extension
    if not filename.endswith('.json'):
        filename += '.json'
    return filename


def add_common_search_args(parser):
    """Add common arguments for search and verse commands."""
    parser.add_argument(
        '-k',
        '--top-k',
        type=int,
        default=10,
        help='Number of results to return (default: 10)'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output results as JSON'
    )
    parser.add_argument(
        '-o',
        '--output',
        type=Path,
        help='Output filename (default: auto-generated)'
    )


def load_vector_store_safe(record_level: str = 'pericope'):
    """Load vector store, checking if it exists first."""
    base_dir = Path(__file__).parent
    persist_dir = get_persist_directory(base_dir, MODEL_KEY, record_level)
    
    if not persist_dir.exists():
        print(f"Error: Vector store not found at {persist_dir}")
        print(f"Run 'python english_st_cli.py index' first to create the index")
        return None
    
    print(f"Loading vector store from {persist_dir}...")
    return load_vector_store(persist_dir, model_key=MODEL_KEY)


def save_json_results(results, reference: str, output_file: Path = None):
    """Save results as JSON to file."""
    json_output = json.dumps(results, indent=2, ensure_ascii=False)
    
    OUTPUTS_DIR.mkdir(exist_ok=True, parents=True)
    
    if output_file:
        output_path = OUTPUTS_DIR / output_file
    else:
        filename = generate_filename_from_reference(reference)
        output_path = OUTPUTS_DIR / filename
    
    output_path.write_text(json_output, encoding='utf-8')
    print(f"Results saved to {output_path}")


def print_results(results):
    """Pretty print search results."""
    for i, result in enumerate(results, 1):
        print(f"Result {i}:")
        print(f"  ID: {result['id']}")
        print(f"  Title: {result['title']}")
        print(f"  Score: {result['score']:.4f}")
        print(f"  English: {result['text'][:100]}...")
        print(f"  Hebrew: {result['hebrew'][:100]}...")
        print()


def load_bibleproject_translation_full(file_path: Path):
    """
    Load BP translation from .txt file and create a lookup dict: (chapter, verse) -> text
    Includes all verses in the file (Genesis 1:1 to 25:18).
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


def get_english_for_verses(bp_translation_path: Path, verse_refs):
    """
    Extract and concatenate English text for multiple verses from BibleProject translation.
    
    Args:
        bp_translation_path: Path to bp_translation_gen_1_25.txt
        verse_refs: List of (book_num, chapter, verse) tuples from parse_verse_reference
    """
    bp_lookup = load_bibleproject_translation_full(bp_translation_path)
    # Extract just (chapter, verse) from (book_num, chapter, verse) tuples
    verses = [(ch, v) for _, ch, v in verse_refs]
    return concatenate_verses(verses, bp_lookup)


def main():
    ensure_correct_working_directory_for_local_data_generation()
    
    parser = argparse.ArgumentParser(
        description='Search English text using English Sentence Transformer embeddings'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Index command
    index_parser = subparsers.add_parser('index', help='Create vector store index')
    index_parser.add_argument(
        '--force',
        action='store_true',
        help='Force re-indexing even if index exists'
    )
    index_parser.add_argument(
        '--record-level',
        choices=['pericope', 'verse'],
        default='pericope',
        help='Record level to index (default: pericope)'
    )
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search for English text')
    search_parser.add_argument(
        'query',
        type=str,
        help='English text to search for'
    )
    add_common_search_args(search_parser)
    
    # Verse command
    verse_parser = subparsers.add_parser('verse', help='Search using a Bible verse reference')
    verse_parser.add_argument(
        'reference',
        type=str,
        help='Verse reference (e.g., "Genesis 1:1" or "Genesis 1:1 Genesis 1:2")'
    )
    add_common_search_args(verse_parser)
    
    args = parser.parse_args()
    
    if args.command == 'index':
        base_dir = Path(__file__).parent
        persist_dir = get_persist_directory(base_dir, MODEL_KEY, args.record_level)
        
        if persist_dir.exists() and not args.force:
            print(f"Vector store already exists at {persist_dir}")
            print("Use --force to re-index")
            return
        
        print(f"Creating English Sentence Transformer vector store index ({args.record_level})...")
        create_vector_store(DATA_DIR, model_key=MODEL_KEY, record_level=args.record_level, force=args.force)
        print("✓ Indexing complete!")
        
    elif args.command == 'search':
        # Default to pericope for search
        vector_store = load_vector_store_safe('pericope')
        if vector_store is None:
            return
        
        print(f"Searching for: {args.query}")
        print()
        
        results = dense_search(args.query, vector_store, k=args.top_k)
        
        if args.json:
            save_json_results(results, args.query, args.output)
        else:
            print_results(results)
    
    elif args.command == 'verse':
        bp_translation_path = DATA_DIR / 'raw' / 'bp_translation_gen_1_25.txt'
        
        if not bp_translation_path.exists():
            print(f"Error: bp_translation_gen_1_25.txt not found at {bp_translation_path}")
            return
        
        try:
            print(f"Parsing verse reference: {args.reference}")
            verse_refs = parse_verse_reference(args.reference)
            print(f"Found {len(verse_refs)} verse(s)")
            
            print(f"Extracting English from {bp_translation_path}...")
            english_text = get_english_for_verses(bp_translation_path, verse_refs)
            print(f"Extracted English: {english_text[:100]}...")
            print()
            
            # Use verse level for verse searches
            vector_store = load_vector_store_safe('verse')
            if vector_store is None:
                return
            
            print(f"Searching for English text...")
            print()
            
            results = dense_search(english_text, vector_store, k=args.top_k)
            
            if args.json:
                save_json_results(results, args.reference, args.output)
            else:
                print_results(results)
        
        except ValueError as e:
            print(f"Error: {e}")
            return
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()

