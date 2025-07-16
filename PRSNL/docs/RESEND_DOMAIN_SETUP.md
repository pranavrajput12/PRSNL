# Resend Domain Setup for prsnl.fyi

## Steps to Configure prsnl.fyi with Resend

1. **Login to Resend Dashboard**
   - Go to https://resend.com/domains
   - Click "Add Domain"
   - Enter `prsnl.fyi`

2. **Add DNS Records**
   You'll need to add these records to your domain's DNS settings:

   ### SPF Record
   - Type: `TXT`
   - Name: `@` (or blank)
   - Value: `v=spf1 include:amazonses.com ~all`

   ### DKIM Records
   Resend will provide 3 CNAME records that look like:
   - `resend._domainkey.prsnl.fyi` → `resend._domainkey.prsnl.fyi.resend.dev`
   - `resend2._domainkey.prsnl.fyi` → `resend2._domainkey.prsnl.fyi.resend.dev`
   - `resend3._domainkey.prsnl.fyi` → `resend3._domainkey.prsnl.fyi.resend.dev`

3. **Verify Domain**
   - After adding DNS records, click "Verify Domain" in Resend
   - DNS propagation can take up to 48 hours, but usually happens within minutes

4. **Update Environment Variables**
   Already configured in `.env`:
   ```
   EMAIL_FROM_ADDRESS=noreply@prsnl.fyi
   EMAIL_FROM_NAME=PRSNL
   ```

## Testing Email Functionality

Once domain is verified, test with:

```bash
# From backend directory
cd backend
source venv/bin/activate
python test_email_resend.py
```

## Alternative for Development

While waiting for domain verification, you can use:
- `onboarding@resend.dev` (Resend's test domain)
- Any email from a verified domain in your Resend account

## Email Types in PRSNL

1. **Verification Email** - Sent when user registers
2. **Magic Link** - Passwordless login
3. **Welcome Email** - After email verification

## Troubleshooting

1. **Domain not verified error**
   - Check DNS records are properly added
   - Wait for DNS propagation
   - Try verifying again in Resend dashboard

2. **Email not received**
   - Check spam folder
   - Verify email logs in database: `SELECT * FROM email_logs ORDER BY created_at DESC LIMIT 10;`
   - Check backend logs: `tail -f backend/backend.log | grep -i email`

3. **Test email addresses**
   - Use real email addresses for testing
   - Resend blocks common test domains (example.com, test.com, etc.)
   - For automated testing, use `delivered@resend.dev`