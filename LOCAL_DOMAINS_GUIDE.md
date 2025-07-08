# Local Development Domains Guide

## Quick Access URLs

### PRSNL Project
- **Frontend**: http://prsnl.local
- **API**: http://api.prsnl.local
- **Alternative Frontend**: http://app.prsnl.local

### Free Test Domains (No Setup Required)
These work immediately without any configuration:

#### Using nip.io (Recommended)
- **Frontend**: http://prsnl.127.0.0.1.nip.io
- **API**: http://api-prsnl.127.0.0.1.nip.io
- **Any App**: http://yourapp.127.0.0.1.nip.io

#### Using sslip.io
- **Frontend**: http://prsnl.127-0-0-1.sslip.io
- **API**: http://api-prsnl.127-0-0-1.sslip.io

#### Using localtest.me
- **Frontend**: http://prsnl.localtest.me
- **API**: http://api.prsnl.localtest.me

## How It Works

1. **Local Domains (.local)**: Configured in /etc/hosts and nginx
2. **nip.io**: Wildcard DNS service that maps to IP in the domain name
3. **sslip.io**: Similar to nip.io with SSL support
4. **localtest.me**: Always resolves to 127.0.0.1

## Adding New Projects

### Method 1: Edit nginx config
```bash
sudo nano /usr/local/etc/nginx/servers/yourproject.conf
```

### Method 2: Use the domain manager script
```bash
./add-local-domain.sh yourproject 3000 8000
```

## Accessing from Other Devices

Use your machine's IP with nip.io:
```
http://prsnl.192.168.1.100.nip.io
```

## SSL/HTTPS Support

### Generate certificates with mkcert:
```bash
mkcert prsnl.local "*.prsnl.local"
mkcert prsnl.127.0.0.1.nip.io
```

## Troubleshooting

1. **Domain not working**: Check nginx is running
   ```bash
   brew services list | grep nginx
   ```

2. **Wrong port**: Update nginx config
   ```bash
   sudo nano /usr/local/etc/nginx/servers/prsnl.conf
   nginx -s reload
   ```

3. **Clear DNS cache**:
   ```bash
   sudo dscacheutil -flushcache
   ```

## Production Deployment

When deploying to production, replace local domains with:
- Vercel: yourapp.vercel.app
- Netlify: yourapp.netlify.app
- Railway: yourapp.railway.app
- Your own domain: yourapp.com