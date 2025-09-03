"""Configuration management for the ChatGPT Investor system."""

import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages configuration loading and validation for the system."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = Path(config_path) if config_path else self._get_default_config_path()
        self.config = {}
        self._load_configuration()
    
    def _get_default_config_path(self) -> Path:
        """Get the default configuration file path."""
        return Path(__file__).resolve().parents[1] / 'config' / 'config.json'
    
    def _load_configuration(self):
        """Load configuration from file and environment variables."""
        # Load environment variables first
        load_dotenv()
        
        # Load base configuration from JSON file
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
            logger.info(f"Loaded configuration from {self.config_path}")
        else:
            logger.warning(f"Configuration file not found: {self.config_path}")
            self.config = self._get_default_config()
        
        # Override with environment variables
        self._apply_environment_overrides()
        
        # Validate configuration
        self._validate_configuration()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration if file doesn't exist."""
        return {
            "openai": {
                "api_key": "",
                "model": "gpt-4o",
                "temperature": 0.7
            },
            "email": {
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "sender_email": "",
                "sender_password": "",
                "recipients": []
            },
            "trading": {
                "max_cash_per_trade": 1000,
                "default_stop_loss_percent": 0.15,
                "max_portfolio_positions": 10,
                "enable_stop_loss": True
            },
            "schedule": {
                "daily_run_time": "19:00",
                "timezone": "America/New_York"
            },
            "api": {
                "host": "0.0.0.0",
                "port": 5000,
                "debug": False
            },
            "data": {
                "portfolio_csv": "chatgpt_portfolio_update.csv",
                "trade_log_csv": "chatgpt_trade_log.csv"
            }
        }
    
    def _apply_environment_overrides(self):
        """Apply environment variable overrides to configuration."""
        env_mappings = {
            'OPENAI_API_KEY': ['openai', 'api_key'],
            'OPENAI_MODEL': ['openai', 'model'],
            'OPENAI_TEMPERATURE': ['openai', 'temperature'],
            'EMAIL_SENDER': ['email', 'sender_email'],
            'EMAIL_PASSWORD': ['email', 'sender_password'],
            'EMAIL_RECIPIENTS': ['email', 'recipients'],
            'SMTP_SERVER': ['email', 'smtp_server'],
            'SMTP_PORT': ['email', 'smtp_port'],
            'MAX_CASH_PER_TRADE': ['trading', 'max_cash_per_trade'],
            'MAX_POSITIONS': ['trading', 'max_portfolio_positions'],
            'STOP_LOSS_PERCENT': ['trading', 'default_stop_loss_percent'],
            'DAILY_RUN_TIME': ['schedule', 'daily_run_time'],
            'API_HOST': ['api', 'host'],
            'API_PORT': ['api', 'port'],
            'API_DEBUG': ['api', 'debug'],
            'PORTFOLIO_CSV': ['data', 'portfolio_csv'],
            'TRADE_LOG_CSV': ['data', 'trade_log_csv']
        }
        
        for env_var, config_path in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                # Handle special cases
                if env_var == 'EMAIL_RECIPIENTS':
                    env_value = [email.strip() for email in env_value.split(',')]
                elif env_var in ['SMTP_PORT', 'API_PORT', 'MAX_CASH_PER_TRADE', 'MAX_POSITIONS']:
                    try:
                        env_value = int(env_value)
                    except ValueError:
                        logger.warning(f"Invalid integer value for {env_var}: {env_value}")
                        continue
                elif env_var in ['OPENAI_TEMPERATURE', 'STOP_LOSS_PERCENT']:
                    try:
                        env_value = float(env_value)
                    except ValueError:
                        logger.warning(f"Invalid float value for {env_var}: {env_value}")
                        continue
                elif env_var == 'API_DEBUG':
                    env_value = env_value.lower() in ['true', '1', 'yes', 'on']
                
                # Set the configuration value
                self._set_nested_config(config_path, env_value)
                logger.info(f"Applied environment override for {env_var}")
    
    def _set_nested_config(self, path: list, value: Any):
        """Set a nested configuration value."""
        current = self.config
        for key in path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[path[-1]] = value
    
    def _validate_configuration(self):
        """Validate the loaded configuration."""
        errors = []
        warnings = []
        
        # Validate OpenAI configuration
        if not self.config.get('openai', {}).get('api_key'):
            errors.append("OpenAI API key is required")
        
        # Validate email configuration
        email_config = self.config.get('email', {})
        if not email_config.get('sender_email'):
            warnings.append("Email sender not configured - email notifications will be disabled")
        if not email_config.get('sender_password'):
            warnings.append("Email password not configured - email notifications will be disabled")
        if not email_config.get('recipients'):
            warnings.append("No email recipients configured - notifications will not be sent")
        
        # Validate trading configuration
        trading_config = self.config.get('trading', {})
        if trading_config.get('max_cash_per_trade', 0) <= 0:
            warnings.append("Max cash per trade should be positive")
        if trading_config.get('max_portfolio_positions', 0) <= 0:
            warnings.append("Max portfolio positions should be positive")
        
        # Validate file paths
        data_config = self.config.get('data', {})
        portfolio_csv = data_config.get('portfolio_csv')
        if portfolio_csv and not Path(portfolio_csv).exists():
            warnings.append(f"Portfolio CSV file not found: {portfolio_csv}")
        
        # Log validation results
        for error in errors:
            logger.error(f"Configuration error: {error}")
        for warning in warnings:
            logger.warning(f"Configuration warning: {warning}")
        
        if errors:
            raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")
        
        logger.info("Configuration validation completed")
    
    def get_config(self) -> Dict[str, Any]:
        """Get the complete configuration."""
        return self.config.copy()
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get a specific configuration section."""
        return self.config.get(section, {}).copy()
    
    def get_value(self, section: str, key: str, default: Any = None) -> Any:
        """Get a specific configuration value."""
        return self.config.get(section, {}).get(key, default)
    
    def is_configured(self, section: str, key: str) -> bool:
        """Check if a configuration value is set."""
        value = self.get_value(section, key)
        return value is not None and value != ""
    
    def save_config(self, config_path: Optional[str] = None):
        """Save the current configuration to file."""
        save_path = Path(config_path) if config_path else self.config_path
        
        # Create directory if it doesn't exist
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Remove sensitive data before saving
        safe_config = self._get_safe_config()
        
        with open(save_path, 'w') as f:
            json.dump(safe_config, f, indent=2)
        
        logger.info(f"Configuration saved to {save_path}")
    
    def _get_safe_config(self) -> Dict[str, Any]:
        """Get configuration with sensitive data removed."""
        safe_config = self.config.copy()
        
        # Remove sensitive keys
        sensitive_keys = [
            ['openai', 'api_key'],
            ['email', 'sender_password']
        ]
        
        for key_path in sensitive_keys:
            current = safe_config
            for key in key_path[:-1]:
                if key in current and isinstance(current[key], dict):
                    current = current[key]
                else:
                    break
            else:
                if key_path[-1] in current:
                    current[key_path[-1]] = ""
        
        return safe_config
    
    def reload_config(self):
        """Reload configuration from file and environment."""
        logger.info("Reloading configuration...")
        self._load_configuration()
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the current configuration status."""
        return {
            'config_file': str(self.config_path),
            'config_exists': self.config_path.exists(),
            'openai_configured': bool(self.get_value('openai', 'api_key')),
            'email_configured': bool(self.get_value('email', 'sender_email') and 
                                   self.get_value('email', 'sender_password')),
            'recipients_count': len(self.get_value('email', 'recipients', [])),
            'trading_params': {
                'max_cash_per_trade': self.get_value('trading', 'max_cash_per_trade'),
                'max_positions': self.get_value('trading', 'max_portfolio_positions'),
                'stop_loss_enabled': self.get_value('trading', 'enable_stop_loss')
            },
            'schedule': {
                'daily_run_time': self.get_value('schedule', 'daily_run_time'),
                'timezone': self.get_value('schedule', 'timezone')
            },
            'api': {
                'host': self.get_value('api', 'host'),
                'port': self.get_value('api', 'port')
            }
        }