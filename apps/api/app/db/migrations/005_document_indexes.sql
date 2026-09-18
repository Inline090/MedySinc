CREATE INDEX IF NOT EXISTS documents_user_created_idx
    ON documents (user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS documents_user_type_idx
    ON documents (user_id, document_type);

CREATE INDEX IF NOT EXISTS documents_tags_idx
    ON documents USING gin (tags);
