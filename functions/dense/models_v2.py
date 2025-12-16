"""
Model configurations and embedding functions for version 2.0 (Weaviate-based).
Always uses mean pooling.
"""

import json
from typing import List, Dict, Optional
from pathlib import Path
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.embeddings import Embeddings

# Import custom embeddings for Hebrew models
from dense.custom_embeddings import HebrewModelEmbeddings


# Model configurations for v2.0
MODEL_CONFIGS = {
    'english_st': {
        'name': 'EnglishST',
        'model_name': 'sentence-transformers/all-mpnet-base-v2',
        'embedding_class': HuggingFaceEmbeddings,
        'embedding_kwargs': {
            'model_name': 'sentence-transformers/all-mpnet-base-v2',
            'model_kwargs': {'device': 'cpu'},
            'encode_kwargs': {'normalize_embeddings': True}
        },
        'text_field': 'text',  # Embed English text (from records, which use 'text' field)
    },
    'dictabert': {
        'name': 'DictaBERT',
        'model_name': 'dicta-il/dictabert',
        'embedding_class': HebrewModelEmbeddings,
        'embedding_kwargs': {
            'model_name': 'dicta-il/dictabert',
            'pooling_mode': 'mean'
        },
        'text_field': 'hebrew',  # Embed Hebrew text
    },
}


def get_embedding_function(model_key: str, data_dir: Optional[Path] = None) -> Embeddings:
    """
    Get an embedding function for the specified model (v2.0).
    Always uses mean pooling.
    
    Args:
        model_key: One of 'english_st', 'dictabert'
        data_dir: Optional data directory (not used, kept for compatibility)
        
    Returns:
        LangChain Embeddings instance
    """
    if model_key not in MODEL_CONFIGS:
        raise ValueError(
            f"Unknown model: {model_key}. "
            f"Available: {list(MODEL_CONFIGS.keys())}"
        )
    
    config = MODEL_CONFIGS[model_key]
    embedding_class = config['embedding_class']
    embedding_kwargs = config['embedding_kwargs'].copy()
    
    print(f"Initializing {config['name']} embedder with mean pooling...")
    return embedding_class(**embedding_kwargs)


def get_text_field(model_key: str) -> str:
    """Get which field to embed for a given model."""
    return MODEL_CONFIGS[model_key]['text_field']


def load_verse_data(data_dir: Path) -> Dict[tuple, Dict]:
    """
    Load verse_data.json and create a lookup dict: (chapter, verse) -> verse_data
    
    Args:
        data_dir: Path to data directory
        
    Returns:
        Dictionary mapping (chapter, verse) tuples to verse data dicts
    """
    verse_data_path = data_dir / 'raw' / 'verse_data.json'
    
    if not verse_data_path.exists():
        raise FileNotFoundError(f"verse_data.json not found at {verse_data_path}")
    
    with open(verse_data_path, 'r', encoding='utf-8') as f:
        verse_records = json.load(f)
    
    # Create lookup: (chapter, verse) -> verse_data
    lookup = {}
    for record in verse_records:
        chapter = record['chapter']
        verse = record['verse']
        lookup[(chapter, verse)] = record
    
    return lookup


def get_text_for_verses(verse_list: List[Dict], model_key: str, data_dir: Path) -> str:
    """
    Get the appropriate text (English or Hebrew) for a list of verses.
    
    Args:
        verse_list: List of verse dicts with 'chapter' and 'verse' keys
                   Example: [{"chapter": 1, "verse": 1}, {"chapter": 1, "verse": 2}]
        model_key: One of 'english_st', 'dictabert'
        data_dir: Path to data directory
        
    Returns:
        Concatenated text for the verses
    """
    verse_data = load_verse_data(data_dir)
    
    # Map model_key to verse_data field
    field_map = {
        'english_st': 'english',
        'dictabert': 'hebrew'
    }
    text_field = field_map.get(model_key, 'english')
    
    text_parts = []
    for verse_obj in verse_list:
        chapter = verse_obj['chapter']
        verse = verse_obj['verse']
        
        verse_record = verse_data.get((chapter, verse))
        if not verse_record:
            raise ValueError(f"Verse {chapter}:{verse} not found in verse_data.json")
        
        text = verse_record.get(text_field, '')
        if text:
            text_parts.append(text)
    
    return ' '.join(text_parts)

