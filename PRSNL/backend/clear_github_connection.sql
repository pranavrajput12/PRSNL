-- Clear GitHub connection to start fresh
DELETE FROM github_accounts WHERE user_id = 'temp-user-for-oauth';

-- Verify it's cleared
SELECT * FROM github_accounts;