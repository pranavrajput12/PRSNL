# Dreamscape Database Schema Documentation

> **Database schema and data models for the Dreamscape PersonaAnalysisCrew feature**

This document details the database schema, tables, relationships, and data models used by the Dreamscape AI-powered personal intelligence system.

## Overview

The Dreamscape feature uses 5 specialized database tables to store behavior tracking, persona analysis results, learning profiles, tag clustering, and personalized suggestions. All tables are designed for high-performance analytics and real-time persona insights.

## Database Tables

### 1. user_behaviors

**Purpose**: Raw behavioral event tracking for all user interactions

```sql
CREATE TABLE user_behaviors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    action_type VARCHAR(50) NOT NULL,
    item_id UUID,
    item_type VARCHAR(50),
    duration_seconds INTEGER,
    context JSONB,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

#### Columns
- **id**: Primary key, auto-generated UUID
- **user_id**: Reference to user performing the action
- **action_type**: Type of action performed (view, edit, search, create, etc.)
- **item_id**: ID of the item being interacted with (nullable for global actions)
- **item_type**: Type of item (article, code, video, note, etc.)
- **duration_seconds**: How long the interaction lasted
- **context**: Additional context data (search queries, page location, etc.)
- **metadata**: Extra metadata for analytics
- **created_at**: Timestamp of the interaction

#### Example Data
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "user_id": "user-uuid",
  "action_type": "view",
  "item_id": "article-uuid", 
  "item_type": "article",
  "duration_seconds": 180,
  "context": {
    "source": "timeline",
    "scroll_depth": 0.8,
    "referrer": "search"
  },
  "metadata": {
    "device": "desktop",
    "browser": "chrome"
  },
  "created_at": "2025-07-28T10:30:00Z"
}
```

#### Indexes
```sql
CREATE INDEX idx_user_behaviors_user_id ON user_behaviors(user_id);
CREATE INDEX idx_user_behaviors_created_at ON user_behaviors(created_at);
CREATE INDEX idx_user_behaviors_action_type ON user_behaviors(action_type);
CREATE INDEX idx_user_behaviors_item_type ON user_behaviors(item_type);
```

---

### 2. user_personas

**Purpose**: Structured persona analysis results from the 5-agent CrewAI system

```sql
CREATE TABLE user_personas (
    user_id UUID PRIMARY KEY,
    technical_profile JSONB,
    lifestyle_profile JSONB,
    learning_style JSONB,
    life_phase VARCHAR(50),
    phase_confidence DECIMAL(3,2),
    interests_evolution JSONB,
    cross_domain_insights JSONB,
    last_analyzed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

#### Columns
- **user_id**: Primary key, references users table
- **technical_profile**: Technical skills, languages, tools, domains (JSONB)
- **lifestyle_profile**: Interests, activity patterns, content preferences (JSONB)
- **learning_style**: Learning formats, attention span, complexity preference (JSONB)
- **life_phase**: Detected life phase (early_career, mid_career, experienced)
- **phase_confidence**: Confidence level in life phase detection (0.0-1.0)
- **interests_evolution**: How interests change over time (JSONB)
- **cross_domain_insights**: Connections between different domains (JSONB)
- **last_analyzed_at**: When the persona was last analyzed
- **created_at**: When the persona was first created
- **updated_at**: When the persona was last updated

#### Example Data Structure

**technical_profile**:
```json
{
  "primary_languages": ["Python", "JavaScript", "TypeScript"],
  "skill_levels": {
    "Python": "intermediate",
    "JavaScript": "advanced",
    "TypeScript": "beginner"
  },
  "domains": ["Web Development", "Data Science", "Machine Learning"],
  "tools": ["VSCode", "Git", "Docker", "PostgreSQL"],
  "learning_velocity": [
    {"domain": "Python", "velocity": 0.8, "trend": "increasing"},
    {"domain": "JavaScript", "velocity": 0.6, "trend": "stable"}
  ]
}
```

**lifestyle_profile**:
```json
{
  "interests": ["technology", "music", "photography", "cooking"],
  "activity_patterns": {
    "morning": 0.2,
    "afternoon": 0.5,
    "evening": 0.3
  },
  "content_preferences": {
    "article": 0.6,
    "video": 0.3,
    "code": 0.1
  },
  "interaction_style": "focused_sessions",
  "social_patterns": ["individual_work", "occasional_collaboration"]
}
```

**learning_style**:
```json
{
  "preferred_formats": ["hands-on", "visual", "text"],
  "attention_span": "medium",
  "complexity_preference": "moderate_to_high",
  "learning_goals": ["skill_development", "career_advancement"],
  "feedback_preference": "detailed",
  "practice_theory_ratio": 0.7
}
```

**cross_domain_insights**:
```json
{
  "connections": [
    {
      "domain1": "programming",
      "domain2": "music",
      "connection_type": "pattern_recognition",
      "strength": 0.8,
      "insights": ["Mathematical patterns in both domains"]
    }
  ],
  "project_potential": [
    "AI-powered music composition tool",
    "Data visualization for audio analysis"
  ],
  "innovation_opportunities": [
    "Combine coding skills with music theory knowledge"
  ]
}
```

#### Indexes
```sql
CREATE INDEX idx_user_personas_life_phase ON user_personas(life_phase);
CREATE INDEX idx_user_personas_last_analyzed ON user_personas(last_analyzed_at);
```

---

### 3. learning_profiles

**Purpose**: Detailed learning analytics and educational progression tracking

```sql
CREATE TABLE learning_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    skill_area VARCHAR(100) NOT NULL,
    current_level VARCHAR(50),
    progression_data JSONB,
    learning_velocity DECIMAL(4,3),
    last_activity TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

#### Columns
- **id**: Primary key, auto-generated UUID
- **user_id**: Reference to user
- **skill_area**: Area of learning (Python, Machine Learning, etc.)
- **current_level**: Current skill level (beginner, intermediate, advanced, expert)
- **progression_data**: Detailed progression metrics and milestones (JSONB)
- **learning_velocity**: Rate of learning progress (0.0-1.0)
- **last_activity**: Timestamp of last learning activity
- **created_at**: When the profile was created
- **updated_at**: When the profile was last updated

#### Example Data

**progression_data**:
```json
{
  "milestones": [
    {
      "date": "2025-01-15",
      "level": "beginner",
      "achievement": "First Python script"
    },
    {
      "date": "2025-03-20", 
      "level": "intermediate",
      "achievement": "Built web scraper"
    }
  ],
  "skills_acquired": [
    {"skill": "variables", "mastery": 0.9},
    {"skill": "functions", "mastery": 0.8},
    {"skill": "classes", "mastery": 0.6}
  ],
  "time_invested_hours": 45.5,
  "projects_completed": 3,
  "assessment_scores": [85, 78, 92]
}
```

#### Indexes
```sql
CREATE INDEX idx_learning_profiles_user_id ON learning_profiles(user_id);
CREATE INDEX idx_learning_profiles_skill_area ON learning_profiles(skill_area);
CREATE INDEX idx_learning_profiles_learning_velocity ON learning_profiles(learning_velocity);
```

---

### 4. tag_clusters

**Purpose**: ML-powered content clustering and theme discovery

```sql
CREATE TABLE tag_clusters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    cluster_name VARCHAR(100),
    tags JSONB NOT NULL,
    cluster_center VECTOR(1536),
    cohesion_score DECIMAL(4,3),
    cluster_size INTEGER,
    evolution_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

#### Columns
- **id**: Primary key, auto-generated UUID
- **user_id**: Reference to user
- **cluster_name**: AI-generated name for the cluster theme
- **tags**: Tags included in this cluster (JSONB array)
- **cluster_center**: Vector embedding representing cluster center
- **cohesion_score**: How tightly related the tags are (0.0-1.0)
- **cluster_size**: Number of items in the cluster
- **evolution_data**: How the cluster has changed over time (JSONB)
- **created_at**: When the cluster was created
- **updated_at**: When the cluster was last updated

#### Example Data

**tags**:
```json
[
  {"tag": "python", "weight": 0.8, "frequency": 25},
  {"tag": "machine-learning", "weight": 0.7, "frequency": 18},
  {"tag": "data-science", "weight": 0.6, "frequency": 15},
  {"tag": "tensorflow", "weight": 0.5, "frequency": 8}
]
```

**evolution_data**:
```json
{
  "size_history": [
    {"date": "2025-01-01", "size": 5},
    {"date": "2025-02-01", "size": 12},
    {"date": "2025-03-01", "size": 18}
  ],
  "new_tags_added": ["tensorflow", "pytorch"],
  "tags_removed": ["numpy-basics"],
  "cohesion_trend": "increasing"
}
```

#### Indexes
```sql
CREATE INDEX idx_tag_clusters_user_id ON tag_clusters(user_id);
CREATE INDEX idx_tag_clusters_cluster_size ON tag_clusters(cluster_size);
CREATE INDEX idx_tag_clusters_cohesion_score ON tag_clusters(cohesion_score);
```

---

### 5. dreamscape_suggestions

**Purpose**: Personalized AI-generated recommendations and insights

```sql
CREATE TABLE dreamscape_suggestions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    suggestion_type VARCHAR(50) NOT NULL,
    title VARCHAR(200),
    content TEXT,
    metadata JSONB,
    priority_score DECIMAL(4,3),
    is_dismissed BOOLEAN DEFAULT FALSE,
    is_acted_upon BOOLEAN DEFAULT FALSE,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

#### Columns
- **id**: Primary key, auto-generated UUID
- **user_id**: Reference to user
- **suggestion_type**: Type of suggestion (learning_path, project_idea, skill_development, etc.)
- **title**: Short title for the suggestion
- **content**: Detailed suggestion content
- **metadata**: Additional data about the suggestion (JSONB)
- **priority_score**: How important/relevant this suggestion is (0.0-1.0)
- **is_dismissed**: Whether user dismissed the suggestion
- **is_acted_upon**: Whether user acted on the suggestion
- **expires_at**: When the suggestion becomes less relevant
- **created_at**: When the suggestion was generated

#### Example Data

```json
{
  "id": "suggestion-uuid",
  "user_id": "user-uuid",
  "suggestion_type": "project_idea",
  "title": "Build a Music Pattern Recognition Tool",
  "content": "Based on your interests in both programming and music, consider building a tool that analyzes musical patterns using machine learning. This could combine your Python skills with your musical interests.",
  "metadata": {
    "skill_areas": ["Python", "Machine Learning", "Music Theory"],
    "estimated_time": "2-3 weeks",
    "difficulty": "intermediate",
    "learning_outcomes": ["Audio processing", "Pattern recognition", "Feature extraction"],
    "related_clusters": ["ai-music-cluster", "python-projects-cluster"]
  },
  "priority_score": 0.85,
  "is_dismissed": false,
  "is_acted_upon": false,
  "expires_at": "2025-09-01T00:00:00Z",
  "created_at": "2025-07-28T10:30:00Z"
}
```

#### Indexes
```sql
CREATE INDEX idx_dreamscape_suggestions_user_id ON dreamscape_suggestions(user_id);
CREATE INDEX idx_dreamscape_suggestions_type ON dreamscape_suggestions(suggestion_type);
CREATE INDEX idx_dreamscape_suggestions_priority ON dreamscape_suggestions(priority_score);
CREATE INDEX idx_dreamscape_suggestions_active ON dreamscape_suggestions(user_id, is_dismissed, expires_at);
```

---

## Relationships and Foreign Keys

```sql
-- Add foreign key constraints
ALTER TABLE user_behaviors 
ADD CONSTRAINT fk_user_behaviors_user_id 
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

ALTER TABLE user_personas 
ADD CONSTRAINT fk_user_personas_user_id 
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

ALTER TABLE learning_profiles 
ADD CONSTRAINT fk_learning_profiles_user_id 
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

ALTER TABLE tag_clusters 
ADD CONSTRAINT fk_tag_clusters_user_id 
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

ALTER TABLE dreamscape_suggestions 
ADD CONSTRAINT fk_dreamscape_suggestions_user_id 
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
```

## Common Queries

### 1. Get User Behavior Summary
```sql
SELECT 
    action_type,
    COUNT(*) as action_count,
    AVG(duration_seconds) as avg_duration,
    COUNT(DISTINCT item_id) as unique_items
FROM user_behaviors 
WHERE user_id = $1 
    AND created_at >= NOW() - INTERVAL '30 days'
GROUP BY action_type
ORDER BY action_count DESC;
```

### 2. Calculate Learning Velocity
```sql
SELECT 
    skill_area,
    learning_velocity,
    current_level,
    progression_data->>'time_invested_hours' as hours_invested
FROM learning_profiles 
WHERE user_id = $1
ORDER BY learning_velocity DESC;
```

### 3. Get Active Suggestions
```sql
SELECT 
    suggestion_type,
    title,
    content,
    priority_score,
    created_at
FROM dreamscape_suggestions 
WHERE user_id = $1 
    AND is_dismissed = FALSE 
    AND (expires_at IS NULL OR expires_at > NOW())
ORDER BY priority_score DESC
LIMIT 10;
```

### 4. Analyze Tag Clusters Evolution
```sql
SELECT 
    cluster_name,
    cluster_size,
    cohesion_score,
    jsonb_array_length(tags) as tag_count,
    evolution_data->'size_history' as size_history
FROM tag_clusters 
WHERE user_id = $1
ORDER BY cohesion_score DESC;
```

## Performance Optimization

### Partitioning Strategy

For high-volume deployments, consider partitioning the `user_behaviors` table by time:

```sql
-- Partition by month for better query performance
CREATE TABLE user_behaviors_y2025m01 PARTITION OF user_behaviors
FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

CREATE TABLE user_behaviors_y2025m02 PARTITION OF user_behaviors
FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');
-- Continue for each month...
```

### Materialized Views

Create materialized views for common analytics queries:

```sql
-- User engagement summary
CREATE MATERIALIZED VIEW user_engagement_summary AS
SELECT 
    user_id,
    COUNT(*) as total_actions,
    COUNT(DISTINCT item_id) as unique_items,
    AVG(duration_seconds) as avg_session_duration,
    COUNT(DISTINCT DATE(created_at)) as active_days,
    MAX(created_at) as last_activity
FROM user_behaviors 
WHERE created_at >= NOW() - INTERVAL '90 days'
GROUP BY user_id;

-- Refresh periodically
CREATE INDEX ON user_engagement_summary(user_id);
```

## Data Privacy and Retention

### Data Retention Policies
```sql
-- Clean up old behavior data (keep 2 years)
DELETE FROM user_behaviors 
WHERE created_at < NOW() - INTERVAL '2 years';

-- Archive old suggestions (keep 1 year)
DELETE FROM dreamscape_suggestions 
WHERE created_at < NOW() - INTERVAL '1 year' 
    AND (is_acted_upon = TRUE OR is_dismissed = TRUE);
```

### Data Anonymization
```sql
-- For GDPR compliance, anonymize persona data while keeping analytics
UPDATE user_personas 
SET 
    technical_profile = '{}',
    lifestyle_profile = '{}',
    learning_style = '{}',
    cross_domain_insights = '{}'
WHERE user_id IN (SELECT id FROM deleted_users);
```

## Migration Commands

### Initial Migration
```sql
-- Run migration to create all Dreamscape tables
\i /migrations/20240728_add_dreamscape_tables.sql
```

### Add Indexes for Performance
```sql
-- Add additional performance indexes
CREATE INDEX CONCURRENTLY idx_user_behaviors_composite 
ON user_behaviors(user_id, action_type, created_at);

CREATE INDEX CONCURRENTLY idx_user_personas_compound 
ON user_personas(life_phase, last_analyzed_at);
```

## Monitoring and Analytics

### Key Metrics to Track
1. **Analysis Performance**: Average time for persona analysis
2. **Data Quality**: Completeness of behavior tracking
3. **Storage Growth**: Table size growth over time
4. **Query Performance**: Slow query identification

### Monitoring Queries
```sql
-- Check table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE tablename LIKE '%dreamscape%' OR tablename LIKE '%user_%'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Analyze behavior tracking coverage
SELECT 
    DATE(created_at) as date,
    COUNT(DISTINCT user_id) as active_users,
    COUNT(*) as total_events,
    AVG(duration_seconds) as avg_duration
FROM user_behaviors 
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY DATE(created_at)
ORDER BY date;
```

---

**Dreamscape Database Schema** - Powering intelligent personal analytics and AI-driven insights 🧠💾