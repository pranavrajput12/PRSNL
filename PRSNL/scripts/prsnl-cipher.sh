#!/bin/bash
# PRSNL Cipher Memory Helper
# Since the current Cipher version doesn't support Azure OpenAI directly,
# we'll use a file-based memory system that can be easily searched

CIPHER_DIR="/Users/pronav/Personal Knowledge Base/PRSNL/.cipher-memories"
mkdir -p "$CIPHER_DIR"

case "$1" in
    "store"|"add")
        shift
        TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
        echo "[$TIMESTAMP] $*" >> "$CIPHER_DIR/memories.log"
        echo "✅ Memory stored: $*"
        ;;
    
    "recall"|"search")
        shift
        if [ -z "$1" ]; then
            # Show recent memories
            echo "📚 Recent memories:"
            tail -20 "$CIPHER_DIR/memories.log" 2>/dev/null || echo "No memories found"
        else
            # Search for specific memory
            echo "🔍 Searching for: $*"
            grep -i "$*" "$CIPHER_DIR"/*.log "$CIPHER_DIR"/*.md 2>/dev/null | sed 's/^.*\/\([^/]*\):/[\1] /' || echo "No matching memories found"
        fi
        ;;
    
    "session")
        shift
        DATE=$(date +"%Y-%m-%d")
        vim "$CIPHER_DIR/$DATE-session.md"
        ;;
    
    "list")
        echo "📁 Memory files:"
        ls -la "$CIPHER_DIR"
        ;;
    
    *)
        echo "PRSNL Cipher Memory System"
        echo "Usage:"
        echo "  $0 store <memory>     - Store a new memory"
        echo "  $0 recall [search]    - Recall memories (optional search term)"
        echo "  $0 session           - Edit today's session notes"
        echo "  $0 list              - List all memory files"
        echo ""
        echo "Examples:"
        echo "  $0 store \"Fixed login bug with force click option\""
        echo "  $0 recall \"login bug\""
        echo "  $0 session"
        ;;
esac