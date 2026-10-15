DO $$ 
BEGIN 
    RAISE NOTICE '--- Starting Releases DB Creation ---';
END $$;

\echo 'Creating database: {{RELEASES_DB_NAME}} ...'

CREATE DATABASE "{{RELEASES_DB_NAME}}";
\c "{{RELEASES_DB_NAME}}";

\echo 'Creating read/write db user: {{RELEASES_DB_USER}} ...'
DROP ROLE IF EXISTS "{{RELEASES_DB_USER}}";

CREATE ROLE "{{RELEASES_DB_USER}}" WITH LOGIN PASSWORD '{{RELEASES_DB_PASSWORD}}';

GRANT CONNECT ON DATABASE "{{RELEASES_DB_NAME}}" TO "{{RELEASES_DB_USER}}";
GRANT USAGE ON SCHEMA public TO "{{RELEASES_DB_USER}}";

-- Existing objects
GRANT SELECT, INSERT, UPDATE, DELETE
  ON ALL TABLES IN SCHEMA public
  TO "{{RELEASES_DB_USER}}";

GRANT USAGE, SELECT
  ON ALL SEQUENCES IN SCHEMA public
  TO "{{RELEASES_DB_USER}}";

-- Future objects (IMPORTANT)
ALTER DEFAULT PRIVILEGES FOR ROLE postgres
IN SCHEMA public
GRANT SELECT, INSERT, UPDATE, DELETE
ON TABLES TO "{{RELEASES_DB_USER}}";

ALTER DEFAULT PRIVILEGES FOR ROLE postgres
IN SCHEMA public
GRANT USAGE, SELECT
ON SEQUENCES TO "{{RELEASES_DB_USER}}";

\echo 'User {{RELEASES_DB_USER}} created.'

 
CREATE TABLE releases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    package_name VARCHAR(255) NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    version_code INTEGER NOT NULL,
    version_name VARCHAR(15) NOT NULL,
    min_sdk INTEGER,
    changelog TEXT,
    download_count INTEGER DEFAULT 0,
    is_critical BOOLEAN DEFAULT FALSE,
    is_processed BOOLEAN DEFAULT FALSE,
    file_size DECIMAL(5,2),
    checksum_sha256 VARCHAR(64),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(package_name, version_code),
    UNIQUE(checksum_sha256)
);


\echo 'Database {{RELEASES_DB_NAME}} created'

DO $$ 
BEGIN 
    RAISE NOTICE '--- Releases DB Creation Complete ---';
END $$;
