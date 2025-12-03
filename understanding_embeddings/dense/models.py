"""
Model configurations and embedding functions for different embedding models.
"""

from typing import List, Callable
from pathlib import Path
import torch
import numpy as np
from transformers import RobertaModel, RobertaTokenizerFast
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.embeddings import Embeddings


class BERiTEmbeddings(Embeddings):
    """
    Custom embedding class for BERiT (Biblical Hebrew RoBERTa).
    BERiT uses RobertaModel, not SentenceTransformer, so we need a custom wrapper.
    """
    
    def __init__(self, model_name: str = "gngpostalsrvc/BERiT"):
        """Initialize BERiT embeddings."""
        self.model_name = model_name
        print(f"Loading BERiT tokenizer from '{model_name}'...")
        self.tokenizer = RobertaTokenizerFast.from_pretrained(model_name)
        print(f"Loading BERiT model from '{model_name}'...")
        self.model = RobertaModel.from_pretrained(model_name)
        self.model.eval()  # Set to evaluation mode
        # Disable gradient computation globally for this model
        for param in self.model.parameters():
            param.requires_grad = False
        print("✓ BERiT loaded successfully!")
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of documents."""
        # Process one at a time to avoid tensor size mismatches
        # This is slower but more reliable
        batch_size = 1
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            
            # Tokenize the batch
            # IMPORTANT: BERiT model has max_position_embeddings=128, not 512!
            # We must truncate to 128 to match the model's training configuration
            encoded = self.tokenizer(
                batch_texts,
                padding=True,
                truncation=True,
                return_tensors='pt',
                max_length=128  # Match model's max_position_embeddings
            )
            
            # Ensure sequence length is within model's max_position_embeddings (128)
            seq_length = encoded['input_ids'].shape[1]
            if seq_length > 128:
                # This shouldn't happen with truncation, but be safe
                seq_length = 128
                encoded['input_ids'] = encoded['input_ids'][:, :128]
                encoded['attention_mask'] = encoded['attention_mask'][:, :128]
            
            # Create explicit position_ids within valid range (0 to 127)
            # The model was trained with max_position_embeddings=128
            batch_size = encoded['input_ids'].shape[0]
            position_ids = torch.arange(0, seq_length, dtype=torch.long).unsqueeze(0).expand(batch_size, -1)
            
            # Get model outputs (no gradient computation needed)
            # Clear any potential cached buffers by ensuring model is in eval mode
            self.model.eval()
            
            # Use the model's forward method with explicit parameters
            # This avoids any internal buffering issues
            with torch.no_grad():
                # Explicitly call forward with position_ids to ensure they're in valid range
                outputs = self.model.forward(
                    input_ids=encoded['input_ids'],
                    attention_mask=encoded['attention_mask'],
                    position_ids=position_ids
                )
                attention_mask = encoded['attention_mask']
                
                # Mean pooling with attention mask
                mask_expanded = attention_mask.unsqueeze(-1).expand(
                    outputs.last_hidden_state.size()
                ).float()
                
                sum_embeddings = torch.sum(
                    outputs.last_hidden_state * mask_expanded, dim=1
                )
                sum_mask = torch.clamp(mask_expanded.sum(dim=1), min=1e-9)
                embeddings = sum_embeddings / sum_mask
                
                # Normalize embeddings for cosine similarity
                embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)
            
            # Convert to list and add to results
            all_embeddings.extend(embeddings.numpy().tolist())
        
        return all_embeddings
    
    def embed_query(self, text: str) -> List[float]:
        """Generate embedding for a single query."""
        return self.embed_documents([text])[0]


# Model configurations
MODEL_CONFIGS = {
    'hebrew_st': {
        'name': 'Hebrew Sentence Transformer',
        'model_name': 'odunola/sentence-transformers-bible-reference-final',
        'embedding_class': HuggingFaceEmbeddings,
        'embedding_kwargs': {
            'model_name': 'odunola/sentence-transformers-bible-reference-final',
            'model_kwargs': {'device': 'cpu'},
            'encode_kwargs': {'normalize_embeddings': True}
        },
        'text_field': 'hebrew',  # Embed Hebrew text
    },
    'berit': {
        'name': 'BERiT',
        'model_name': 'gngpostalsrvc/BERiT',
        'embedding_class': BERiTEmbeddings,
        'embedding_kwargs': {
            'model_name': 'gngpostalsrvc/BERiT'
        },
        'text_field': 'hebrew',  # Embed Hebrew text
    },
    'english_st': {
        'name': 'English Sentence Transformer',
        'model_name': 'sentence-transformers/all-mpnet-base-v2',
        'embedding_class': HuggingFaceEmbeddings,
        'embedding_kwargs': {
            'model_name': 'sentence-transformers/all-mpnet-base-v2',
            'model_kwargs': {'device': 'cpu'},
            'encode_kwargs': {'normalize_embeddings': True}
        },
        'text_field': 'text',  # Embed English text
    },
}


def get_embedding_function(model_key: str) -> Embeddings:
    """
    Get an embedding function for the specified model.
    
    Args:
        model_key: One of 'hebrew_st', 'berit', 'english_st'
        
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
    embedding_kwargs = config['embedding_kwargs']
    
    print(f"Initializing {config['name']} embedder...")
    return embedding_class(**embedding_kwargs)


def get_text_field(model_key: str) -> str:
    """Get which field to embed for a given model."""
    return MODEL_CONFIGS[model_key]['text_field']


def get_persist_directory(base_dir: Path, model_key: str, record_level: str = 'pericope') -> Path:
    """
    Get the persist directory for a model's vector store.
    
    Args:
        base_dir: Base directory (typically dense folder)
        model_key: Model key ('hebrew_st', 'berit', or 'english_st')
        record_level: 'pericope', 'verse', 'agentic_berit', 'agentic_hebrew_st', or 'agentic_english_st'
        
    Returns:
        Path to the persist directory (e.g., dense/chroma_db/hebrew_st_pericope or berit_agentic_berit)
    """
    chroma_db_dir = base_dir / 'chroma_db'
    # For agentic record levels, use format: {model_key}_{record_level}
    # e.g., berit_agentic_berit, hebrew_st_agentic_berit, english_agentic_berit
    return chroma_db_dir / f'{model_key}_{record_level}'


def get_outputs_directory(base_outputs_dir: Path, model_key: str) -> Path:
    """Get the outputs directory for a model."""
    return base_outputs_dir / model_key

