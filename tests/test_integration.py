#!/usr/bin/env python3
"""Integration tests for the ChatGPT Investor automation system."""

import json
import sys
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).resolve().parents[1]))

from core.config_manager import ConfigManager
from core.analyzer import InvestmentAnalyzer
from core.ai_decision import AIDecisionMaker
from notifications.email_sender import EmailNotifier


def test_config_manager():
    """Test configuration management."""
    print("Testing ConfigManager...")
    
    try:
        config_manager = ConfigManager()
        config = config_manager.get_config()
        summary = config_manager.get_summary()
        
        assert isinstance(config, dict), "Config should be a dictionary"
        assert 'openai' in config, "Config should have openai section"
        assert 'email' in config, "Config should have email section"
        assert 'trading' in config, "Config should have trading section"
        
        print("✅ ConfigManager test passed")
        return True
        
    except Exception as e:
        print(f"❌ ConfigManager test failed: {e}")
        return False


def test_investment_analyzer():
    """Test investment analyzer."""
    print("Testing InvestmentAnalyzer...")
    
    try:
        config_manager = ConfigManager()
        config = config_manager.get_config()
        analyzer = InvestmentAnalyzer(config)
        
        # Test portfolio summary
        summary = analyzer.get_portfolio_summary()
        assert isinstance(summary, dict), "Portfolio summary should be dict"
        assert 'cash_balance' in summary, "Should have cash_balance"
        assert 'total_equity' in summary, "Should have total_equity"
        
        # Test market data
        market_data = analyzer.get_market_data(['SPY', 'QQQ'])
        assert isinstance(market_data, dict), "Market data should be dict"
        
        print("✅ InvestmentAnalyzer test passed")
        return True
        
    except Exception as e:
        print(f"❌ InvestmentAnalyzer test failed: {e}")
        return False


def test_ai_decision_maker():
    """Test AI decision maker (with mocked API)."""
    print("Testing AIDecisionMaker...")
    
    try:
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        # Skip if no API key configured
        if not config.get('openai', {}).get('api_key'):
            print("⏭️  Skipping AI test - no API key configured")
            return True
        
        ai_maker = AIDecisionMaker(config)
        
        # Create mock analysis data
        mock_analysis = {
            'portfolio': {
                'cash_balance': 1000.0,
                'total_equity': 1000.0,
                'positions_count': 0,
                'portfolio': []
            },
            'market_data': {
                'SPY': {'price': 450.0, 'change_percent': 1.0}
            },
            'trading_constraints': {
                'max_cash_per_trade': 1000,
                'available_cash': 1000
            }
        }
        
        # Mock OpenAI API call
        mock_response = MagicMock()
        mock_response.choices[0].message.content = """
ACTION: BUY
TICKER: TEST
SHARES: 10
REASON: Test purchase for validation
STOP_LOSS: 45.00
        """
        
        with patch.object(ai_maker.client.chat.completions, 'create', return_value=mock_response):
            decisions = ai_maker.make_trading_decision(mock_analysis)
            
            assert isinstance(decisions, dict), "Decisions should be dict"
            assert 'decisions' in decisions, "Should have decisions list"
            
            decision_list = decisions.get('decisions', [])
            if decision_list:
                first_decision = decision_list[0]
                assert 'action' in first_decision, "Decision should have action"
                assert 'ticker' in first_decision, "Decision should have ticker"
        
        print("✅ AIDecisionMaker test passed")
        return True
        
    except Exception as e:
        print(f"❌ AIDecisionMaker test failed: {e}")
        return False


def test_email_notifier():
    """Test email notifier (without actually sending)."""
    print("Testing EmailNotifier...")
    
    try:
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        # Skip if no email configured
        email_config = config.get('email', {})
        if not email_config.get('sender_email') or not email_config.get('recipients'):
            print("⏭️  Skipping email test - not configured")
            return True
        
        notifier = EmailNotifier(config)
        
        # Test HTML generation (without sending)
        mock_portfolio = {
            'total_equity': 1000.0,
            'cash_balance': 500.0,
            'total_pnl': 50.0,
            'positions_count': 2,
            'portfolio': [
                {
                    'ticker': 'TEST',
                    'shares': 10,
                    'buy_price': 45.0,
                    'current_price': 50.0,
                    'pnl': 50.0,
                    'pnl_percent': 11.1,
                    'stop_loss': 40.0
                }
            ]
        }
        
        mock_decisions = {
            'decisions': [
                {
                    'action': 'hold',
                    'reason': 'Market conditions uncertain'
                }
            ],
            'model_used': 'gpt-4o',
            'timestamp': '2025-09-02T19:00:00'
        }
        
        # Test HTML generation
        html_content = notifier._generate_inline_html_report(mock_portfolio, mock_decisions)
        assert isinstance(html_content, str), "HTML content should be string"
        assert 'TEST' in html_content, "Should contain ticker symbol"
        assert '$1,000.00' in html_content, "Should contain equity value"
        
        print("✅ EmailNotifier test passed")
        return True
        
    except Exception as e:
        print(f"❌ EmailNotifier test failed: {e}")
        return False


def test_full_workflow():
    """Test the complete workflow integration."""
    print("Testing complete workflow...")
    
    try:
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        # Initialize components
        analyzer = InvestmentAnalyzer(config)
        
        # Generate analysis report
        analysis_report = analyzer.generate_analysis_report()
        assert isinstance(analysis_report, dict), "Analysis report should be dict"
        assert 'portfolio' in analysis_report, "Should have portfolio data"
        assert 'market_data' in analysis_report, "Should have market data"
        
        # Test with mocked AI if API key available
        if config.get('openai', {}).get('api_key'):
            ai_maker = AIDecisionMaker(config)
            
            # Mock the OpenAI call for testing
            mock_response = MagicMock()
            mock_response.choices[0].message.content = "ACTION: HOLD\nREASON: Test workflow"
            
            with patch.object(ai_maker.client.chat.completions, 'create', return_value=mock_response):
                decisions = ai_maker.make_trading_decision(analysis_report)
                assert isinstance(decisions, dict), "Decisions should be dict"
        
        print("✅ Full workflow test passed")
        return True
        
    except Exception as e:
        print(f"❌ Full workflow test failed: {e}")
        return False


def main():
    """Run all integration tests."""
    print("=" * 60)
    print("  ChatGPT Investor Integration Tests")
    print("=" * 60)
    
    tests = [
        test_config_manager,
        test_investment_analyzer,
        test_ai_decision_maker,
        test_email_notifier,
        test_full_workflow
    ]
    
    results = []
    for test_func in tests:
        print(f"\n--- {test_func.__name__} ---")
        result = test_func()
        results.append(result)
        time.sleep(0.5)  # Brief pause between tests
    
    print("\n" + "=" * 60)
    print("  Test Results Summary")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    for i, (test_func, result) in enumerate(zip(tests, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_func.__name__}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! System is ready for automation.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check configuration and dependencies.")
        return 1


if __name__ == "__main__":
    sys.exit(main())