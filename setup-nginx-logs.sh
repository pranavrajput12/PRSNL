#!/bin/bash
echo "Run this script to fix nginx permissions:"
echo "sudo mkdir -p /usr/local/var/log/nginx"
echo "sudo mkdir -p /usr/local/var/run"
echo "sudo chmod 755 /usr/local/var/log/nginx"
echo "sudo touch /usr/local/var/log/nginx/error.log"
echo "sudo touch /usr/local/var/log/nginx/access.log"
echo "sudo chown -R $(whoami):staff /usr/local/var/log/nginx"