#!/usr/bin/env python3
"""
Generate embeddings for Hebrew models using Python (fallback when ONNX not available).
Called from Node.js backend for BERiT and Hebrew ST models.
"""
import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from understanding_embeddings.dense.models import get_embedding_function
from understanding_embeddings.shared.utils import ensure_correct_working_directory

def main():
    ensure_correct_working_directory()
    
    if len(sys.argv) != 3:
        print(json.dumps({"error": "Usage: generate_embedding_python.py <model_key> <text>"}), file=sys.stderr)
        sys.exit(1)
    
    model_key = sys.argv[1]
    text = sys.argv[2]
    
    try:
        # Get embedding function
        embeddings = get_embedding_function(model_key)
        
        # Generate embedding
        embedding = embeddings.embed_query(text)
        
        # Output as JSON array
        print(json.dumps(embedding))
        
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

