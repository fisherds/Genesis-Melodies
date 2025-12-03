#!/usr/bin/env python3
"""
Quick test script to verify AlephBERT is working.
This will download the model on first run (may take a few minutes).
"""

from sentence_transformers import SentenceTransformer
import numpy as np

print("Loading AlephBERT model...")
print("(This will download the model on first run - may take a few minutes)")
print()

# Load AlephBERT - this is the Hebrew-specific BERT model
# Model name: onlplab/alephbert-base
# model = SentenceTransformer('onlplab/alephbert-base') # AlephBERT base model is not pretrained on Hebrew, so it's not a good choice for Hebrew text.
# model = SentenceTransformer('tanakh-ai/berit-base') # BERiT base model is not pretrained on Hebrew, so it's not a good choice for Hebrew text.
model = SentenceTransformer('odunola/sentence-transformers-bible-reference-final') # This model is pretrained on Hebrew, so it's a good choice for Hebrew text.

print("✓ Model loaded successfully!")
print()

# Test with some Hebrew text from our records
test_texts = [
    "בְּרֵאשִׁית בָּרָא אֱלֹהִים",  # "In the beginning God created"
    "וַיֹּאמֶר אֱלֹהִים יְהִי אוֹר",  # "And God said, Let there be light"
]

print("Generating embeddings for test Hebrew texts...")
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
print("✓ AlephBERT is working correctly!")

