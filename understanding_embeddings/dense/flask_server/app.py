import flask
from pathlib import Path
import sys

# Add project root to path for imports
# flask_server/app.py -> dense/ -> understanding_embeddings/ -> project root
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from understanding_embeddings.dense.vector_store import load_vector_store
from understanding_embeddings.dense.search import dense_search
from understanding_embeddings.dense.models import get_persist_directory
from understanding_embeddings.shared.utils import ensure_correct_working_directory
from understanding_embeddings.shared.verse_parser import get_hebrew_for_verses
from understanding_embeddings.data.decoder_ring_record_generator import concatenate_verses
import json
import re

# Ensure we're running from the project root
ensure_correct_working_directory()

app = flask.Flask(__name__, static_folder="public", static_url_path="")

# Get directories
# app.py is in: flask_server/ -> dense/ -> understanding_embeddings/ -> project root
# BASE_DIR should be: dense folder
BASE_DIR = Path(__file__).parent.parent  # dense folder
DATA_DIR = BASE_DIR.parent / "data"

@app.get("/")
def handle_naked_domain():
    return flask.redirect("/index.html")

def load_bibleproject_translation_full(file_path: Path):
    """
    Load BP translation from .txt file and create a lookup dict: (chapter, verse) -> text
    Includes all verses in the file (Genesis 1:1 to 25:18).
    """
    import re
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


@app.get("/api/search")
def handle_search():
    """
    Perform dense semantic search.
    
    Query parameters:
    - model_name: hebrew_st, berit, or english_st
    - record_level: pericope, verse, agentic_berit, agentic_hebrew_st, or agentic_english_st
    - search_verses: JSON array of [{"chapter": int, "verse": int}, ...]
    - top_k: number of results to return (default: 10)
    """
    # Get query parameters
    model_name = flask.request.args.get("model_name", "hebrew_st")
    record_level = flask.request.args.get("record_level", "pericope")
    top_k = int(flask.request.args.get("top_k", 10))
    
    # Validate model_name and record_level combination
    valid_combinations = {
        'pericope': ['hebrew_st', 'english_st'],
        'verse': ['hebrew_st', 'berit', 'english_st'],
        'agentic_berit': ['berit', 'hebrew_st', 'english_st'],
        'agentic_hebrew_st': ['hebrew_st', 'english_st'],
        'agentic_english_st': ['hebrew_st', 'english_st'],
    }
    
    if record_level not in valid_combinations:
        return flask.jsonify({
            "error": f"Invalid record_level: {record_level}. "
            f"Must be one of: {list(valid_combinations.keys())}"
        }), 400
    
    if model_name not in valid_combinations[record_level]:
        return flask.jsonify({
            "error": f"Invalid combination: model_name '{model_name}' cannot be used with record_level '{record_level}'. "
            f"Valid models for {record_level}: {valid_combinations[record_level]}"
        }), 400
    
    # Get search_verses from query parameter (JSON string)
    search_verses_str = flask.request.args.get("search_verses", "[]")
    
    try:
        # Parse search_verses JSON array
        search_verses = json.loads(search_verses_str)
        
        if not search_verses:
            return flask.jsonify({"error": "search_verses cannot be empty"}), 400
        
        # Validate search_verses format
        if not isinstance(search_verses, list):
            return flask.jsonify({"error": "search_verses must be a JSON array"}), 400
        
        # Convert search_verses from [{"chapter": int, "verse": int}, ...] to (book_num, chapter, verse) tuples
        # Since we're only dealing with Genesis 1-25, book_num is always 1 (Genesis)
        GENESIS_BOOK_NUM = 1
        verse_refs = []
        for verse_obj in search_verses:
            if not isinstance(verse_obj, dict) or 'chapter' not in verse_obj or 'verse' not in verse_obj:
                return flask.jsonify({"error": "Each verse must be an object with 'chapter' and 'verse' fields"}), 400
            chapter = int(verse_obj['chapter'])
            verse = int(verse_obj['verse'])
            verse_refs.append((GENESIS_BOOK_NUM, chapter, verse))
        
        # Extract search text based on model_name
        if model_name in ['hebrew_st', 'berit']:
            # Get Hebrew text from WLCa.json
            wlca_path = DATA_DIR / 'raw' / 'WLCa.json'
            if not wlca_path.exists():
                return flask.jsonify({"error": f"WLCa.json not found at {wlca_path}"}), 500
            search_text = get_hebrew_for_verses(wlca_path, verse_refs)
        
        elif model_name == 'english_st':
            # Get English text from bp_translation_gen_1_25.txt
            bp_translation_path = DATA_DIR / 'raw' / 'bp_translation_gen_1_25.txt'
            if not bp_translation_path.exists():
                return flask.jsonify({"error": f"bp_translation_gen_1_25.txt not found at {bp_translation_path}"}), 500
            search_text = get_english_for_verses(bp_translation_path, verse_refs)
        
        else:
            return flask.jsonify({"error": f"Invalid model_name: {model_name}. Must be 'hebrew_st', 'berit', or 'english_st'"}), 400
        
        if not search_text:
            return flask.jsonify({"error": "No text found for the specified verses"}), 400
        
        # Load the appropriate vector store based on model_name and record_level
        persist_dir = get_persist_directory(BASE_DIR, model_name, record_level)
        if not persist_dir.exists():
            return flask.jsonify({"error": f"Vector store not found at {persist_dir}. Run indexing first."}), 500
        
        vector_store = load_vector_store(persist_dir, model_name)
        
        # Get English text for display (regardless of model)
        bp_translation_path = DATA_DIR / 'raw' / 'bp_translation_gen_1_25.txt'
        english_search_text = None
        if bp_translation_path.exists():
            english_search_text = get_english_for_verses(bp_translation_path, verse_refs)
        
        # Perform search
        results = dense_search(search_text, vector_store, k=top_k)
        
        # Add english_search_text to response
        response_data = {
            "english_search_text": english_search_text,
            "results": results
        }
        
        return flask.jsonify(response_data)
        
    except json.JSONDecodeError as e:
        return flask.jsonify({"error": f"Invalid JSON in search_verses: {str(e)}"}), 400
    except ValueError as e:
        return flask.jsonify({"error": str(e)}), 400
    except Exception as e:
        return flask.jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)

