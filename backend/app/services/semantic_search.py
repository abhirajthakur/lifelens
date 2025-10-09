import logging
import numpy as np
from typing import List, Optional, Tuple, Dict, Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.media import MediaMetadata, Media
from app.services.ml_services import generate_embeddings


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors.

    Args:
        vec1: First vector
        vec2: Second vector

    Returns:
        Cosine similarity score between 0 and 1
    """
    try:
        # Convert to numpy arrays for efficient computation
        a = np.array(vec1)
        b = np.array(vec2)

        # Calculate cosine similarity
        similarity = np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

        # Ensure the result is between 0 and 1
        return max(0.0, min(1.0, float(similarity)))
    except Exception as e:
        logging.error(f"Error calculating cosine similarity: {e}")
        return 0.0


def semantic_search_media(
    db: Session,
    query: str,
    similarity_threshold: float = 0.7,
    limit: int = 10,
    user_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Search media using semantic similarity based on the query.

    Args:
        db: Database session
        query: Search query text
        similarity_threshold: Minimum similarity score (0.0 to 1.0)
        limit: Maximum number of results to return
        user_id: Optional user ID to filter by

    Returns:
        List of media items with similarity scores
    """
    try:
        # Generate embeddings for the search query
        query_embeddings = generate_embeddings(query)
        if not query_embeddings:
            logging.error("Failed to generate embeddings for search query")
            return []

        # Base query to get media metadata with embeddings
        base_query = db.query(MediaMetadata).filter(
            MediaMetadata.embeddings.isnot(None) and MediaMetadata.media_id == Media.id
        )

        if user_id:
            base_query = base_query.filter(Media.user_id == user_id)

        # Get all media metadata with embeddings
        results = base_query.all()

        if not results:
            logging.warning("No media with embeddings found")
            return []

        # Calculate similarity scores
        scored_results = []
        for metadata, media in results:
            try:
                if metadata.embeddings and len(metadata.embeddings) > 0:
                    # Convert pgvector to list if needed
                    stored_embeddings = metadata.embeddings
                    if hasattr(stored_embeddings, "tolist"):
                        stored_embeddings = stored_embeddings.tolist()
                    elif not isinstance(stored_embeddings, list):
                        stored_embeddings = list(stored_embeddings)

                    similarity_score = cosine_similarity(
                        query_embeddings, stored_embeddings
                    )

                    if similarity_score >= similarity_threshold:
                        scored_results.append(
                            {
                                "media_id": str(media.id),
                                "file_name": media.file_name,
                                "file_type": media.file_type.value,
                                "created_at": metadata.created_at.isoformat(),
                                "caption": metadata.caption,
                                "ocr_text": metadata.ocr_text,
                                "similarity_score": similarity_score,
                            }
                        )
            except Exception as e:
                logging.error(f"Error processing media {metadata.media_id}: {e}")
                continue

        # Sort by similarity score (highest first) and limit results
        scored_results.sort(key=lambda x: x["similarity_score"], reverse=True)
        final_results = scored_results[:limit]

        logging.info(
            f"Semantic search found {len(final_results)} results for query: '{query}'"
        )
        return final_results

    except Exception as e:
        logging.error(f"Error in semantic search: {e}")
        return []


def search_by_postgresql_similarity(
    db: Session,
    query: str,
    similarity_threshold: float = 0.7,
    limit: int = 10,
    user_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Use PostgreSQL's vector similarity search with pgvector extension.
    This is more efficient for large datasets.

    Args:
        db: Database session
        query: Search query text
        similarity_threshold: Minimum similarity score
        limit: Maximum number of results
        user_id: Optional user ID to filter by

    Returns:
        List of media items with similarity scores
    """
    try:
        query_embeddings = generate_embeddings(query)
        if not query_embeddings:
            logging.error("Failed to generate embeddings for search query")
            return []

        # Convert embeddings to PostgreSQL array format
        query_vector = str(query_embeddings).replace(" ", "")

        # Build SQL query with vector similarity
        sql_query = """
        SELECT 
            m.id as media_id,
            m.file_name,
            m.file_type,
            mm.created_at,
            mm.caption,
            mm.ocr_text,
            1 - (mm.embeddings <=> %s::vector) as similarity_score
        FROM media_metadata mm
        JOIN media m ON mm.media_id = m.id
        WHERE mm.embeddings IS NOT NULL
        """

        params = [query_vector]

        # Add user filter if provided
        if user_id:
            sql_query += " AND m.user_id = %s"
            params.append(user_id)

        # Add similarity threshold and ordering
        sql_query += """
        AND 1 - (mm.embeddings <=> %s::vector) >= %s
        ORDER BY mm.embeddings <=> %s::vector
        LIMIT %s
        """
        params.extend([query_vector, similarity_threshold, query_vector, limit])

        # Execute the query
        result = db.execute(text(sql_query), params)
        rows = result.fetchall()

        # Format results
        formatted_results = []
        for row in rows:
            formatted_results.append(
                {
                    "media_id": str(row.media_id),
                    "file_name": row.file_name,
                    "file_type": row.file_type,
                    "created_at": row.created_at.isoformat(),
                    "caption": row.caption,
                    "ocr_text": row.ocr_text,
                    "similarity_score": float(row.similarity_score),
                }
            )

        logging.info(
            f"PostgreSQL similarity search found {len(formatted_results)} results"
        )
        return formatted_results

    except Exception as e:
        logging.error(f"Error in PostgreSQL similarity search: {e}")
        # Fall back to Python-based similarity search
        return semantic_search_media(db, query, similarity_threshold, limit, user_id)


def search_media_by_content(
    db: Session, search_terms: List[str], user_id: Optional[str] = None, limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Search media by textual content in captions and OCR text.

    Args:
        db: Database session
        search_terms: List of terms to search for
        user_id: Optional user ID to filter by
        limit: Maximum number of results

    Returns:
        List of matching media items
    """
    try:
        base_query = db.query(MediaMetadata, Media).join(
            Media, MediaMetadata.media_id == Media.id
        )

        # Add user filter
        if user_id:
            base_query = base_query.filter(Media.user_id == user_id)

        # Search in captions and OCR text
        search_conditions = []
        for term in search_terms:
            term_pattern = f"%{term.lower()}%"
            search_conditions.append(MediaMetadata.caption.ilike(term_pattern))
            search_conditions.append(MediaMetadata.ocr_text.ilike(term_pattern))

        if search_conditions:
            from sqlalchemy import or_

            base_query = base_query.filter(or_(*search_conditions))

        results = (
            base_query.order_by(MediaMetadata.created_at.desc()).limit(limit).all()
        )

        # Format results
        formatted_results = []
        for metadata, media in results:
            formatted_results.append(
                {
                    "media_id": str(media.id),
                    "file_name": media.file_name,
                    "file_type": media.file_type.value,
                    "created_at": metadata.created_at.isoformat(),
                    "caption": metadata.caption,
                    "ocr_text": metadata.ocr_text,
                    "similarity_score": 1.0,  # Perfect match for text search
                }
            )

        logging.info(f"Content search found {len(formatted_results)} results")
        return formatted_results

    except Exception as e:
        logging.error(f"Error in content search: {e}")
        return []


def hybrid_search(
    db: Session,
    query: str,
    similarity_threshold: float = 0.6,
    limit: int = 10,
    user_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Hybrid search combining semantic similarity and keyword matching.

    Args:
        db: Database session
        query: Search query
        similarity_threshold: Minimum similarity threshold
        limit: Maximum number of results
        user_id: Optional user ID to filter by

    Returns:
        Combined and deduplicated search results
    """
    try:
        # Perform semantic search
        semantic_results = search_by_postgresql_similarity(
            db, query, similarity_threshold, limit, user_id
        )

        # Perform keyword search
        keywords = query.lower().split()
        keyword_results = search_media_by_content(db, keywords, user_id, limit)

        # Combine and deduplicate results
        combined_results = {}

        # Add semantic results with higher weight
        for result in semantic_results:
            media_id = result["media_id"]
            result["search_type"] = "semantic"
            result["combined_score"] = result["similarity_score"] * 1.0
            combined_results[media_id] = result

        # Add keyword results with lower weight, but boost if already exists
        for result in keyword_results:
            media_id = result["media_id"]
            if media_id in combined_results:
                # Boost existing result
                combined_results[media_id]["combined_score"] += 0.3
                combined_results[media_id]["search_type"] = "hybrid"
            else:
                result["search_type"] = "keyword"
                result["combined_score"] = result["similarity_score"] * 0.7
                combined_results[media_id] = result

        # Sort by combined score and return top results
        final_results = sorted(
            combined_results.values(), key=lambda x: x["combined_score"], reverse=True
        )[:limit]

        logging.info(f"Hybrid search found {len(final_results)} results")
        return final_results

    except Exception as e:
        logging.error(f"Error in hybrid search: {e}")
        return []

