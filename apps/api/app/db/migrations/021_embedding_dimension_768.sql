-- Swaps the embedding model from bge-m3 (1024) to GTE-ModernBERT (768).
-- The vector column and its HNSW index are tied to the model's dimension, so
-- both have to be rebuilt. Every stored vector is re-ingested afterwards.
DROP INDEX IF EXISTS document_chunks_embedding_hnsw_idx;

ALTER TABLE document_chunks
    ALTER COLUMN embedding TYPE vector(768);

CREATE INDEX IF NOT EXISTS document_chunks_embedding_hnsw_idx
    ON document_chunks USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);