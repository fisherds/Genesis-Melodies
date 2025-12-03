#!/usr/bin/env python3
"""
Quick test script to verify BERiT (Biblical Hebrew BERT) is working.
This will download the model on first run (may take a few minutes).

STEP-BY-STEP WALKTHROUGH:
1. Import necessary libraries
2. Load the model
3. Test with Hebrew text
4. Compare with AlephBERT (if available)
"""

# STEP 1: Import necessary libraries
# BERiT uses RobertaModel, not SentenceTransformer
# We need transformers for the model, torch for tensors, and numpy for calculations
from transformers import RobertaModel, RobertaTokenizerFast
import torch
import numpy as np

print("=" * 60)
print("BERiT Model Test Script")
print("=" * 60)
print()

# STEP 2: Load the BERiT model
# BERiT uses RobertaModel architecture, so we need to load tokenizer and model separately
print("STEP 1: Loading BERiT model...")
print("(This will download the model on first run - may take a few minutes)")
print()

BERIT_MODEL_NAME = "gngpostalsrvc/BERiT"

try:
    print(f"Loading tokenizer from '{BERIT_MODEL_NAME}'...")
    tokenizer = RobertaTokenizerFast.from_pretrained(BERIT_MODEL_NAME)
    print(f"✓ Tokenizer loaded!")
    
    print(f"Loading model from '{BERIT_MODEL_NAME}'...")
    model = RobertaModel.from_pretrained(BERIT_MODEL_NAME)
    model.eval()  # Set to evaluation mode (disables dropout, etc.)
    print(f"✓ BERiT model loaded successfully!")
except Exception as e:
    print(f"✗ Error loading model '{BERIT_MODEL_NAME}': {e}")
    print()
    print("Troubleshooting:")
    print("1. Make sure you have transformers installed: pip install transformers")
    print("2. Make sure you have torch installed: pip install torch")
    print("3. Check your internet connection (model needs to download)")
    raise

print()

# STEP 3: Test with Hebrew text from our records
# Using the same test texts as test_alephbert.py for comparison
print("STEP 2: Testing with Hebrew text...")
test_texts = [
    "בְּרֵאשִׁית בָּרָא אֱלֹהִים",  # "In the beginning God created"
    "וַיֹּאמֶר אֱלֹהִים יְהִי אוֹר",  # "And God said, Let there be light"
]

print(f"Test texts:")
for i, text in enumerate(test_texts, 1):
    print(f"  {i}. {text}")
print()

# STEP 4: Generate embeddings
# RobertaModel doesn't have a simple .encode() method like SentenceTransformer
# We need to: tokenize → get model outputs → extract embeddings (mean pooling)
print("STEP 3: Generating embeddings...")

def get_embeddings(texts):
    """
    Generate embeddings for texts using BERiT.
    Uses mean pooling of the last hidden state.
    """
    # Tokenize the texts
    encoded = tokenizer(
        texts,
        padding=True,
        truncation=True,
        return_tensors='pt',
        max_length=128  # BERiT model has max_position_embeddings=128, not 512!
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
    # Ensure model is in eval mode and use explicit position_ids to avoid tensor size mismatches
    model.eval()
    with torch.no_grad():
        outputs = model.forward(
            input_ids=encoded['input_ids'],
            attention_mask=encoded['attention_mask'],
            position_ids=position_ids
        )
        # outputs.last_hidden_state shape: (batch_size, sequence_length, hidden_size)
        # We'll use mean pooling: average across the sequence length dimension
        # But we need to ignore padding tokens, so we'll use attention_mask
        attention_mask = encoded['attention_mask']
        
        # Expand attention mask to match hidden state dimensions
        # Shape: (batch_size, sequence_length, 1)
        mask_expanded = attention_mask.unsqueeze(-1).expand(outputs.last_hidden_state.size()).float()
        
        # Sum the hidden states, but only for non-padding tokens
        sum_embeddings = torch.sum(outputs.last_hidden_state * mask_expanded, dim=1)
        
        # Count non-padding tokens for each sentence
        sum_mask = torch.clamp(mask_expanded.sum(dim=1), min=1e-9)
        
        # Mean pooling: divide by number of non-padding tokens
        embeddings = sum_embeddings / sum_mask
    
    return embeddings.numpy()

embeddings = get_embeddings(test_texts)

print(f"✓ Generated embeddings!")
print(f"  Number of texts: {len(test_texts)}")
print(f"  Embedding dimension: {embeddings.shape[1]}")
print()

# STEP 5: Test similarity
print("STEP 4: Testing similarity...")
# Calculate cosine similarity between the two embeddings
similarity = np.dot(embeddings[0], embeddings[1]) / (
    np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
)
print(f"Cosine similarity between texts: {similarity:.4f}")
print()

print("=" * 60)
print("✓ BERiT test complete!")
print("=" * 60)
print()
