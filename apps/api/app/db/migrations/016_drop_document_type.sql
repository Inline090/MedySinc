-- Removes document_type entirely.
--
-- It was a five-value dropdown on the upload form, and the two lists had drifted
-- apart: the frontend offered lab_report, discharge_summary and imaging, none of
-- which the API accepted, so three of five choices failed on upload with a 422.
--
-- Rather than keep two lists that must agree, the field is gone. A prescription
-- will be understood from what is IN it - medicine, dose, date, doctor - instead
-- of a label picked at upload time. See MedSync-Future-Ideas.md.
--
-- Dropping the column also drops documents_user_type_idx, its only index.
-- Retrieval is unaffected: its citations come from document_title, selected in the
-- same join.

ALTER TABLE documents DROP COLUMN IF EXISTS document_type;