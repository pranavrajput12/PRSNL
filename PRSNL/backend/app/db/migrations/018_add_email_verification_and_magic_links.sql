-- Migration: Add email verification and magic link tables
-- Description: Support for email verification and passwordless magic link authentication

-- Add email verification columns to users table
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS email_verification_token VARCHAR(255),
ADD COLUMN IF NOT EXISTS email_verification_token_expires TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS email_verified_at TIMESTAMP WITH TIME ZONE;

-- Create index for email verification token lookups
CREATE INDEX IF NOT EXISTS idx_users_email_verification_token 
ON users(email_verification_token) 
WHERE email_verification_token IS NOT NULL;

-- Magic links table for passwordless authentication
CREATE TABLE IF NOT EXISTS magic_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    token VARCHAR(255) NOT NULL UNIQUE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    used_at TIMESTAMP WITH TIME ZONE,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    CONSTRAINT magic_links_user_fk FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Indexes for magic links
CREATE INDEX IF NOT EXISTS idx_magic_links_token ON magic_links(token);
CREATE INDEX IF NOT EXISTS idx_magic_links_email ON magic_links(email);
CREATE INDEX IF NOT EXISTS idx_magic_links_expires_at ON magic_links(expires_at);

-- Email templates table for customizable email content
CREATE TABLE IF NOT EXISTS email_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    subject VARCHAR(255) NOT NULL,
    html_template TEXT NOT NULL,
    text_template TEXT NOT NULL,
    variables JSONB DEFAULT '[]'::jsonb,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Insert default email templates
INSERT INTO email_templates (name, subject, html_template, text_template, variables) VALUES
(
    'email_verification',
    'Verify your email for PRSNL',
    '<h2>Welcome to PRSNL!</h2><p>Please verify your email by clicking the link below:</p><p><a href="{{verification_link}}" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Verify Email</a></p><p>This link will expire in 24 hours.</p><p>If you didn''t create an account, please ignore this email.</p>',
    'Welcome to PRSNL!\n\nPlease verify your email by clicking the link below:\n\n{{verification_link}}\n\nThis link will expire in 24 hours.\n\nIf you didn''t create an account, please ignore this email.',
    '["verification_link", "user_name"]'::jsonb
),
(
    'magic_link',
    'Sign in to PRSNL',
    '<h2>Sign in to PRSNL</h2><p>Click the link below to sign in to your account:</p><p><a href="{{magic_link}}" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Sign In</a></p><p>This link will expire in 15 minutes.</p><p>If you didn''t request this, please ignore this email.</p>',
    'Sign in to PRSNL\n\nClick the link below to sign in to your account:\n\n{{magic_link}}\n\nThis link will expire in 15 minutes.\n\nIf you didn''t request this, please ignore this email.',
    '["magic_link", "user_email"]'::jsonb
),
(
    'welcome',
    'Welcome to PRSNL!',
    '<h2>Welcome to PRSNL, {{user_name}}!</h2><p>Your account has been successfully created and verified.</p><p>Get started by:</p><ul><li>Setting up your profile</li><li>Exploring the dashboard</li><li>Creating your first project</li></ul><p><a href="{{app_link}}" style="background-color: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Go to Dashboard</a></p>',
    'Welcome to PRSNL, {{user_name}}!\n\nYour account has been successfully created and verified.\n\nGet started by:\n- Setting up your profile\n- Exploring the dashboard\n- Creating your first project\n\nGo to Dashboard: {{app_link}}',
    '["user_name", "app_link"]'::jsonb
)
ON CONFLICT (name) DO NOTHING;

-- Email logs table for tracking sent emails
CREATE TABLE IF NOT EXISTS email_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    email_to VARCHAR(255) NOT NULL,
    email_type VARCHAR(50) NOT NULL,
    template_name VARCHAR(100),
    subject VARCHAR(255),
    status VARCHAR(20) DEFAULT 'pending', -- pending, sent, failed
    provider VARCHAR(50) DEFAULT 'resend',
    provider_message_id VARCHAR(255),
    error_message TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    sent_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for email logs
CREATE INDEX IF NOT EXISTS idx_email_logs_user_id ON email_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_email_logs_email_to ON email_logs(email_to);
CREATE INDEX IF NOT EXISTS idx_email_logs_status ON email_logs(status);
CREATE INDEX IF NOT EXISTS idx_email_logs_created_at ON email_logs(created_at DESC);

-- Function to clean up expired magic links
CREATE OR REPLACE FUNCTION cleanup_expired_magic_links()
RETURNS void AS $$
BEGIN
    DELETE FROM magic_links 
    WHERE expires_at < NOW() 
    AND used_at IS NULL;
END;
$$ LANGUAGE plpgsql;

-- Function to clean up expired email verification tokens
CREATE OR REPLACE FUNCTION cleanup_expired_email_tokens()
RETURNS void AS $$
BEGIN
    UPDATE users 
    SET email_verification_token = NULL,
        email_verification_token_expires = NULL
    WHERE email_verification_token_expires < NOW()
    AND email_verification_token IS NOT NULL
    AND is_verified = false;
END;
$$ LANGUAGE plpgsql;