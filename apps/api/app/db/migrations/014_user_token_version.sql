-- Revocation support. Every token carries the value of this column at the moment
-- it was minted. The auth middleware refuses a token whose version no longer
-- matches, so bumping it on logout ends every existing session for that user.
--
-- DEFAULT 0 means the column is populated for existing rows, and tokens issued
-- before this migration carry no version claim - which reads as 0 and therefore
-- still works. Nobody is logged out by adding this.
ALTER TABLE users
    ADD COLUMN IF NOT EXISTS token_version INTEGER NOT NULL DEFAULT 0;