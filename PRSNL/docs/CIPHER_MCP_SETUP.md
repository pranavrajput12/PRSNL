# Cipher MCP Setup for Automatic Memory in Claude Code

## What's Actually Required for Automatic Memory

For Cipher to automatically save memories from Claude Code conversations, it needs to be configured as an MCP (Model Context Protocol) server. Just running `cipher` on the command line is NOT enough.

## Setup Steps

### 1. Azure OpenAI Proxy (Already Done)
- Proxy script: `/scripts/cipher-azure-proxy.py`
- Runs on port 8002
- Handles Azure OpenAI authentication

### 2. MCP Wrapper Script (Created)
- Location: `/scripts/cipher-mcp-wrapper.sh`
- Ensures proxy is running
- Sets environment variables
- Launches Cipher in MCP server mode

### 3. Claude Desktop Configuration (Updated)
- File: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Added Cipher as an MCP server
- Points to the wrapper script

### 4. Restart Claude Desktop (Required)
**IMPORTANT**: You must restart Claude Desktop for the MCP server to connect!

1. Quit Claude Desktop completely (Cmd+Q)
2. Start Claude Desktop again
3. Look for the MCP indicator in the bottom-right of the input box
4. You should see "cipher" listed as a connected server

## How It Works

1. Claude Desktop starts the Cipher MCP server via the wrapper script
2. The wrapper ensures the Azure proxy is running
3. Cipher connects to Claude via MCP protocol
4. All conversations are automatically saved to Cipher's memory
5. You can recall memories using `cipher recall` commands

## Verification

After restarting Claude Desktop:
- Check MCP servers: Look for the server icon in the input box
- Test memory: Have a conversation and then use `cipher recall` to verify it was saved

## Troubleshooting

If Cipher doesn't appear as an MCP server:
1. Check the wrapper script has execute permissions
2. Verify the Azure proxy is running: `lsof -ti:8002`
3. Check Claude Desktop logs for errors
4. Ensure the config.json syntax is valid

## Manual Testing

You can still test Cipher manually:
```bash
export OPENAI_API_KEY="sk-cipher-azure-proxy"
export OPENAI_BASE_URL="http://localhost:8002/v1"
cipher "test message"
cipher recall "test"
```

But for automatic memory, the MCP configuration is essential!