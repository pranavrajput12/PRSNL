-- Migration: Add Open Source Integrations Feature
-- Description: Creates tables for tracking, analyzing, and managing open source integrations
-- Date: 2025-07-13
-- Version: 015

-- Main table for open source integrations
CREATE TABLE IF NOT EXISTS open_source_integrations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    item_id UUID REFERENCES items(id) ON DELETE CASCADE,
    
    -- Repository Information
    repository_url TEXT NOT NULL,
    repository_name TEXT NOT NULL,
    owner_name TEXT NOT NULL,
    repository_full_name TEXT, -- e.g., "facebook/react"
    
    -- Package Information
    package_name TEXT,
    package_manager TEXT, -- 'npm', 'pip', 'cargo', 'maven', 'composer', 'gem', etc.
    package_version TEXT,
    latest_version TEXT,
    
    -- Integration Status & Classification
    integration_status TEXT DEFAULT 'discovered', -- 'discovered', 'evaluated', 'integrated', 'deprecated', 'archived'
    integration_confidence FLOAT DEFAULT 0.0, -- AI confidence score (0-1)
    technology_stack TEXT[], -- ['frontend', 'backend', 'ai', 'database', 'devops', etc.]
    primary_language TEXT,
    secondary_languages TEXT[],
    
    -- GitHub/Repository Metadata
    stars INTEGER DEFAULT 0,
    forks INTEGER DEFAULT 0,
    watchers INTEGER DEFAULT 0,
    open_issues INTEGER DEFAULT 0,
    contributors_count INTEGER DEFAULT 0,
    last_commit_date TIMESTAMPTZ,
    created_date TIMESTAMPTZ,
    license_type TEXT,
    license_url TEXT,
    
    -- AI Analysis Results
    description TEXT,
    ai_generated_summary TEXT,
    use_cases TEXT[], -- ['state-management', 'routing', 'ui-components', etc.]
    categories TEXT[], -- ['framework', 'library', 'tool', 'utility', etc.]
    
    -- Quality & Risk Assessment (AI-powered scores 0-1)
    quality_score FLOAT DEFAULT 0.0,
    security_score FLOAT DEFAULT 0.0,
    maintenance_score FLOAT DEFAULT 0.0,
    community_score FLOAT DEFAULT 0.0,
    documentation_score FLOAT DEFAULT 0.0,
    performance_score FLOAT DEFAULT 0.0,
    popularity_score FLOAT DEFAULT 0.0,
    
    -- Integration Analysis
    integration_complexity TEXT, -- 'low', 'medium', 'high'
    bundle_size_impact TEXT, -- 'minimal', 'moderate', 'significant'
    learning_curve TEXT, -- 'easy', 'moderate', 'steep'
    alternatives TEXT[], -- List of alternative packages
    
    -- Security & Vulnerability Info
    has_vulnerabilities BOOLEAN DEFAULT FALSE,
    vulnerability_count INTEGER DEFAULT 0,
    last_security_audit TIMESTAMPTZ,
    security_advisories JSONB DEFAULT '[]',
    
    -- Compatibility & Dependencies
    node_version_required TEXT,
    python_version_required TEXT,
    peer_dependencies JSONB DEFAULT '{}',
    breaking_changes_history JSONB DEFAULT '[]',
    
    -- Usage & Analytics
    weekly_downloads BIGINT DEFAULT 0,
    monthly_downloads BIGINT DEFAULT 0,
    download_trend TEXT, -- 'growing', 'stable', 'declining'
    github_topics TEXT[],
    
    -- AI Insights & Recommendations
    ai_recommendation TEXT, -- 'recommended', 'conditional', 'not_recommended'
    ai_recommendation_reason TEXT,
    ai_integration_notes TEXT,
    similar_projects UUID[], -- References to other integrations
    
    -- Tracking
    discovery_method TEXT, -- 'automatic', 'manual', 'imported', 'suggested'
    discovery_source TEXT, -- 'content_analysis', 'package_json', 'requirements_txt', 'user_input'
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_analyzed TIMESTAMPTZ,
    analysis_version INTEGER DEFAULT 1,
    
    -- Indexes for performance
    UNIQUE(repository_url, item_id),
    UNIQUE(package_name, package_manager, item_id) -- Allow same package but different managers
);

-- Integration dependencies relationship table
CREATE TABLE IF NOT EXISTS integration_dependencies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    integration_id UUID REFERENCES open_source_integrations(id) ON DELETE CASCADE,
    
    -- Dependency Information
    dependency_name TEXT NOT NULL,
    dependency_version TEXT,
    dependency_type TEXT NOT NULL, -- 'direct', 'peer', 'dev', 'optional'
    dependency_manager TEXT, -- 'npm', 'pip', etc.
    
    -- Dependency Analysis
    is_security_critical BOOLEAN DEFAULT FALSE,
    is_deprecated BOOLEAN DEFAULT FALSE,
    has_alternatives BOOLEAN DEFAULT FALSE,
    update_urgency TEXT, -- 'low', 'medium', 'high', 'critical'
    
    -- Tracking
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(integration_id, dependency_name, dependency_type)
);

-- Integration usage patterns and code snippets
CREATE TABLE IF NOT EXISTS integration_usage_patterns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    integration_id UUID REFERENCES open_source_integrations(id) ON DELETE CASCADE,
    
    -- Pattern Information
    pattern_type TEXT NOT NULL, -- 'import_pattern', 'configuration', 'api_usage', 'setup'
    pattern_name TEXT,
    pattern_content TEXT NOT NULL,
    code_language TEXT, -- 'javascript', 'typescript', 'python', etc.
    
    -- Pattern Analysis
    complexity_level TEXT, -- 'beginner', 'intermediate', 'advanced'
    frequency_score FLOAT DEFAULT 0.0, -- How commonly this pattern is used (0-1)
    is_best_practice BOOLEAN DEFAULT FALSE,
    performance_impact TEXT, -- 'minimal', 'moderate', 'significant'
    
    -- Context
    use_case_context TEXT,
    framework_context TEXT, -- 'react', 'vue', 'angular', 'django', etc.
    
    -- Tracking
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    INDEX(integration_id, pattern_type),
    INDEX(code_language, complexity_level)
);

-- Integration reviews and user feedback
CREATE TABLE IF NOT EXISTS integration_reviews (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    integration_id UUID REFERENCES open_source_integrations(id) ON DELETE CASCADE,
    
    -- Review Information
    reviewer_type TEXT DEFAULT 'ai', -- 'ai', 'user', 'expert'
    rating FLOAT CHECK (rating >= 0 AND rating <= 5), -- 1-5 star rating
    review_title TEXT,
    review_content TEXT,
    
    -- Review Categories
    ease_of_use_rating FLOAT CHECK (ease_of_use_rating >= 0 AND ease_of_use_rating <= 5),
    documentation_rating FLOAT CHECK (documentation_rating >= 0 AND documentation_rating <= 5),
    performance_rating FLOAT CHECK (performance_rating >= 0 AND performance_rating <= 5),
    community_support_rating FLOAT CHECK (community_support_rating >= 0 AND community_support_rating <= 5),
    
    -- Review Context
    project_context TEXT, -- Description of project where this was used
    integration_duration TEXT, -- How long this integration was used
    would_recommend BOOLEAN,
    
    -- Tracking
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    INDEX(integration_id, reviewer_type),
    INDEX(rating, would_recommend)
);

-- Integration comparison matrix for alternatives
CREATE TABLE IF NOT EXISTS integration_comparisons (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    primary_integration_id UUID REFERENCES open_source_integrations(id) ON DELETE CASCADE,
    alternative_integration_id UUID REFERENCES open_source_integrations(id) ON DELETE CASCADE,
    
    -- Comparison Analysis
    comparison_type TEXT DEFAULT 'alternative', -- 'alternative', 'complementary', 'competing'
    similarity_score FLOAT DEFAULT 0.0, -- How similar these integrations are (0-1)
    
    -- Comparison Categories
    performance_comparison TEXT, -- 'better', 'similar', 'worse'
    ease_of_use_comparison TEXT,
    documentation_comparison TEXT,
    community_comparison TEXT,
    bundle_size_comparison TEXT,
    
    -- Decision Factors
    key_differences TEXT[],
    migration_difficulty TEXT, -- 'easy', 'moderate', 'difficult'
    migration_notes TEXT,
    
    -- AI Analysis
    ai_recommendation TEXT, -- Which one AI recommends and why
    ai_analysis_confidence FLOAT DEFAULT 0.0,
    
    -- Tracking
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(primary_integration_id, alternative_integration_id),
    CHECK(primary_integration_id != alternative_integration_id)
);

-- Integration analytics and metrics
CREATE TABLE IF NOT EXISTS integration_analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    integration_id UUID REFERENCES open_source_integrations(id) ON DELETE CASCADE,
    
    -- Time-based metrics
    metric_date DATE NOT NULL,
    
    -- Download metrics
    daily_downloads BIGINT DEFAULT 0,
    weekly_downloads BIGINT DEFAULT 0,
    monthly_downloads BIGINT DEFAULT 0,
    
    -- Repository metrics
    stars_count INTEGER DEFAULT 0,
    forks_count INTEGER DEFAULT 0,
    issues_count INTEGER DEFAULT 0,
    contributors_count INTEGER DEFAULT 0,
    
    -- Version metrics
    version_at_date TEXT,
    releases_last_30_days INTEGER DEFAULT 0,
    commits_last_30_days INTEGER DEFAULT 0,
    
    -- Community metrics
    stackoverflow_questions INTEGER DEFAULT 0,
    blog_mentions INTEGER DEFAULT 0,
    tutorial_count INTEGER DEFAULT 0,
    
    -- Tracking
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(integration_id, metric_date),
    INDEX(integration_id, metric_date DESC)
);

-- Indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_integrations_technology_stack ON open_source_integrations USING GIN (technology_stack);
CREATE INDEX IF NOT EXISTS idx_integrations_use_cases ON open_source_integrations USING GIN (use_cases);
CREATE INDEX IF NOT EXISTS idx_integrations_categories ON open_source_integrations USING GIN (categories);
CREATE INDEX IF NOT EXISTS idx_integrations_quality_scores ON open_source_integrations (quality_score, security_score, maintenance_score);
CREATE INDEX IF NOT EXISTS idx_integrations_popularity ON open_source_integrations (stars, monthly_downloads, popularity_score);
CREATE INDEX IF NOT EXISTS idx_integrations_status ON open_source_integrations (integration_status, ai_recommendation);
CREATE INDEX IF NOT EXISTS idx_integrations_language ON open_source_integrations (primary_language, package_manager);
CREATE INDEX IF NOT EXISTS idx_integrations_discovery ON open_source_integrations (discovery_method, discovery_source, created_at);

-- Triggers for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_integrations_updated_at BEFORE UPDATE ON open_source_integrations
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_dependencies_updated_at BEFORE UPDATE ON integration_dependencies
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_patterns_updated_at BEFORE UPDATE ON integration_usage_patterns
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_reviews_updated_at BEFORE UPDATE ON integration_reviews
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_comparisons_updated_at BEFORE UPDATE ON integration_comparisons
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Add helpful comments
COMMENT ON TABLE open_source_integrations IS 'Comprehensive tracking and analysis of open source integrations with AI-powered insights';
COMMENT ON TABLE integration_dependencies IS 'Dependencies and their relationships for each integration';
COMMENT ON TABLE integration_usage_patterns IS 'Code patterns, configurations, and usage examples for integrations';
COMMENT ON TABLE integration_reviews IS 'Reviews and ratings for integrations from AI analysis and users';
COMMENT ON TABLE integration_comparisons IS 'Comparative analysis between similar or alternative integrations';
COMMENT ON TABLE integration_analytics IS 'Time-series metrics and analytics for integration popularity and health';