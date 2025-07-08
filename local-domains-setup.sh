#!/bin/bash

# Local Domain Setup Script
echo "Setting up local development domains..."

# Add to /etc/hosts
echo "
# Local Development Domains
127.0.0.1 prsnl.local
127.0.0.1 api.prsnl.local
127.0.0.1 app.prsnl.local
127.0.0.1 db.prsnl.local
127.0.0.1 redis.prsnl.local

# Other local projects
127.0.0.1 dev.local
127.0.0.1 test.local
127.0.0.1 staging.local" | sudo tee -a /etc/hosts

# Install dnsmasq for wildcard domains
brew install dnsmasq

# Configure dnsmasq
echo 'address=/.local/127.0.0.1
address=/.test/127.0.0.1
address=/.dev/127.0.0.1' | sudo tee /usr/local/etc/dnsmasq.conf

# Start dnsmasq
sudo brew services start dnsmasq

# Install nginx
brew install nginx

# Install mkcert for local SSL
brew install mkcert
mkcert -install

echo "Local domains configured!"