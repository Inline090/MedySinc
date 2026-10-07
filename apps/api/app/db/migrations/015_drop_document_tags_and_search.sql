-- Removes the two document-list filters that were never wired to a client.
--
-- 006 added search_vector (a generated tsvector over title + extracted_text) plus
-- a GIN index, and 002 created the tags TEXT[] column plus a GIN index. Both
-- backed optional query parameters on GET /documents that no caller ever sent -
-- the frontend lists documents with no filters at all.
--
-- Dropping a column also drops every index on it, so documents_search_idx and
-- documents_tags_idx disappear with these two statements.
--
-- Nothing else reads either column. Retrieval searches document_chunks.tsv, a
-- different column in a different table, so hybrid search is untouched.

ALTER TABLE documents DROP COLUMN IF EXISTS search_vector;

ALTER TABLE documents DROP COLUMN IF EXISTS tags;
