CREATE TABLE IF NOT EXISTS answer_cache (
    user_id UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    question_hash VARCHAR(64) NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    sources JSONB NOT NULL DEFAULT '[]'::jsonb,
    model VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, question_hash)
);

CREATE INDEX IF NOT EXISTS answer_cache_created_at_idx
    ON answer_cache (created_at);
