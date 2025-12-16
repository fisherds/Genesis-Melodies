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

# Import v2.0 modules for Weaviate-based search
try:
    import weaviate
    from weaviate.classes.init import Auth
    from weaviate.classes.query import MetadataQuery
    from dense.models_v2 import get_embedding_function, get_text_for_verses as get_text_for_verses_v2
except ImportError as e:
    print(f"Warning: Could not import v2.0 modules: {e}", flush=True)
    weaviate = None
    Auth = None
    MetadataQuery = None
    get_embedding_function = None
    get_text_for_verses_v2 = None

# Global cache for embedding models (loaded once per function instance)
_embedding_cache = {}
_weaviate_client_cache = None


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


def router(request: Request) -> Tuple[dict[str, Any], int, dict[str, str]]:
    """
    Router function that handles both /api/search (v1.0) and /api/search2 (v2.0) endpoints.
    Routes to the appropriate handler based on the request path or parameters.
    """
    # Try to get the path from various sources
    path = ''
    if hasattr(request, 'path'):
        path = request.path
    elif hasattr(request, 'url'):
        # Extract path from URL
        from urllib.parse import urlparse
        parsed = urlparse(request.url)
        path = parsed.path
    
    # Also check for v2.0-specific parameter (chunking_level vs record_level)
    has_chunking_level = request.args.get('chunking_level') is not None
    has_record_level = request.args.get('record_level') is not None
    
    # Route to v2.0 handler if:
    # 1. Path contains /search2, OR
    # 2. Has chunking_level parameter (v2.0) but not record_level (v1.0)
    if '/search2' in path or (has_chunking_level and not has_record_level):
        return search2(request)
    else:
        # Default to v1.0 handler
        return search(request)


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


def get_weaviate_client():
    """
    Get a Weaviate client connection (cached globally).
    
    The client automatically uses gRPC when connecting to Weaviate Cloud.
    For WEAVIATE_URL, use the REST endpoint (without 'grpc-' prefix).
    The client will automatically infer and use the gRPC endpoint for better performance.
    """
    global _weaviate_client_cache
    
    if _weaviate_client_cache is not None:
        return _weaviate_client_cache
    
    import os
    WEAVIATE_URL = os.getenv('WEAVIATE_URL')
    WEAVIATE_API_KEY = os.getenv('WEAVIATE_API_KEY')
    
    if not WEAVIATE_URL or not WEAVIATE_API_KEY:
        raise ValueError("WEAVIATE_URL and WEAVIATE_API_KEY must be set in environment variables")
    
    # Remove 'grpc-' prefix if present, as connect_to_weaviate_cloud expects REST endpoint
    # and automatically uses gRPC
    cluster_url = WEAVIATE_URL
    if cluster_url.startswith('grpc-'):
        cluster_url = cluster_url.replace('grpc-', '', 1)
    elif not cluster_url.startswith('http'):
        # If no protocol specified, assume https
        cluster_url = f"https://{cluster_url}"
    
    print("Connecting to Weaviate (caching connection)...", flush=True)
    _weaviate_client_cache = weaviate.connect_to_weaviate_cloud(
        cluster_url=cluster_url,
        auth_credentials=Auth.api_key(WEAVIATE_API_KEY),
    )
    return _weaviate_client_cache


def search_weaviate(
    verse_list: list,
    model_key: str,
    chunking_level: str,
    top_k: int = 10
) -> list:
    """
    Search Weaviate for similar verses.
    
    Args:
        verse_list: List of verse dicts with 'chapter' and 'verse' keys
        model_key: One of 'english_st', 'dictabert'
        chunking_level: One of 'quilt_piece', 'pericope', 'note', 'verse'
        top_k: Number of results to return
        
    Returns:
        List of search results with 'id', 'title', 'text', 'hebrew', 'score', etc.
    """
    if not get_text_for_verses_v2 or not get_embedding_function:
        raise ValueError("v2.0 modules not available")
    
    # Get text for the verses
    search_text = get_text_for_verses_v2(verse_list, model_key, DATA_DIR)
    
    # Get embedding function (cached globally)
    cache_key = model_key
    if cache_key not in _embedding_cache:
        print(f"Loading embedding model '{model_key}' (this happens once per function instance)...", flush=True)
        _embedding_cache[cache_key] = get_embedding_function(
            model_key,
            data_dir=DATA_DIR
        )
        print(f"✓ Embedding model '{model_key}' loaded and cached", flush=True)
    else:
        print(f"Using cached embedding model '{model_key}'", flush=True)
    
    embeddings = _embedding_cache[cache_key]
    
    # Generate query embedding
    query_vector = embeddings.embed_query(search_text)
    
    # Collection name matches ChromaDB naming convention
    collection_name = f"{model_key}_{chunking_level}"
    
    # Connect to Weaviate and perform search (client is cached globally)
    client = get_weaviate_client()
    
    # Check if collection exists
    if not client.collections.exists(collection_name):
        raise ValueError(
            f"Collection '{collection_name}' does not exist in Weaviate. "
            f"Please run the upsert script first to create the collection."
        )
    
    collection = client.collections.get(collection_name)
    
    # Perform vector similarity search
    response = collection.query.near_vector(
        near_vector=query_vector,
        limit=top_k,
        return_metadata=MetadataQuery(distance=True),
        return_properties=["title", "text", "hebrew", "strongs", "verses", "verse_display"]
    )
    
    # Format results to match ChromaDB format
    results = []
    for obj in response.objects:
        properties = obj.properties
        metadata = obj.metadata
        
        # Use distance directly to match ChromaDB behavior
        # Distance is 0-2 for cosine, where 0 is most similar (identical)
        # ChromaDB returns distance where 0.0 = identical, so we match that
        distance = metadata.distance if metadata.distance is not None else 1.0
        
        # Parse verses from string array back to list of dicts
        verses = []
        verses_array = properties.get('verses', [])
        for verse_str in verses_array:
            if isinstance(verse_str, str) and ':' in verse_str:
                parts = verse_str.split(':')
                if len(parts) == 2:
                    try:
                        verses.append({
                            'chapter': int(parts[0]),
                            'verse': float(parts[1]) if '.' in parts[1] else int(parts[1])
                        })
                    except ValueError:
                        pass
        
        result = {
            'id': str(obj.uuid),  # Weaviate uses UUIDs
            'title': properties.get('title', 'Unknown'),
            'text': properties.get('text', ''),
            'hebrew': properties.get('hebrew', ''),
            'strongs': properties.get('strongs', ''),
            'verses': verses,
            'verse_display': properties.get('verse_display', ''),
            'score': distance  # Return distance to match ChromaDB (0.0 = identical)
        }
        results.append(result)
    
    return results


def search2(request: Request) -> Tuple[dict[str, Any], int, dict[str, str]]:
    """
    Cloud Function entry point for v2.0 search requests (Weaviate-based).
    
    Query parameters:
    - model_name: english_st, dictabert
    - chunking_level: quilt_piece, pericope, note, or verse
    - search_verses: JSON array of [{"chapter": int, "verse": int}, ...]
    - top_k: number of results to return (default: 10)
    """
    # CORS headers
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
        "Content-Type": "application/json"
    }
    
    # Handle OPTIONS request
    if request.method == "OPTIONS":
        return ("", 204, headers)
    
    try:
        # Get query parameters
        model_name = request.args.get("model_name", "english_st")
        chunking_level = request.args.get("chunking_level", "pericope")
        top_k = int(request.args.get("top_k", 10))
        
        # Validate model_name
        valid_models = ['english_st', 'dictabert']
        if model_name not in valid_models:
            return (
                {"error": f"Invalid model_name: {model_name}. Must be one of: {valid_models}"},
                400,
                headers
            )
        
        # Validate chunking_level
        valid_chunking_levels = ['quilt_piece', 'pericope', 'note', 'verse']
        if chunking_level not in valid_chunking_levels:
            return (
                {"error": f"Invalid chunking_level: {chunking_level}. Must be one of: {valid_chunking_levels}"},
                400,
                headers
            )
        
        # Get search_verses from query parameter (JSON string)
        search_verses_str = request.args.get("search_verses", "[]")
        
        # Parse search_verses JSON array
        verse_list = json.loads(search_verses_str)
        
        if not verse_list:
            return (
                {"error": "search_verses cannot be empty"},
                400,
                headers
            )
        
        # Validate search_verses format
        if not isinstance(verse_list, list):
            return (
                {"error": "search_verses must be a JSON array"},
                400,
                headers
            )
        
        # Validate each verse object
        for verse_obj in verse_list:
            if not isinstance(verse_obj, dict) or 'chapter' not in verse_obj or 'verse' not in verse_obj:
                return (
                    {"error": "Each verse must be an object with 'chapter' and 'verse' fields"},
                    400,
                    headers
                )
        
        # Perform search using Weaviate
        results = search_weaviate(
            verse_list=verse_list,
            model_key=model_name,
            chunking_level=chunking_level,
            top_k=top_k
        )
        
        # Get English text for display (regardless of model)
        english_search_text = get_text_for_verses_v2(verse_list, 'english_st', DATA_DIR)
        
        # Add english_search_text to response
        response_data = {
            "english_search_text": english_search_text,
            "results": results
        }
        
        return (
            response_data,
            200,
            headers
        )
        
    except json.JSONDecodeError as e:
        return (
            {"error": f"Invalid JSON in search_verses: {str(e)}"},
            400,
            headers
        )
    except ValueError as e:
        return (
            {"error": str(e)},
            400,
            headers
        )
    except Exception as e:
        # Log error
        import traceback
        error_traceback = traceback.format_exc()
        print(f"Error in search2 function: {str(e)}", flush=True)
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
    
    @app.route('/api/search', methods=['GET', 'OPTIONS'])
    def handler_search():
        result = search(flask_request)
        if isinstance(result, tuple) and len(result) == 3:
            response_data, status_code, headers = result
            from flask import jsonify, make_response
            resp = make_response(jsonify(response_data), status_code)
            for key, value in headers.items():
                resp.headers[key] = value
            return resp
        return result
    
    @app.route('/api/search2', methods=['GET', 'OPTIONS'])
    def handler_search2():
        result = search2(flask_request)
        if isinstance(result, tuple) and len(result) == 3:
            response_data, status_code, headers = result
            from flask import jsonify, make_response
            resp = make_response(jsonify(response_data), status_code)
            for key, value in headers.items():
                resp.headers[key] = value
            return resp
        return result
    
    app.run(port=8080, debug=True)
