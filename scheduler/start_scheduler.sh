#!/bin/bash

# ChatGPT Investor Daily Scheduler Startup Script

set -e

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=== ChatGPT Investor Daily Scheduler ==="
echo "Project root: $PROJECT_ROOT"
echo "Starting scheduler..."

# Change to project root
cd "$PROJECT_ROOT"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
elif [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
fi

# Install/upgrade dependencies
echo "Checking dependencies..."
pip install -q -r requirements.txt

# Create logs directory
mkdir -p logs

# Set PYTHONPATH
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# Start the scheduler
echo "Starting daily automation scheduler..."
python3 scheduler/daily_runner.py "$@"