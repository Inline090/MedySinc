-- Medicines pulled out of a prescription, so the app can list them as structured
-- rows instead of leaving them buried in the extracted text.
--
-- Every field is nullable except the medicine name, because a prescription rarely
-- states all of them. A field the model could not find in the text is stored as
-- NULL rather than guessed - see app/ai/medicines.py, where a value that does not
-- appear in the source is dropped before it ever reaches here.
--
-- prescribed_on is TEXT, not DATE, and that is deliberate. The model is asked to
-- return the date as it was WRITTEN, because that is the only form the verbatim
-- check can verify. Parsing "12/03/26" into a real date is a separate problem with
-- its own ambiguities, and getting it wrong silently is worse than sorting by the
-- upload date instead.
--
-- user_id is copied onto the row the same way document_chunks does it, so the
-- medications list can filter on the row itself without trusting a join.

CREATE TABLE IF NOT EXISTS document_medicines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents (id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    hospital VARCHAR(255),
    medicine VARCHAR(255) NOT NULL,
    dose VARCHAR(160),
    frequency VARCHAR(160),
    prescribed_on VARCHAR(120),
    notes TEXT,
    source_line TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS document_medicines_user_created_idx
    ON document_medicines (user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS document_medicines_document_idx
    ON document_medicines (document_id);