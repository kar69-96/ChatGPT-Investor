"""Investment analyzer module for automated trading decisions."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import pandas as pd

# Import from the existing trading script
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))
from trading_script import (
    download_price_data, 
    load_latest_portfolio_state,
    last_trading_date,
    trading_day_window,
    load_benchmarks,
    PORTFOLIO_CSV
)

logger = logging.getLogger(__name__)


class InvestmentAnalyzer:
    """Core investment analysis and portfolio management."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.trading_config = config.get('trading', {})
        self.data_config = config.get('data', {})
        
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get current portfolio state and performance metrics."""
        try:
            # Load portfolio from CSV
            portfolio_file = self.data_config.get('portfolio_csv', 'chatgpt_portfolio_update.csv')
            portfolio_path = Path(portfolio_file)
            
            if not portfolio_path.exists():
                return {
                    'portfolio': [],
                    'cash_balance': 100.0,
                    'total_equity': 100.0,
                    'total_pnl': 0.0,
                    'positions_count': 0,
                    'message': 'No existing portfolio found - starting fresh'
                }
            
            portfolio, cash = load_latest_portfolio_state(str(portfolio_path))
            
            # Calculate current values
            total_value = 0.0
            total_pnl = 0.0
            position_details = []
            
            if isinstance(portfolio, list):
                portfolio_df = pd.DataFrame(portfolio)
            else:
                portfolio_df = portfolio
                
            if not portfolio_df.empty:
                s, e = trading_day_window()
                for _, stock in portfolio_df.iterrows():
                    ticker = str(stock["ticker"]).upper()
                    shares = float(stock["shares"]) if not pd.isna(stock["shares"]) else 0
                    cost_basis = float(stock["cost_basis"]) if not pd.isna(stock["cost_basis"]) else 0
                    buy_price = float(stock["buy_price"]) if not pd.isna(stock["buy_price"]) else 0
                    stop_loss = float(stock["stop_loss"]) if not pd.isna(stock["stop_loss"]) else 0
                    
                    # Get current price
                    fetch = download_price_data(ticker, start=s, end=e, auto_adjust=False, progress=False)
                    current_price = 0.0
                    if not fetch.df.empty:
                        current_price = float(fetch.df["Close"].iloc[-1])
                    
                    position_value = current_price * shares
                    position_pnl = (current_price - buy_price) * shares
                    
                    total_value += position_value
                    total_pnl += position_pnl
                    
                    position_details.append({
                        'ticker': ticker,
                        'shares': shares,
                        'buy_price': buy_price,
                        'current_price': current_price,
                        'cost_basis': cost_basis,
                        'current_value': position_value,
                        'pnl': position_pnl,
                        'pnl_percent': (position_pnl / cost_basis * 100) if cost_basis > 0 else 0,
                        'stop_loss': stop_loss
                    })
            
            return {
                'portfolio': position_details,
                'cash_balance': float(cash),
                'total_equity': total_value + float(cash),
                'total_pnl': total_pnl,
                'positions_count': len(position_details),
                'message': 'Portfolio loaded successfully'
            }
            
        except Exception as e:
            logger.error(f"Error getting portfolio summary: {e}")
            return {
                'portfolio': [],
                'cash_balance': 0.0,
                'total_equity': 0.0,
                'total_pnl': 0.0,
                'positions_count': 0,
                'error': str(e)
            }
    
    def get_market_data(self, tickers: List[str] = None) -> Dict[str, Any]:
        """Get comprehensive market data for deep analysis."""
        if tickers is None:
            benchmarks = load_benchmarks()
            tickers = benchmarks + ['SPY', 'QQQ', 'IWM', 'VIX']  # Add common market indicators
        
        market_data = {}
        
        # Get extended data window for technical analysis
        end_date = last_trading_date() + pd.Timedelta(days=1)
        start_date = end_date - pd.Timedelta(days=60)  # 60 days for moving averages
        
        for ticker in tickers:
            try:
                fetch = download_price_data(ticker, start=start_date, end=end_date, auto_adjust=False, progress=False)
                if not fetch.df.empty:
                    data = fetch.df.sort_index()
                    current_price = float(data["Close"].iloc[-1])
                    
                    # Basic price data
                    percent_change = 0.0
                    if len(data) >= 2:
                        prev_price = float(data["Close"].iloc[-2])
                        percent_change = ((current_price - prev_price) / prev_price) * 100
                    
                    # Technical indicators
                    closes = data["Close"].astype(float)
                    volumes = data["Volume"].astype(float)
                    
                    # Moving averages
                    sma_20 = closes.rolling(window=20).mean().iloc[-1] if len(closes) >= 20 else current_price
                    sma_50 = closes.rolling(window=50).mean().iloc[-1] if len(closes) >= 50 else current_price
                    
                    # Volume analysis
                    avg_volume = volumes.rolling(window=20).mean().iloc[-1] if len(volumes) >= 20 else volumes.iloc[-1]
                    volume_ratio = float(volumes.iloc[-1] / avg_volume) if avg_volume > 0 else 1.0
                    
                    # Price momentum
                    week_change = 0.0
                    month_change = 0.0
                    if len(closes) >= 5:
                        week_ago_price = closes.iloc[-5]
                        week_change = ((current_price - week_ago_price) / week_ago_price) * 100
                    if len(closes) >= 20:
                        month_ago_price = closes.iloc[-20]
                        month_change = ((current_price - month_ago_price) / month_ago_price) * 100
                    
                    # Support/Resistance levels (last 20 days)
                    recent_data = data.tail(20)
                    support_level = float(recent_data["Low"].min())
                    resistance_level = float(recent_data["High"].max())
                    
                    # Relative Strength Index (RSI) - simplified
                    if len(closes) >= 14:
                        delta = closes.diff()
                        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                        rs = gain / loss
                        rsi = 100 - (100 / (1 + rs)).iloc[-1]
                    else:
                        rsi = 50  # Neutral RSI
                    
                    market_data[ticker] = {
                        # Current price data
                        'price': current_price,
                        'change_percent': percent_change,
                        'volume': float(data["Volume"].iloc[-1]) if "Volume" in data else 0,
                        'high': float(data["High"].iloc[-1]),
                        'low': float(data["Low"].iloc[-1]),
                        'open': float(data["Open"].iloc[-1]) if "Open" in data else current_price,
                        
                        # Technical analysis
                        'sma_20': float(sma_20),
                        'sma_50': float(sma_50),
                        'price_vs_sma20': ((current_price - sma_20) / sma_20) * 100,
                        'price_vs_sma50': ((current_price - sma_50) / sma_50) * 100,
                        
                        # Volume analysis
                        'avg_volume': float(avg_volume),
                        'volume_ratio': volume_ratio,
                        'volume_trend': 'high' if volume_ratio > 1.5 else 'normal' if volume_ratio > 0.5 else 'low',
                        
                        # Momentum indicators
                        'week_change': week_change,
                        'month_change': month_change,
                        'rsi': float(rsi),
                        'rsi_signal': 'oversold' if rsi < 30 else 'overbought' if rsi > 70 else 'neutral',
                        
                        # Support/Resistance
                        'support_level': support_level,
                        'resistance_level': resistance_level,
                        'distance_to_support': ((current_price - support_level) / current_price) * 100,
                        'distance_to_resistance': ((resistance_level - current_price) / current_price) * 100,
                        
                        # Trading signals
                        'trend': 'bullish' if current_price > sma_20 > sma_50 else 'bearish' if current_price < sma_20 < sma_50 else 'sideways',
                        'breakout_potential': resistance_level - current_price < current_price * 0.05,  # Within 5% of resistance
                        'breakdown_risk': current_price - support_level < current_price * 0.05  # Within 5% of support
                    }
                    
            except Exception as e:
                logger.warning(f"Could not get comprehensive data for {ticker}: {e}")
                market_data[ticker] = {'error': str(e)}
        
        return market_data
    
    def check_stop_losses(self, portfolio_summary: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for stop loss triggers and return sell recommendations."""
        sell_recommendations = []
        
        for position in portfolio_summary.get('portfolio', []):
            ticker = position['ticker']
            current_price = position['current_price']
            stop_loss = position['stop_loss']
            shares = position['shares']
            
            if stop_loss > 0 and current_price <= stop_loss:
                sell_recommendations.append({
                    'action': 'sell',
                    'ticker': ticker,
                    'shares': shares,
                    'reason': 'stop_loss_triggered',
                    'current_price': current_price,
                    'stop_loss': stop_loss,
                    'urgency': 'high'
                })
        
        return sell_recommendations
    
    def analyze_performance(self) -> Dict[str, Any]:
        """Analyze portfolio performance metrics."""
        try:
            df = pd.read_csv(PORTFOLIO_CSV)
            if df.empty:
                return {'error': 'No performance data available'}
            
            # Get TOTAL rows only
            totals = df[df["Ticker"] == "TOTAL"].copy()
            if totals.empty:
                return {'error': 'No total equity data found'}
            
            totals["Date"] = pd.to_datetime(totals["Date"])
            totals = totals.sort_values("Date")
            
            equity_series = totals.set_index("Date")["Total Equity"].astype(float)
            
            # Calculate key metrics
            returns = equity_series.pct_change().dropna()
            total_return = (equity_series.iloc[-1] / equity_series.iloc[0]) - 1
            
            # Volatility (annualized)
            volatility = returns.std() * np.sqrt(252) if len(returns) > 1 else 0
            
            # Max drawdown
            running_max = equity_series.cummax()
            drawdowns = (equity_series / running_max) - 1.0
            max_drawdown = drawdowns.min()
            
            # Sharpe ratio (assuming 4.5% risk-free rate)
            rf_daily = (1.045) ** (1/252) - 1
            excess_returns = returns - rf_daily
            sharpe_ratio = (excess_returns.mean() / returns.std()) * np.sqrt(252) if returns.std() > 0 else 0
            
            return {
                'total_return': total_return,
                'volatility': volatility,
                'max_drawdown': max_drawdown,
                'sharpe_ratio': sharpe_ratio,
                'trading_days': len(equity_series),
                'current_equity': equity_series.iloc[-1],
                'starting_equity': equity_series.iloc[0]
            }
            
        except Exception as e:
            logger.error(f"Error analyzing performance: {e}")
            return {'error': str(e)}
    
    def generate_analysis_report(self) -> Dict[str, Any]:
        """Generate comprehensive analysis for AI decision making."""
        portfolio_summary = self.get_portfolio_summary()
        
        # Get market data for portfolio stocks + benchmarks
        portfolio_tickers = [pos['ticker'] for pos in portfolio_summary.get('portfolio', [])]
        benchmarks = load_benchmarks()
        all_tickers = list(set(portfolio_tickers + benchmarks + ['SPY', 'QQQ', 'IWM', 'VIX']))
        
        market_data = self.get_market_data(all_tickers)
        performance = self.analyze_performance()
        stop_loss_checks = self.check_stop_losses(portfolio_summary)
        
        # Enhanced portfolio analysis with technical data
        enhanced_portfolio = self._enhance_portfolio_with_technical_data(portfolio_summary, market_data)
        
        # Market sentiment analysis based on key indicators
        market_sentiment = self._analyze_market_sentiment(market_data)
        
        # Sector analysis for diversification insights
        sector_analysis = self._analyze_sector_diversification(enhanced_portfolio)
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'portfolio': enhanced_portfolio,
            'market_data': market_data,
            'performance': performance,
            'stop_loss_alerts': stop_loss_checks,
            'market_sentiment': market_sentiment,
            'sector_analysis': sector_analysis,
            'trading_constraints': {
                'max_cash_per_trade': self.trading_config.get('max_cash_per_trade', 1000),
                'max_positions': self.trading_config.get('max_portfolio_positions', 10),
                'current_positions': portfolio_summary.get('positions_count', 0),
                'available_cash': portfolio_summary.get('cash_balance', 0)
            },
            'investment_opportunities': self._identify_investment_opportunities(market_data, enhanced_portfolio)
        }
        
        return report
    
    def _analyze_market_sentiment(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze overall market sentiment from key indicators."""
        sentiment_score = 0
        sentiment_factors = []
        
        # Check major indices
        indices = ['SPY', 'QQQ', 'IWM']
        for index in indices:
            if index in market_data and 'change_percent' in market_data[index]:
                change = market_data[index]['change_percent']
                if change > 1:
                    sentiment_score += 1
                    sentiment_factors.append(f"{index} up {change:.1f}%")
                elif change < -1:
                    sentiment_score -= 1
                    sentiment_factors.append(f"{index} down {change:.1f}%")
        
        # Check VIX if available
        if 'VIX' in market_data and 'price' in market_data['VIX']:
            vix = market_data['VIX']['price']
            if vix > 30:
                sentiment_score -= 2
                sentiment_factors.append(f"VIX elevated at {vix:.1f}")
            elif vix < 20:
                sentiment_score += 1
                sentiment_factors.append(f"VIX low at {vix:.1f}")
        
        # Determine overall sentiment
        if sentiment_score >= 2:
            sentiment = 'bullish'
        elif sentiment_score <= -2:
            sentiment = 'bearish'
        else:
            sentiment = 'neutral'
        
        return {
            'sentiment': sentiment,
            'score': sentiment_score,
            'factors': sentiment_factors
        }
    
    def _enhance_portfolio_with_technical_data(self, portfolio_summary: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance portfolio positions with technical analysis data."""
        enhanced_portfolio = portfolio_summary.copy()
        enhanced_positions = []
        
        for position in portfolio_summary.get('portfolio', []):
            ticker = position['ticker']
            enhanced_position = position.copy()
            
            # Add technical data if available
            if ticker in market_data and 'error' not in market_data[ticker]:
                tech_data = market_data[ticker]
                enhanced_position.update({
                    'technical_analysis': {
                        'trend': tech_data.get('trend', 'unknown'),
                        'rsi': tech_data.get('rsi', 50),
                        'rsi_signal': tech_data.get('rsi_signal', 'neutral'),
                        'price_vs_sma20': tech_data.get('price_vs_sma20', 0),
                        'price_vs_sma50': tech_data.get('price_vs_sma50', 0),
                        'volume_trend': tech_data.get('volume_trend', 'normal'),
                        'support_level': tech_data.get('support_level', position.get('current_price', 0)),
                        'resistance_level': tech_data.get('resistance_level', position.get('current_price', 0)),
                        'week_change': tech_data.get('week_change', 0),
                        'month_change': tech_data.get('month_change', 0),
                        'breakout_potential': tech_data.get('breakout_potential', False),
                        'breakdown_risk': tech_data.get('breakdown_risk', False)
                    },
                    'trading_signals': self._generate_position_signals(position, tech_data)
                })
            
            enhanced_positions.append(enhanced_position)
        
        enhanced_portfolio['portfolio'] = enhanced_positions
        return enhanced_portfolio
    
    def _generate_position_signals(self, position: Dict[str, Any], tech_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate trading signals for a specific position."""
        current_price = position.get('current_price', 0)
        buy_price = position.get('buy_price', 0)
        pnl_percent = position.get('pnl_percent', 0)
        
        signals = {
            'strength': 'neutral',
            'recommendation': 'hold',
            'risk_level': 'medium',
            'key_factors': []
        }
        
        # Trend analysis
        trend = tech_data.get('trend', 'sideways')
        if trend == 'bullish':
            signals['key_factors'].append('Bullish trend - price above moving averages')
            signals['strength'] = 'bullish'
        elif trend == 'bearish':
            signals['key_factors'].append('Bearish trend - price below moving averages')
            signals['strength'] = 'bearish'
            signals['risk_level'] = 'high'
        
        # RSI analysis
        rsi = tech_data.get('rsi', 50)
        if rsi > 70:
            signals['key_factors'].append(f'Overbought RSI: {rsi:.1f}')
            signals['risk_level'] = 'high'
        elif rsi < 30:
            signals['key_factors'].append(f'Oversold RSI: {rsi:.1f} - potential bounce')
        
        # Support/Resistance analysis
        if tech_data.get('breakdown_risk', False):
            signals['key_factors'].append('Near support level - breakdown risk')
            signals['risk_level'] = 'high'
        elif tech_data.get('breakout_potential', False):
            signals['key_factors'].append('Near resistance - breakout potential')
        
        # Position P&L considerations
        if pnl_percent < -10:
            signals['key_factors'].append(f'Large loss: {pnl_percent:.1f}% - consider stop loss')
            signals['recommendation'] = 'consider_sell'
        elif pnl_percent > 20:
            signals['key_factors'].append(f'Strong gain: {pnl_percent:.1f}% - consider taking profits')
        
        return signals
    
    def _analyze_sector_diversification(self, portfolio: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze sector diversification of the portfolio."""
        # Note: This is simplified - in practice you'd use sector mapping data
        positions = portfolio.get('portfolio', [])
        
        if not positions:
            return {'message': 'No positions to analyze'}
        
        # Simplified sector analysis based on common patterns
        tech_keywords = ['TECH', 'SOFT', 'DATA', 'SEMI', 'CYBER']
        biotech_keywords = ['BIO', 'PHARM', 'DRUG', 'GENE', 'THER']
        energy_keywords = ['OIL', 'GAS', 'ENERGY', 'SOLAR', 'WIND']
        
        sector_exposure = {'Technology': 0, 'Healthcare': 0, 'Energy': 0, 'Other': 0}
        total_value = sum(pos.get('current_value', 0) for pos in positions)
        
        for position in positions:
            ticker = position.get('ticker', '').upper()
            value = position.get('current_value', 0)
            
            if any(keyword in ticker for keyword in tech_keywords):
                sector_exposure['Technology'] += value
            elif any(keyword in ticker for keyword in biotech_keywords):
                sector_exposure['Healthcare'] += value  
            elif any(keyword in ticker for keyword in energy_keywords):
                sector_exposure['Energy'] += value
            else:
                sector_exposure['Other'] += value
        
        # Calculate percentages
        sector_percentages = {}
        if total_value > 0:
            for sector, value in sector_exposure.items():
                sector_percentages[sector] = (value / total_value) * 100
        
        return {
            'sector_exposure': sector_exposure,
            'sector_percentages': sector_percentages,
            'diversification_score': self._calculate_diversification_score(sector_percentages),
            'recommendations': self._generate_diversification_recommendations(sector_percentages)
        }
    
    def _calculate_diversification_score(self, sector_percentages: Dict[str, float]) -> float:
        """Calculate a diversification score (0-100, higher is more diversified)."""
        if not sector_percentages:
            return 0
        
        # Calculate Herfindahl-Hirschman Index (lower is more diversified)
        hhi = sum((pct/100) ** 2 for pct in sector_percentages.values())
        
        # Convert to diversification score (0-100, higher is better)
        max_hhi = 1.0  # Completely concentrated
        min_hhi = 1.0 / len(sector_percentages)  # Perfectly diversified
        
        if max_hhi == min_hhi:
            return 100
        
        diversification_score = ((max_hhi - hhi) / (max_hhi - min_hhi)) * 100
        return max(0, min(100, diversification_score))
    
    def _generate_diversification_recommendations(self, sector_percentages: Dict[str, float]) -> List[str]:
        """Generate recommendations for improving diversification."""
        recommendations = []
        
        for sector, percentage in sector_percentages.items():
            if percentage > 50:
                recommendations.append(f"High concentration in {sector} ({percentage:.1f}%) - consider diversifying")
            elif percentage == 0 and sector != 'Other':
                recommendations.append(f"No exposure to {sector} - consider adding positions")
        
        if not recommendations:
            recommendations.append("Portfolio shows reasonable sector diversification")
        
        return recommendations
    
    def _identify_investment_opportunities(self, market_data: Dict[str, Any], portfolio: Dict[str, Any]) -> Dict[str, Any]:
        """Identify potential investment opportunities based on market analysis."""
        opportunities = {
            'high_conviction': [],
            'moderate_conviction': [],
            'watch_list': [],
            'market_themes': []
        }
        
        # Analyze market data for opportunities
        for ticker, data in market_data.items():
            if ticker in ['SPY', 'QQQ', 'IWM', 'VIX'] or 'error' in data:
                continue
                
            # Skip if already in portfolio
            current_tickers = [pos['ticker'] for pos in portfolio.get('portfolio', [])]
            if ticker in current_tickers:
                continue
            
            signals = []
            conviction = 'low'
            
            # Technical opportunity signals
            if data.get('rsi', 50) < 30:
                signals.append('Oversold RSI - potential bounce')
                conviction = 'moderate'
            
            if data.get('trend') == 'bullish' and data.get('breakout_potential', False):
                signals.append('Bullish trend with breakout potential')
                conviction = 'high'
            
            if data.get('volume_trend') == 'high' and data.get('change_percent', 0) > 2:
                signals.append('High volume breakout')
                conviction = 'moderate'
            
            # Add to appropriate list based on conviction
            if signals:
                opportunity = {
                    'ticker': ticker,
                    'current_price': data.get('price', 0),
                    'signals': signals,
                    'technical_score': self._calculate_technical_score(data)
                }
                
                if conviction == 'high':
                    opportunities['high_conviction'].append(opportunity)
                elif conviction == 'moderate':
                    opportunities['moderate_conviction'].append(opportunity)
                else:
                    opportunities['watch_list'].append(opportunity)
        
        # Market themes analysis
        if market_data.get('VIX', {}).get('price', 0) < 20:
            opportunities['market_themes'].append('Low volatility environment - good for growth stocks')
        
        if market_data.get('QQQ', {}).get('change_percent', 0) > 1:
            opportunities['market_themes'].append('Technology sector showing strength')
        
        return opportunities
    
    def _calculate_technical_score(self, data: Dict[str, Any]) -> float:
        """Calculate a technical score for a stock (0-100)."""
        score = 50  # Base score
        
        # Trend score
        if data.get('trend') == 'bullish':
            score += 20
        elif data.get('trend') == 'bearish':
            score -= 20
        
        # RSI score
        rsi = data.get('rsi', 50)
        if 30 <= rsi <= 70:
            score += 10  # Neutral RSI is good
        elif rsi < 30:
            score += 5   # Oversold can be opportunity
        elif rsi > 70:
            score -= 10  # Overbought is risky
        
        # Volume score
        volume_trend = data.get('volume_trend', 'normal')
        if volume_trend == 'high':
            score += 10
        elif volume_trend == 'low':
            score -= 5
        
        # Momentum score
        week_change = data.get('week_change', 0)
        if week_change > 5:
            score += 10
        elif week_change < -5:
            score -= 10
        
        return max(0, min(100, score))