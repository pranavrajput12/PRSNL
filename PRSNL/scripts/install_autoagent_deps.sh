#!/bin/bash

echo "Installing AutoAgent dependencies for PRSNL backend..."

# Navigate to backend directory
cd /Users/pronav/Personal\ Knowledge\ Base/PRSNL/backend

# Install key AutoAgent dependencies that are missing
pip3 install inquirer prompt_toolkit chromadb litellm==1.55.0 instructor browsergym==0.13.0

echo "AutoAgent dependencies installed!"