#!/bin/bash
# Start Cloudflare tunnel for PRSNL

echo "Starting Cloudflare tunnel for prsnl.fyi..."
echo "Press Ctrl+C to stop"
echo ""
echo "Your site will be available at:"
echo "  - https://prsnl.fyi"
echo "  - https://www.prsnl.fyi"
echo "  - https://api.prsnl.fyi"
echo ""

cloudflared tunnel run prsnl-tunnel