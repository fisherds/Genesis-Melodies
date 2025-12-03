"""
Dense search functionality using ChromaDB vector store.
"""

from pathlib import Path
from typing import List, Dict, Optional
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

from .vector_store import load_vector_store


def dense_search(
    query_hebrew: str,
    vector_store: Chroma,
    k: int = 10
) -> List[Dict]:
    """
    Perform dense semantic search using Hebrew query.
    
    Args:
        query_hebrew: Hebrew text to search for
        vector_store: ChromaDB vector store
        k: Number of results to return
        
    Returns:
        List of result dictionaries, each containing:
        - id: Record ID
        - title: Record title
        - text: English text
        - hebrew: Hebrew text
        - strongs: Strong's numbers
        - verses: Verse references
        - score: Similarity score (0-1, higher is more similar)
    """
    # Perform similarity search
    docs_with_scores = vector_store.similarity_search_with_score(
        query_hebrew,
        k=k
    )
    
    # Format results
    results = []
    for doc, score in docs_with_scores:
        result = {
            'id': doc.metadata.get('id', 'unknown'),
            'title': doc.metadata.get('title', 'Unknown'),
            'text': doc.metadata.get('text', ''),
            'hebrew': doc.metadata.get('hebrew', ''),
            'strongs': doc.metadata.get('strongs', ''),
            'verses': doc.metadata.get('verses', ''),
            'score': float(score)  # Convert numpy float to Python float
        }
        results.append(result)
    
    return results

