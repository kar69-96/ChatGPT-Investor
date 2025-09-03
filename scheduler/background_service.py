#!/usr/bin/env python3
"""Background service that runs ChatGPT Investor continuously without user intervention."""

import json
import logging
import os
import signal
import sys
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional

import schedule
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).resolve().parents[1]))

from core.config_manager import ConfigManager
from core.analyzer import InvestmentAnalyzer
from core.ai_decision import AIDecisionMaker
from notifications.simple_email_sender import SimpleEmailNotifier

# Setup logging
log_dir = Path('logs')
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'background_service.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class BackgroundInvestorService:
    """Continuously running service for automated trading decisions."""
    
    def __init__(self):
        self.running = False
        self.config_manager = ConfigManager()
        self.config = self.config_manager.get_config()
        
        # Initialize components
        self.analyzer = InvestmentAnalyzer(self.config)
        self.ai_decision_maker = AIDecisionMaker(self.config)
        self.email_notifier = SimpleEmailNotifier(self.config)
        
        # Service state
        self.last_daily_run = None
        self.last_health_check = None
        self.error_count = 0
        self.max_errors = 5
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("Background Investor Service initialized")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.stop_service()
    
    def start_service(self):
        """Start the background service."""
        logger.info("🚀 Starting ChatGPT Investor Background Service")
        logger.info("🔧 Service Configuration:")
        logger.info(f"  - Daily run time: {self.config.get('schedule', {}).get('daily_run_time', '19:00')}")
        logger.info(f"  - Email notifications: {bool(self.config.get('email', {}).get('sender_email'))}")
        logger.info(f"  - AI model: {self.config.get('openai', {}).get('model', 'gpt-4o')}")
        logger.info(f"  - Max positions: {self.config.get('trading', {}).get('max_portfolio_positions', 10)}")
        
        self.running = True
        
        # Schedule daily automation
        daily_time = self.config.get('schedule', {}).get('daily_run_time', '19:00')
        schedule.every().day.at(daily_time).do(self._run_daily_automation)
        
        # Schedule health checks every 30 minutes
        schedule.every(30).minutes.do(self._health_check)
        
        # Schedule configuration reload every hour
        schedule.every().hour.do(self._reload_configuration)
        
        # Run initial health check
        self._health_check()
        
        logger.info("📅 Scheduled tasks:")
        logger.info(f"  - Daily automation: {daily_time}")
        logger.info("  - Health checks: Every 30 minutes")
        logger.info("  - Config reload: Every hour")
        
        # Send startup notification
        self._send_startup_notification()
        
        # Main service loop
        self._run_service_loop()
    
    def _run_service_loop(self):
        """Main service loop that runs continuously."""
        logger.info("🔄 Starting main service loop...")
        
        while self.running:
            try:
                # Run pending scheduled tasks
                schedule.run_pending()
                
                # Sleep for 60 seconds before next check
                time.sleep(60)
                
            except KeyboardInterrupt:
                logger.info("Service interrupted by user")
                break
            except Exception as e:
                logger.error(f"Error in service loop: {e}")
                self.error_count += 1
                
                if self.error_count >= self.max_errors:
                    logger.error(f"Maximum error count ({self.max_errors}) reached, shutting down")
                    self._send_error_notification(f"Service shutting down due to repeated errors: {e}")
                    break
                
                # Wait before retrying
                time.sleep(300)  # 5 minutes
        
        logger.info("📴 Service loop ended")
    
    def _run_daily_automation(self):
        """Execute the daily trading automation workflow."""
        logger.info("=" * 60)
        logger.info("📊 STARTING DAILY AUTOMATION")
        logger.info("=" * 60)
        
        start_time = datetime.now()
        
        try:
            # Check if it's a weekend
            if self._is_weekend():
                logger.info("📅 Weekend detected - skipping trading automation")
                self._send_weekend_notification()
                return
            
            # Generate comprehensive analysis
            logger.info("🔍 Generating portfolio analysis...")
            analysis_report = self.analyzer.generate_analysis_report()
            
            # Log portfolio status
            portfolio = analysis_report.get('portfolio', {})
            logger.info(f"💰 Portfolio Status:")
            logger.info(f"  - Total Equity: ${portfolio.get('total_equity', 0):,.2f}")
            logger.info(f"  - Cash Balance: ${portfolio.get('cash_balance', 0):,.2f}")
            logger.info(f"  - Total P&L: ${portfolio.get('total_pnl', 0):,.2f}")
            logger.info(f"  - Positions: {portfolio.get('positions_count', 0)}")
            
            # Check for urgent stop-loss alerts
            stop_loss_alerts = analysis_report.get('stop_loss_alerts', [])
            if stop_loss_alerts:
                logger.warning(f"🚨 STOP LOSS ALERTS: {len(stop_loss_alerts)} position(s) triggered")
                self._send_stop_loss_alert(stop_loss_alerts)
            
            # Generate AI trading decisions
            logger.info("🤖 Generating AI trading decisions...")
            decisions = self.ai_decision_maker.make_trading_decision(analysis_report)
            
            # Log AI decisions
            decision_list = decisions.get('decisions', [])
            logger.info(f"📋 AI Decisions: {len(decision_list)} recommendations")
            
            for decision in decision_list:
                action = decision.get('action', 'unknown').upper()
                ticker = decision.get('ticker', 'N/A')
                shares = decision.get('shares', 'N/A')
                conviction = decision.get('conviction', 'N/A')
                logger.info(f"  - {action} {ticker}: {shares} shares (Conviction: {conviction})")
            
            # Send daily email report
            logger.info("📧 Sending daily email report...")
            email_success = self.email_notifier.send_daily_report(analysis_report, decisions)
            
            if email_success:
                logger.info("✅ Daily email report sent successfully")
            else:
                logger.error("❌ Failed to send daily email report")
            
            # Update service state
            self.last_daily_run = datetime.now()
            self.error_count = 0  # Reset error count on successful run
            
            # Calculate execution time
            end_time = datetime.now()
            duration = end_time - start_time
            
            logger.info("=" * 60)
            logger.info(f"✅ DAILY AUTOMATION COMPLETED ({duration.total_seconds():.1f}s)")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"❌ Daily automation failed: {e}")
            self.error_count += 1
            
            # Send error notification
            self._send_error_notification(f"Daily automation failed: {str(e)}")
    
    def _health_check(self):
        """Perform system health check."""
        logger.debug("🔍 Performing health check...")
        
        try:
            health_status = {
                'timestamp': datetime.now().isoformat(),
                'service_uptime': self._get_service_uptime(),
                'last_daily_run': self.last_daily_run.isoformat() if self.last_daily_run else 'Never',
                'error_count': self.error_count,
                'config_status': 'OK',
                'components': {}
            }
            
            # Test portfolio data access
            try:
                portfolio_summary = self.analyzer.get_portfolio_summary()
                health_status['components']['portfolio_analyzer'] = 'OK'
            except Exception as e:
                health_status['components']['portfolio_analyzer'] = f'ERROR: {str(e)}'
            
            # Test AI API (without making actual request)
            if self.config.get('openai', {}).get('api_key'):
                health_status['components']['ai_decision_maker'] = 'OK'
            else:
                health_status['components']['ai_decision_maker'] = 'ERROR: No API key'
            
            # Test email configuration
            email_config = self.config.get('email', {})
            if email_config.get('sender_email') and email_config.get('sender_password'):
                health_status['components']['email_notifier'] = 'OK'
            else:
                health_status['components']['email_notifier'] = 'ERROR: Email not configured'
            
            self.last_health_check = datetime.now()
            
            # Log critical issues only
            failed_components = [k for k, v in health_status['components'].items() if 'ERROR' in str(v)]
            if failed_components:
                logger.warning(f"⚠️  Health check found issues: {', '.join(failed_components)}")
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
    
    def _reload_configuration(self):
        """Reload configuration from files."""
        try:
            logger.debug("🔄 Reloading configuration...")
            self.config_manager.reload_config()
            self.config = self.config_manager.get_config()
            
            # Reinitialize components with new config
            self.analyzer = InvestmentAnalyzer(self.config)
            self.ai_decision_maker = AIDecisionMaker(self.config)
            self.email_notifier = SimpleEmailNotifier(self.config)
            
            logger.debug("✅ Configuration reloaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to reload configuration: {e}")
    
    def _is_weekend(self) -> bool:
        """Check if today is a weekend (markets closed)."""
        return datetime.now().weekday() >= 5  # Saturday=5, Sunday=6
    
    def _get_service_uptime(self) -> str:
        """Get service uptime as human-readable string."""
        if hasattr(self, '_start_time'):
            uptime = datetime.now() - self._start_time
            return str(uptime).split('.')[0]  # Remove microseconds
        return "Unknown"
    
    def _send_startup_notification(self):
        """Send notification that service has started."""
        try:
            self._start_time = datetime.now()
            
            self.email_notifier.send_alert(
                "Service Started",
                "ChatGPT Investor Background Service has started successfully.",
                {
                    'start_time': self._start_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'daily_run_time': self.config.get('schedule', {}).get('daily_run_time', '19:00'),
                    'max_positions': self.config.get('trading', {}).get('max_portfolio_positions', 10),
                    'max_per_trade': f"${self.config.get('trading', {}).get('max_cash_per_trade', 1000):,}"
                }
            )
            
            logger.info("📧 Startup notification sent")
            
        except Exception as e:
            logger.error(f"Failed to send startup notification: {e}")
    
    def _send_weekend_notification(self):
        """Send weekend skip notification."""
        try:
            self.email_notifier.send_alert(
                "Weekend - No Trading",
                "Markets are closed for the weekend. Daily automation skipped.",
                {
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'next_trading_day': 'Monday',
                    'service_status': 'Running normally'
                }
            )
            
        except Exception as e:
            logger.debug(f"Weekend notification failed: {e}")
    
    def _send_stop_loss_alert(self, alerts: list):
        """Send urgent stop-loss alert."""
        try:
            alert_details = []
            for alert in alerts:
                alert_details.append(f"{alert['ticker']}: ${alert['current_price']:.2f} (Stop: ${alert['stop_loss']:.2f})")
            
            self.email_notifier.send_alert(
                "🚨 URGENT: Stop Loss Triggered",
                f"{len(alerts)} position(s) have hit their stop-loss levels and require immediate attention.",
                {
                    'triggered_positions': alert_details,
                    'action_required': 'Review and execute sell orders',
                    'urgency': 'HIGH'
                }
            )
            
            logger.info("🚨 Stop-loss alert sent")
            
        except Exception as e:
            logger.error(f"Failed to send stop-loss alert: {e}")
    
    def _send_error_notification(self, error_message: str):
        """Send error notification."""
        try:
            self.email_notifier.send_alert(
                "Service Error",
                f"ChatGPT Investor service encountered an error: {error_message}",
                {
                    'error_count': self.error_count,
                    'max_errors': self.max_errors,
                    'timestamp': datetime.now().isoformat(),
                    'service_status': 'Running' if self.running else 'Stopped'
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to send error notification: {e}")
    
    def stop_service(self):
        """Stop the background service gracefully."""
        logger.info("🛑 Stopping ChatGPT Investor Background Service...")
        self.running = False
        
        # Send shutdown notification
        try:
            self.email_notifier.send_alert(
                "Service Stopped",
                "ChatGPT Investor Background Service has been stopped.",
                {
                    'stop_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'uptime': self._get_service_uptime(),
                    'last_daily_run': self.last_daily_run.isoformat() if self.last_daily_run else 'Never'
                }
            )
        except Exception as e:
            logger.error(f"Failed to send shutdown notification: {e}")
        
        logger.info("📴 Service stopped")


def main():
    """Main entry point for the background service."""
    import argparse
    
    parser = argparse.ArgumentParser(description='ChatGPT Investor Background Service')
    parser.add_argument('--daemon', action='store_true', help='Run as daemon process')
    parser.add_argument('--test', action='store_true', help='Test configuration and exit')
    
    args = parser.parse_args()
    
    if args.test:
        # Test mode - validate configuration
        logger.info("🧪 Testing service configuration...")
        try:
            service = BackgroundInvestorService()
            service._health_check()
            logger.info("✅ Configuration test passed")
            sys.exit(0)
        except Exception as e:
            logger.error(f"❌ Configuration test failed: {e}")
            sys.exit(1)
    
    # Normal service mode
    try:
        service = BackgroundInvestorService()
        
        if args.daemon:
            # TODO: Implement proper daemon mode with pid file
            logger.info("🔧 Daemon mode requested (running in foreground for now)")
        
        service.start_service()
        
    except KeyboardInterrupt:
        logger.info("Service interrupted by user")
    except Exception as e:
        logger.error(f"Service failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()