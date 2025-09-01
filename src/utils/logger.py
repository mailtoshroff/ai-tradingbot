"""
Logging utility for the AI Trading Bot
"""
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
import structlog
from typing import Optional

class TradingBotLogger:
    """Centralized logging for the trading bot"""
    
    def __init__(self, log_level: str = "INFO", log_file: Optional[str] = None):
        self.log_level = getattr(logging, log_level.upper())
        self.log_file = log_file or "logs/trading_bot.log"
        
        # Create logs directory if it doesn't exist
        Path(self.log_file).parent.mkdir(parents=True, exist_ok=True)
        
        # Configure structlog
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
        
        # Configure standard logging
        self._setup_logging()
        
    def _setup_logging(self):
        """Setup logging configuration"""
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Setup file handler
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(self.log_level)
        file_handler.setFormatter(formatter)
        
        # Setup console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.log_level)
        console_handler.setFormatter(formatter)
        
        # Setup root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(self.log_level)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
        
        # Prevent duplicate logs
        root_logger.propagate = False
        
    def get_logger(self, name: str):
        """Get a logger instance for a specific component"""
        return structlog.get_logger(name)
    
    def log_trade_signal(self, ticker: str, signal: str, confidence: float, 
                         reasoning: str, agent: str):
        """Log trade signals with structured data"""
        logger = self.get_logger("trade_signals")
        logger.info(
            "Trade signal generated",
            ticker=ticker,
            signal=signal,
            confidence=confidence,
            reasoning=reasoning,
            agent=agent,
            timestamp=datetime.utcnow().isoformat()
        )
    
    def log_trade_execution(self, ticker: str, action: str, quantity: int, 
                           price: float, order_id: str):
        """Log trade executions"""
        logger = self.get_logger("trade_execution")
        logger.info(
            "Trade executed",
            ticker=ticker,
            action=action,
            quantity=quantity,
            price=price,
            order_id=order_id,
            timestamp=datetime.utcnow().isoformat()
        )
    
    def log_portfolio_update(self, portfolio_value: float, positions: dict):
        """Log portfolio updates"""
        logger = self.get_logger("portfolio")
        logger.info(
            "Portfolio updated",
            portfolio_value=portfolio_value,
            positions=positions,
            timestamp=datetime.utcnow().isoformat()
        )
    
    def log_error(self, error: Exception, context: str, agent: str):
        """Log errors with context"""
        logger = self.get_logger("errors")
        logger.error(
            "Error occurred",
            error=str(error),
            error_type=type(error).__name__,
            context=context,
            agent=agent,
            timestamp=datetime.utcnow().isoformat()
        )
    
    def log_agent_activity(self, agent: str, action: str, details: dict):
        """Log agent activities"""
        logger = self.get_logger("agent_activity")
        logger.info(
            "Agent activity",
            agent=agent,
            action=action,
            details=details,
            timestamp=datetime.utcnow().isoformat()
        )

# Global logger instance
trading_logger = TradingBotLogger()
