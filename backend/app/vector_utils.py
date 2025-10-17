"""
Vector Utilities for Embeddings

Provides utilities for working with vector embeddings in PostgreSQL with pgvector.
Includes functions for:
- Converting between JSONB and vector format
- Computing cosine similarity using pgvector
- Batch vector operations
- Vector search queries

Usage:
    from app.vector_utils import compute_similarity_pgvector, save_embedding_to_db
"""

from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


def embedding_to_vector_string(embedding: List[float]) -> str:
    """
    Convert a list of floats to pgvector string format.
    
    Args:
        embedding: List of float values (e.g., [0.1, 0.2, 0.3, ...])
    
    Returns:
        String in format "[0.1,0.2,0.3,...]" suitable for pgvector
    
    Example:
        >>> embedding_to_vector_string([0.1, 0.2, 0.3])
        '[0.1,0.2,0.3]'
    """
    if not embedding:
        return None
    
    # Format as [val1,val2,val3,...]
    values = ','.join(str(v) for v in embedding)
    return f'[{values}]'


def vector_string_to_embedding(vector_str: str) -> Optional[List[float]]:
    """
    Convert pgvector string format to list of floats.
    
    Args:
        vector_str: String in format "[0.1,0.2,0.3,...]"
    
    Returns:
        List of float values or None if invalid
    
    Example:
        >>> vector_string_to_embedding('[0.1,0.2,0.3]')
        [0.1, 0.2, 0.3]
    """
    if not vector_str:
        return None
    
    try:
        # Remove brackets and split
        values_str = vector_str.strip('[]')
        values = [float(v.strip()) for v in values_str.split(',')]
        return values
    except Exception as e:
        logger.error(f"Error parsing vector string: {e}")
        return None


def get_similarity_query(
    table: str,
    vector_column: str,
    query_embedding: List[float],
    limit: int = 10,
    distance_threshold: Optional[float] = None
) -> str:
    """
    Generate SQL query for vector similarity search using pgvector.
    
    Args:
        table: Table name (e.g., 'jobs', 'resumes')
        vector_column: Column containing vector embeddings
        query_embedding: The query vector to search for
        limit: Maximum number of results
        distance_threshold: Optional maximum distance (smaller = more similar)
    
    Returns:
        SQL query string
    
    Example:
        >>> get_similarity_query('jobs', 'embedding', my_embedding, limit=5)
        "SELECT *, 1 - (embedding <=> '[...]') as similarity FROM jobs ORDER BY embedding <=> '[...]' LIMIT 5"
    """
    vector_str = embedding_to_vector_string(query_embedding)
    
    # Use <=> operator for cosine distance
    # Note: 1 - distance = similarity score
    query = f"""
        SELECT *, 
               1 - ({vector_column} <=> '{vector_str}') as similarity,
               {vector_column} <=> '{vector_str}' as distance
        FROM {table}
        WHERE {vector_column} IS NOT NULL
    """
    
    if distance_threshold is not None:
        query += f" AND {vector_column} <=> '{vector_str}' < {distance_threshold}"
    
    query += f"""
        ORDER BY {vector_column} <=> '{vector_str}'
        LIMIT {limit}
    """
    
    return query


def batch_save_embeddings(
    supabase_client,
    table: str,
    records: List[Dict[str, Any]],
    id_field: str = 'id',
    embedding_field: str = 'embedding',
    source_field: str = 'embedding'
):
    """
    Batch save embeddings to vector column from JSONB field.
    
    This is useful for migrating existing JSONB embeddings to pgvector columns.
    
    Args:
        supabase_client: Supabase client instance
        table: Table name
        records: List of records with embeddings
        id_field: Name of ID field
        embedding_field: Name of vector column to update
        source_field: Name of JSONB field containing embedding
    
    Example:
        >>> batch_save_embeddings(supabase, 'jobs', jobs, 'id', 'embedding', 'raw.embedding')
    """
    updated = 0
    failed = 0
    
    for record in records:
        try:
            record_id = record.get(id_field)
            
            # Extract embedding from JSONB
            if '.' in source_field:
                # Nested field like 'raw.embedding'
                parts = source_field.split('.')
                value = record
                for part in parts:
                    value = value.get(part, {})
                embedding = value
            else:
                embedding = record.get(source_field)
            
            if not embedding or not isinstance(embedding, list):
                continue
            
            # Convert to vector string
            vector_str = embedding_to_vector_string(embedding)
            
            # Update record
            # Note: This uses raw SQL update since Supabase client doesn't support vector type directly
            supabase_client.rpc(
                'update_embedding',
                {
                    'table_name': table,
                    'record_id': record_id,
                    'vector_value': vector_str
                }
            ).execute()
            
            updated += 1
            
        except Exception as e:
            logger.error(f"Failed to save embedding for record {record.get(id_field)}: {e}")
            failed += 1
    
    logger.info(f"Batch save complete: {updated} updated, {failed} failed")
    return {'updated': updated, 'failed': failed}


# SQL function to create (run this in Supabase SQL Editor once)
CREATE_VECTOR_UPDATE_FUNCTION = """
-- Function to update vector column from text representation
CREATE OR REPLACE FUNCTION update_embedding(
    table_name TEXT,
    record_id UUID,
    vector_value TEXT
) RETURNS void AS $$
DECLARE
    sql TEXT;
BEGIN
    sql := format('UPDATE %I SET embedding = %L::vector WHERE id = %L',
                  table_name, vector_value, record_id);
    EXECUTE sql;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
"""


def optimize_vector_search_params():
    """
    Return recommended pgvector HNSW index parameters.
    
    These parameters control the index build and search quality:
    - m: Number of connections per layer (higher = better recall, more memory)
    - ef_construction: Size of dynamic candidate list (higher = better index, slower build)
    - ef_search: Size of search list (higher = better recall, slower search)
    
    Returns:
        Dict with recommended parameters
    """
    return {
        'index_params': {
            'm': 16,  # Good balance for most use cases
            'ef_construction': 64  # Good for up to 100K vectors
        },
        'search_params': {
            'ef_search': 40  # Good recall with reasonable speed
        },
        'recommendations': {
            'small_dataset': {'m': 16, 'ef_construction': 64, 'ef_search': 40},
            'medium_dataset': {'m': 24, 'ef_construction': 128, 'ef_search': 64},
            'large_dataset': {'m': 32, 'ef_construction': 256, 'ef_search': 100}
        }
    }


# Example usage for setting search parameters
SET_EF_SEARCH = """
-- Set ef_search parameter for current session
-- Run before vector similarity queries for better results
SET hnsw.ef_search = 100;
"""

