"""Simple email notification system for trading decisions and portfolio updates."""

import smtplib
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class SimpleEmailNotifier:
    """Simple email notifier that works around email module issues."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config.get('email', {})
        self.smtp_server = self.config.get('smtp_server', 'smtp.gmail.com')
        self.smtp_port = self.config.get('smtp_port', 587)
        self.sender_email = self.config.get('sender_email', '')
        self.sender_password = self.config.get('sender_password', '')
        self.recipients = self.config.get('recipients', [])
        
    def send_daily_report(self, 
                         portfolio_analysis: Dict[str, Any], 
                         ai_decisions: Dict[str, Any]) -> bool:
        """Send daily portfolio report with AI trading decisions."""
        try:
            subject = f"Daily Trading Report - {datetime.now().strftime('%Y-%m-%d')}"
            body = self._generate_daily_report_text(portfolio_analysis, ai_decisions)
            
            return self._send_simple_email(subject, body)
            
        except Exception as e:
            logger.error(f"Error sending daily report: {e}")
            return False
    
    def send_alert(self, alert_type: str, message: str, data: Dict[str, Any] = None) -> bool:
        """Send urgent trading alerts (stop losses, errors, etc.)."""
        try:
            subject = f"Trading Alert: {alert_type}"
            
            body = f"""
Trading Alert: {alert_type}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Message: {message}
"""
            
            if data:
                body += "\nDetails:\n"
                for key, value in data.items():
                    body += f"- {key}: {value}\n"
            
            return self._send_simple_email(subject, body)
            
        except Exception as e:
            logger.error(f"Error sending alert: {e}")
            return False
    
    def _send_simple_email(self, subject: str, body: str) -> bool:
        """Send email using simple SMTP."""
        try:
            for recipient in self.recipients:
                email_message = f"""Subject: {subject}
From: {self.sender_email}
To: {recipient}

{body}
"""
                
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.sender_email, self.sender_password)
                    server.sendmail(self.sender_email, recipient, email_message)
            
            logger.info(f"Email sent successfully to {len(self.recipients)} recipients")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False
    
    def _generate_daily_report_text(self, 
                                   portfolio_analysis: Dict[str, Any], 
                                   ai_decisions: Dict[str, Any]) -> str:
        """Generate plain text version of daily report."""
        portfolio = portfolio_analysis.get('portfolio', {})
        decisions = ai_decisions.get('decisions', [])
        
        text = f"""
ChatGPT Investor Daily Report - {datetime.now().strftime('%Y-%m-%d')}
{'='*60}

PORTFOLIO SUMMARY
Total Equity: ${portfolio.get('total_equity', 0):,.2f}
Cash Balance: ${portfolio.get('cash_balance', 0):,.2f}
Total P&L: ${portfolio.get('total_pnl', 0):,.2f}
Positions: {portfolio.get('positions_count', 0)}

"""
        
        # Add current positions
        if portfolio.get('portfolio'):
            text += "CURRENT POSITIONS\n"
            text += f"{'Ticker':<8} {'Shares':<8} {'Buy $':<10} {'Current $':<12} {'P&L $':<12} {'P&L %':<8}\n"
            text += "-" * 70 + "\n"
            
            for pos in portfolio['portfolio']:
                text += f"{pos.get('ticker', ''):<8} {pos.get('shares', 0):>7.0f} {pos.get('buy_price', 0):>9.2f} {pos.get('current_price', 0):>11.2f} {pos.get('pnl', 0):>11.2f} {pos.get('pnl_percent', 0):>+6.1f}%\n"
            text += "\n"
        
        # Add trading decisions
        if decisions:
            text += "AI TRADING DECISIONS\n"
            text += "-" * 30 + "\n"
            for i, decision in enumerate(decisions, 1):
                action = decision.get('action', '').upper()
                ticker = decision.get('ticker', '')
                shares = decision.get('shares', '')
                target_price = decision.get('target_price', 0)
                stop_loss = decision.get('stop_loss', 0)
                conviction = decision.get('conviction', 'N/A')
                reason = decision.get('reason', '')
                
                text += f"{i}. {action} {ticker}\n"
                if shares and shares != 'N/A':
                    text += f"   Shares: {shares}\n"
                if target_price:
                    text += f"   Target Price: ${target_price:.2f}\n"
                if stop_loss:
                    text += f"   Stop Loss: ${stop_loss:.2f}\n"
                if conviction and conviction != 'N/A':
                    text += f"   Conviction: {conviction}\n"
                if reason:
                    text += f"   Reason: {reason}\n"
                text += "\n"
        else:
            text += "AI RECOMMENDATION: HOLD\n"
            text += "No trading actions recommended today.\n\n"
        
        # Add AI reasoning if available
        if ai_decisions.get('raw_response'):
            text += "AI MARKET ANALYSIS\n"
            text += "-" * 25 + "\n"
            # Truncate if too long
            analysis = ai_decisions['raw_response']
            if len(analysis) > 1000:
                analysis = analysis[:1000] + "...\n[Analysis truncated for email]"
            text += analysis + "\n\n"
        
        # Add market sentiment
        market_sentiment = portfolio_analysis.get('market_sentiment', {})
        if market_sentiment:
            text += "MARKET SENTIMENT\n"
            text += "-" * 20 + "\n"
            text += f"Overall: {market_sentiment.get('sentiment', 'neutral').upper()}\n"
            for factor in market_sentiment.get('factors', []):
                text += f"- {factor}\n"
            text += "\n"
        
        # Add performance metrics
        performance = portfolio_analysis.get('performance', {})
        if performance and 'error' not in performance:
            text += "PERFORMANCE METRICS\n"
            text += "-" * 25 + "\n"
            text += f"Total Return: {performance.get('total_return', 0):+.1%}\n"
            text += f"Max Drawdown: {performance.get('max_drawdown', 0):+.1%}\n"
            text += f"Sharpe Ratio: {performance.get('sharpe_ratio', 0):.2f}\n"
            text += f"Trading Days: {performance.get('trading_days', 0)}\n"
            text += "\n"
        
        text += "IMPORTANT NOTES:\n"
        text += "- This is an automated analysis for informational purposes\n"
        text += "- Review all recommendations before executing trades\n"
        text += "- Consider your risk tolerance and investment objectives\n"
        text += "- Past performance does not guarantee future results\n"
        text += "\n"
        text += f"Report generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} EST\n"
        text += "Powered by ChatGPT Investor Automation System"
        
        return text