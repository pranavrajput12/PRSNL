-- Migration: Add GitHub integration tables
-- This enables GitHub OAuth login and repository synchronization

-- GitHub accounts table (connected GitHub accounts)
CREATE TABLE github_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL, -- Simple text ID for now
    github_id BIGINT UNIQUE NOT NULL,
    github_username TEXT NOT NULL,
    github_email TEXT,
    avatar_url TEXT,
    
    -- OAuth tokens (encrypted)
    access_token_encrypted BYTEA NOT NULL,
    access_token_nonce BYTEA NOT NULL,
    refresh_token_encrypted BYTEA,
    refresh_token_nonce BYTEA,
    token_expires_at TIMESTAMPTZ,
    
    -- Account metadata
    repos_url TEXT,
    organizations_url TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(user_id, github_id)
);

-- GitHub repositories table
CREATE TABLE github_repos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID REFERENCES github_accounts(id) ON DELETE CASCADE,
    github_id BIGINT NOT NULL,
    
    -- Repository info
    name TEXT NOT NULL,
    full_name TEXT NOT NULL,
    description TEXT,
    language TEXT,
    stars INTEGER DEFAULT 0,
    forks INTEGER DEFAULT 0,
    open_issues INTEGER DEFAULT 0,
    is_private BOOLEAN DEFAULT false,
    is_fork BOOLEAN DEFAULT false,
    
    -- Repository metadata
    default_branch TEXT DEFAULT 'main',
    clone_url TEXT,
    html_url TEXT,
    created_at_github TIMESTAMPTZ,
    updated_at_github TIMESTAMPTZ,
    pushed_at TIMESTAMPTZ,
    
    -- Sync tracking
    last_synced_at TIMESTAMPTZ,
    sync_enabled BOOLEAN DEFAULT true,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(account_id, github_id)
);

-- GitHub webhooks table (for real-time updates)
CREATE TABLE github_webhooks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repo_id UUID REFERENCES github_repos(id) ON DELETE CASCADE,
    webhook_id BIGINT NOT NULL,
    webhook_secret TEXT NOT NULL,
    events TEXT[] DEFAULT '{}',
    active BOOLEAN DEFAULT true,
    
    -- Webhook metadata
    url TEXT NOT NULL,
    last_delivery_at TIMESTAMPTZ,
    last_status INTEGER,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(repo_id, webhook_id)
);

-- Create indexes
CREATE INDEX idx_github_accounts_user ON github_accounts(user_id);
CREATE INDEX idx_github_repos_account ON github_repos(account_id);
CREATE INDEX idx_github_repos_language ON github_repos(language);
CREATE INDEX idx_github_repos_stars ON github_repos(stars DESC);
CREATE INDEX idx_github_webhooks_repo ON github_webhooks(repo_id);

-- Add triggers for updated_at
CREATE TRIGGER update_github_accounts_updated_at 
    BEFORE UPDATE ON github_accounts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_github_repos_updated_at 
    BEFORE UPDATE ON github_repos
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_github_webhooks_updated_at 
    BEFORE UPDATE ON github_webhooks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Comments
COMMENT ON TABLE github_accounts IS 'Stores connected GitHub accounts with encrypted OAuth tokens';
COMMENT ON TABLE github_repos IS 'Stores synchronized GitHub repositories for CodeMirror analysis';
COMMENT ON TABLE github_webhooks IS 'Stores GitHub webhook configurations for real-time updates';