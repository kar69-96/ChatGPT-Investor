"""AI-powered investment decision maker using OpenAI GPT-4."""

import json
import logging
import re
from typing import Dict, List, Any, Optional
from datetime import datetime

import openai
from openai import OpenAI

logger = logging.getLogger(__name__)


class AIDecisionMaker:
    """Uses ChatGPT to make investment decisions based on portfolio analysis."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config.get('openai', {})
        self.client = OpenAI(api_key=self.config.get('api_key'))
        self.model = self.config.get('model', 'gpt-4o')
        self.temperature = self.config.get('temperature', 0.7)
        
    def make_trading_decision(self, analysis_report: Dict[str, Any]) -> Dict[str, Any]:
        """Generate trading decisions based on comprehensive analysis."""
        try:
            # Create the prompt for ChatGPT
            prompt = self._create_trading_prompt(analysis_report)
            
            # Get decision from ChatGPT
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=self.temperature,
                max_tokens=1500
            )
            
            # Parse the response
            decision_text = response.choices[0].message.content
            parsed_decisions = self._parse_ai_response(decision_text)
            
            return {
                'timestamp': datetime.now().isoformat(),
                'decisions': parsed_decisions,
                'raw_response': decision_text,
                'analysis_used': analysis_report,
                'model_used': self.model
            }
            
        except Exception as e:
            logger.error(f"Error making trading decision: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'decisions': []
            }
    
    def _get_system_prompt(self) -> str:
        """System prompt that defines the AI's role and behavior."""
        return """You are an expert quantitative trader and portfolio manager with deep research capabilities. 
You manage a micro-cap stock portfolio with the goal of generating superior returns through data-driven analysis.

DEEP RESEARCH MANDATE:
- Conduct thorough fundamental analysis of all positions and potential investments
- Analyze financial metrics: P/E ratios, revenue growth, profit margins, debt levels
- Evaluate technical indicators: moving averages, RSI, volume trends, chart patterns
- Consider sector rotation, market cycles, and macroeconomic factors
- Research recent earnings, news, analyst upgrades/downgrades
- Assess competitive positioning and industry dynamics

TRADING RULES:
1. Focus on US micro-cap stocks (market cap < $300M) with growth potential
2. Set intelligent stop-losses based on technical support levels (typically 10-20% below entry)
3. Maximum 10 positions, diversified across sectors
4. Position sizing based on conviction level and risk (typically $500-2000 per trade)
5. Prioritize stocks with strong fundamentals and technical momentum
6. Cut losses quickly, scale into winners on strength

REQUIRED DECISION FORMAT:
You must provide specific, actionable trading decisions:

ACTION: BUY
TICKER: [STOCK_SYMBOL]
SHARES: [EXACT_NUMBER]
TARGET_PRICE: [SPECIFIC_ENTRY_PRICE]
STOP_LOSS: [SPECIFIC_STOP_PRICE]
REASON: [Detailed fundamental + technical analysis]
CONVICTION: [HIGH/MEDIUM/LOW]

ACTION: SELL
TICKER: [STOCK_SYMBOL]
SHARES: [EXACT_NUMBER or "ALL"]
TARGET_PRICE: [SPECIFIC_EXIT_PRICE]
REASON: [Detailed exit rationale]
URGENCY: [HIGH/MEDIUM/LOW]

ACTION: HOLD
TICKER: [STOCK_SYMBOL]
REASON: [Detailed hold rationale with price targets]

CRITICAL REQUIREMENTS:
- Provide specific dollar amounts and share quantities
- Include exact entry/exit prices based on technical analysis
- Give detailed reasoning combining fundamental and technical factors
- Consider portfolio balance and risk management
- Be decisive - weak signals should result in HOLD, not trades"""

    def _create_trading_prompt(self, analysis_report: Dict[str, Any]) -> str:
        """Create a comprehensive prompt with all relevant data."""
        portfolio = analysis_report.get('portfolio', {})
        market_data = analysis_report.get('market_data', {})
        performance = analysis_report.get('performance', {})
        constraints = analysis_report.get('trading_constraints', {})
        sentiment = analysis_report.get('market_sentiment', {})
        stop_losses = analysis_report.get('stop_loss_alerts', [])
        
        prompt_parts = [
            "=== PORTFOLIO ANALYSIS REQUEST ===",
            f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "",
            "=== CURRENT PORTFOLIO ===",
            f"Cash Balance: ${portfolio.get('cash_balance', 0):,.2f}",
            f"Total Equity: ${portfolio.get('total_equity', 0):,.2f}",
            f"Total P&L: ${portfolio.get('total_pnl', 0):,.2f}",
            f"Positions: {portfolio.get('positions_count', 0)}/{constraints.get('max_positions', 10)}",
            ""
        ]
        
        # Add current positions
        if portfolio.get('portfolio'):
            prompt_parts.append("=== CURRENT POSITIONS ===")
            for pos in portfolio['portfolio']:
                prompt_parts.append(
                    f"{pos['ticker']}: {pos['shares']} shares @ ${pos['buy_price']:.2f} "
                    f"(Current: ${pos['current_price']:.2f}, "
                    f"P&L: {pos['pnl_percent']:+.1f}%, "
                    f"Stop: ${pos['stop_loss']:.2f})"
                )
            prompt_parts.append("")
        
        # Add stop loss alerts
        if stop_losses:
            prompt_parts.append("=== URGENT STOP LOSS ALERTS ===")
            for alert in stop_losses:
                prompt_parts.append(
                    f"SELL {alert['ticker']}: Stop loss triggered at ${alert['current_price']:.2f} "
                    f"(Stop was ${alert['stop_loss']:.2f})"
                )
            prompt_parts.append("")
        
        # Add market data
        prompt_parts.append("=== MARKET CONDITIONS ===")
        prompt_parts.append(f"Market Sentiment: {sentiment.get('sentiment', 'neutral').upper()}")
        if sentiment.get('factors'):
            for factor in sentiment['factors']:
                prompt_parts.append(f"- {factor}")
        prompt_parts.append("")
        
        prompt_parts.append("Key Market Data:")
        major_indices = ['SPY', 'QQQ', 'IWM', 'VIX']
        for ticker in major_indices:
            if ticker in market_data and 'price' in market_data[ticker]:
                data = market_data[ticker]
                prompt_parts.append(
                    f"{ticker}: ${data['price']:.2f} "
                    f"({data.get('change_percent', 0):+.1f}%)"
                )
        prompt_parts.append("")
        
        # Add performance data
        if 'error' not in performance:
            prompt_parts.extend([
                "=== PORTFOLIO PERFORMANCE ===",
                f"Total Return: {performance.get('total_return', 0):+.1%}",
                f"Max Drawdown: {performance.get('max_drawdown', 0):+.1%}",
                f"Sharpe Ratio: {performance.get('sharpe_ratio', 0):.2f}",
                f"Trading Days: {performance.get('trading_days', 0)}",
                ""
            ])
        
        # Add trading constraints
        prompt_parts.extend([
            "=== TRADING CONSTRAINTS ===",
            f"Available Cash: ${constraints.get('available_cash', 0):,.2f}",
            f"Max Per Trade: ${constraints.get('max_cash_per_trade', 1000):,.2f}",
            f"Max Positions: {constraints.get('max_positions', 10)}",
            f"Current Positions: {constraints.get('current_positions', 0)}",
            "",
            "=== DEEP RESEARCH ANALYSIS REQUEST ===",
            "Conduct comprehensive analysis and provide specific trading recommendations:",
            "",
            "1. FUNDAMENTAL ANALYSIS:",
            "   - Analyze each current position's financial health",
            "   - Review recent earnings, revenue growth, profitability",
            "   - Assess competitive position and industry outlook",
            "   - Consider valuation metrics (P/E, P/S, EV/EBITDA)",
            "",
            "2. TECHNICAL ANALYSIS:",
            "   - Evaluate price action, support/resistance levels",
            "   - Analyze volume trends and momentum indicators",
            "   - Identify chart patterns and trend direction",
            "   - Set precise entry/exit prices based on technicals",
            "",
            "3. PORTFOLIO OPTIMIZATION:",
            "   - Assess sector diversification and concentration risk",
            "   - Determine optimal position sizes based on conviction",
            "   - Balance growth vs value opportunities",
            "   - Consider correlation between holdings",
            "",
            "4. MARKET CONTEXT:",
            "   - Factor in current market cycle and sentiment",
            "   - Consider sector rotation and macroeconomic trends",
            "   - Evaluate relative strength vs benchmarks",
            "",
            "PROVIDE SPECIFIC ACTIONABLE DECISIONS:",
            "- Exact share quantities and dollar amounts",
            "- Precise entry/exit target prices",
            "- Specific stop-loss levels based on technical support",
            "- Detailed reasoning combining fundamental + technical factors",
            "- Clear conviction levels (HIGH/MEDIUM/LOW) for each decision",
            "",
            "Remember: Be decisive with strong convictions, conservative with weak signals."
        ])
        
        return "\n".join(prompt_parts)
    
    def _parse_ai_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse the AI's response into structured trading decisions."""
        decisions = []
        
        # Split response into sections
        sections = re.split(r'\n(?=ACTION:)', response)
        
        for section in sections:
            section = section.strip()
            if not section or 'ACTION:' not in section:
                continue
                
            decision = {}
            lines = section.split('\n')
            
            for line in lines:
                line = line.strip()
                if line.startswith('ACTION:'):
                    decision['action'] = line.split(':', 1)[1].strip().lower()
                elif line.startswith('TICKER:'):
                    decision['ticker'] = line.split(':', 1)[1].strip().upper()
                elif line.startswith('SHARES:'):
                    shares_text = line.split(':', 1)[1].strip()
                    if shares_text.upper() == 'ALL':
                        decision['shares'] = 'all'
                    else:
                        try:
                            decision['shares'] = float(shares_text)
                        except ValueError:
                            decision['shares'] = 0
                elif line.startswith('TARGET_PRICE:'):
                    try:
                        decision['target_price'] = float(line.split(':', 1)[1].strip().replace('$', ''))
                    except ValueError:
                        decision['target_price'] = 0
                elif line.startswith('STOP_LOSS:'):
                    try:
                        decision['stop_loss'] = float(line.split(':', 1)[1].strip().replace('$', ''))
                    except ValueError:
                        decision['stop_loss'] = 0
                elif line.startswith('REASON:'):
                    decision['reason'] = line.split(':', 1)[1].strip()
                elif line.startswith('CONVICTION:'):
                    decision['conviction'] = line.split(':', 1)[1].strip().upper()
                elif line.startswith('URGENCY:'):
                    decision['urgency'] = line.split(':', 1)[1].strip().upper()
            
            # Validate decision
            if decision.get('action') in ['buy', 'sell', 'hold']:
                # For buy/sell actions, require ticker
                if decision['action'] in ['buy', 'sell']:
                    if decision.get('ticker'):
                        decisions.append(decision)
                    else:
                        logger.warning(f"Invalid {decision['action']} decision missing ticker: {decision}")
                else:
                    # Hold decision doesn't need ticker
                    decisions.append(decision)
        
        # If no structured decisions found, try to extract from natural language
        if not decisions:
            decisions = self._extract_decisions_from_text(response)
        
        return decisions
    
    def _extract_decisions_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Fallback method to extract decisions from natural language response."""
        decisions = []
        
        # Look for common trading phrases
        buy_pattern = r'(?:buy|purchase|add)\s+(\d+)?\s*(?:shares?\s+of\s+)?([A-Z]{2,5})'
        sell_pattern = r'(?:sell|close|exit)\s+(?:all\s+)?(?:(\d+)\s+)?(?:shares?\s+of\s+)?([A-Z]{2,5})'
        
        # Find buy signals
        for match in re.finditer(buy_pattern, text, re.IGNORECASE):
            shares = match.group(1)
            ticker = match.group(2).upper()
            decisions.append({
                'action': 'buy',
                'ticker': ticker,
                'shares': float(shares) if shares else 100,  # Default to 100 shares
                'reason': 'Extracted from AI text response'
            })
        
        # Find sell signals
        for match in re.finditer(sell_pattern, text, re.IGNORECASE):
            shares = match.group(1)
            ticker = match.group(2).upper()
            decisions.append({
                'action': 'sell',
                'ticker': ticker,
                'shares': float(shares) if shares else 'all',
                'reason': 'Extracted from AI text response'
            })
        
        # If still no decisions, default to hold
        if not decisions:
            decisions.append({
                'action': 'hold',
                'reason': 'No clear trading signals identified in response'
            })
        
        return decisions