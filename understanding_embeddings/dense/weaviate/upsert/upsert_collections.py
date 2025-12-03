"""
Upsert records into Weaviate collections with custom embeddings.
"""
import json
import os
import sys
from pathlib import Path
from typing import List, Dict

import weaviate
from tqdm import tqdm
from weaviate.classes.init import Auth
from weaviate.classes.config import Configure, DataType, Property
from weaviate.collections.classes.config_vectorizers import VectorDistances

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from understanding_embeddings.shared.load_records import load_records
from understanding_embeddings.dense.models import get_embedding_function, get_text_field
from understanding_embeddings.shared.utils import ensure_correct_working_directory


def upsert_chunks(model_key: str, record_level: str):
    """
    Upsert records into a Weaviate collection.
    
    Args:
        model_key: One of 'hebrew_st', 'berit', 'english_st'
        record_level: One of 'pericope', 'verse', 'agentic_berit', 'agentic_hebrew_st', 'agentic_english_st'
    """
    # Ensure we're in the correct directory
    ensure_correct_working_directory()
    
    # Collection name matches ChromaDB naming convention
    collection_name = f"{model_key}_{record_level}"
    
    print(f"\n{'='*60}")
    print(f"Upserting: {collection_name}")
    print(f"{'='*60}\n")
    
    # Load records
    data_dir = project_root / 'understanding_embeddings' / 'data'
    print(f"Loading records from {record_level}...")
    records = load_records(data_dir, record_level=record_level)
    print(f"Loaded {len(records)} records")
    
    # Get embedding function and text field
    print(f"Initializing {model_key} embedding model...")
    embeddings = get_embedding_function(model_key)
    text_field = get_text_field(model_key)
    print(f"Using '{text_field}' field for embeddings\n")
    
    # Connect to Weaviate
    weaviate_url = os.getenv('WEAVIATE_URL')
    weaviate_api_key = os.getenv('WEAVIATE_API_KEY')
    
    if not weaviate_url or not weaviate_api_key:
        raise ValueError("WEAVIATE_URL and WEAVIATE_API_KEY must be set in environment variables")
    
    client = weaviate.connect_to_weaviate_cloud(
        cluster_url=weaviate_url,
        auth_credentials=Auth.api_key(weaviate_api_key),
    )
    
    try:
        # Check if collection exists
        if client.collections.exists(collection_name):
            print(f"Using existing collection: {collection_name}")
            collection = client.collections.get(collection_name)
        else:
            print(f"Creating collection: {collection_name}")
            
            # Determine embedding dimension based on model
            # BERiT: 256, Hebrew ST: 768, English ST: 768
            embedding_dims = {
                'berit': 256,
                'hebrew_st': 768,
                'english_st': 768
            }
            vector_dimension = embedding_dims.get(model_key, 768)
            
            # Create collection with manual vector configuration
            # We'll generate embeddings ourselves and pass them in
            # Using self_provided vectorizer (manual vectors) with HNSW index
            collection = client.collections.create(
                name=collection_name,
                vector_config=Configure.Vectors.self_provided(
                    vector_index_config=Configure.VectorIndex.hnsw(
                        distance_metric=VectorDistances.COSINE
                    )
                ),
                properties=[
                    Property(name="title", data_type=DataType.TEXT),
                    Property(name="text", data_type=DataType.TEXT),  # English text
                    Property(name="hebrew", data_type=DataType.TEXT),
                    Property(name="strongs", data_type=DataType.TEXT),
                    Property(name="verses", data_type=DataType.TEXT_ARRAY),  # Store as array of strings
                ]
            )
            print(f"Created collection with vector dimension: {vector_dimension}")
        
        # Generate embeddings and prepare objects for Weaviate
        print(f"\nGenerating embeddings for {len(records)} records...")
        weaviate_objects = []
        
        for record in tqdm(records, desc="Generating embeddings"):
            # Get the text to embed
            text_to_embed = record.get(text_field, "")
            
            if not text_to_embed:
                print(f"Warning: Record {record.get('id')} has no {text_field} field, skipping")
                continue
            
            # Generate embedding using our custom model
            # This is the field we use for vector search (hebrew for BERiT/Hebrew ST, text for English ST)
            # Weaviate doesn't know about this - we just pass the vector
            embedding_vector = embeddings.embed_query(text_to_embed)
            
            # Convert verses to string array format for Weaviate
            verses_array = []
            for verse_obj in record.get('verses', []):
                if isinstance(verse_obj, dict):
                    chapter = verse_obj.get('chapter', '')
                    verse = verse_obj.get('verse', '')
                    # Handle float verses (partial verses like 1:2.4)
                    if isinstance(verse, float):
                        verses_array.append(f"{chapter}:{verse}")
                    else:
                        verses_array.append(f"{chapter}:{verse}")
                else:
                    verses_array.append(str(verse_obj))
            
            # Create Weaviate object
            # Note: 'id' is reserved in Weaviate, so we don't include it
            # Weaviate will auto-generate UUIDs for each object
            weaviate_obj = {
                "title": record.get('title', ''),
                "text": record.get('text', ''),  # English text
                "hebrew": record.get('hebrew', ''),
                "strongs": record.get('strongs', ''),
                "verses": verses_array,
            }
            
            weaviate_objects.append({
                "object": weaviate_obj,
                "vector": embedding_vector
            })
        
        print(f"\nUpserting {len(weaviate_objects)} objects to Weaviate...")
        
        # Batch upsert
        batch_size = 200
        num_batches = (len(weaviate_objects) + batch_size - 1) // batch_size
        
        with collection.batch.fixed_size(batch_size=batch_size) as batch:
            for batch_idx in tqdm(range(num_batches), desc="Upserting batches"):
                start = batch_idx * batch_size
                end = min(start + batch_size, len(weaviate_objects))
                
                for obj_data in weaviate_objects[start:end]:
                    # Add object with manual vector
                    batch.add_object(
                        properties=obj_data["object"],
                        vector=obj_data["vector"]
                    )
                
                if batch.number_errors > 10:
                    print("Batch import stopped due to excessive errors.")
                    break
        
        # Check for failed objects
        failed_objects = collection.batch.failed_objects
        if failed_objects:
            print(f"\n⚠️  Number of failed imports: {len(failed_objects)}")
            if len(failed_objects) > 0:
                print(f"First failed object: {failed_objects[0]}")
        else:
            print(f"\n✅ Successfully upserted {len(weaviate_objects)} objects to {collection_name}")
        
    finally:
        client.close()


if __name__ == "__main__":
    # Ensure we're in the correct directory
    ensure_correct_working_directory()
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Connect to Weaviate
    weaviate_url = os.getenv('WEAVIATE_URL')
    weaviate_api_key = os.getenv('WEAVIATE_API_KEY')
    
    if not weaviate_url or not weaviate_api_key:
        raise ValueError("WEAVIATE_URL and WEAVIATE_API_KEY must be set in environment variables")
    
    try:
        # Upsert the original 5 collections (no agentic chunking yet)
        collections_to_upsert = [
            ("hebrew_st", "pericope"),
            ("hebrew_st", "verse"),
            ("english_st", "pericope"),
            ("english_st", "verse"),
            ("berit", "verse"),
        ]
        
        for model_key, record_level in collections_to_upsert:
            try:
                upsert_chunks(model_key, record_level)
            except Exception as e:
                print(f"\n❌ Error upserting {model_key}_{record_level}: {e}")
                import traceback
                traceback.print_exc()
                print("\nContinuing with next collection...\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

