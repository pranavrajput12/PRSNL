-- Add audio_journals table for Synaptic Echo feature
-- This table extends the existing files/items system for audio journaling

CREATE TABLE IF NOT EXISTS audio_journals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    item_id UUID NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    file_id UUID NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    
    -- Audio session metadata
    session_title VARCHAR(255),
    session_description TEXT,
    duration_seconds INTEGER DEFAULT 0,
    
    -- Privacy and mood
    privacy_level VARCHAR(20) DEFAULT 'private' CHECK (privacy_level IN ('public', 'private', 'confidential')),
    mood_tags JSONB DEFAULT '[]'::jsonb,
    emotional_tone VARCHAR(50), -- AI-detected emotional tone
    
    -- Location and context
    location_name VARCHAR(255),
    location_coordinates POINT,
    ambient_description TEXT,
    
    -- Processing status
    transcription_status VARCHAR(20) DEFAULT 'pending' CHECK (transcription_status IN ('pending', 'processing', 'completed', 'failed')),
    transcription_service VARCHAR(20), -- 'whisper_cloud', 'whisper_cpp'
    ai_analysis_status VARCHAR(20) DEFAULT 'pending' CHECK (ai_analysis_status IN ('pending', 'processing', 'completed', 'failed')),
    
    -- Content analysis
    transcript_quality_score FLOAT DEFAULT 0.0,
    word_count INTEGER DEFAULT 0,
    silence_duration_seconds INTEGER DEFAULT 0,
    speech_pace_wpm INTEGER DEFAULT 0,
    
    -- Knowledge base integration
    related_items JSONB DEFAULT '[]'::jsonb, -- IDs of related items found during processing
    auto_tags JSONB DEFAULT '[]'::jsonb, -- AI-generated tags from audio content
    key_topics JSONB DEFAULT '[]'::jsonb, -- Extracted key topics/themes
    action_items JSONB DEFAULT '[]'::jsonb, -- Detected action items or todos
    
    -- Neural interface metadata
    neural_patterns JSONB DEFAULT '{}'::jsonb, -- For future advanced audio analysis
    synaptic_connections JSONB DEFAULT '[]'::jsonb, -- Links to related memory traces
    
    -- Timestamps
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_audio_journals_item_id ON audio_journals(item_id);
CREATE INDEX IF NOT EXISTS idx_audio_journals_file_id ON audio_journals(file_id);
CREATE INDEX IF NOT EXISTS idx_audio_journals_recorded_at ON audio_journals(recorded_at DESC);
CREATE INDEX IF NOT EXISTS idx_audio_journals_privacy_level ON audio_journals(privacy_level);
CREATE INDEX IF NOT EXISTS idx_audio_journals_transcription_status ON audio_journals(transcription_status);
CREATE INDEX IF NOT EXISTS idx_audio_journals_mood_tags ON audio_journals USING GIN(mood_tags);
CREATE INDEX IF NOT EXISTS idx_audio_journals_related_items ON audio_journals USING GIN(related_items);
CREATE INDEX IF NOT EXISTS idx_audio_journals_auto_tags ON audio_journals USING GIN(auto_tags);

-- Add trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_audio_journals_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_audio_journals_updated_at
    BEFORE UPDATE ON audio_journals
    FOR EACH ROW
    EXECUTE FUNCTION update_audio_journals_updated_at();

-- Add audio journal specific content type to items table if not exists
DO $$
BEGIN
    -- Add 'audio_journal' as a valid content_type
    UPDATE items SET content_type = 'audio_journal' 
    WHERE content_type = 'audio' AND id IN (
        SELECT item_id FROM audio_journals
    );
END;
$$;

-- Create view for easy querying of audio journal entries with full details
CREATE OR REPLACE VIEW synaptic_echo_entries AS
SELECT 
    aj.id as journal_id,
    aj.session_title,
    aj.session_description,
    aj.duration_seconds,
    aj.privacy_level,
    aj.mood_tags,
    aj.emotional_tone,
    aj.location_name,
    aj.transcription_status,
    aj.transcription_service,
    aj.ai_analysis_status,
    aj.transcript_quality_score,
    aj.word_count,
    aj.related_items,
    aj.auto_tags,
    aj.key_topics,
    aj.action_items,
    aj.recorded_at,
    aj.processed_at,
    aj.created_at,
    aj.updated_at,
    
    -- Item details
    i.id as item_id,
    i.title,
    i.summary,
    i.status as item_status,
    i.type as item_type,
    
    -- File details  
    f.id as file_id,
    f.original_filename,
    f.file_path,
    f.file_size,
    f.mime_type,
    f.extracted_text as transcript,
    f.processing_status as file_processing_status,
    
    -- Tags
    COALESCE(
        (SELECT json_agg(t.name) 
         FROM tags t 
         JOIN item_tags it ON t.id = it.tag_id 
         WHERE it.item_id = i.id), 
        '[]'::json
    ) as manual_tags

FROM audio_journals aj
JOIN items i ON aj.item_id = i.id
JOIN files f ON aj.file_id = f.id
ORDER BY aj.recorded_at DESC;

-- Grant permissions (adjust as needed for your user setup)
-- GRANT ALL PRIVILEGES ON TABLE audio_journals TO your_app_user;
-- GRANT ALL PRIVILEGES ON SEQUENCE audio_journals_id_seq TO your_app_user;

COMMENT ON TABLE audio_journals IS 'Synaptic Echo: Audio journaling system for neural voice processing and memory synthesis';
COMMENT ON VIEW synaptic_echo_entries IS 'Complete view of audio journal entries with item, file, and tag details';