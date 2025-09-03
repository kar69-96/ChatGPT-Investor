"""Email notification system for trading decisions and portfolio updates."""

import smtplib
import logging
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from email.mime.base import MimeBase
from email import encoders
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)


class EmailNotifier:
    """Handles sending email notifications with trading decisions and portfolio updates."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config.get('email', {})
        self.smtp_server = self.config.get('smtp_server', 'smtp.gmail.com')
        self.smtp_port = self.config.get('smtp_port', 587)
        self.sender_email = self.config.get('sender_email', '')
        self.sender_password = self.config.get('sender_password', '')
        self.recipients = self.config.get('recipients', [])
        
        # Setup Jinja2 template environment
        template_dir = Path(__file__).parent / 'templates'
        template_dir.mkdir(exist_ok=True)
        self.jinja_env = Environment(loader=FileSystemLoader(str(template_dir)))
        
    def send_daily_report(self, 
                         portfolio_analysis: Dict[str, Any], 
                         ai_decisions: Dict[str, Any]) -> bool:
        """Send daily portfolio report with AI trading decisions."""
        try:
            # Generate email content
            subject = f"Daily Trading Report - {datetime.now().strftime('%Y-%m-%d')}"
            html_content = self._generate_daily_report_html(portfolio_analysis, ai_decisions)
            text_content = self._generate_daily_report_text(portfolio_analysis, ai_decisions)
            
            # Send email
            return self._send_email(subject, html_content, text_content)
            
        except Exception as e:
            logger.error(f"Error sending daily report: {e}")
            return False
    
    def send_alert(self, alert_type: str, message: str, data: Dict[str, Any] = None) -> bool:
        """Send urgent trading alerts (stop losses, errors, etc.)."""
        try:
            subject = f"🚨 Trading Alert: {alert_type}"
            
            html_content = f"""
            <html>
            <body>
                <h2 style="color: #d32f2f;">Trading Alert: {alert_type}</h2>
                <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p><strong>Message:</strong> {message}</p>
                {self._format_alert_data(data) if data else ''}
            </body>
            </html>
            """
            
            text_content = f"""
Trading Alert: {alert_type}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Message: {message}
            """
            
            return self._send_email(subject, html_content, text_content)
            
        except Exception as e:
            logger.error(f"Error sending alert: {e}")
            return False
    
    def _send_email(self, subject: str, html_content: str, text_content: str) -> bool:
        """Send email using SMTP."""
        try:
            # Create message
            msg = MimeMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.sender_email
            msg['To'] = ', '.join(self.recipients)
            
            # Add text and HTML parts
            text_part = MimeText(text_content, 'plain')
            html_part = MimeText(html_content, 'html')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {len(self.recipients)} recipients")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False
    
    def _generate_daily_report_html(self, 
                                   portfolio_analysis: Dict[str, Any], 
                                   ai_decisions: Dict[str, Any]) -> str:
        """Generate HTML email content for daily report."""
        try:
            template = self.jinja_env.get_template('daily_report.html')
            return template.render(
                date=datetime.now().strftime('%Y-%m-%d'),
                portfolio=portfolio_analysis,
                decisions=ai_decisions
            )
        except:
            # Fallback to inline HTML if template not found
            return self._generate_inline_html_report(portfolio_analysis, ai_decisions)
    
    def _generate_inline_html_report(self, 
                                    portfolio_analysis: Dict[str, Any], 
                                    ai_decisions: Dict[str, Any]) -> str:
        """Generate inline HTML report as fallback."""
        portfolio = portfolio_analysis.get('portfolio', {})
        decisions = ai_decisions.get('decisions', [])
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .positive {{ color: #4caf50; }}
                .negative {{ color: #f44336; }}
                .buy {{ background-color: #e8f5e8; }}
                .sell {{ background-color: #ffeaea; }}
                .hold {{ background-color: #fff3e0; }}
                .summary {{ background-color: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <h1>Daily Trading Report - {datetime.now().strftime('%Y-%m-%d')}</h1>
            
            <div class="summary">
                <h2>Portfolio Summary</h2>
                <p><strong>Total Equity:</strong> ${portfolio.get('total_equity', 0):,.2f}</p>
                <p><strong>Cash Balance:</strong> ${portfolio.get('cash_balance', 0):,.2f}</p>
                <p><strong>Total P&L:</strong> <span class="{'positive' if portfolio.get('total_pnl', 0) >= 0 else 'negative'}">${portfolio.get('total_pnl', 0):,.2f}</span></p>
                <p><strong>Positions:</strong> {portfolio.get('positions_count', 0)}</p>
            </div>
        """
        
        # Add current positions table
        if portfolio.get('portfolio'):
            html += """
            <h2>Current Positions</h2>
            <table>
                <tr>
                    <th>Ticker</th>
                    <th>Shares</th>
                    <th>Buy Price</th>
                    <th>Current Price</th>
                    <th>P&L</th>
                    <th>P&L %</th>
                    <th>Stop Loss</th>
                </tr>
            """
            
            for pos in portfolio['portfolio']:
                pnl_class = 'positive' if pos.get('pnl', 0) >= 0 else 'negative'
                html += f"""
                <tr>
                    <td>{pos.get('ticker', '')}</td>
                    <td>{pos.get('shares', 0):,.0f}</td>
                    <td>${pos.get('buy_price', 0):.2f}</td>
                    <td>${pos.get('current_price', 0):.2f}</td>
                    <td class="{pnl_class}">${pos.get('pnl', 0):,.2f}</td>
                    <td class="{pnl_class}">{pos.get('pnl_percent', 0):+.1f}%</td>
                    <td>${pos.get('stop_loss', 0):.2f}</td>
                </tr>
                """
            html += "</table>"
        
        # Add AI decisions
        if decisions:
            html += """
            <h2>Today's Trading Decisions</h2>
            <table>
                <tr>
                    <th>Action</th>
                    <th>Ticker</th>
                    <th>Shares</th>
                    <th>Stop Loss</th>
                    <th>Reason</th>
                </tr>
            """
            
            for decision in decisions:
                action = decision.get('action', '').lower()
                action_class = action if action in ['buy', 'sell', 'hold'] else ''
                html += f"""
                <tr class="{action_class}">
                    <td>{action.upper()}</td>
                    <td>{decision.get('ticker', '')}</td>
                    <td>{decision.get('shares', '')}</td>
                    <td>${decision.get('stop_loss', 0):.2f}</td>
                    <td>{decision.get('reason', '')}</td>
                </tr>
                """
            html += "</table>"
        
        # Add AI reasoning if available
        if ai_decisions.get('raw_response'):
            html += f"""
            <h2>AI Analysis</h2>
            <div class="summary">
                <pre style="white-space: pre-wrap; font-size: 12px;">{ai_decisions['raw_response'][:1000]}...</pre>
            </div>
            """
        
        html += """
            <hr>
            <p><small>This is an automated report generated by the ChatGPT Investor system.</small></p>
        </body>
        </html>
        """
        
        return html
    
    def _generate_daily_report_text(self, 
                                   portfolio_analysis: Dict[str, Any], 
                                   ai_decisions: Dict[str, Any]) -> str:
        """Generate plain text version of daily report."""
        portfolio = portfolio_analysis.get('portfolio', {})
        decisions = ai_decisions.get('decisions', [])
        
        text = f"""
Daily Trading Report - {datetime.now().strftime('%Y-%m-%d')}
{'='*50}

PORTFOLIO SUMMARY
Total Equity: ${portfolio.get('total_equity', 0):,.2f}
Cash Balance: ${portfolio.get('cash_balance', 0):,.2f}
Total P&L: ${portfolio.get('total_pnl', 0):,.2f}
Positions: {portfolio.get('positions_count', 0)}

"""
        
        # Add current positions
        if portfolio.get('portfolio'):
            text += "CURRENT POSITIONS\\n"
            text += f"{'Ticker':<6} {'Shares':<8} {'Buy $':<8} {'Current $':<10} {'P&L $':<10} {'P&L %':<8}\\n"
            text += "-" * 60 + "\\n"
            
            for pos in portfolio['portfolio']:
                text += f"{pos.get('ticker', ''):<6} {pos.get('shares', 0):>7.0f} {pos.get('buy_price', 0):>7.2f} {pos.get('current_price', 0):>9.2f} {pos.get('pnl', 0):>9.2f} {pos.get('pnl_percent', 0):>+6.1f}%\\n"
            text += "\\n"
        
        # Add trading decisions
        if decisions:
            text += "TODAY'S TRADING DECISIONS\\n"
            for decision in decisions:
                action = decision.get('action', '').upper()
                ticker = decision.get('ticker', '')
                shares = decision.get('shares', '')
                reason = decision.get('reason', '')
                text += f"{action} {ticker}: {shares} shares - {reason}\\n"
            text += "\\n"
        
        text += "This is an automated report generated by the ChatGPT Investor system."
        
        return text
    
    def _format_alert_data(self, data: Dict[str, Any]) -> str:
        """Format additional alert data as HTML."""
        html = "<h3>Details:</h3><ul>"
        for key, value in data.items():
            html += f"<li><strong>{key}:</strong> {value}</li>"
        html += "</ul>"
        return html