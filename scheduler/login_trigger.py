#!/usr/bin/env python3
"""Login-triggered trading report system - runs when you log in after 4PM EST."""

import json
import logging
import os
import sys
from datetime import datetime, time
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).resolve().parents[1]))

from core.config_manager import ConfigManager
from core.analyzer import InvestmentAnalyzer
from core.ai_decision import AIDecisionMaker
from notifications.simple_email_sender import SimpleEmailNotifier

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def is_after_trading_hours() -> bool:
    """Check if current time is after 4PM EST (market close)."""
    now = datetime.now()
    
    # Convert to EST (approximate - ignoring DST for simplicity)
    # In production, you'd want proper timezone handling
    market_close = time(16, 0)  # 4:00 PM
    current_time = now.time()
    
    return current_time >= market_close


def is_trading_day() -> bool:
    """Check if today is a trading day (Monday-Friday)."""
    return datetime.now().weekday() < 5  # 0=Monday, 4=Friday


def should_send_report() -> bool:
    """Determine if we should send a trading report now."""
    if not is_trading_day():
        logger.info("Weekend - no trading report needed")
        return False
    
    if not is_after_trading_hours():
        logger.info("Markets still open - waiting until after 4PM EST")
        return False
    
    return True


def send_trading_report():
    """Generate and send trading report via email."""
    try:
        logger.info("🔍 Generating portfolio analysis...")
        
        # Initialize components
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        analyzer = InvestmentAnalyzer(config)
        ai_decision_maker = AIDecisionMaker(config)
        email_notifier = SimpleEmailNotifier(config)
        
        # Generate comprehensive analysis
        analysis_report = analyzer.generate_analysis_report()
        
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
            # Send immediate stop-loss alert
            email_notifier.send_alert(
                "🚨 URGENT: Stop Loss Triggered",
                f"{len(stop_loss_alerts)} position(s) have hit their stop-loss levels.",
                {'triggered_positions': [f"{alert['ticker']}: ${alert['current_price']:.2f}" for alert in stop_loss_alerts]}
            )
        
        # Generate AI trading decisions
        logger.info("🤖 Generating AI trading decisions...")
        decisions = ai_decision_maker.make_trading_decision(analysis_report)
        
        # Log AI decisions
        decision_list = decisions.get('decisions', [])
        logger.info(f"📋 AI Decisions: {len(decision_list)} recommendations")
        
        for decision in decision_list:
            action = decision.get('action', 'unknown').upper()
            ticker = decision.get('ticker', 'N/A')
            shares = decision.get('shares', 'N/A')
            conviction = decision.get('conviction', 'N/A')
            logger.info(f"  - {action} {ticker}: {shares} shares (Conviction: {conviction})")
        
        # Send email report
        logger.info("📧 Sending trading report email...")
        email_success = email_notifier.send_daily_report(analysis_report, decisions)
        
        if email_success:
            logger.info("✅ Trading report sent successfully to kreddy.2027@gmail.com")
            print("✅ Trading report email sent!")
            print("📧 Check your inbox for AI trading recommendations")
        else:
            logger.error("❌ Failed to send trading report email")
            print("❌ Failed to send email - check configuration")
        
        return email_success
        
    except Exception as e:
        logger.error(f"❌ Failed to generate trading report: {e}")
        print(f"❌ Error: {e}")
        return False


def main():
    """Main entry point - check conditions and send report if appropriate."""
    print("🔍 Checking if trading report should be sent...")
    
    if should_send_report():
        print("✅ Conditions met - generating trading report...")
        success = send_trading_report()
        if success:
            print("🎉 Trading report sent! Check your email.")
        else:
            print("❌ Failed to send report.")
    else:
        print("⏭️  No report needed right now:")
        if not is_trading_day():
            print("   - Weekend (markets closed)")
        elif not is_after_trading_hours():
            current_time = datetime.now().strftime('%I:%M %p')
            print(f"   - Markets still open (current time: {current_time}, closes at 4:00 PM EST)")
        
        print("💡 Run this script after 4PM EST on trading days for reports")


if __name__ == '__main__':
    main()