ALTER TABLE documents
    ADD COLUMN IF NOT EXISTS content_hash VARCHAR(64);

CREATE UNIQUE INDEX IF NOT EXISTS documents_user_content_hash_idx
    ON documents (user_id, content_hash);
