"""
Model configurations and embedding functions for version 2.0 (Weaviate-based).
Includes weighted pooling support.
"""

import json
from typing import List, Dict, Optional
from pathlib import Path
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.embeddings import Embeddings

# Import custom embeddings for weighted pooling
from dense.custom_embeddings import HebrewModelEmbeddings
from dense.weighted_pooling import load_token_weights


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
    'tavbert': {
        'name': 'TavBERT',
        'model_name': 'tau/tavbert-he',
        'embedding_class': HebrewModelEmbeddings,
        'embedding_kwargs': {
            'model_name': 'tau/tavbert-he',
            'pooling_mode': 'mean'
        },
        'text_field': 'hebrew',  # Embed Hebrew text
    },
}


def get_embedding_function(model_key: str, use_weighted_pooling: bool = True, data_dir: Optional[Path] = None) -> Embeddings:
    """
    Get an embedding function for the specified model (v2.0 with weighted pooling support).
    
    Args:
        model_key: One of 'english_st', 'dictabert', 'tavbert'
        use_weighted_pooling: Whether to use weighted pooling (default: True)
        data_dir: Optional data directory for loading token weights
        
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
    
    # For all models, try to load token weights for weighted pooling
    if use_weighted_pooling:
        # Try to load token weights from frequency analysis
        # Token frequency files are in the dense folder (same as this file)
        base_dir = Path(__file__).parent
        if data_dir is None:
            data_dir = base_dir.parent / 'data'
        
        # Token frequency files are in the dense folder, not data folder
        token_weights = load_token_weights(embedding_kwargs['model_name'], base_dir, tokenizer=None)
        
        if token_weights:
            # For EnglishST, we need to use HebrewModelEmbeddings to support weighted pooling
            if model_key == 'english_st':
                embedding_class = HebrewModelEmbeddings
                embedding_kwargs = {
                    'model_name': embedding_kwargs['model_name'],
                    'pooling_mode': 'weighted',
                    'token_weights': token_weights
                }
            else:
                # token_weights is actually token_string_weights at this point
                embedding_kwargs['pooling_mode'] = 'weighted'
                embedding_kwargs['token_weights'] = token_weights
            print(f"  Using weighted pooling with {len(token_weights)} token weights")
        else:
            if model_key == 'english_st':
                # EnglishST can use standard HuggingFaceEmbeddings with mean pooling
                print(f"  Token weights not found, using mean pooling")
            else:
                print(f"  Token weights not found, using mean pooling")
                print(f"  Run compute_token_frequencies.py to enable weighted pooling")
    
    print(f"Initializing {config['name']} embedder...")
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
        model_key: One of 'english_st', 'dictabert', 'tavbert'
        data_dir: Path to data directory
        
    Returns:
        Concatenated text for the verses
    """
    verse_data = load_verse_data(data_dir)
    
    # Map model_key to verse_data field
    field_map = {
        'english_st': 'english',
        'dictabert': 'hebrew',
        'tavbert': 'hebrew'
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

