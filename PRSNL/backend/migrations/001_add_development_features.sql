-- Migration: Add Development Content Type Features
-- Date: 2025-07-11
-- Description: Add support for development content with enhanced metadata

BEGIN;

-- 1. Add development-specific columns to items table
ALTER TABLE items 
ADD COLUMN IF NOT EXISTS programming_language TEXT,
ADD COLUMN IF NOT EXISTS project_category TEXT,
ADD COLUMN IF NOT EXISTS difficulty_level INTEGER CHECK (difficulty_level BETWEEN 1 AND 5),
ADD COLUMN IF NOT EXISTS is_career_related BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS learning_path TEXT,
ADD COLUMN IF NOT EXISTS code_snippets JSONB DEFAULT '[]';

-- 2. Create development categories table
CREATE TABLE IF NOT EXISTS development_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    icon TEXT DEFAULT '📁',
    color TEXT DEFAULT '#10b981',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Insert default development categories
INSERT INTO development_categories (name, description, icon, color) VALUES
('Documentation', 'Technical documentation and guides', '📚', '#3b82f6'),
('Tutorials', 'Learning materials and how-tos', '🎓', '#8b5cf6'),
('Code Snippets', 'Reusable code pieces', '💻', '#10b981'),
('Project Notes', 'Development project documentation', '📋', '#f59e0b'),
('Learning Paths', 'Structured learning materials', '🎯', '#ef4444'),
('Frontend', 'Frontend development resources', '🎨', '#06b6d4'),
('Backend', 'Backend development resources', '⚙️', '#6b7280'),
('DevOps', 'DevOps and infrastructure resources', '🚀', '#ec4899'),
('Mobile', 'Mobile development resources', '📱', '#14b8a6'),
('Data Science', 'Data science and analytics', '📊', '#a855f7'),
('AI/ML', 'Artificial Intelligence and Machine Learning', '🤖', '#f97316')
ON CONFLICT (name) DO NOTHING;

-- 4. Create indexes for new columns
CREATE INDEX IF NOT EXISTS idx_items_programming_language ON items(programming_language);
CREATE INDEX IF NOT EXISTS idx_items_project_category ON items(project_category);
CREATE INDEX IF NOT EXISTS idx_items_difficulty_level ON items(difficulty_level);
CREATE INDEX IF NOT EXISTS idx_items_is_career_related ON items(is_career_related);
CREATE INDEX IF NOT EXISTS idx_items_learning_path ON items(learning_path);
CREATE INDEX IF NOT EXISTS idx_items_type_category ON items(type, project_category);

-- 5. Create GIN index for code_snippets JSONB column
CREATE INDEX IF NOT EXISTS idx_items_code_snippets ON items USING gin(code_snippets);

-- 6. Update existing .md files to development type (if any exist)
UPDATE items 
SET type = 'development',
    is_career_related = CASE 
        WHEN lower(title) LIKE '%career%' OR lower(title) LIKE '%job%' OR lower(title) LIKE '%interview%' 
        THEN TRUE 
        ELSE FALSE 
    END
WHERE (url LIKE '%.md' OR url LIKE '%.markdown' OR metadata->>'file_extension' = '.md')
AND type != 'development';

-- 7. Add trigger to auto-update development categories timestamp
CREATE OR REPLACE FUNCTION update_development_categories_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER development_categories_updated_at
    BEFORE UPDATE ON development_categories
    FOR EACH ROW
    EXECUTE FUNCTION update_development_categories_timestamp();

-- 8. Create function to auto-detect programming language from content
CREATE OR REPLACE FUNCTION detect_programming_language(content_text TEXT)
RETURNS TEXT AS $$
BEGIN
    -- Simple language detection based on common patterns
    IF content_text ~* '\b(import|from|def|class|if __name__|print\()\b' THEN
        RETURN 'python';
    ELSIF content_text ~* '\b(function|const|let|var|=>|console\.log)\b' THEN
        RETURN 'javascript';
    ELSIF content_text ~* '\b(interface|type|extends|implements|console\.log)\b' THEN
        RETURN 'typescript';
    ELSIF content_text ~* '\b(public|private|static|void|System\.out)\b' THEN
        RETURN 'java';
    ELSIF content_text ~* '\b(func|package|import|fmt\.Println)\b' THEN
        RETURN 'go';
    ELSIF content_text ~* '\b(fn|let|mut|println!)\b' THEN
        RETURN 'rust';
    ELSIF content_text ~* '\b(#include|using namespace|std::)\b' THEN
        RETURN 'cpp';
    ELSIF content_text ~* '\b(SELECT|FROM|WHERE|INSERT|UPDATE)\b' THEN
        RETURN 'sql';
    ELSIF content_text ~* '\b(<!DOCTYPE|<html|<div|<script)\b' THEN
        RETURN 'html';
    ELSIF content_text ~* '\b(\$|sudo|chmod|grep|awk)\b' THEN
        RETURN 'bash';
    ELSE
        RETURN NULL;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- 9. Create function to estimate difficulty level
CREATE OR REPLACE FUNCTION estimate_difficulty_level(content_text TEXT, title_text TEXT)
RETURNS INTEGER AS $$
BEGIN
    -- Basic difficulty estimation
    IF title_text ~* '\b(beginner|intro|basic|getting started|hello world)\b' THEN
        RETURN 1;
    ELSIF title_text ~* '\b(intermediate|medium|advanced beginner)\b' THEN
        RETURN 3;
    ELSIF title_text ~* '\b(advanced|expert|master|professional)\b' THEN
        RETURN 5;
    ELSIF content_text ~* '\b(tutorial|guide|how to|step by step)\b' THEN
        RETURN 2;
    ELSIF content_text ~* '\b(architecture|design patterns|optimization|performance)\b' THEN
        RETURN 4;
    ELSE
        RETURN 2; -- Default to intermediate-beginner
    END IF;
END;
$$ LANGUAGE plpgsql;

-- 10. Create trigger to auto-populate development metadata
CREATE OR REPLACE FUNCTION auto_populate_development_metadata()
RETURNS TRIGGER AS $$
BEGIN
    -- Only process if this is a development type item
    IF NEW.type = 'development' THEN
        -- Auto-detect programming language if not set
        IF NEW.programming_language IS NULL AND NEW.processed_content IS NOT NULL THEN
            NEW.programming_language = detect_programming_language(NEW.processed_content);
        END IF;
        
        -- Auto-estimate difficulty if not set
        IF NEW.difficulty_level IS NULL THEN
            NEW.difficulty_level = estimate_difficulty_level(
                COALESCE(NEW.processed_content, ''), 
                NEW.title
            );
        END IF;
        
        -- Auto-detect if career related
        IF NEW.is_career_related IS FALSE THEN
            NEW.is_career_related = (
                NEW.title ~* '\b(career|job|interview|resume|linkedin|professional|work|employment)\b' OR
                COALESCE(NEW.processed_content, '') ~* '\b(career|job|interview|resume|professional development)\b'
            );
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER items_auto_development_metadata
    BEFORE INSERT OR UPDATE ON items
    FOR EACH ROW
    EXECUTE FUNCTION auto_populate_development_metadata();

COMMIT;

-- Verify the migration
SELECT 'Migration completed successfully' as status;