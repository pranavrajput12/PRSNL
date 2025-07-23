-- Migration: Add password reset email template
-- Description: Add email template for password reset functionality

-- Insert password reset email template
INSERT INTO email_templates (name, subject, html_template, text_template, variables) VALUES
(
    'password_reset',
    'Reset your PRSNL password',
    '<h2>Reset Your Password</h2>
     <p>Hi {{user_name}},</p>
     <p>You recently requested to reset your password for your PRSNL account. Click the button below to reset it:</p>
     <p style="text-align: center; margin: 30px 0;">
         <a href="{{reset_link}}" style="background-color: #dc3545; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">Reset Password</a>
     </p>
     <p><strong>This link will expire in 1 hour.</strong></p>
     <p>If you didn''t request this password reset, please ignore this email. Your password will remain unchanged.</p>
     <p>For security reasons, this link can only be used once.</p>
     <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
     <p style="color: #666; font-size: 12px;">
         If the button doesn''t work, copy and paste this link into your browser:<br>
         {{reset_link}}
     </p>',
    'Reset Your Password

Hi {{user_name}},

You recently requested to reset your password for your PRSNL account. Click the link below to reset it:

{{reset_link}}

This link will expire in 1 hour.

If you didn''t request this password reset, please ignore this email. Your password will remain unchanged.

For security reasons, this link can only be used once.

Best regards,
The PRSNL Team',
    '["user_name", "reset_link"]'::jsonb
)
ON CONFLICT (name) DO UPDATE SET
    subject = EXCLUDED.subject,
    html_template = EXCLUDED.html_template,
    text_template = EXCLUDED.text_template,
    variables = EXCLUDED.variables,
    updated_at = CURRENT_TIMESTAMP;