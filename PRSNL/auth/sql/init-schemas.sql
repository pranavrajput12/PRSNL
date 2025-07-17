-- PostgreSQL Schema Initialization for Keycloak + FusionAuth
-- This script creates separate schemas for auth systems while preserving your existing PRSNL data

-- Create Keycloak schema
CREATE SCHEMA IF NOT EXISTS keycloak;
GRANT ALL PRIVILEGES ON SCHEMA keycloak TO pronav;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA keycloak TO pronav;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA keycloak TO pronav;
ALTER DEFAULT PRIVILEGES IN SCHEMA keycloak GRANT ALL ON TABLES TO pronav;
ALTER DEFAULT PRIVILEGES IN SCHEMA keycloak GRANT ALL ON SEQUENCES TO pronav;

-- Create FusionAuth schema  
CREATE SCHEMA IF NOT EXISTS fusionauth;
GRANT ALL PRIVILEGES ON SCHEMA fusionauth TO pronav;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA fusionauth TO pronav;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA fusionauth TO pronav;
ALTER DEFAULT PRIVILEGES IN SCHEMA fusionauth GRANT ALL ON TABLES TO pronav;
ALTER DEFAULT PRIVILEGES IN SCHEMA fusionauth GRANT ALL ON SEQUENCES TO pronav;

-- Create auth integration schema for our custom tables
CREATE SCHEMA IF NOT EXISTS auth_integration;
GRANT ALL PRIVILEGES ON SCHEMA auth_integration TO pronav;

-- User mapping table to link PRSNL users with Keycloak/FusionAuth
CREATE TABLE IF NOT EXISTS auth_integration.user_mapping (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prsnl_user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    keycloak_user_id UUID,
    fusionauth_user_id UUID,
    external_provider VARCHAR(50), -- 'google', 'github', 'microsoft', etc.
    external_user_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    UNIQUE(prsnl_user_id),
    UNIQUE(keycloak_user_id),
    UNIQUE(fusionauth_user_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_mapping_prsnl_user_id ON auth_integration.user_mapping(prsnl_user_id);
CREATE INDEX IF NOT EXISTS idx_user_mapping_keycloak_user_id ON auth_integration.user_mapping(keycloak_user_id);
CREATE INDEX IF NOT EXISTS idx_user_mapping_fusionauth_user_id ON auth_integration.user_mapping(fusionauth_user_id);
CREATE INDEX IF NOT EXISTS idx_user_mapping_external ON auth_integration.user_mapping(external_provider, external_user_id);

-- Auth session tracking for audit trails
CREATE TABLE IF NOT EXISTS auth_integration.auth_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_mapping_id UUID NOT NULL REFERENCES auth_integration.user_mapping(id) ON DELETE CASCADE,
    session_type VARCHAR(20) NOT NULL, -- 'keycloak', 'fusionauth'
    session_id VARCHAR(255) NOT NULL,
    ip_address INET,
    user_agent TEXT,
    login_method VARCHAR(50), -- 'password', 'google', 'github', etc.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    revoked_at TIMESTAMP WITH TIME ZONE
);

-- Indexes for auth_sessions
CREATE INDEX IF NOT EXISTS idx_auth_sessions_user_mapping ON auth_integration.auth_sessions(user_mapping_id);
CREATE INDEX IF NOT EXISTS idx_auth_sessions_session_id ON auth_integration.auth_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_auth_sessions_created_at ON auth_integration.auth_sessions(created_at);

-- User preferences and settings managed by FusionAuth
CREATE TABLE IF NOT EXISTS auth_integration.user_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_mapping_id UUID NOT NULL REFERENCES auth_integration.user_mapping(id) ON DELETE CASCADE,
    preference_key VARCHAR(100) NOT NULL,
    preference_value JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    UNIQUE(user_mapping_id, preference_key)
);

-- Notification settings and email preferences
CREATE TABLE IF NOT EXISTS auth_integration.notification_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_mapping_id UUID NOT NULL REFERENCES auth_integration.user_mapping(id) ON DELETE CASCADE,
    email_notifications BOOLEAN DEFAULT true,
    push_notifications BOOLEAN DEFAULT true,
    marketing_emails BOOLEAN DEFAULT false,
    weekly_digest BOOLEAN DEFAULT true,
    security_alerts BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    UNIQUE(user_mapping_id)
);

-- Grant permissions on new tables
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA auth_integration TO pronav;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA auth_integration TO pronav;

-- Create update trigger function
CREATE OR REPLACE FUNCTION auth_integration.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add update triggers
CREATE TRIGGER update_user_mapping_updated_at BEFORE UPDATE ON auth_integration.user_mapping
    FOR EACH ROW EXECUTE FUNCTION auth_integration.update_updated_at_column();

CREATE TRIGGER update_user_preferences_updated_at BEFORE UPDATE ON auth_integration.user_preferences  
    FOR EACH ROW EXECUTE FUNCTION auth_integration.update_updated_at_column();

CREATE TRIGGER update_notification_settings_updated_at BEFORE UPDATE ON auth_integration.notification_settings
    FOR EACH ROW EXECUTE FUNCTION auth_integration.update_updated_at_column();

-- Create a view for easy user data access
CREATE OR REPLACE VIEW auth_integration.user_auth_view AS
SELECT 
    u.id as prsnl_user_id,
    u.email,
    COALESCE(u.first_name || ' ' || u.last_name, u.first_name, u.last_name, u.email) as display_name,
    u.first_name,
    u.last_name,
    u.is_active,
    u.is_verified,
    u.created_at as prsnl_created_at,
    um.keycloak_user_id,
    um.fusionauth_user_id,
    um.external_provider,
    um.external_user_id,
    ns.email_notifications,
    ns.push_notifications,
    ns.marketing_emails,
    ns.weekly_digest,
    ns.security_alerts
FROM public.users u
LEFT JOIN auth_integration.user_mapping um ON u.id = um.prsnl_user_id
LEFT JOIN auth_integration.notification_settings ns ON um.id = ns.user_mapping_id;

-- Grant view permissions
GRANT SELECT ON auth_integration.user_auth_view TO pronav;

-- Insert any existing users into the mapping table (for migration)
INSERT INTO auth_integration.user_mapping (prsnl_user_id)
SELECT id FROM public.users 
WHERE id NOT IN (SELECT prsnl_user_id FROM auth_integration.user_mapping);

-- Create default notification settings for existing users
INSERT INTO auth_integration.notification_settings (user_mapping_id)
SELECT um.id 
FROM auth_integration.user_mapping um
WHERE um.id NOT IN (SELECT user_mapping_id FROM auth_integration.notification_settings);

-- Success message
SELECT 'Auth schemas created successfully!' as status;