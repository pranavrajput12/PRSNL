# Updating FusionAuth Admin Email

This guide explains how to update the admin email address in FusionAuth for the PRSNL application.

## Prerequisites

- FusionAuth instance running (check with `docker compose -f docker-compose.auth.yml ps`)
- FusionAuth API key (found in `fusionauth/kickstart/kickstart.json`)
- Access to the FusionAuth API

## Methods to Update Admin Email

### Method 1: Using FusionAuth API

1. **Find the Admin User ID**

First, search for the admin user using the current email:

```bash
curl -X POST http://localhost:9011/api/user/search \
  -H "Authorization: bf69486b-4733-4470-a592-f1bfce7af580" \
  -H "Content-Type: application/json" \
  -d '{
    "search": {
      "queryString": "email:admin@prsnl.local",
      "numberOfResults": 1
    }
  }'
```

2. **Update the User Email**

Once you have the user ID, update the email:

```bash
curl -X PATCH http://localhost:9011/api/user/{USER_ID} \
  -H "Authorization: bf69486b-4733-4470-a592-f1bfce7af580" \
  -H "Content-Type: application/json" \
  -d '{
    "user": {
      "email": "new-admin@prsnl.fyi",
      "verified": true
    }
  }'
```

### Method 2: Using the Python Script

A Python script is provided to help with this process:

```bash
# Run the script (dry run by default)
python3 update_fusionauth_admin.py
```

To actually update the email, modify the script and uncomment the update section.

### Method 3: Using FusionAuth UI

1. Access FusionAuth admin UI at http://localhost:9011
2. Login with current admin credentials:
   - Email: `admin@prsnl.local`
   - Password: `prsnl_admin_2024!`
3. Navigate to Users → Search for the admin user
4. Click on the user and update the email address
5. Save changes

## Important Considerations

1. **Update Kickstart Configuration**
   
   After changing the admin email, update the kickstart configuration to reflect the new email:
   
   ```bash
   # Edit fusionauth/kickstart/kickstart.json
   # Change line 4: "adminEmail": "admin@prsnl.local"
   # To: "adminEmail": "new-admin@prsnl.fyi"
   ```

2. **Database Direct Update (Emergency Only)**
   
   If API access is not available, you can update directly in the database:
   
   ```sql
   -- Connect to FusionAuth database
   psql -h localhost -p 5432 -U pronav -d fusionauth
   
   -- Update admin email
   UPDATE users 
   SET email = 'new-admin@prsnl.fyi' 
   WHERE email = 'admin@prsnl.local';
   ```

3. **Verification Status**
   
   Ensure the admin user remains verified after the email change to prevent login issues.

4. **Session Management**
   
   Active sessions will remain valid after email change, but users will need to use the new email for future logins.

## Troubleshooting

### Cannot Find Admin User

If the admin user is not found, it might be because:
- FusionAuth hasn't been initialized with kickstart
- The admin user was created with a different email
- Database connection issues

### API Returns 404

This could indicate:
- Wrong user ID
- User doesn't exist
- API endpoint has changed

### Permission Denied

Ensure you're using the correct API key with sufficient permissions.

## Security Notes

- Always use HTTPS in production environments
- Rotate API keys regularly
- Keep admin credentials secure
- Consider enabling 2FA for admin accounts

## Related Configuration

- Admin password: Can be changed through FusionAuth UI or API
- API keys: Managed in FusionAuth → Settings → API Keys
- Email templates: Customizable in FusionAuth → Customizations → Email Templates