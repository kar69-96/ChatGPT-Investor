# ChatGPT Investor Automation System

## Overview

This automation system transforms the manual ChatGPT trading experiment into a fully automated investment platform that:

- **Analyzes your portfolio** using real-time market data
- **Makes trading decisions** via ChatGPT-4 AI integration  
- **Sends daily email reports** at 7PM with recommendations
- **Provides REST API access** for programmatic control
- **Runs completely hands-off** with scheduling and error handling

## 🚀 Quick Start

### 1. Install and Configure

```bash
# Run the automated setup wizard
python3 setup_automation.py

# Or install dependencies manually
pip install -r requirements.txt
```

### 2. Test the System

```bash
# Test configuration and connections
./test_system.sh

# Run automation once to verify
./run_once.sh
```

### 3. Start Automation

```bash
# Option A: Manual start (runs in foreground)
./scheduler/start_scheduler.sh

# Option B: Start API server separately
./start_api.sh &
python3 scheduler/daily_runner.py

# Option C: Install as system service
sudo cp chatgpt-investor.service /etc/systemd/system/
sudo systemctl enable chatgpt-investor
sudo systemctl start chatgpt-investor
```

## 📧 Daily Email Reports

Every day at 7:00 PM EST, you'll receive an automated email containing:

- **Portfolio Summary**: Current positions, P&L, cash balance
- **AI Trading Decisions**: Buy/sell recommendations with reasoning
- **Market Analysis**: Key indicators and sentiment
- **Stop-Loss Alerts**: Urgent notifications for triggered positions

### Sample Email Content:

```
📊 Daily Trading Report - 2025-09-02

📈 Portfolio Summary
Total Equity: $1,247.85
Cash Balance: $152.33
Total P&L: +$47.85 (+3.98%)
Active Positions: 3

💼 Current Positions
TICKER | SHARES | BUY PRICE | CURRENT | P&L    | STOP LOSS
ABCD   | 100    | $12.50    | $13.75  | +$125  | $10.62
XYZ    | 50     | $8.25     | $7.90   | -$17.5 | $7.01

🤖 Today's AI Trading Decisions
BUY MNOP: 75 shares - Strong earnings report, oversold bounce expected
HOLD existing positions - Market uncertainty, wait for clearer signals
```

## 🔧 API Endpoints

The system provides a REST API for programmatic access:

### Portfolio & Analysis
- `GET /api/portfolio/summary` - Current portfolio status
- `GET /api/market/data` - Market data for key indices
- `GET /api/analysis/full` - Comprehensive analysis report

### AI Decisions
- `POST /api/decisions/generate` - Generate new trading decisions
- `POST /api/decisions/custom` - Custom analysis input

### Automation
- `POST /api/automation/run-daily` - Run full daily workflow
- `POST /api/email/daily-report` - Send email report now
- `POST /api/email/alert` - Send urgent alert

### System
- `GET /` - Health check
- `GET /api/config` - Configuration status

### Example API Usage:

```bash
# Check portfolio status
curl http://localhost:5000/api/portfolio/summary

# Run automation manually
curl -X POST http://localhost:5000/api/automation/run-daily

# Send custom alert
curl -X POST http://localhost:5000/api/email/alert \
  -H "Content-Type: application/json" \
  -d '{"type":"Test Alert","message":"System is working!"}'
```

## 📁 Project Structure

```
ChatGPT-Investor/
├── 📁 api/                    # REST API server
│   └── app.py                 # Flask application
├── 📁 core/                   # Core business logic
│   ├── analyzer.py            # Portfolio analysis
│   ├── ai_decision.py         # ChatGPT integration
│   └── config_manager.py      # Configuration handling
├── 📁 notifications/          # Email system
│   ├── email_sender.py        # Email functionality
│   └── templates/             # HTML email templates
├── 📁 scheduler/              # Automation scheduling
│   ├── daily_runner.py        # Daily execution logic
│   └── start_scheduler.sh     # Startup script
├── 📁 config/                 # Configuration files
│   ├── config.json            # Main settings
│   └── .env                   # Environment variables
├── 📁 logs/                   # Application logs
├── 📄 setup_automation.py     # Interactive setup wizard
├── 📄 requirements.txt        # Python dependencies
└── 📜 start_api.sh           # API server starter
```

## ⚙️ Configuration

### Required Settings

**OpenAI API**: 
- Get your API key from https://platform.openai.com/api-keys
- Set in `config.json` or `OPENAI_API_KEY` environment variable

**Email Settings**:
- For Gmail: Use App Password (not your regular password)
- Set sender email and recipients in configuration
- Supports any SMTP server (Gmail, Outlook, etc.)

**Trading Parameters**:
- `max_cash_per_trade`: Maximum $ per individual trade
- `max_portfolio_positions`: Maximum number of stocks to hold
- `default_stop_loss_percent`: Default stop-loss percentage (15%)

### Configuration Files

1. **`config/config.json`** - Main configuration (safe to commit)
2. **`config/.env`** - Sensitive data (never commit)
3. **Environment variables** - Override any setting

## 🤖 How the AI Works

### Decision Process

1. **Data Collection**: Gathers portfolio status, market data, performance metrics
2. **Analysis**: Calculates P&L, risk metrics, market sentiment
3. **AI Prompt**: Sends comprehensive analysis to ChatGPT-4
4. **Parsing**: Extracts structured buy/sell decisions from AI response
5. **Validation**: Ensures decisions meet risk parameters
6. **Notification**: Emails recommendations to you

### AI Prompt Example

```
=== PORTFOLIO ANALYSIS REQUEST ===
Date: 2025-09-02 19:00

=== CURRENT PORTFOLIO ===
Cash Balance: $152.33
Total Equity: $1,247.85
Total P&L: $47.85
Positions: 3/10

=== CURRENT POSITIONS ===
ABCD: 100 shares @ $12.50 (Current: $13.75, P&L: +10.0%, Stop: $10.62)

=== MARKET CONDITIONS ===
Market Sentiment: BULLISH
- SPY up 1.2%
- QQQ up 0.8% 
- VIX low at 18.5

Based on this analysis, what trading decisions should be made today?
```

### AI Response Format

The AI responds with structured decisions:

```
ACTION: BUY
TICKER: MNOP
SHARES: 75
REASON: Strong earnings report, technical breakout above resistance
STOP_LOSS: 8.50

ACTION: HOLD
REASON: Market uncertainty due to Fed meeting, maintain current positions
```

## 📊 Risk Management

### Automated Safeguards

- **Stop-Loss Protection**: Automatic alerts when positions hit stop-loss levels
- **Position Limits**: Maximum number of holdings enforced
- **Cash Management**: Limits per-trade exposure
- **Weekend Detection**: Skips trading on market-closed days
- **Error Handling**: Comprehensive logging and email alerts

### Risk Parameters

Configure risk tolerance in `config.json`:

```json
{
  "trading": {
    "max_cash_per_trade": 1000,
    "default_stop_loss_percent": 0.15,
    "max_portfolio_positions": 10,
    "enable_stop_loss": true
  }
}
```

## 📈 Monitoring & Logs

### Log Files

- `logs/automation.log` - Daily automation runs
- `logs/api.log` - API requests and responses  
- `logs/email.log` - Email sending status

### Health Monitoring

- **Hourly health checks** during market hours
- **Error notifications** via email alerts
- **API status endpoint** for external monitoring

## 🔒 Security Best Practices

### API Keys
- Store OpenAI API key in environment variables
- Never commit sensitive data to version control
- Rotate keys periodically

### Email Security  
- Use app passwords, not account passwords
- Consider dedicated email account for notifications
- Limit recipient list to trusted addresses

### System Security
- Run with minimal permissions
- Use HTTPS for production API deployments
- Regular security updates for dependencies

## 🛠️ Troubleshooting

### Common Issues

**"OpenAI API key not configured"**
- Set `OPENAI_API_KEY` environment variable
- Or update `config/config.json` with your key

**"Email sending failed"**
- Check SMTP settings and credentials
- For Gmail, ensure 2FA is enabled and use App Password
- Verify network connectivity

**"Portfolio CSV not found"**
- Ensure `chatgpt_portfolio_update.csv` exists
- Check file permissions
- Run original trading script once to create initial data

**"No trading decisions made"**
- Check OpenAI API quota and billing
- Verify model availability (gpt-4o)
- Review AI response parsing in logs

### Debug Mode

Enable detailed logging:

```json
{
  "api": {
    "debug": true
  }
}
```

Or set environment variable: `API_DEBUG=true`

## 🔄 Deployment Options

### Development
```bash
# Terminal 1: Start API
./start_api.sh

# Terminal 2: Run scheduler
./scheduler/start_scheduler.sh
```

### Production (Linux Server)
```bash
# Install as system service
sudo cp chatgpt-investor.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable chatgpt-investor
sudo systemctl start chatgpt-investor

# Check status
sudo systemctl status chatgpt-investor
sudo journalctl -u chatgpt-investor -f
```

### Docker (Optional)
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "scheduler/daily_runner.py"]
```

## 📝 Customization

### Email Templates
- Modify `notifications/templates/daily_report.html`
- Customize styling, layout, and content
- Templates use Jinja2 syntax

### AI Prompts
- Edit system prompt in `core/ai_decision.py`
- Adjust trading strategy and risk parameters
- Customize decision parsing logic

### Schedule Timing
- Change daily run time in `config.json`
- Modify `schedule.daily_run_time` (24-hour format)
- Timezone support via `schedule.timezone`

## 🎯 Next Steps

After automation is running:

1. **Monitor for 1 week** - Verify emails and decisions
2. **Review AI decisions** - Ensure they align with your strategy
3. **Adjust parameters** - Fine-tune risk settings as needed
4. **Scale gradually** - Increase position sizes as confidence grows
5. **Add integrations** - Connect to broker APIs for execution

## 🆘 Support

- **Issues**: Check logs in `logs/` directory
- **Configuration**: Re-run `python3 setup_automation.py`
- **API Testing**: Use `curl` or Postman with provided endpoints
- **Email**: Verify SMTP settings and test with manual send

---

⚠️ **Important Disclaimer**: This is an experimental system for educational purposes. Always review AI decisions before executing trades. Past performance doesn't guarantee future results.