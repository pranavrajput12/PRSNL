# PRSNL Email Configuration (Current Implementation)

## Overview
Currently focusing on core authentication emails only:
- **Signup Verification**
- **Welcome Email** (post-verification)
- **Magic Link Login**

## Email Addresses Configuration

### 1. Verification Email
- **From**: noreply@fyi.prsnl.fyi
- **From Name**: PRSNL Security
- **Subject**: "Verify your email for PRSNL"
- **Purpose**: Transactional email for account verification

### 2. Welcome Email
- **From**: hello@fyi.prsnl.fyi
- **From Name**: PRSNL Brain Trust
- **Subject**: "Your brain just got an upgrade 🧠"
- **Purpose**: Onboarding email after verification
- **Tone**: Excited professor meeting a promising student

### 3. Magic Link
- **From**: noreply@fyi.prsnl.fyi
- **From Name**: PRSNL Security
- **Subject**: "Your magic sign-in link for PRSNL"
- **Purpose**: Passwordless authentication

## Implementation Details

### Email Service Configuration
Located in `/backend/app/services/email/email_config.py`:
- Centralized email type definitions
- From address mappings
- Subject line templates
- Tone guidelines

### Email Flow
1. **User Registration** → Verification email sent
2. **Email Verified** → Welcome email sent automatically
3. **Magic Link Request** → Login link sent

## DNS Configuration Required

For the domain `fyi.prsnl.fyi`, you need to verify in Resend:
- Add SPF, DKIM, and DMARC records
- Currently verified and working

## Testing

Test emails can be sent to:
- `delivered@resend.dev` - Resend's test address
- Any real email address

## Future Email Types (Not Implemented)

These are planned but not yet implemented:
- **insights@fyi.prsnl.fyi** - Weekly intelligence reports
- **cortex@fyi.prsnl.fyi** - Code insights
- **brain@fyi.prsnl.fyi** - Milestone achievements
- **capture@fyi.prsnl.fyi** - Email-to-capture feature

## Current Status
✅ All authentication emails are configured and working with proper from addresses and branding.