-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm" SCHEMA public;

-- Set up full-text search configuration
CREATE TEXT SEARCH CONFIGURATION IF NOT EXISTS english_unaccent ( COPY = english );

-- Create unaccent dictionary if needed (for better search)
-- This handles accented characters in search