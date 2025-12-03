"""
Cloud Function for Genesis Melodies Search API

This function handles search requests for dense vector embeddings and ChromaDB retrievals.
Refactored from Flask app.py to work with Firebase Cloud Functions Python Runtime.
"""

import json
import re
import sys
from pathlib import Path
from flask import Request
from typing import Any, Tuple

# Add functions directory to path for imports
# In Cloud Functions, the working directory is the functions folder
functions_dir = Path(__file__).parent
if str(functions_dir) not in sys.path:
    sys.path.insert(0, str(functions_dir))

# Import modules from the flattened structure
# All modules are now directly in functions/dense, functions/shared, functions/data
try:
    from dense.vector_store import load_vector_store
    from dense.search import dense_search
    from dense.models import get_persist_directory
    from shared.verse_parser import get_hebrew_for_verses
    from data.decoder_ring_record_generator import concatenate_verses
except ImportError as e:
    print(f"Warning: Could not import modules: {e}", flush=True)
    print("Make sure all required modules are in functions/dense, functions/shared, and functions/data", flush=True)
    # These will be set to None and we'll handle errors gracefully
    load_vector_store = None
    dense_search = None
    get_persist_directory = None
    get_hebrew_for_verses = None
    concatenate_verses = None


# Determine base directories
# In Cloud Functions, the functions directory is the working directory
# All folders are now inside functions/
FUNCTIONS_DIR = Path(__file__).parent

# Data and dense folders are inside functions/
BASE_DIR = FUNCTIONS_DIR / "dense"  # Contains chroma_db subdirectory
DATA_DIR = FUNCTIONS_DIR / "data"  # Contains raw and records subdirectories


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
        verse_refs: List of (book_num, chapter, verse) tuples
    """
    bp_lookup = load_bibleproject_translation_full(bp_translation_path)
    # Extract just (chapter, verse) from (book_num, chapter, verse) tuples
    verses = [(ch, v) for _, ch, v in verse_refs]
    return concatenate_verses(verses, bp_lookup)


def search(request: Request) -> Tuple[dict[str, Any], int, dict[str, str]]:
    """
    Cloud Function entry point for search requests.
    
    Expected query parameters:
    - model_name: str (e.g., 'hebrew_st', 'berit', 'english_st')
    - record_level: str (e.g., 'pericope', 'verse', 'agentic_berit', etc.)
    - top_k: int (number of results to return, default: 10)
    - search_verses: str (JSON string of verse array, e.g., '[{"chapter": 12, "verse": 1}]')
    
    Returns:
    - Tuple of (response_data, status_code, headers)
    """
    
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600'
        }
        return ('', 204, headers)
    
    # Set CORS headers for actual response
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Content-Type': 'application/json'
    }
    
    try:
        # Get query parameters
        model_name = request.args.get("model_name", "hebrew_st")
        record_level = request.args.get("record_level", "pericope")
        top_k_str = request.args.get("top_k", "10")
        search_verses_str = request.args.get("search_verses", "[]")
        
        # Validate model_name and record_level combination
        valid_combinations = {
            'pericope': ['hebrew_st', 'english_st'],
            'verse': ['hebrew_st', 'berit', 'english_st'],
            'agentic_berit': ['berit', 'hebrew_st', 'english_st'],
            'agentic_hebrew_st': ['hebrew_st', 'english_st'],
            'agentic_english_st': ['hebrew_st', 'english_st'],
        }
        
        if record_level not in valid_combinations:
            return (
                {
                    "error": f"Invalid record_level: {record_level}. "
                    f"Must be one of: {list(valid_combinations.keys())}"
                },
                400,
                headers
            )
        
        if model_name not in valid_combinations[record_level]:
            return (
                {
                    "error": f"Invalid combination: model_name '{model_name}' cannot be used with record_level '{record_level}'. "
                    f"Valid models for {record_level}: {valid_combinations[record_level]}"
                },
                400,
                headers
            )
        
        # Parse search_verses JSON array
        try:
            search_verses = json.loads(search_verses_str)
        except json.JSONDecodeError as e:
            return (
                {"error": f"Invalid JSON in search_verses: {str(e)}"},
                400,
                headers
            )
        
        if not search_verses:
            return (
                {"error": "search_verses cannot be empty"},
                400,
                headers
            )
        
        # Validate search_verses format
        if not isinstance(search_verses, list):
            return (
                {"error": "search_verses must be a JSON array"},
                400,
                headers
            )
        
        # Convert search_verses from [{"chapter": int, "verse": int}, ...] to (book_num, chapter, verse) tuples
        # Since we're only dealing with Genesis 1-25, book_num is always 1 (Genesis)
        GENESIS_BOOK_NUM = 1
        verse_refs = []
        for verse_obj in search_verses:
            if not isinstance(verse_obj, dict) or 'chapter' not in verse_obj or 'verse' not in verse_obj:
                return (
                    {"error": "Each verse must be an object with 'chapter' and 'verse' fields"},
                    400,
                    headers
                )
            try:
                chapter = int(verse_obj['chapter'])
                verse = int(verse_obj['verse'])
                verse_refs.append((GENESIS_BOOK_NUM, chapter, verse))
            except (ValueError, TypeError) as e:
                return (
                    {"error": f"Invalid chapter or verse value: {str(e)}"},
                    400,
                    headers
                )
        
        # Validate top_k
        try:
            top_k = int(top_k_str)
            if top_k < 1 or top_k > 50:
                return (
                    {"error": "top_k must be between 1 and 50"},
                    400,
                    headers
                )
        except ValueError:
            return (
                {"error": "top_k must be a valid integer"},
                400,
                headers
            )
        
        # Check if modules are available
        if not all([load_vector_store, dense_search, get_persist_directory]):
            return (
                {"error": "Search modules not available. Check that all required modules are in functions/dense, functions/shared, and functions/data directories."},
                500,
                headers
            )
        
        
        # Extract search text based on model_name
        if model_name in ['hebrew_st', 'berit']:
            # Get Hebrew text from WLCa.json
            wlca_path = DATA_DIR / 'raw' / 'WLCa.json'
            if not wlca_path.exists():
                return (
                    {"error": f"WLCa.json not found at {wlca_path}"},
                    500,
                    headers
                )
            search_text = get_hebrew_for_verses(wlca_path, verse_refs)
        
        elif model_name == 'english_st':
            # Get English text from bp_translation_gen_1_25.txt
            bp_translation_path = DATA_DIR / 'raw' / 'bp_translation_gen_1_25.txt'
            if not bp_translation_path.exists():
                return (
                    {"error": f"bp_translation_gen_1_25.txt not found at {bp_translation_path}"},
                    500,
                    headers
                )
            search_text = get_english_for_verses(bp_translation_path, verse_refs)
        
        else:
            return (
                {"error": f"Invalid model_name: {model_name}. Must be 'hebrew_st', 'berit', or 'english_st'"},
                400,
                headers
            )
        
        if not search_text:
            return (
                {"error": "No text found for the specified verses"},
                400,
                headers
            )
        
        # Load the appropriate vector store based on model_name and record_level
        persist_dir = get_persist_directory(BASE_DIR, model_name, record_level)
        if not persist_dir.exists():
            return (
                {"error": f"Vector store not found at {persist_dir}. Run indexing first."},
                500,
                headers
            )
        
        vector_store = load_vector_store(persist_dir, model_name)
        
        # Get English text for display (regardless of model)
        bp_translation_path = DATA_DIR / 'raw' / 'bp_translation_gen_1_25.txt'
        english_search_text = None
        if bp_translation_path.exists():
            english_search_text = get_english_for_verses(bp_translation_path, verse_refs)
        
        # Perform search
        results = dense_search(search_text, vector_store, k=top_k)
        
        # Format response
        response_data = {
            "english_search_text": english_search_text,
            "results": results
        }
        
        return (response_data, 200, headers)
        
    except ValueError as e:
        return (
            {"error": str(e)},
            400,
            headers
        )
    except Exception as e:
        # Log error (will appear in Cloud Functions logs and functions-framework output)
        import traceback
        error_traceback = traceback.format_exc()
        print(f"Error in search function: {str(e)}", flush=True)
        print(error_traceback, flush=True)
        # Return JSON error response
        error_response = {
            "error": f"Internal server error: {str(e)}",
            "details": error_traceback.split('\n')[-2] if error_traceback else None
        }
        return (
            error_response,
            500,
            headers
        )


# For local testing with Functions Framework
if __name__ == '__main__':
    from flask import Flask, request as flask_request
    app = Flask(__name__)
    
    @app.route('/', methods=['GET', 'OPTIONS'])
    def handler():
        result = search(flask_request)
        if isinstance(result, tuple) and len(result) == 3:
            response_data, status_code, headers = result
            from flask import jsonify, make_response
            resp = make_response(jsonify(response_data), status_code)
            for key, value in headers.items():
                resp.headers[key] = value
            return resp
        return result
    
    app.run(port=8080, debug=True)
