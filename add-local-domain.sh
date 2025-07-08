#!/bin/bash

# Script to add new local domain configurations

PROJECT_NAME=$1
FRONTEND_PORT=$2
BACKEND_PORT=$3

if [ -z "$PROJECT_NAME" ] || [ -z "$FRONTEND_PORT" ]; then
    echo "Usage: $0 <project-name> <frontend-port> [backend-port]"
    echo "Example: $0 myapp 3000 8000"
    exit 1
fi

# Create nginx config
NGINX_CONFIG="/usr/local/etc/nginx/servers/${PROJECT_NAME}.conf"

echo "Creating nginx configuration for $PROJECT_NAME..."

if [ -z "$BACKEND_PORT" ]; then
    # Frontend only
    cat > "$NGINX_CONFIG" << EOF
server {
    listen 80;
    server_name ${PROJECT_NAME}.local app.${PROJECT_NAME}.local;

    location / {
        proxy_pass http://localhost:${FRONTEND_PORT};
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}

# Free domain support
server {
    listen 80;
    server_name ~^${PROJECT_NAME}\.(.+)\.nip\.io$;

    location / {
        proxy_pass http://localhost:${FRONTEND_PORT};
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }
}
EOF
else
    # Frontend and Backend
    cat > "$NGINX_CONFIG" << EOF
server {
    listen 80;
    server_name ${PROJECT_NAME}.local app.${PROJECT_NAME}.local;

    location / {
        proxy_pass http://localhost:${FRONTEND_PORT};
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}

server {
    listen 80;
    server_name api.${PROJECT_NAME}.local;

    location / {
        proxy_pass http://localhost:${BACKEND_PORT};
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}

# Free domain support
server {
    listen 80;
    server_name ~^${PROJECT_NAME}\.(.+)\.nip\.io$;

    location / {
        proxy_pass http://localhost:${FRONTEND_PORT};
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }
}

server {
    listen 80;
    server_name ~^api-${PROJECT_NAME}\.(.+)\.nip\.io$;

    location / {
        proxy_pass http://localhost:${BACKEND_PORT};
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
fi

# Add to /etc/hosts
echo "Adding to /etc/hosts..."
echo "127.0.0.1 ${PROJECT_NAME}.local api.${PROJECT_NAME}.local app.${PROJECT_NAME}.local" | sudo tee -a /etc/hosts

# Reload nginx
echo "Reloading nginx..."
nginx -s reload

echo "✅ Domain configuration complete!"
echo ""
echo "Access your project at:"
echo "  - http://${PROJECT_NAME}.local"
[ ! -z "$BACKEND_PORT" ] && echo "  - http://api.${PROJECT_NAME}.local"
echo ""
echo "Or use free domains:"
echo "  - http://${PROJECT_NAME}.127.0.0.1.nip.io"
[ ! -z "$BACKEND_PORT" ] && echo "  - http://api-${PROJECT_NAME}.127.0.0.1.nip.io"
echo "  - http://${PROJECT_NAME}.localtest.me"