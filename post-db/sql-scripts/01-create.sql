DO $$ 
BEGIN 
    RAISE NOTICE '--- Starting Data Insertion ---';
END $$;

\echo 'Creating database: {{DB_NAME}} and tables ...'

CREATE DATABASE "{{DB_NAME}}";
\c "{{DB_NAME}}";

\echo 'Creating read/write db user: {{DB_USER}} ...'
DROP ROLE IF EXISTS "{{DB_USER}}";

CREATE ROLE "{{DB_USER}}" WITH LOGIN PASSWORD '{{DB_PASSWORD}}';

-- Fait par ChatGPT (Samuel Baribault) --

GRANT CONNECT ON DATABASE "{{DB_NAME}}" TO "{{DB_USER}}";
GRANT USAGE ON SCHEMA public TO "{{DB_USER}}";

-- Existing objectsWITH LOGIN PASSWORD
GRANT SELECT, INSERT, UPDATE, DELETE
  ON ALL TABLES IN SCHEMA public
  TO "{{DB_USER}}";

GRANT USAGE, SELECT
  ON ALL SEQUENCES IN SCHEMA public
  TO "{{DB_USER}}";

-- Future objects (IMPORTANT)
ALTER DEFAULT PRIVILEGES FOR ROLE postgres
IN SCHEMA public
GRANT SELECT, INSERT, UPDATE, DELETE
ON TABLES TO "{{DB_USER}}";

ALTER DEFAULT PRIVILEGES FOR ROLE postgres
IN SCHEMA public
GRANT USAGE, SELECT
ON SEQUENCES TO "{{DB_USER}}";

-- Fin ChatGPT --
\echo 'User {{DB_USER}} created.'


-- Schéma communautaire Saint-Roch. Dates stockées en UTC (TIMESTAMPTZ).
CREATE TABLE IF NOT EXISTS post (
    id UUID PRIMARY KEY,
    user_id VARCHAR(128) NOT NULL,
    title VARCHAR(128) NOT NULL CHECK (char_length(title) BETWEEN 3 AND 128),
    description VARCHAR(5000) NOT NULL CHECK (char_length(description) BETWEEN 1 AND 5000),
    content_type VARCHAR(32) NOT NULL DEFAULT 'publication',
    location VARCHAR(256),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    starts_at TIMESTAMPTZ,
    ends_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMPTZ,
    closed_at TIMESTAMPTZ,
    CONSTRAINT post_type_check CHECK (content_type IN ('publication', 'event', 'urban_alert', 'safety_alert')),
    CONSTRAINT post_coordinate_pair CHECK ((latitude IS NULL) = (longitude IS NULL)),
    CONSTRAINT post_coordinate_range CHECK (latitude BETWEEN -90 AND 90 AND longitude BETWEEN -180 AND 180),
    CONSTRAINT post_required_coordinates CHECK (content_type = 'publication' OR latitude IS NOT NULL),
    CONSTRAINT post_event_dates CHECK (
        (content_type = 'event' AND starts_at IS NOT NULL AND ends_at IS NOT NULL AND ends_at > starts_at)
        OR (content_type <> 'event' AND starts_at IS NULL AND ends_at IS NULL)),
    CONSTRAINT post_alert_lifecycle CHECK (
        (content_type IN ('urban_alert', 'safety_alert') AND expires_at IS NOT NULL AND expires_at > created_at)
        OR (content_type NOT IN ('urban_alert', 'safety_alert') AND expires_at IS NULL AND closed_at IS NULL))
);
CREATE INDEX IF NOT EXISTS ix_post_user_id ON post(user_id);
CREATE INDEX IF NOT EXISTS ix_post_created_at ON post(created_at);
CREATE INDEX IF NOT EXISTS ix_post_content_type_expires_at ON post(content_type, expires_at);

CREATE TABLE IF NOT EXISTS image (
    id UUID PRIMARY KEY,
    post_id UUID NOT NULL REFERENCES post(id) ON DELETE CASCADE,
    image_index INTEGER NOT NULL CHECK (image_index BETWEEN 0 AND 10),
    image_path TEXT UNIQUE NOT NULL,
    UNIQUE (post_id, image_index)
);

-- Une alerte expire après 2h même lors d'une insertion SQL directe.
CREATE OR REPLACE FUNCTION set_post_alert_expiration() RETURNS trigger AS $$
BEGIN
    IF NEW.content_type IN ('urban_alert', 'safety_alert') AND NEW.expires_at IS NULL THEN
        NEW.expires_at := NEW.created_at + INTERVAL '2 hours';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
DROP TRIGGER IF EXISTS post_alert_expiration ON post;
CREATE TRIGGER post_alert_expiration BEFORE INSERT ON post
    FOR EACH ROW EXECUTE FUNCTION set_post_alert_expiration();

\echo 'Database {{DB_NAME}} created'

DO $$ 
BEGIN 
    RAISE NOTICE '--- Data Insertion Complete ---';
END $$;
