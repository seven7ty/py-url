CREATE TABLE IF NOT EXISTS links (
    slug VARCHAR(55),
    link VARCHAR(105),
    visits INTEGER,
    created_at TIMESTAMPTZ
)