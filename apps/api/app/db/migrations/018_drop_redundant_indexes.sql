-- Drops two indexes that no query in the app needs.
--
-- document_chunks_document_id_idx
--   003 created this alongside UNIQUE (document_id, chunk_index). The composite
--   index already answers WHERE document_id = ?, because the first column of a
--   composite index can be used on its own. So this was a second copy of the same
--   entries, maintained on every insert, that no plan ever chose.
--   Both callers stay served: replace_document_chunks (DELETE ... WHERE
--   document_id = $1) and find_chunks_for_document (WHERE document_id = $1
--   ORDER BY chunk_index), the second of which now gets its ORDER BY from the
--   composite index for free.
--
-- answer_cache_created_at_idx
--   011 created this expecting a TTL sweep over created_at, but nothing queries
--   that column on its own:
--     - the lookup is WHERE user_id = $1 AND question_hash = $2 AND created_at > ...
--       which the primary key (user_id, question_hash) serves, testing created_at
--       against the single row it finds;
--     - invalidation is DELETE FROM answer_cache WHERE user_id = $1, also the
--       primary key.
--   The index was never read.
--
-- Both are recoverable - the CREATE statements still exist in 003 and 011.

DROP INDEX IF EXISTS document_chunks_document_id_idx;
DROP INDEX IF EXISTS answer_cache_created_at_idx;
