"""
Set up ChromaDB vector store for dense embeddings.
"""

from pathlib import Path
from typing import List, Dict, Optional
import chromadb
from chromadb.config import Settings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

from pathlib import Path
import sys

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from understanding_embeddings.shared.load_records import load_records
from understanding_embeddings.dense.models import (
    get_embedding_function,
    get_text_field,
    get_persist_directory
)


def create_vector_store(
    data_dir: Path,
    model_key: str = 'hebrew_st',
    record_level: str = 'pericope',
    persist_directory: Optional[Path] = None,
    collection_name: Optional[str] = None,
    force: bool = False
) -> Chroma:
    """
    Create and populate a ChromaDB vector store with embeddings.
    
    Args:
        data_dir: Path to data directory containing records
        model_key: Model to use ('hebrew_st', 'berit', or 'english_st')
        record_level: 'pericope', 'verse', 'agentic_berit', 'agentic_hebrew_st', or 'agentic_english_st' (default: 'pericope')
        persist_directory: Directory to persist the vector store 
                          (default: dense/chroma_db/{model_key}_{record_level})
        collection_name: Name for the ChromaDB collection
                        (default: {model_key}_{record_level})
        
    Returns:
        LangChain Chroma vector store
    """
    # Get base directory (dense folder)
    base_dir = Path(__file__).parent
    
    # Set up persist directory
    if persist_directory is None:
        persist_directory = get_persist_directory(base_dir, model_key, record_level)
    
    # If force is True, delete existing directory to start fresh
    if force and persist_directory.exists():
        import shutil
        print(f"Removing existing vector store at {persist_directory}...")
        shutil.rmtree(persist_directory)
    
    persist_directory.mkdir(exist_ok=True, parents=True)
    
    # Set up collection name
    if collection_name is None:
        collection_name = f"{model_key}_{record_level}"
    
    # Load records
    print(f"Loading {record_level} records...")
    records = load_records(data_dir, record_level=record_level)
    print(f"Loaded {len(records)} records")
    
    # Get which field to embed (hebrew or text/english)
    text_field = get_text_field(model_key)
    
    # Create LangChain documents from records
    documents = []
    metadatas = []
    
    for record in records:
        # Use the appropriate text field for embedding
        doc = Document(
            page_content=record[text_field],
            metadata={
                'id': record['id'],
                'title': record['title'],
                'text': record['text'],  # English text
                'hebrew': record['hebrew'],
                'strongs': record['strongs'],
                'verses': str(record['verses'])  # Store as string for metadata
            }
        )
        documents.append(doc)
        metadatas.append(record['id'])
    
    # Get embedding function for the model
    embeddings = get_embedding_function(model_key)
    
    # Create ChromaDB vector store
    print(f"Creating vector store in {persist_directory}...")
    vector_store = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory=str(persist_directory),
        collection_name=collection_name,
        ids=metadatas
    )
    
    print(f"✓ Vector store created with {len(documents)} documents")
    
    return vector_store


def load_vector_store(
    persist_directory: Path,
    model_key: str = 'hebrew_st',
    collection_name: Optional[str] = None
) -> Chroma:
    """
    Load an existing ChromaDB vector store.
    
    Args:
        persist_directory: Directory where the vector store is persisted
        model_key: Model to use ('hebrew_st', 'berit', or 'english_st')
        collection_name: Name of the ChromaDB collection
                        (default: inferred from persist_directory name)
        
    Returns:
        LangChain Chroma vector store
    """
    # Set up collection name - infer from directory name if not provided
    if collection_name is None:
        # Directory name is like "hebrew_st_pericope", use that as collection name
        collection_name = persist_directory.name
    
    # Get embedding function for the model
    embeddings = get_embedding_function(model_key)
    
    vector_store = Chroma(
        persist_directory=str(persist_directory),
        embedding_function=embeddings,
        collection_name=collection_name
    )
    
    return vector_store

