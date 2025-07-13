-- Migration: Add Repository Metadata Support
-- Description: Extends items table to support repository collection with AI auto-categorization
-- Date: 2025-07-13
-- Version: 016

-- Add repository metadata column to existing items table
ALTER TABLE items ADD COLUMN IF NOT EXISTS repository_metadata JSONB DEFAULT NULL;

-- Add index for repository metadata queries
CREATE INDEX IF NOT EXISTS idx_items_repository_metadata ON items USING GIN (repository_metadata);

-- Add index for repository-specific searches
CREATE INDEX IF NOT EXISTS idx_items_repository_url ON items ((repository_metadata->>'repo_url')) WHERE repository_metadata IS NOT NULL;

-- Add index for tech stack searches
CREATE INDEX IF NOT EXISTS idx_items_tech_stack ON items USING GIN ((repository_metadata->'tech_stack')) WHERE repository_metadata IS NOT NULL;

-- Add constraint to ensure repository_metadata structure
ALTER TABLE items ADD CONSTRAINT check_repository_metadata_structure 
CHECK (
    repository_metadata IS NULL OR (
        repository_metadata ? 'repo_url' AND 
        jsonb_typeof(repository_metadata->'repo_url') = 'string'
    )
);

-- Create helper function to check if item is a repository
CREATE OR REPLACE FUNCTION is_repository_item(item_row items)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN item_row.repository_metadata IS NOT NULL AND 
           item_row.repository_metadata ? 'repo_url';
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Create helper function to get repository tech stack
CREATE OR REPLACE FUNCTION get_repository_tech_stack(repo_metadata JSONB)
RETURNS TEXT[] AS $$
BEGIN
    IF repo_metadata IS NULL OR NOT (repo_metadata ? 'tech_stack') THEN
        RETURN ARRAY[]::TEXT[];
    END IF;
    
    RETURN ARRAY(
        SELECT jsonb_array_elements_text(repo_metadata->'tech_stack')
    );
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Create helper function to extract repository name from URL
CREATE OR REPLACE FUNCTION extract_repo_name(repo_url TEXT)
RETURNS TEXT AS $$
BEGIN
    -- Extract repository name from GitHub/GitLab URLs
    -- Example: https://github.com/owner/repo -> repo
    RETURN regexp_replace(repo_url, '^.*/([^/]+)/?$', '\1');
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Create view for repository items only
CREATE OR REPLACE VIEW repository_items AS
SELECT 
    i.*,
    repository_metadata->>'repo_url' as repo_url,
    repository_metadata->>'repo_name' as repo_name,
    repository_metadata->>'owner' as repo_owner,
    repository_metadata->>'language' as primary_language,
    COALESCE((repository_metadata->>'stars')::INTEGER, 0) as stars,
    repository_metadata->>'license' as license,
    repository_metadata->'tech_stack' as tech_stack,
    repository_metadata->>'use_case' as use_case,
    repository_metadata->>'difficulty' as difficulty,
    repository_metadata->'ai_analysis' as ai_analysis
FROM items i
WHERE repository_metadata IS NOT NULL 
  AND repository_metadata ? 'repo_url';

-- Add comments for documentation
COMMENT ON COLUMN items.repository_metadata IS 'JSONB column storing repository-specific metadata including tech stack, analysis, and GitHub data';
COMMENT ON INDEX idx_items_repository_metadata IS 'GIN index for efficient repository metadata queries';
COMMENT ON VIEW repository_items IS 'View providing easy access to repository items with extracted metadata fields';

-- Create function to update repository search vector with tech stack
CREATE OR REPLACE FUNCTION update_repository_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    -- If this is a repository item, include tech stack in search vector
    IF NEW.repository_metadata IS NOT NULL AND NEW.repository_metadata ? 'tech_stack' THEN
        DECLARE
            tech_stack_text TEXT;
            use_case_text TEXT;
            ai_description TEXT;
        BEGIN
            -- Extract tech stack as searchable text
            SELECT string_agg(value, ' ') INTO tech_stack_text
            FROM jsonb_array_elements_text(NEW.repository_metadata->'tech_stack') AS value;
            
            -- Extract use case
            use_case_text := NEW.repository_metadata->>'use_case';
            
            -- Extract AI analysis description
            ai_description := NEW.repository_metadata->'ai_analysis'->>'purpose';
            
            -- Update search vector to include repository-specific terms
            NEW.search_vector := to_tsvector('english', 
                COALESCE(NEW.title, '') || ' ' ||
                COALESCE(NEW.summary, '') || ' ' ||
                COALESCE(NEW.content, '') || ' ' ||
                COALESCE(tech_stack_text, '') || ' ' ||
                COALESCE(use_case_text, '') || ' ' ||
                COALESCE(ai_description, '') || ' ' ||
                COALESCE(NEW.repository_metadata->>'repo_name', '') || ' ' ||
                COALESCE(NEW.repository_metadata->>'language', '')
            );
        END;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically update search vector for repositories
CREATE TRIGGER update_repository_search_vector_trigger
    BEFORE INSERT OR UPDATE OF repository_metadata, title, summary, content
    ON items
    FOR EACH ROW
    WHEN (NEW.repository_metadata IS NOT NULL)
    EXECUTE FUNCTION update_repository_search_vector();

-- Sample repository metadata structure (for documentation)
/*
Example repository_metadata JSONB structure:
{
  "repo_url": "https://github.com/facebook/react",
  "repo_name": "react",
  "owner": "facebook",
  "description": "The library for web and native user interfaces",
  "stars": 230000,
  "forks": 47000,
  "language": "JavaScript",
  "tech_stack": ["javascript", "react", "frontend", "ui"],
  "use_case": "ui-framework",
  "category": "frontend",
  "difficulty": "intermediate",
  "license": "MIT",
  "topics": ["react", "javascript", "library", "ui"],
  "last_updated": "2025-07-13T10:30:00Z",
  "ai_analysis": {
    "purpose": "A JavaScript library for building user interfaces",
    "key_features": ["component-based", "virtual-dom", "declarative"],
    "learning_curve": "moderate",
    "community_size": "very-large",
    "maintenance_status": "active",
    "confidence": 0.95,
    "generated_at": "2025-07-13T10:30:00Z"
  },
  "github_data": {
    "created_at": "2013-05-24T16:15:54Z",
    "updated_at": "2025-07-13T10:30:00Z",
    "has_wiki": true,
    "has_issues": true,
    "open_issues": 842,
    "default_branch": "main"
  }
}
*/