-- Migration: Add repository slug for permalinks
-- This adds slug support for repository permalink URLs

-- Add slug column to github_repos table
ALTER TABLE github_repos ADD COLUMN slug TEXT;

-- Create unique index on slug for fast lookups
CREATE UNIQUE INDEX idx_github_repos_slug ON github_repos(slug) WHERE slug IS NOT NULL;

-- Add slug column to codemirror_analyses for analysis permalinks
ALTER TABLE codemirror_analyses ADD COLUMN analysis_slug TEXT;

-- Create unique index on analysis slug
CREATE UNIQUE INDEX idx_codemirror_analyses_slug ON codemirror_analyses(analysis_slug) WHERE analysis_slug IS NOT NULL;

-- Function to generate URL-safe slug from repository name
CREATE OR REPLACE FUNCTION generate_repo_slug(repo_name TEXT, account_name TEXT DEFAULT NULL) 
RETURNS TEXT AS $$
DECLARE
    base_slug TEXT;
    final_slug TEXT;
    counter INTEGER := 0;
BEGIN
    -- Create base slug from repo name
    base_slug := lower(regexp_replace(repo_name, '[^a-zA-Z0-9\-]', '-', 'g'));
    base_slug := regexp_replace(base_slug, '-+', '-', 'g');
    base_slug := trim(both '-' from base_slug);
    
    -- If account name provided, prefix it
    IF account_name IS NOT NULL THEN
        base_slug := lower(regexp_replace(account_name, '[^a-zA-Z0-9\-]', '-', 'g')) || '-' || base_slug;
    END IF;
    
    -- Ensure uniqueness
    final_slug := base_slug;
    WHILE EXISTS (SELECT 1 FROM github_repos WHERE slug = final_slug) LOOP
        counter := counter + 1;
        final_slug := base_slug || '-' || counter;
    END LOOP;
    
    RETURN final_slug;
END;
$$ LANGUAGE plpgsql;

-- Function to generate analysis slug
CREATE OR REPLACE FUNCTION generate_analysis_slug(repo_slug TEXT, analysis_date TIMESTAMPTZ, analysis_depth TEXT DEFAULT 'standard') 
RETURNS TEXT AS $$
DECLARE
    base_slug TEXT;
    final_slug TEXT;
    counter INTEGER := 0;
    date_part TEXT;
    time_part TEXT;
BEGIN
    -- Create meaningful base slug: repo-depth-YYYYMMDD-HHMM
    date_part := to_char(analysis_date, 'YYYYMMDD');
    time_part := to_char(analysis_date, 'HH24MI');
    
    -- Handle unknown repo case
    IF repo_slug IS NULL OR repo_slug = '' THEN
        repo_slug := 'unknown-repo';
    END IF;
    
    -- Create base slug: repo-depth-date-time
    base_slug := repo_slug || '-' || analysis_depth || '-' || date_part || '-' || time_part;
    
    -- Ensure uniqueness
    final_slug := base_slug;
    WHILE EXISTS (SELECT 1 FROM codemirror_analyses WHERE analysis_slug = final_slug) LOOP
        counter := counter + 1;
        final_slug := base_slug || '-' || counter;
    END LOOP;
    
    RETURN final_slug;
END;
$$ LANGUAGE plpgsql;

-- Populate existing repository slugs
UPDATE github_repos 
SET slug = generate_repo_slug(name, (
    SELECT github_username FROM github_accounts WHERE id = github_repos.account_id
))
WHERE slug IS NULL;

-- Populate existing analysis slugs
UPDATE codemirror_analyses 
SET analysis_slug = generate_analysis_slug(
    COALESCE(
        (SELECT slug FROM github_repos WHERE id = codemirror_analyses.repo_id),
        'unknown-repo'
    ),
    created_at,
    analysis_depth
)
WHERE analysis_slug IS NULL;

-- Add trigger to auto-generate slugs for new repositories
CREATE OR REPLACE FUNCTION auto_generate_repo_slug() 
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.slug IS NULL THEN
        NEW.slug := generate_repo_slug(NEW.name, (
            SELECT github_username FROM github_accounts WHERE id = NEW.account_id
        ));
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_auto_generate_repo_slug 
    BEFORE INSERT OR UPDATE ON github_repos
    FOR EACH ROW 
    EXECUTE FUNCTION auto_generate_repo_slug();

-- Add trigger to auto-generate analysis slugs
CREATE OR REPLACE FUNCTION auto_generate_analysis_slug() 
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.analysis_slug IS NULL THEN
        NEW.analysis_slug := generate_analysis_slug(
            COALESCE(
                (SELECT slug FROM github_repos WHERE id = NEW.repo_id),
                'unknown-repo'
            ),
            NEW.created_at,
            NEW.analysis_depth
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_auto_generate_analysis_slug 
    BEFORE INSERT OR UPDATE ON codemirror_analyses
    FOR EACH ROW 
    EXECUTE FUNCTION auto_generate_analysis_slug();

-- Comments
COMMENT ON COLUMN github_repos.slug IS 'URL-safe slug for repository permalinks';
COMMENT ON COLUMN codemirror_analyses.analysis_slug IS 'URL-safe slug for analysis permalinks';
COMMENT ON FUNCTION generate_repo_slug(TEXT, TEXT) IS 'Generates unique URL-safe slug for repositories';
COMMENT ON FUNCTION generate_analysis_slug(TEXT, TIMESTAMPTZ) IS 'Generates unique URL-safe slug for analyses';