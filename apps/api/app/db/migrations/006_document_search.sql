ALTER TABLE documents
    ADD COLUMN IF NOT EXISTS search_vector tsvector
    GENERATED ALWAYS AS (
        to_tsvector(
            'english',
            coalesce(title, '') || ' ' || coalesce(extracted_text, '')
        )
    ) STORED;

CREATE INDEX IF NOT EXISTS documents_search_idx
    ON documents USING gin (search_vector);
