#!/usr/bin/env python3
"""Setup and configuration script for ChatGPT Investor automation system."""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any

def print_header(title: str):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n--- {title} ---")

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required")
        sys.exit(1)
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

def install_dependencies():
    """Install required Python packages."""
    print_section("Installing Dependencies")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        return False
    return True

def setup_configuration():
    """Set up configuration interactively."""
    print_section("Configuration Setup")
    
    config_path = Path("config/config.json")
    env_path = Path("config/.env")
    
    # Load existing config if it exists
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = json.load(f)
        print("📁 Existing configuration found")
    else:
        print("📄 Creating new configuration")
        config = {
            "openai": {"api_key": "", "model": "gpt-4o", "temperature": 0.7},
            "email": {"smtp_server": "smtp.gmail.com", "smtp_port": 587, "sender_email": "", "sender_password": "", "recipients": []},
            "trading": {"max_cash_per_trade": 1000, "default_stop_loss_percent": 0.15, "max_portfolio_positions": 10, "enable_stop_loss": True},
            "schedule": {"daily_run_time": "19:00", "timezone": "America/New_York"},
            "api": {"host": "0.0.0.0", "port": 5000, "debug": False},
            "data": {"portfolio_csv": "chatgpt_portfolio_update.csv", "trade_log_csv": "chatgpt_trade_log.csv"}
        }
    
    # Interactive configuration
    print("\n🔧 Configuration Wizard")
    print("Press Enter to keep existing values, or type new values:")
    
    # OpenAI Configuration
    print("\n📡 OpenAI Configuration:")
    current_key = "***configured***" if config["openai"]["api_key"] else "not set"
    api_key = input(f"OpenAI API Key ({current_key}): ").strip()
    if api_key:
        config["openai"]["api_key"] = api_key
    
    model = input(f"OpenAI Model ({config['openai']['model']}): ").strip()
    if model:
        config["openai"]["model"] = model
    
    # Email Configuration
    print("\n📧 Email Configuration:")
    sender = input(f"Sender Email ({config['email']['sender_email']}): ").strip()
    if sender:
        config["email"]["sender_email"] = sender
    
    password = input(f"Email Password (use App Password for Gmail): ").strip()
    if password:
        config["email"]["sender_password"] = password
    
    recipients_str = input(f"Recipients (comma-separated): ").strip()
    if recipients_str:
        config["email"]["recipients"] = [email.strip() for email in recipients_str.split(",")]
    
    # Trading Configuration
    print("\n💰 Trading Configuration:")
    max_trade = input(f"Max Cash Per Trade ({config['trading']['max_cash_per_trade']}): ").strip()
    if max_trade:
        config["trading"]["max_cash_per_trade"] = float(max_trade)
    
    max_positions = input(f"Max Portfolio Positions ({config['trading']['max_portfolio_positions']}): ").strip()
    if max_positions:
        config["trading"]["max_portfolio_positions"] = int(max_positions)
    
    # Schedule Configuration
    print("\n⏰ Schedule Configuration:")
    run_time = input(f"Daily Run Time ({config['schedule']['daily_run_time']}): ").strip()
    if run_time:
        config["schedule"]["daily_run_time"] = run_time
    
    # Save configuration
    config_path.parent.mkdir(exist_ok=True)
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    # Create .env file
    env_content = f"""# Environment variables for ChatGPT Investor
OPENAI_API_KEY={config['openai']['api_key']}
EMAIL_SENDER={config['email']['sender_email']}
EMAIL_PASSWORD={config['email']['sender_password']}
EMAIL_RECIPIENTS={','.join(config['email']['recipients'])}
"""
    
    with open(env_path, 'w') as f:
        f.write(env_content)
    
    print(f"✅ Configuration saved to {config_path}")
    print(f"✅ Environment file created at {env_path}")
    
    return config

def test_configuration(config: Dict[str, Any]):
    """Test the configuration by running API tests."""
    print_section("Testing Configuration")
    
    # Test imports
    try:
        from core.config_manager import ConfigManager
        from core.analyzer import InvestmentAnalyzer  
        from core.ai_decision import AIDecisionMaker
        from notifications.email_sender import EmailNotifier
        print("✅ All modules import successfully")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    
    # Test configuration loading
    try:
        config_manager = ConfigManager()
        summary = config_manager.get_summary()
        
        print("\n📊 Configuration Summary:")
        print(f"  OpenAI Configured: {'✅' if summary['openai_configured'] else '❌'}")
        print(f"  Email Configured: {'✅' if summary['email_configured'] else '❌'}")
        print(f"  Recipients: {summary['recipients_count']}")
        print(f"  Max Cash/Trade: ${summary['trading_params']['max_cash_per_trade']:,.2f}")
        print(f"  Daily Run Time: {summary['schedule']['daily_run_time']}")
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False
    
    return True

def create_startup_scripts():
    """Create convenient startup scripts."""
    print_section("Creating Startup Scripts")
    
    # API startup script
    api_script = """#!/bin/bash
# Start the ChatGPT Investor API server

cd "$(dirname "$0")"
export PYTHONPATH="$(pwd):$PYTHONPATH"

echo "Starting ChatGPT Investor API..."
python3 api/app.py
"""
    
    with open("start_api.sh", "w") as f:
        f.write(api_script)
    os.chmod("start_api.sh", 0o755)
    
    # Test script
    test_script = """#!/bin/bash
# Test the ChatGPT Investor system

cd "$(dirname "$0")"
export PYTHONPATH="$(pwd):$PYTHONPATH"

echo "Testing ChatGPT Investor system..."
python3 scheduler/daily_runner.py --test
"""
    
    with open("test_system.sh", "w") as f:
        f.write(test_script)
    os.chmod("test_system.sh", 0o755)
    
    # Run once script
    run_script = """#!/bin/bash
# Run automation once immediately

cd "$(dirname "$0")"
export PYTHONPATH="$(pwd):$PYTHONPATH"

echo "Running automation immediately..."
python3 scheduler/daily_runner.py --run-now
"""
    
    with open("run_once.sh", "w") as f:
        f.write(run_script)
    os.chmod("run_once.sh", 0o755)
    
    print("✅ Created startup scripts:")
    print("  - start_api.sh (start API server)")
    print("  - test_system.sh (test configuration)")
    print("  - run_once.sh (run automation immediately)")
    print("  - scheduler/start_scheduler.sh (start daily scheduler)")

def create_systemd_service():
    """Create a systemd service file for automation."""
    print_section("System Service Setup")
    
    current_user = os.getenv('USER', 'ubuntu')
    project_dir = Path.cwd().resolve()
    
    service_content = f"""[Unit]
Description=ChatGPT Investor Background Service
After=network.target
Wants=network-online.target

[Service]
Type=simple
User={current_user}
Group={current_user}
WorkingDirectory={project_dir}
Environment=PYTHONPATH={project_dir}
Environment=HOME=/home/{current_user}
ExecStart=/usr/bin/python3 {project_dir}/scheduler/background_service.py
Restart=always
RestartSec=30
StandardOutput=journal
StandardError=journal
SyslogIdentifier=chatgpt-investor

# Resource limits
LimitNOFILE=1024
MemoryLimit=512M

[Install]
WantedBy=multi-user.target
"""
    
    service_path = Path("chatgpt-investor.service")
    with open(service_path, "w") as f:
        f.write(service_content)
    
    print(f"✅ Created systemd service file: {service_path}")
    print("\n📝 To install the service (requires sudo):")
    print(f"  sudo cp {service_path} /etc/systemd/system/")
    print("  sudo systemctl daemon-reload")
    print("  sudo systemctl enable chatgpt-investor")
    print("  sudo systemctl start chatgpt-investor")

def print_next_steps():
    """Print next steps for the user."""
    print_header("Setup Complete! 🎉")
    
    print("\n📋 Next Steps:")
    print("\n1. Test your configuration:")
    print("   ./test_system.sh")
    
    print("\n2. Run automation once to verify:")
    print("   ./run_once.sh")
    
    print("\n3. Start the API server (in background):")
    print("   ./start_api.sh &")
    
    print("\n4. Start the daily scheduler:")
    print("   ./scheduler/start_scheduler.sh")
    
    print("\n5. Or install as a system service:")
    print("   sudo cp chatgpt-investor.service /etc/systemd/system/")
    print("   sudo systemctl enable chatgpt-investor")
    print("   sudo systemctl start chatgpt-investor")
    
    print("\n📧 Email Schedule:")
    print("   Daily reports will be sent at 7:00 PM EST")
    print("   Stop-loss alerts sent immediately when triggered")
    
    print("\n🔧 API Endpoints:")
    print("   http://localhost:5000/api/portfolio/summary")
    print("   http://localhost:5000/api/automation/run-daily")
    
    print("\n📁 Important Files:")
    print("   config/config.json - Main configuration")
    print("   config/.env - Environment variables")
    print("   logs/ - Application logs")
    
    print("\n⚠️  Security Notes:")
    print("   - Keep your OpenAI API key secure")
    print("   - Use app passwords for Gmail")
    print("   - Review all trades before execution")

def main():
    """Main setup function."""
    print_header("ChatGPT Investor Automation Setup")
    
    # Check Python version
    print_section("System Check")
    check_python_version()
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Setup configuration
    config = setup_configuration()
    
    # Test configuration
    if not test_configuration(config):
        print("\n⚠️  Configuration test failed. Please check your settings.")
        sys.exit(1)
    
    # Create startup scripts
    create_startup_scripts()
    
    # Create systemd service
    create_systemd_service()
    
    # Print next steps
    print_next_steps()

if __name__ == "__main__":
    main()