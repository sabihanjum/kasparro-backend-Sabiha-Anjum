-- Migration: Add entity unification fields to normalized_data table
-- Date: 2025-12-24
-- Description: Adds entity_id and content_hash fields for cross-source duplicate detection

-- Add new columns
ALTER TABLE normalized_data 
ADD COLUMN IF NOT EXISTS entity_id VARCHAR(64),
ADD COLUMN IF NOT EXISTS content_hash VARCHAR(64);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS ix_normalized_data_entity_id ON normalized_data(entity_id);
CREATE INDEX IF NOT EXISTS ix_normalized_data_content_hash ON normalized_data(content_hash);

-- Add unique constraint on source + source_id
ALTER TABLE normalized_data 
ADD CONSTRAINT IF NOT EXISTS uix_source_source_id UNIQUE (source, source_id);

-- Backfill entity_id and content_hash for existing records
-- This generates entity_id based on a hash of title and content
UPDATE normalized_data 
SET 
    content_hash = encode(sha256(
        COALESCE(
            lower(regexp_replace(data->>'title', '\s+', ' ', 'g')) || '|' || 
            left(lower(regexp_replace(COALESCE(data->>'content', data->>'description', ''), '\s+', ' ', 'g')), 500),
            ''
        )::bytea
    ), 'hex'),
    entity_id = 'entity_' || substring(encode(sha256(
        COALESCE(
            lower(regexp_replace(data->>'title', '\s+', ' ', 'g')) || '|' || 
            left(lower(regexp_replace(COALESCE(data->>'content', data->>'description', ''), '\s+', ' ', 'g')), 500),
            ''
        )::bytea
    ), 'hex'), 1, 16)
WHERE entity_id IS NULL OR content_hash IS NULL;

-- Make columns NOT NULL after backfill
ALTER TABLE normalized_data 
ALTER COLUMN entity_id SET NOT NULL,
ALTER COLUMN content_hash SET NOT NULL;

-- Verify migration
DO $$
DECLARE
    entity_count INTEGER;
    duplicate_count INTEGER;
BEGIN
    SELECT COUNT(DISTINCT entity_id) INTO entity_count FROM normalized_data;
    SELECT COUNT(*) - COUNT(DISTINCT entity_id) INTO duplicate_count FROM normalized_data;
    
    RAISE NOTICE 'Migration complete: % unique entities, % cross-source duplicates detected', 
        entity_count, duplicate_count;
END $$;
