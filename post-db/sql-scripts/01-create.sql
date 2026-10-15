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


CREATE TABLE damage_state (
    id UUID PRIMARY KEY,
    name VARCHAR(64) UNIQUE NOT NULL
);

CREATE TABLE sold_state (
    id UUID PRIMARY KEY,
    name VARCHAR(64) UNIQUE NOT NULL
);

CREATE TABLE shipping_offer (
    id UUID PRIMARY KEY,
    name VARCHAR(64) UNIQUE NOT NULL,
    delivery_offer BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE listing (
    id UUID PRIMARY KEY,
    vendor_id VARCHAR(28) NOT NULL,
    book_id VARCHAR(12) NOT NULL,
    title VARCHAR(128) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    damage_state_id UUID REFERENCES damage_state(id),
    sold_state_id UUID REFERENCES sold_state(id),
    shipping_offer_id UUID REFERENCES shipping_offer(id),
    location VARCHAR(128) NOT NULL DEFAULT 'Unknown',
    is_annoted BOOLEAN NOT NULL DEFAULT FALSE,
    seller_rep SMALLINT NOT NULL DEFAULT 0,
    buyer VARCHAR(28) NULL DEFAULT NULL,
    book_categories TEXT[] DEFAULT '{}',
    view_count INT NOT NULL DEFAULT 0
);

CREATE TABLE listing_view (
    listing_id UUID NOT NULL REFERENCES listing(id) ON DELETE CASCADE,
    user_id VARCHAR(28) NOT NULL,
    PRIMARY KEY (listing_id, user_id)
);

CREATE TABLE image (
    id UUID PRIMARY KEY,
    listing_id UUID REFERENCES listing(id) ON DELETE CASCADE,
    image_index SMALLINT NOT NULL,
    image_path TEXT UNIQUE NOT NULL,
    UNIQUE (listing_id, image_index)
);

\echo 'Database {{DB_NAME}} created'

DO $$ 
BEGIN 
    RAISE NOTICE '--- Data Insertion Complete ---';
END $$;
