"""
Embedding Service for CV Vector Storage and Similarity Search

This service handles:
1. Storing embeddings from external scripts (colleague's work)
2. Vector similarity search with pgvector
3. Integration with existing ParsedDocument workflow
"""

import uuid
from typing import List, Optional, Tuple, Union
import numpy as np
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from ..models.embedding import Embedding
from ..models.document import Document
from ..database import get_db


class EmbeddingService:
    """Service for managing CV embeddings with pgvector."""
    
    def __init__(self, session: Optional[Union[Session, AsyncSession]] = None):
        self.session = session
        
    async def store_cv_embedding(
        self,
        document_id: uuid.UUID,
        embedding_vector: Union[List[float], np.ndarray],
        model_name: str = "sentence-transformers/all-MiniLM-L12-v2",
        overwrite: bool = True
    ) -> Embedding:
        """
        Store CV embedding vector in PostgreSQL with pgvector.
        
        Args:
            document_id: UUID of the parsed document
            embedding_vector: The embedding vector (384, 768, or 1536 dimensions)
            model_name: Name of the embedding model used
            overwrite: Whether to overwrite existing embedding for same document
            
        Returns:
            Created/updated Embedding record
        """
        session = self.session or next(get_db())
        
        try:
            # Convert numpy array to list if needed
            if isinstance(embedding_vector, np.ndarray):
                embedding_vector = embedding_vector.tolist()
            
            # Validate vector dimension
            vector_dim = len(embedding_vector)
            if vector_dim not in [384, 768, 1024, 1536]:
                raise ValueError(f"Unsupported vector dimension: {vector_dim}")
            
            # Check if embedding already exists
            existing = session.query(Embedding).filter(
                Embedding.document_id == document_id
            ).first()
            
            if existing and overwrite:
                # Update existing
                existing.embedding = embedding_vector
                existing.model_name = model_name
                existing.model_dim = vector_dim
                existing.is_active = True
                session.commit()
                return existing
            elif existing and not overwrite:
                raise ValueError(f"Embedding already exists for document {document_id}")
            else:
                # Create new
                new_embedding = Embedding(
                    id=uuid.uuid4(),
                    document_id=document_id,
                    embedding=embedding_vector,
                    model_name=model_name,
                    model_dim=vector_dim,
                    is_active=True
                )
                session.add(new_embedding)
                session.commit()
                session.refresh(new_embedding)
                return new_embedding
                
        except Exception as e:
            session.rollback()
            raise e
        finally:
            if not self.session:  # Close only if we created the session
                session.close()

    async def find_similar_cvs(
        self,
        query_vector: Union[List[float], np.ndarray],
        limit: int = 10,
        similarity_threshold: float = 0.7,
        exclude_document_ids: Optional[List[uuid.UUID]] = None
    ) -> List[Tuple[Document, float]]:
        """
        Find CVs similar to the query vector using cosine similarity.
        
        Args:
            query_vector: The query embedding vector
            limit: Maximum number of results
            similarity_threshold: Minimum cosine similarity (0-1)
            exclude_document_ids: Document IDs to exclude from results
            
        Returns:
            List of (Document, similarity_score) tuples, ordered by similarity desc
        """
        session = self.session or next(get_db())
        
        try:
            # Convert numpy array to list if needed
            if isinstance(query_vector, np.ndarray):
                query_vector = query_vector.tolist()
            
            # Build exclusion clause
            exclude_clause = ""
            if exclude_document_ids:
                exclude_ids = "', '".join(str(doc_id) for doc_id in exclude_document_ids)
                exclude_clause = f"AND e.document_id NOT IN ('{exclude_ids}')"
            
            # Raw SQL query for vector similarity with pgvector
            # Using cosine similarity: 1 - (embedding <=> query_vector)
            similarity_query = text(f"""
                SELECT 
                    d.*,
                    (1 - (e.embedding <=> :query_vector)) as similarity_score
                FROM embeddings e
                INNER JOIN documents d ON e.document_id = d.id
                WHERE e.is_active = true 
                  AND (1 - (e.embedding <=> :query_vector)) >= :threshold
                  {exclude_clause}
                ORDER BY similarity_score DESC
                LIMIT :limit
            """)
            
            result = session.execute(similarity_query, {
                "query_vector": query_vector,
                "threshold": similarity_threshold,
                "limit": limit
            })
            
            # Parse results
            similar_cvs = []
            for row in result:
                # Reconstruct Document object from row data
                doc_data = dict(row._mapping)
                similarity_score = doc_data.pop('similarity_score')
                
                document = Document(**doc_data)
                similar_cvs.append((document, similarity_score))
            
            return similar_cvs
            
        except Exception as e:
            raise e
        finally:
            if not self.session:
                session.close()

    async def search_by_job_description(
        self,
        job_description_embedding: Union[List[float], np.ndarray],
        skills_filter: Optional[List[str]] = None,
        experience_years_min: Optional[int] = None,
        limit: int = 20
    ) -> List[Tuple[Document, float]]:
        """
        Find CVs that match a job description embedding.
        
        Args:
            job_description_embedding: Embedding of job description text
            skills_filter: Optional list of required skills
            experience_years_min: Minimum years of experience
            limit: Maximum results
            
        Returns:
            List of matching (Document, similarity_score) tuples
        """
        session = self.session or next(get_db())
        
        try:
            # Convert numpy array to list if needed  
            if isinstance(job_description_embedding, np.ndarray):
                job_description_embedding = job_description_embedding.tolist()
            
            # Build dynamic WHERE clauses
            additional_filters = []
            query_params = {
                "query_vector": job_description_embedding,
                "limit": limit
            }
            
            if skills_filter:
                # Assuming document has a skills JSON field we can search
                skills_condition = " OR ".join([f"d.parsed_content::text ILIKE '%{skill}%'" 
                                             for skill in skills_filter])
                additional_filters.append(f"({skills_condition})")
            
            if experience_years_min:
                # This would need custom logic based on your document structure
                additional_filters.append("d.years_experience >= :min_years")
                query_params["min_years"] = experience_years_min
            
            where_clause = " AND ".join(additional_filters)
            if where_clause:
                where_clause = f"AND {where_clause}"
            
            # Enhanced query with job matching logic
            job_match_query = text(f"""
                SELECT 
                    d.*,
                    (1 - (e.embedding <=> :query_vector)) as similarity_score,
                    -- Additional scoring factors can be added here
                    CASE 
                        WHEN d.parsed_content::text ILIKE '%senior%' THEN 1.1
                        WHEN d.parsed_content::text ILIKE '%lead%' THEN 1.05  
                        ELSE 1.0
                    END as experience_boost
                FROM embeddings e
                INNER JOIN documents d ON e.document_id = d.id  
                WHERE e.is_active = true 
                  AND (1 - (e.embedding <=> :query_vector)) >= 0.5
                  {where_clause}
                ORDER BY 
                    (similarity_score * experience_boost) DESC
                LIMIT :limit
            """)
            
            result = session.execute(job_match_query, query_params)
            
            # Parse results
            matches = []
            for row in result:
                doc_data = dict(row._mapping)
                similarity_score = doc_data.pop('similarity_score')
                doc_data.pop('experience_boost', None)  # Remove helper field
                
                document = Document(**doc_data)
                matches.append((document, similarity_score))
            
            return matches
            
        except Exception as e:
            raise e
        finally:
            if not self.session:
                session.close()

    async def get_embedding_stats(self) -> dict:
        """Get statistics about stored embeddings."""
        session = self.session or next(get_db())
        
        try:
            stats_query = text("""
                SELECT 
                    COUNT(*) as total_embeddings,
                    COUNT(DISTINCT model_name) as unique_models,
                    model_name,
                    COUNT(*) as count_per_model,
                    AVG(model_dim) as avg_dimension
                FROM embeddings 
                WHERE is_active = true
                GROUP BY model_name
            """)
            
            result = session.execute(stats_query)
            
            stats = {
                "total_active_embeddings": 0,
                "models_breakdown": []
            }
            
            for row in result:
                stats["total_active_embeddings"] += row.count_per_model
                stats["models_breakdown"].append({
                    "model_name": row.model_name,
                    "count": row.count_per_model,
                    "avg_dimension": row.avg_dimension
                })
            
            return stats
            
        except Exception as e:
            raise e
        finally:
            if not self.session:
                session.close()

    def batch_store_embeddings(
        self,
        embeddings_data: List[dict],
        batch_size: int = 100
    ) -> List[Embedding]:
        """
        Store multiple embeddings in batches for better performance.
        
        Args:
            embeddings_data: List of dicts with keys: document_id, embedding, model_name
            batch_size: Number of records per batch
            
        Returns:
            List of created Embedding objects
        """
        session = self.session or next(get_db())
        
        try:
            created_embeddings = []
            
            for i in range(0, len(embeddings_data), batch_size):
                batch = embeddings_data[i:i + batch_size]
                
                batch_embeddings = []
                for data in batch:
                    embedding_vector = data["embedding"]
                    if isinstance(embedding_vector, np.ndarray):
                        embedding_vector = embedding_vector.tolist()
                    
                    new_embedding = Embedding(
                        id=uuid.uuid4(),
                        document_id=data["document_id"],
                        embedding=embedding_vector,
                        model_name=data.get("model_name", "unknown"),
                        model_dim=len(embedding_vector),
                        is_active=True
                    )
                    batch_embeddings.append(new_embedding)
                
                session.add_all(batch_embeddings)
                session.commit()
                
                created_embeddings.extend(batch_embeddings)
                
                print(f"Stored batch {i//batch_size + 1}: {len(batch)} embeddings")
            
            return created_embeddings
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            if not self.session:
                session.close()


# Utility functions for integration with colleague's script

def embedding_from_colleague_output(
    document_id: str, 
    embedding_output: dict,
    service: Optional[EmbeddingService] = None
) -> Embedding:
    """
    Helper function to convert colleague's script output to database storage.
    
    Expected format from colleague's script:
    {
        "document_id": "uuid-string",
        "embedding": [0.1, 0.2, ...],  # or numpy array
        "model_name": "sentence-transformers/all-MiniLM-L12-v2",
        "metadata": {...}  # optional
    }
    """
    if not service:
        service = EmbeddingService()
    
    return service.store_cv_embedding(
        document_id=uuid.UUID(document_id),
        embedding_vector=embedding_output["embedding"],
        model_name=embedding_output.get("model_name", "colleague-script-v1.0")
    )