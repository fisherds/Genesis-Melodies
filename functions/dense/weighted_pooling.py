"""
Weighted pooling implementation for Hebrew models.
Uses token frequency analysis to weight rare tokens more heavily.
"""

import json
import torch
import numpy as np
from typing import Dict, Optional
from pathlib import Path
from sentence_transformers.models import Pooling
from sentence_transformers import SentenceTransformer


class WeightedPooling(Pooling):
    """
    Custom pooling that weights tokens by inverse frequency.
    Rare tokens get higher weights.
    """
    
    def __init__(self, word_embedding_dimension: int, token_id_weights: Dict[int, float]):
        """
        Initialize weighted pooling.
        
        Args:
            word_embedding_dimension: Dimension of token embeddings
            token_id_weights: Dictionary mapping token IDs to weights (pre-computed for efficiency)
        """
        super().__init__(
            word_embedding_dimension=word_embedding_dimension,
            pooling_mode_mean_tokens=False,
            pooling_mode_cls_token=False,
            pooling_mode_max_tokens=False
        )
        self.token_id_weights = token_id_weights
        self.word_embedding_dimension = word_embedding_dimension
        # Default weight for tokens not in the dictionary
        self.default_weight = 1.0
        # Register as buffer so it's moved to the correct device
        self.register_buffer('_dummy', torch.zeros(1))
    
    def forward(self, features):
        """
        Apply weighted pooling to token embeddings.
        
        Args:
            features: Dictionary with 'token_embeddings', 'attention_mask', and 'input_ids'
            
        Returns:
            Dictionary with 'sentence_embedding'
        """
        token_embeddings = features['token_embeddings']
        attention_mask = features['attention_mask']
        input_ids = features.get('input_ids', None)
        
        batch_size, seq_len, hidden_dim = token_embeddings.shape
        
        # Create weight tensor from token IDs
        if input_ids is not None:
            # Look up weights for each token ID
            device = token_embeddings.device
            weights = torch.ones((batch_size, seq_len), dtype=torch.float32, device=device)
            
            for batch_idx in range(batch_size):
                for token_idx in range(seq_len):
                    if attention_mask[batch_idx, token_idx] == 0:
                        continue  # Skip padding tokens
                    
                    token_id = input_ids[batch_idx, token_idx].item()
                    weight = self.token_id_weights.get(token_id, self.default_weight)
                    weights[batch_idx, token_idx] = weight
        else:
            # Fall back to uniform weights (mean pooling)
            weights = attention_mask.float()
        
        # Apply weighted pooling
        weights_expanded = weights.unsqueeze(-1).expand(token_embeddings.size())
        weighted_embeddings = token_embeddings * weights_expanded * attention_mask.unsqueeze(-1).float()
        
        sum_embeddings = torch.sum(weighted_embeddings, dim=1)
        sum_weights = torch.clamp(weights_expanded.sum(dim=1), min=1e-9)
        sentence_embeddings = sum_embeddings / sum_weights
        
        features.update({'sentence_embedding': sentence_embeddings})
        return features


def load_token_weights(model_name: str, data_dir: Path, tokenizer=None) -> Optional[Dict]:
    """
    Load token weights from frequency analysis file and convert to token ID mapping.
    
    Args:
        model_name: Model name ('dicta-il/dictabert' or 'tau/tavbert-he')
        data_dir: Path to data directory (where frequency files are stored)
        tokenizer: Tokenizer to convert token strings to IDs (optional)
        
    Returns:
        Dictionary mapping token IDs to weights, or None if file not found
    """
    # Map model names to frequency file names
    model_to_file = {
        'dicta-il/dictabert': 'dictabert_token_frequencies.json',
        'tau/tavbert-he': 'tavbert_token_frequencies.json',
        'odunola/sentence-transformers-bible-reference-final': 'english_st_token_frequencies.json',
        'sentence-transformers/all-mpnet-base-v2': 'english_st_token_frequencies.json'
    }
    
    filename = model_to_file.get(model_name)
    if not filename:
        return None
    
    freq_file = data_dir / filename
    if not freq_file.exists():
        return None
    
    with open(freq_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    token_string_weights = data.get('token_weights', {})
    
    # Convert token strings to token IDs if tokenizer is provided
    if tokenizer and token_string_weights:
        token_id_weights = {}
        for token_str, weight in token_string_weights.items():
            try:
                token_id = tokenizer.convert_tokens_to_ids([token_str])[0]
                token_id_weights[token_id] = weight
            except:
                # Skip tokens that can't be converted
                continue
        return token_id_weights
    
    # Return token string weights if no tokenizer (will be converted later)
    return token_string_weights if token_string_weights else None


def create_weighted_model(model_name: str, token_weights: Dict[str, float], data_dir: Path) -> SentenceTransformer:
    """
    Create a SentenceTransformer model with weighted pooling.
    
    Args:
        model_name: HuggingFace model name
        token_weights: Dictionary mapping token strings to weights
        data_dir: Path to data directory
        
    Returns:
        SentenceTransformer model with weighted pooling
    """
    from sentence_transformers.models import Transformer
    
    # Load base transformer
    word_embedding_model = Transformer(model_name, max_seq_length=512)
    embedding_dim = word_embedding_model.get_word_embedding_dimension()
    
    # Create weighted pooling
    pooling_model = WeightedPooling(embedding_dim, token_weights)
    
    # Create SentenceTransformer
    model = SentenceTransformer(modules=[word_embedding_model, pooling_model])
    model.eval()
    
    return model

