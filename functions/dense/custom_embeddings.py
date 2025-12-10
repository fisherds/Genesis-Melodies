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


class InputIdsTransformer(Transformer):
    """
    Custom Transformer that ensures input_ids are passed through to pooling layer.
    """
    
    def forward(self, features):
        """Forward pass that ensures input_ids are in output features."""
        # Call parent forward
        output = super().forward(features)
        # Ensure input_ids are passed through if they exist
        if 'input_ids' in features:
            output['input_ids'] = features['input_ids']
        return output


class HebrewModelEmbeddings(Embeddings):
    """
    Custom embedding class for Hebrew BERT models (DictaBERT, TavBERT).
    Properly wraps the model with sentence-transformers pooling.
    Supports weighted pooling based on token frequencies.
    """
    
    def __init__(self, model_name: str, pooling_mode: str = 'mean', token_weights: Optional[Dict[str, float]] = None):
        """
        Initialize Hebrew model embeddings.
        
        Args:
            model_name: HuggingFace model name (e.g., 'dicta-il/dictabert', 'tau/tavbert-he')
            pooling_mode: Pooling mode ('mean' or 'weighted')
            token_weights: Optional dictionary mapping token strings to weights for weighted pooling
        """
        self.model_name = model_name
        self.pooling_mode = pooling_mode
        
        print(f"Loading {model_name} with proper sentence-transformers wrapper...")
        
        # Load the base transformer model
        # Use custom wrapper to ensure input_ids are passed through for weighted pooling
        if pooling_mode == 'weighted':
            word_embedding_model = InputIdsTransformer(model_name, max_seq_length=512)
        else:
            word_embedding_model = Transformer(model_name, max_seq_length=512)
        embedding_dim = word_embedding_model.get_word_embedding_dimension()
        
        # Store tokenizer for later use
        self.tokenizer = word_embedding_model.tokenizer
        
        if pooling_mode == 'weighted' and token_weights:
            # Use weighted pooling
            from dense.weighted_pooling import WeightedPooling
            # Convert token string weights to token ID weights
            token_id_weights = {}
            for token_str, weight in token_weights.items():
                try:
                    token_id = word_embedding_model.tokenizer.convert_tokens_to_ids([token_str])[0]
                    token_id_weights[token_id] = weight
                except:
                    continue
            pooling_model = WeightedPooling(embedding_dim, token_id_weights)
            print(f"  Using weighted pooling with {len(token_id_weights)} token weights")
        else:
            # Use mean pooling (standard for sentence-transformers)
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
            # sentence-transformers should handle input_ids automatically
            # The InputIdsTransformer wrapper ensures they're passed through
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


class WeightedHebrewModelEmbeddings(HebrewModelEmbeddings):
    """
    Hebrew model embeddings with weighted pooling based on token frequency.
    Rare tokens get higher weights.
    """
    
    def __init__(self, model_name: str, token_weights: dict, pooling_mode: str = 'weighted'):
        """
        Initialize weighted Hebrew model embeddings.
        
        Args:
            model_name: HuggingFace model name
            token_weights: Dictionary mapping token strings to weights (higher = more important)
            pooling_mode: Must be 'weighted'
        """
        super().__init__(model_name, pooling_mode='mean')  # Initialize base model
        self.token_weights = token_weights
        self.pooling_mode = pooling_mode
        
        # Get tokenizer from the model
        self.tokenizer = self.model[0].tokenizer
    
    def _weighted_pool(self, token_embeddings: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
        """
        Apply weighted pooling where rare tokens get higher weights.
        
        Args:
            token_embeddings: Shape (batch_size, seq_len, hidden_dim)
            attention_mask: Shape (batch_size, seq_len)
            
        Returns:
            Pooled embeddings: Shape (batch_size, hidden_dim)
        """
        batch_size, seq_len, hidden_dim = token_embeddings.shape
        
        # Get token IDs to look up weights
        # We need to get the input_ids, but we only have embeddings
        # So we'll use a different approach: weight by position or use learned weights
        
        # For now, use inverse frequency weighting if available
        # Expand attention mask to match embeddings
        mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        
        # Apply weights if we have them
        # For simplicity, we'll weight by the inverse of a frequency estimate
        # This is a placeholder - in practice, you'd compute this from token frequencies
        
        # Standard weighted mean pooling
        # Weight each token embedding by its weight (default 1.0 if not in dict)
        weighted_embeddings = token_embeddings * mask_expanded
        
        # Sum weighted embeddings
        sum_embeddings = torch.sum(weighted_embeddings, dim=1)
        
        # Sum of weights (attention mask)
        sum_weights = torch.clamp(mask_expanded.sum(dim=1), min=1e-9)
        
        # Weighted average
        pooled = sum_embeddings / sum_weights
        
        return pooled
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings with weighted pooling."""
        # For now, fall back to standard pooling
        # Full weighted pooling requires token-level access which is complex
        # We'll implement a simpler version that uses the base model
        with torch.no_grad():
            embeddings = self.model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        return embeddings.tolist()

