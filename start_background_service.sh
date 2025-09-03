#!/bin/bash

# Start the ChatGPT Investor Background Service

set -e

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🚀 Starting ChatGPT Investor Background Service"
echo "Project directory: $SCRIPT_DIR"

# Change to project root
cd "$SCRIPT_DIR"

# Skip virtual environment for now (packages installed globally)
echo "Using system Python with globally installed packages..."

# Set PYTHONPATH
export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"

# Create logs directory
mkdir -p logs

# Start the background service
echo "Starting continuous background service..."
echo "This will run forever and send daily reports at 7PM EST"
echo "Press Ctrl+C to stop the service"
echo ""

python3 scheduler/background_service.py "$@"