CREATE TABLE IF NOT EXISTS rate_limits (
    scope VARCHAR(50) NOT NULL,
    identifier VARCHAR(255) NOT NULL,
    window_start TIMESTAMPTZ NOT NULL,
    count INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (scope, identifier, window_start)
);

CREATE INDEX IF NOT EXISTS rate_limits_window_start_idx
    ON rate_limits (window_start);
