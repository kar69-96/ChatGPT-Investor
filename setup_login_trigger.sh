#!/bin/bash

# Setup login trigger for ChatGPT Investor trading reports

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TRIGGER_SCRIPT="$SCRIPT_DIR/scheduler/login_trigger.py"

echo "🔧 Setting up login trigger for ChatGPT Investor"
echo "This will automatically send trading reports when you log in after 4PM EST"
echo ""

# Create the profile addition
PROFILE_ADDITION="
# ChatGPT Investor - Auto-send trading report on login after 4PM EST
if [ -f \"$TRIGGER_SCRIPT\" ]; then
    python3 \"$TRIGGER_SCRIPT\" 2>/dev/null &
fi
"

# Determine which profile file to use
if [ -f ~/.zshrc ]; then
    PROFILE_FILE=~/.zshrc
    SHELL_NAME="zsh"
elif [ -f ~/.bash_profile ]; then
    PROFILE_FILE=~/.bash_profile
    SHELL_NAME="bash"
elif [ -f ~/.bashrc ]; then
    PROFILE_FILE=~/.bashrc
    SHELL_NAME="bash"
else
    echo "❌ Could not find shell profile file"
    echo "Please manually add the following to your shell profile:"
    echo "$PROFILE_ADDITION"
    exit 1
fi

echo "📝 Detected shell: $SHELL_NAME"
echo "📄 Profile file: $PROFILE_FILE"
echo ""

# Check if already added
if grep -q "ChatGPT Investor" "$PROFILE_FILE" 2>/dev/null; then
    echo "✅ Login trigger already configured in $PROFILE_FILE"
else
    echo "Adding login trigger to $PROFILE_FILE..."
    echo "$PROFILE_ADDITION" >> "$PROFILE_FILE"
    echo "✅ Login trigger added successfully"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "📧 How it works:"
echo "  - When you log in/open terminal after 4PM EST on trading days"
echo "  - The system automatically checks your portfolio"
echo "  - Generates AI trading recommendations"  
echo "  - Sends detailed email report to kreddy.2027@gmail.com"
echo "  - Runs silently in background (no terminal output)"
echo ""
echo "🔧 Manual commands:"
echo "  Test now:           python3 scheduler/login_trigger.py"
echo "  Background service: $SCRIPT_DIR/.env -> RUN_COMMAND"
echo ""
echo "⚠️  Note: You may need to restart your terminal or run 'source $PROFILE_FILE' for changes to take effect"