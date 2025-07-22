-- Migration 024: Add voice interactions table for Cortex voice chat

-- Create voice interactions table
CREATE TABLE IF NOT EXISTS voice_interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    user_text TEXT NOT NULL,
    ai_response TEXT NOT NULL,
    mood VARCHAR(50),
    audio_duration_ms INTEGER,
    processing_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_voice_interactions_user_id ON voice_interactions(user_id);
CREATE INDEX idx_voice_interactions_created_at ON voice_interactions(created_at DESC);
CREATE INDEX idx_voice_interactions_mood ON voice_interactions(mood);

-- Add voice preferences to user profile
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS voice_preferences JSONB DEFAULT '{
    "enabled": true,
    "voice_gender": "female",
    "auto_play_responses": true,
    "save_transcripts": true
}'::jsonb;

-- Create voice analytics view
CREATE OR REPLACE VIEW voice_usage_analytics AS
SELECT 
    DATE(created_at) as date,
    COUNT(*) as total_interactions,
    COUNT(DISTINCT user_id) as unique_users,
    AVG(processing_time_ms) as avg_processing_time,
    mood,
    COUNT(*) FILTER (WHERE mood = 'discovering') as discovering_count,
    COUNT(*) FILTER (WHERE mood = 'explaining') as explaining_count,
    COUNT(*) FILTER (WHERE mood = 'encouraging') as encouraging_count
FROM voice_interactions
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(created_at), mood;