#!/usr/bin/env python3
"""
Quick test script to verify English Sentence Transformer is working.
This will download the model on first run (may take a few minutes).
"""

from sentence_transformers import SentenceTransformer
import numpy as np

print("Loading English Sentence Transformer model...")
print("(This will download the model on first run - may take a few minutes)")
print()

# Load English Sentence Transformer model
# Using all-mpnet-base-v2 for better quality and 512 token limit
model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')

print("✓ Model loaded successfully!")
print()

# Test with some English text from our records (BibleProject translation)
test_texts = [
    "In the beginning, Elohim created the skies and the land,",  # Genesis 1:1
    "and Elohim said, \"Let there be light\" and there was light.",  # Genesis 1:3
]

print("Generating embeddings for test English texts...")
embeddings = model.encode(test_texts)

print(f"✓ Generated embeddings!")
print(f"  Number of texts: {len(test_texts)}")
print(f"  Embedding dimension: {embeddings.shape[1]}")
print()

# Test similarity
similarity = np.dot(embeddings[0], embeddings[1]) / (
    np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
)
print(f"Cosine similarity between texts: {similarity:.4f}")
print()
print("✓ English Sentence Transformer is working correctly!")

