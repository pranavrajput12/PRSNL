-- Dreamscape Feature: Personal Intelligence System
-- Date: 2025-07-28
-- Purpose: Add tables for user behavior tracking, persona development, and intelligent suggestions

-- =====================================================
-- USER BEHAVIOR TRACKING
-- =====================================================

-- User behaviors table for tracking all interactions
CREATE TABLE IF NOT EXISTS user_behaviors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    action_type VARCHAR(50) NOT NULL, -- 'view', 'save', 'tag', 'share', 'search', 'filter', 'navigate'
    item_id UUID REFERENCES items(id) ON DELETE CASCADE,
    item_type VARCHAR(50), -- 'article', 'video', 'code', etc.
    context JSONB DEFAULT '{}', -- Additional context like search terms, filters, referrer
    duration_seconds INTEGER, -- How long they engaged with content
    metadata JSONB DEFAULT '{}', -- Device info, location (if permitted), etc.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT fk_user_behaviors_item FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
);

-- Indexes for user behaviors
CREATE INDEX idx_behaviors_user_action ON user_behaviors(user_id, action_type, created_at DESC);
CREATE INDEX idx_behaviors_item ON user_behaviors(item_id, action_type);
CREATE INDEX idx_behaviors_created ON user_behaviors(created_at DESC);

-- =====================================================
-- USER PERSONAS
-- =====================================================

-- User personas table for storing multi-dimensional profiles
CREATE TABLE IF NOT EXISTS user_personas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE NOT NULL,
    
    -- Technical Profile
    technical_profile JSONB DEFAULT '{}', -- {
        -- "primary_languages": ["Python", "JavaScript"],
        -- "skill_levels": {"Python": "advanced", "React": "intermediate"},
        -- "domains": ["AI/ML", "Web Development"],
        -- "tools": ["VSCode", "Docker", "Git"],
        -- "learning_velocity": 0.85
    -- }
    
    -- Lifestyle Profile
    lifestyle_profile JSONB DEFAULT '{}', -- {
        -- "interests": ["cooking", "travel", "fitness"],
        -- "dietary_preferences": ["vegetarian", "low-carb"],
        -- "activity_patterns": {"morning": 0.8, "evening": 0.6},
        -- "content_preferences": {"video": 0.7, "article": 0.9}
    -- }
    
    -- Learning Style
    learning_style JSONB DEFAULT '{}', -- {
        -- "preferred_formats": ["hands-on", "visual"],
        -- "attention_span": "long",
        -- "complexity_preference": "challenging",
        -- "learning_goals": ["career_advancement", "personal_growth"]
    -- }
    
    -- Life Phase Detection
    life_phase VARCHAR(50), -- 'student', 'early_career', 'mid_career', 'career_change', 'expert', 'retirement'
    phase_confidence FLOAT DEFAULT 0.0,
    
    -- Interest Evolution Tracking
    interests_evolution JSONB DEFAULT '{}', -- Time-series data of changing interests
    
    -- Cross-Domain Patterns
    cross_domain_insights JSONB DEFAULT '{}', -- {
        -- "connections": [{"tech": "Python", "lifestyle": "cooking", "insight": "automation_enthusiast"}],
        -- "project_potential": ["recipe_automation", "meal_planning_ai"]
    -- }
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_analyzed_at TIMESTAMP WITH TIME ZONE
);

-- =====================================================
-- LEARNING PROFILES
-- =====================================================

-- Learning profiles for AI-powered education
CREATE TABLE IF NOT EXISTS learning_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    
    -- Current Skill Levels
    skill_levels JSONB DEFAULT '{}', -- {
        -- "Python": {"level": 7, "last_assessed": "2025-01-15", "growth_rate": 0.3},
        -- "Machine Learning": {"level": 5, "last_assessed": "2025-01-20", "growth_rate": 0.5}
    -- }
    
    -- Active Learning Paths
    learning_paths JSONB DEFAULT '[]', -- [
        -- {"path_id": "uuid", "name": "Advanced Python", "progress": 0.6, "est_completion": "2025-03-01"}
    -- ]
    
    -- Study Preferences
    study_preferences JSONB DEFAULT '{}', -- {
        -- "session_length": "45min",
        -- "best_times": ["morning", "late_evening"],
        -- "difficulty_preference": "gradual",
        -- "practice_vs_theory": 0.7
    -- }
    
    -- Progress Tracking
    progress_data JSONB DEFAULT '{}', -- {
        -- "total_hours": 234,
        -- "streak_days": 15,
        -- "completed_topics": ["Python Basics", "Data Structures"],
        -- "milestones": [{"date": "2025-01-01", "achievement": "First AI Model"}]
    -- }
    
    -- Recommendations
    next_recommendations JSONB DEFAULT '[]', -- AI-generated next steps
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- TAG CLUSTERS & THEMES
-- =====================================================

-- Tag clusters for ML-discovered themes
CREATE TABLE IF NOT EXISTS tag_clusters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cluster_name VARCHAR(255) NOT NULL,
    cluster_type VARCHAR(50), -- 'domain', 'cross_domain', 'emerging', 'temporal'
    tags TEXT[] NOT NULL,
    theme VARCHAR(255),
    theme_description TEXT,
    
    -- Cross-domain connections
    cross_domain_connections JSONB DEFAULT '{}', -- {
        -- "primary_domain": "technology",
        -- "secondary_domains": ["cooking", "health"],
        -- "connection_strength": 0.75,
        -- "insights": ["automation in daily life", "data-driven health"]
    -- }
    
    -- Cluster metrics
    cluster_metrics JSONB DEFAULT '{}', -- {
        -- "cohesion_score": 0.85,
        -- "user_adoption": 0.6,
        -- "growth_rate": 0.2
    -- }
    
    -- User associations
    user_affinity_scores JSONB DEFAULT '{}', -- {"user_id": affinity_score}
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- DREAMSCAPE SUGGESTIONS
-- =====================================================

-- Predictive suggestions from Dreamscape
CREATE TABLE IF NOT EXISTS dreamscape_suggestions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    suggestion_type VARCHAR(50), -- 'content', 'project', 'learning_path', 'career', 'lifestyle'
    
    -- Suggestion details
    title VARCHAR(255) NOT NULL,
    description TEXT,
    reasoning TEXT, -- Why this suggestion was made
    
    -- Suggestion data
    suggestion_data JSONB NOT NULL, -- Type-specific data
    
    -- Scoring and tracking
    confidence_score FLOAT DEFAULT 0.0,
    relevance_score FLOAT DEFAULT 0.0,
    novelty_score FLOAT DEFAULT 0.0, -- How different from user's usual patterns
    
    -- User interaction
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'viewed', 'accepted', 'rejected', 'completed'
    user_feedback JSONB, -- Rating, comments, etc.
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    presented_at TIMESTAMP WITH TIME ZONE,
    interacted_at TIMESTAMP WITH TIME ZONE
);

-- =====================================================
-- INDEXES
-- =====================================================

-- Persona indexes
CREATE INDEX idx_personas_user ON user_personas(user_id);
CREATE INDEX idx_personas_phase ON user_personas(life_phase);
CREATE INDEX idx_personas_updated ON user_personas(updated_at DESC);

-- Learning profile indexes
CREATE INDEX idx_learning_user ON learning_profiles(user_id);
CREATE INDEX idx_learning_updated ON learning_profiles(updated_at DESC);

-- Tag cluster indexes
CREATE INDEX idx_clusters_type ON tag_clusters(cluster_type);
CREATE INDEX idx_clusters_tags ON tag_clusters USING GIN(tags);

-- Suggestion indexes
CREATE INDEX idx_suggestions_user_status ON dreamscape_suggestions(user_id, status);
CREATE INDEX idx_suggestions_type ON dreamscape_suggestions(suggestion_type);
CREATE INDEX idx_suggestions_created ON dreamscape_suggestions(created_at DESC);

-- =====================================================
-- FUNCTIONS
-- =====================================================

-- Function to update persona timestamps
CREATE OR REPLACE FUNCTION update_persona_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers
CREATE TRIGGER trigger_update_personas_updated_at
    BEFORE UPDATE ON user_personas
    FOR EACH ROW
    EXECUTE FUNCTION update_persona_updated_at();

CREATE TRIGGER trigger_update_learning_profiles_updated_at
    BEFORE UPDATE ON learning_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_persona_updated_at();

CREATE TRIGGER trigger_update_tag_clusters_updated_at
    BEFORE UPDATE ON tag_clusters
    FOR EACH ROW
    EXECUTE FUNCTION update_persona_updated_at();

-- =====================================================
-- VIEWS
-- =====================================================

-- User engagement summary view
CREATE OR REPLACE VIEW user_engagement_summary AS
SELECT 
    ub.user_id,
    COUNT(DISTINCT DATE(ub.created_at)) as active_days,
    COUNT(DISTINCT ub.item_id) as unique_items_viewed,
    COUNT(DISTINCT ub.item_type) as content_type_diversity,
    AVG(ub.duration_seconds) as avg_engagement_seconds,
    MAX(ub.created_at) as last_active_at,
    COUNT(*) FILTER (WHERE ub.action_type = 'save') as total_saves,
    COUNT(*) FILTER (WHERE ub.action_type = 'share') as total_shares
FROM user_behaviors ub
GROUP BY ub.user_id;

-- Persona overview
CREATE OR REPLACE VIEW persona_overview AS
SELECT 
    up.user_id,
    up.life_phase,
    up.technical_profile->>'primary_languages' as primary_languages,
    up.lifestyle_profile->>'interests' as lifestyle_interests,
    up.learning_style->>'preferred_formats' as learning_formats,
    up.updated_at
FROM user_personas up;

-- =====================================================
-- COMMENTS
-- =====================================================

COMMENT ON TABLE user_behaviors IS 'Tracks all user interactions for behavior analysis and persona development';
COMMENT ON TABLE user_personas IS 'Stores multi-dimensional user profiles for intelligent personalization';
COMMENT ON TABLE learning_profiles IS 'Maintains user learning progress and preferences for adaptive education';
COMMENT ON TABLE tag_clusters IS 'ML-discovered tag groupings and cross-domain themes';
COMMENT ON TABLE dreamscape_suggestions IS 'AI-generated predictive suggestions based on user persona and patterns';

-- =====================================================
-- SAMPLE DATA STRUCTURE EXAMPLES
-- =====================================================

/*
-- Example user behavior entry:
{
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "action_type": "save",
    "item_id": "456e7890-e89b-12d3-a456-426614174000",
    "item_type": "article",
    "context": {
        "source": "recommendation",
        "search_query": null,
        "filters": {"category": "AI/ML"}
    },
    "duration_seconds": 245,
    "metadata": {
        "device": "desktop",
        "browser": "Chrome",
        "viewport": "1920x1080"
    }
}

-- Example persona technical profile:
{
    "primary_languages": ["Python", "JavaScript", "Go"],
    "skill_levels": {
        "Python": "expert",
        "JavaScript": "advanced",
        "Go": "intermediate",
        "Docker": "advanced",
        "Kubernetes": "beginner"
    },
    "domains": ["Backend Development", "DevOps", "Machine Learning"],
    "tools": ["VSCode", "PyCharm", "Docker", "Git", "AWS"],
    "learning_velocity": 0.85,
    "project_types": ["web_apps", "data_pipelines", "microservices"]
}

-- Example cross-domain insight:
{
    "connections": [
        {
            "domains": ["programming", "cooking"],
            "pattern": "systematic_approach",
            "strength": 0.82,
            "insight": "Applies engineering mindset to recipe optimization"
        },
        {
            "domains": ["fitness", "data_analysis"],
            "pattern": "quantified_self",
            "strength": 0.91,
            "insight": "Tracks and analyzes personal metrics systematically"
        }
    ],
    "project_potential": [
        "Automated meal planning system",
        "Personal health analytics dashboard",
        "Recipe optimization algorithm"
    ]
}
*/