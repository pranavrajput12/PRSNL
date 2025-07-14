-- Fix processing_time_ms field to handle large timestamp values
-- Change from INTEGER to BIGINT to accommodate millisecond timestamps

ALTER TABLE ai_conversation_imports 
ALTER COLUMN processing_time_ms TYPE BIGINT;