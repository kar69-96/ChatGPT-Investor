"""Daily automation runner for the ChatGPT Investor system."""

import json
import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any

import schedule
import requests
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Create logs directory
Path('logs').mkdir(exist_ok=True)


class DailyAutomationRunner:
    """Handles daily execution of trading automation."""
    
    def __init__(self, config_path: str = None):
        self.config = self._load_config(config_path)
        self.api_base_url = f"http://{self.config['api']['host']}:{self.config['api']['port']}"
        self.schedule_config = self.config.get('schedule', {})
        self.running = False
        
    def _load_config(self, config_path: str = None) -> Dict[str, Any]:
        """Load configuration from file and environment."""
        if config_path is None:
            config_path = Path(__file__).resolve().parents[1] / 'config' / 'config.json'
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Override with environment variables
        if os.getenv('OPENAI_API_KEY'):
            config['openai']['api_key'] = os.getenv('OPENAI_API_KEY')
        if os.getenv('EMAIL_SENDER'):
            config['email']['sender_email'] = os.getenv('EMAIL_SENDER')
        if os.getenv('EMAIL_PASSWORD'):
            config['email']['sender_password'] = os.getenv('EMAIL_PASSWORD')
        if os.getenv('EMAIL_RECIPIENTS'):
            config['email']['recipients'] = os.getenv('EMAIL_RECIPIENTS').split(',')
        
        return config
    
    def run_daily_automation(self):
        """Execute the daily trading automation workflow."""
        logger.info("=== Starting Daily Trading Automation ===")
        start_time = datetime.now()
        
        try:
            # Check if it's a weekend
            if self._is_weekend():
                logger.info("Weekend detected - skipping trading automation")
                return
            
            # Run the automation via API
            logger.info("Calling automation API endpoint...")
            response = requests.post(f"{self.api_base_url}/api/automation/run-daily", timeout=120)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    logger.info("Daily automation completed successfully")
                    self._log_automation_result(result.get('data', {}))
                else:
                    logger.error(f"Automation API returned error: {result.get('error')}")
            else:
                logger.error(f"Automation API request failed: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to connect to automation API: {e}")
            self._send_error_notification(f"API Connection Error: {e}")
            
        except Exception as e:
            logger.error(f"Unexpected error in daily automation: {e}")
            self._send_error_notification(f"Automation Error: {e}")
        
        end_time = datetime.now()
        duration = end_time - start_time
        logger.info(f"=== Daily automation completed in {duration.total_seconds():.1f} seconds ===")
    
    def _is_weekend(self) -> bool:
        """Check if today is a weekend (markets closed)."""
        return datetime.now().weekday() >= 5  # Saturday=5, Sunday=6
    
    def _log_automation_result(self, result_data: Dict[str, Any]):
        """Log the results of automation run."""
        analysis = result_data.get('analysis', {})
        decisions = result_data.get('decisions', {})
        
        portfolio = analysis.get('portfolio', {})
        logger.info(f"Portfolio Summary:")
        logger.info(f"  Total Equity: ${portfolio.get('total_equity', 0):,.2f}")
        logger.info(f"  Cash Balance: ${portfolio.get('cash_balance', 0):,.2f}")
        logger.info(f"  Total P&L: ${portfolio.get('total_pnl', 0):,.2f}")
        logger.info(f"  Positions: {portfolio.get('positions_count', 0)}")
        
        decision_list = decisions.get('decisions', [])
        logger.info(f"AI Decisions: {len(decision_list)} actions")
        for decision in decision_list:
            action = decision.get('action', 'unknown').upper()
            ticker = decision.get('ticker', 'N/A')
            logger.info(f"  {action} {ticker}: {decision.get('reason', 'No reason provided')}")
        
        stop_loss_alerts = result_data.get('stop_loss_alerts', 0)
        if stop_loss_alerts > 0:
            logger.warning(f"STOP LOSS ALERTS: {stop_loss_alerts} position(s) triggered")
    
    def _send_error_notification(self, error_message: str):
        """Send error notification via API if possible."""
        try:
            requests.post(f"{self.api_base_url}/api/email/alert", 
                         json={
                             'type': 'Scheduler Error',
                             'message': error_message,
                             'data': {'timestamp': datetime.now().isoformat()}
                         },
                         timeout=30)
        except:
            logger.error("Failed to send error notification email")
    
    def schedule_daily_runs(self):
        """Set up the daily schedule for automation."""
        run_time = self.schedule_config.get('daily_run_time', '19:00')
        
        logger.info(f"Scheduling daily automation runs at {run_time}")
        schedule.every().day.at(run_time).do(self.run_daily_automation)
        
        # Also schedule a health check every hour during market hours
        schedule.every().hour.do(self._health_check)
        
        self.running = True
        logger.info("Daily scheduler started successfully")
    
    def _health_check(self):
        """Perform hourly health check of the system."""
        try:
            # Only run health checks during market hours (9 AM - 4 PM EST)
            current_hour = datetime.now().hour
            if current_hour < 9 or current_hour > 16:
                return
            
            # Check API health
            response = requests.get(f"{self.api_base_url}/", timeout=10)
            if response.status_code != 200:
                logger.warning(f"API health check failed: {response.status_code}")
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
    
    def run_scheduler(self):
        """Main scheduler loop."""
        logger.info("Starting ChatGPT Investor Daily Scheduler")
        logger.info(f"API Base URL: {self.api_base_url}")
        
        # Set up schedules
        self.schedule_daily_runs()
        
        # Main loop
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except KeyboardInterrupt:
                logger.info("Scheduler stopped by user")
                break
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(60)  # Wait before retrying
    
    def stop_scheduler(self):
        """Stop the scheduler gracefully."""
        logger.info("Stopping scheduler...")
        self.running = False
    
    def run_once_now(self):
        """Run automation immediately (for testing)."""
        logger.info("Running automation immediately...")
        self.run_daily_automation()


def main():
    """Main entry point for the scheduler."""
    import argparse
    
    parser = argparse.ArgumentParser(description='ChatGPT Investor Daily Scheduler')
    parser.add_argument('--config', help='Path to config file', default=None)
    parser.add_argument('--run-now', action='store_true', help='Run automation immediately and exit')
    parser.add_argument('--test', action='store_true', help='Run in test mode (no actual scheduling)')
    
    args = parser.parse_args()
    
    # Initialize runner
    runner = DailyAutomationRunner(args.config)
    
    if args.run_now:
        # Run once and exit
        runner.run_once_now()
    elif args.test:
        # Test mode - just validate configuration
        logger.info("Test mode - validating configuration...")
        logger.info(f"API URL: {runner.api_base_url}")
        logger.info(f"Schedule time: {runner.schedule_config.get('daily_run_time')}")
        logger.info("Configuration validated successfully")
    else:
        # Normal scheduler mode
        try:
            runner.run_scheduler()
        except KeyboardInterrupt:
            logger.info("Scheduler stopped")
        except Exception as e:
            logger.error(f"Scheduler failed: {e}")
            raise


if __name__ == '__main__':
    main()