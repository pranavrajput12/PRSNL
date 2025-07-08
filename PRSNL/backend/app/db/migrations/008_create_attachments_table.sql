-- Create attachments table for storing media files associated with items
CREATE TABLE IF NOT EXISTS attachments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    item_id UUID NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    file_type VARCHAR(50) NOT NULL, -- 'image', 'video', 'audio', 'document'
    file_path TEXT NOT NULL,
    mime_type VARCHAR(100),
    file_size BIGINT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_attachments_item_id ON attachments(item_id);
CREATE INDEX IF NOT EXISTS idx_attachments_file_type ON attachments(file_type);
CREATE INDEX IF NOT EXISTS idx_attachments_created_at ON attachments(created_at DESC);

-- Add update trigger
CREATE TRIGGER attachments_updated_at
    BEFORE UPDATE ON attachments
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();