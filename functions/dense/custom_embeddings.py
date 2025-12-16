"""
Custom embedding classes for Hebrew models with proper sentence-transformers integration.
"""

import json
import torch
import numpy as np
import warnings
import logging
from typing import List, Dict, Optional
from pathlib import Path

# Suppress harmless warnings about uninitialized pooler weights BEFORE importing transformers
# These occur because we use mean pooling instead of the pooler layer
warnings.filterwarnings("ignore", message=".*pooler.dense.*")
warnings.filterwarnings("ignore", message=".*Some weights.*were not initialized.*")
warnings.filterwarnings("ignore", message=".*You should probably TRAIN.*")

# Also suppress transformers logging warnings
logging.getLogger("transformers.modeling_utils").setLevel(logging.ERROR)

from sentence_transformers import SentenceTransformer
from sentence_transformers.models import Pooling, Transformer
from langchain_core.embeddings import Embeddings


class HebrewModelEmbeddings(Embeddings):
    """
    Custom embedding class for Hebrew BERT models (DictaBERT).
    Properly wraps the model with sentence-transformers mean pooling.
    """
    
    def __init__(self, model_name: str, pooling_mode: str = 'mean', token_weights: Optional[Dict[str, float]] = None):
        """
        Initialize Hebrew model embeddings.
        
        Args:
            model_name: HuggingFace model name (e.g., 'dicta-il/dictabert')
            pooling_mode: Pooling mode (always 'mean')
            token_weights: Not used (kept for compatibility)
        """
        self.model_name = model_name
        
        print(f"Loading {model_name} with proper sentence-transformers wrapper...")
        
        # Load the base transformer model
        word_embedding_model = Transformer(model_name, max_seq_length=512)
        embedding_dim = word_embedding_model.get_word_embedding_dimension()
        
        # Store tokenizer for later use
        self.tokenizer = word_embedding_model.tokenizer
        
        # Always use mean pooling (standard for sentence-transformers)
        # This properly initializes the pooling layer
        pooling_model = Pooling(
            embedding_dim,
            pooling_mode_mean_tokens=True,
            pooling_mode_cls_token=False,
            pooling_mode_max_tokens=False
        )
        print(f"  Using mean pooling")
        
        # Create SentenceTransformer with proper modules
        self.model = SentenceTransformer(modules=[word_embedding_model, pooling_model])
        self.model.eval()
        
        print(f"✓ {model_name} loaded successfully with sentence-transformers wrapper!")
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of documents."""
        with torch.no_grad():
            embeddings = self.model.encode(
                texts, 
                convert_to_numpy=True, 
                normalize_embeddings=True,
                show_progress_bar=False
            )
        return embeddings.tolist()
    
    def embed_query(self, text: str) -> List[float]:
        """Generate embedding for a single query."""
        return self.embed_documents([text])[0]

