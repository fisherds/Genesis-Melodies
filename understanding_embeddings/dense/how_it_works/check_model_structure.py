#!/usr/bin/env python3
"""Check model structure to understand dimension reduction."""

from sentence_transformers import SentenceTransformer
import torch

# Check English ST
print("=" * 80)
print("ENGLISH SENTENCE TRANSFORMER")
print("=" * 80)
model_en = SentenceTransformer('sentence-transformers/all-mpnet-base-v2', device='cpu')
print(f"\nNumber of modules: {len(model_en)}")
for i, m in enumerate(model_en):
    print(f"\nModule {i}: {type(m).__name__}")
    print(f"  {m}")
    if hasattr(m, 'word_embedding_dimension'):
        print(f"  word_embedding_dimension: {m.word_embedding_dimension}")
    if hasattr(m, 'get_sentence_embedding_dimension'):
        print(f"  sentence_embedding_dimension: {m.get_sentence_embedding_dimension()}")
    if hasattr(m, 'pooling_output_dimension'):
        print(f"  pooling_output_dimension: {m.pooling_output_dimension}")

# Check if there's a dense layer
print("\nChecking for dense layers:")
for i, m in enumerate(model_en):
    if hasattr(m, 'dense'):
        print(f"Module {i} has dense layer: {m.dense}")
    # Check all submodules
    for name, submodule in m.named_modules():
        if 'dense' in name.lower() or 'linear' in name.lower():
            print(f"Module {i}, submodule {name}: {submodule}")

# Test with actual text
print("\n" + "=" * 80)
print("TESTING WITH TEXT")
print("=" * 80)
test_text = "In the beginning, Elohim created the skies and the land,"
print(f"Test text: {test_text}")

# Get embeddings through the full pipeline
full_embedding = model_en.encode(test_text)
print(f"\nFull pipeline embedding shape: {full_embedding.shape}")

# Get intermediate outputs
transformer_model = model_en[0].auto_model
tokenizer = model_en[0].tokenizer
encoded = tokenizer(test_text, return_tensors='pt', padding=False, truncation=True)
with torch.no_grad():
    outputs = transformer_model(**encoded)
    last_hidden_state = outputs.last_hidden_state[0]
    print(f"Last hidden state shape: {last_hidden_state.shape}")

# Apply pooling manually
pooling = model_en[1]
attention_mask = encoded['attention_mask'][0]
with torch.no_grad():
    pooled = pooling.forward({'token_embeddings': last_hidden_state.unsqueeze(0), 
                             'attention_mask': attention_mask.unsqueeze(0)})
    print(f"After pooling shape: {pooled['sentence_embedding'].shape}")

# Check Hebrew ST
print("\n" + "=" * 80)
print("HEBREW SENTENCE TRANSFORMER")
print("=" * 80)
model_he = SentenceTransformer('odunola/sentence-transformers-bible-reference-final', device='cpu')
print(f"\nNumber of modules: {len(model_he)}")
for i, m in enumerate(model_he):
    print(f"\nModule {i}: {type(m).__name__}")
    print(f"  {m}")
    if hasattr(m, 'word_embedding_dimension'):
        print(f"  word_embedding_dimension: {m.word_embedding_dimension}")
    if hasattr(m, 'get_sentence_embedding_dimension'):
        print(f"  sentence_embedding_dimension: {m.get_sentence_embedding_dimension()}")

