"""Flask API for the ChatGPT Investor automation system."""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Import our modules
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))
from core.analyzer import InvestmentAnalyzer
from core.ai_decision import AIDecisionMaker
from notifications.email_sender import EmailNotifier

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Load configuration
def load_config() -> Dict[str, Any]:
    """Load configuration from config.json and environment variables."""
    config_path = Path(__file__).resolve().parents[1] / 'config' / 'config.json'
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Override with environment variables if present
    if os.getenv('OPENAI_API_KEY'):
        config['openai']['api_key'] = os.getenv('OPENAI_API_KEY')
    
    if os.getenv('EMAIL_SENDER'):
        config['email']['sender_email'] = os.getenv('EMAIL_SENDER')
        
    if os.getenv('EMAIL_PASSWORD'):
        config['email']['sender_password'] = os.getenv('EMAIL_PASSWORD')
        
    if os.getenv('EMAIL_RECIPIENTS'):
        config['email']['recipients'] = os.getenv('EMAIL_RECIPIENTS').split(',')
    
    return config

# Initialize global components
config = load_config()
analyzer = InvestmentAnalyzer(config)
ai_decision_maker = AIDecisionMaker(config)
email_notifier = EmailNotifier(config)


@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'ChatGPT Investor API',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })


@app.route('/api/portfolio/summary', methods=['GET'])
def get_portfolio_summary():
    """Get current portfolio summary and performance metrics."""
    try:
        summary = analyzer.get_portfolio_summary()
        return jsonify({
            'success': True,
            'data': summary,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting portfolio summary: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/market/data', methods=['GET'])
def get_market_data():
    """Get current market data for key indices and indicators."""
    try:
        tickers = request.args.get('tickers')
        if tickers:
            tickers = [t.strip().upper() for t in tickers.split(',')]
        else:
            tickers = None
            
        market_data = analyzer.get_market_data(tickers)
        return jsonify({
            'success': True,
            'data': market_data,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting market data: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/analysis/full', methods=['GET'])
def get_full_analysis():
    """Get comprehensive portfolio and market analysis."""
    try:
        analysis = analyzer.generate_analysis_report()
        return jsonify({
            'success': True,
            'data': analysis,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error generating analysis: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/decisions/generate', methods=['POST'])
def generate_trading_decisions():
    """Generate AI-powered trading decisions."""
    try:
        # Get analysis report
        analysis_report = analyzer.generate_analysis_report()
        
        # Generate AI decisions
        decisions = ai_decision_maker.make_trading_decision(analysis_report)
        
        return jsonify({
            'success': True,
            'data': decisions,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error generating trading decisions: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/decisions/custom', methods=['POST'])
def generate_custom_decisions():
    """Generate trading decisions with custom analysis data."""
    try:
        # Get custom analysis from request body
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No analysis data provided',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # Generate AI decisions
        decisions = ai_decision_maker.make_trading_decision(data)
        
        return jsonify({
            'success': True,
            'data': decisions,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error generating custom trading decisions: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/email/daily-report', methods=['POST'])
def send_daily_email_report():
    """Send daily email report with portfolio analysis and AI decisions."""
    try:
        # Generate analysis and decisions
        analysis_report = analyzer.generate_analysis_report()
        decisions = ai_decision_maker.make_trading_decision(analysis_report)
        
        # Send email
        success = email_notifier.send_daily_report(analysis_report, decisions)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Daily report sent successfully',
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to send email report',
                'timestamp': datetime.now().isoformat()
            }), 500
            
    except Exception as e:
        logger.error(f"Error sending daily email report: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/email/alert', methods=['POST'])
def send_email_alert():
    """Send email alert for urgent trading situations."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No alert data provided',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        alert_type = data.get('type', 'General Alert')
        message = data.get('message', 'No message provided')
        alert_data = data.get('data', {})
        
        # Send alert email
        success = email_notifier.send_alert(alert_type, message, alert_data)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Alert sent successfully',
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to send alert',
                'timestamp': datetime.now().isoformat()
            }), 500
            
    except Exception as e:
        logger.error(f"Error sending email alert: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/config', methods=['GET'])
def get_config():
    """Get current configuration (excluding sensitive data)."""
    try:
        safe_config = {
            'trading': config.get('trading', {}),
            'schedule': config.get('schedule', {}),
            'api': {k: v for k, v in config.get('api', {}).items() if k != 'debug'},
            'data': config.get('data', {}),
            'email': {
                'smtp_server': config.get('email', {}).get('smtp_server'),
                'smtp_port': config.get('email', {}).get('smtp_port'),
                'recipients_count': len(config.get('email', {}).get('recipients', []))
            },
            'openai': {
                'model': config.get('openai', {}).get('model'),
                'temperature': config.get('openai', {}).get('temperature'),
                'api_key_configured': bool(config.get('openai', {}).get('api_key'))
            }
        }
        
        return jsonify({
            'success': True,
            'data': safe_config,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting configuration: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/automation/run-daily', methods=['POST'])
def run_daily_automation():
    """Run the complete daily automation process."""
    try:
        # Generate analysis
        logger.info("Generating portfolio analysis...")
        analysis_report = analyzer.generate_analysis_report()
        
        # Generate AI decisions
        logger.info("Generating AI trading decisions...")
        decisions = ai_decision_maker.make_trading_decision(analysis_report)
        
        # Send email report
        logger.info("Sending daily email report...")
        email_success = email_notifier.send_daily_report(analysis_report, decisions)
        
        # Check for urgent alerts (stop losses)
        stop_loss_alerts = analysis_report.get('stop_loss_alerts', [])
        if stop_loss_alerts:
            logger.warning(f"Stop loss alerts detected: {len(stop_loss_alerts)} positions")
            email_notifier.send_alert(
                'Stop Loss Triggered',
                f'{len(stop_loss_alerts)} position(s) have triggered stop losses',
                {'alerts': stop_loss_alerts}
            )
        
        return jsonify({
            'success': True,
            'message': 'Daily automation completed successfully',
            'data': {
                'analysis': analysis_report,
                'decisions': decisions,
                'email_sent': email_success,
                'stop_loss_alerts': len(stop_loss_alerts)
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error running daily automation: {e}")
        
        # Send error alert
        try:
            email_notifier.send_alert(
                'Automation Error',
                f'Daily automation failed: {str(e)}',
                {'error': str(e), 'timestamp': datetime.now().isoformat()}
            )
        except:
            pass  # Don't fail the response if alert email fails
        
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found',
        'timestamp': datetime.now().isoformat()
    }), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'timestamp': datetime.now().isoformat()
    }), 500


if __name__ == '__main__':
    # Get configuration for Flask app
    api_config = config.get('api', {})
    host = api_config.get('host', '0.0.0.0')
    port = api_config.get('port', 5000)
    debug = api_config.get('debug', False)
    
    logger.info(f"Starting ChatGPT Investor API on {host}:{port}")
    app.run(host=host, port=port, debug=debug)