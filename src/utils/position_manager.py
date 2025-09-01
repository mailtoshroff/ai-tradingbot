"""
Position Management utility for the AI Trading Bot
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import math

class PositionManager:
    """Position management with ATR-based sizing and averaging down"""
    
    def __init__(self):
        self.logger = None
        self.positions = {}  # Track all positions
        
    def set_logger(self, logger):
        """Set logger instance"""
        self.logger = logger
    
    def calculate_atr_position_size(self, portfolio_value: float, current_price: float, 
                                   atr_value: float, purchase_limit_pct: float) -> Dict:
        """
        Calculate position size using ATR vs purchase_limit_pct (whichever is less)
        
        Args:
            portfolio_value: Total portfolio value
            current_price: Current stock price
            atr_value: Current ATR value
            purchase_limit_pct: Maximum percentage of portfolio allowed
            
        Returns:
            Dict with position details
        """
        try:
            # Calculate position size based on 1 ATR per trade
            atr_position_value = portfolio_value * (atr_value / current_price)
            atr_position_pct = (atr_position_value / portfolio_value) * 100
            
            # Calculate position size based on purchase_limit_pct
            limit_position_value = portfolio_value * (purchase_limit_pct / 100)
            limit_position_pct = purchase_limit_pct
            
            # Use whichever is smaller
            if atr_position_pct <= limit_position_pct:
                final_position_pct = atr_position_pct
                final_position_value = atr_position_value
                sizing_method = "ATR-based"
            else:
                final_position_pct = limit_position_pct
                final_position_value = limit_position_value
                sizing_method = "Limit-based"
            
            # Calculate shares
            shares = int(final_position_value / current_price)
            actual_position_value = shares * current_price
            
            return {
                'shares': shares,
                'position_value': actual_position_value,
                'position_pct': (actual_position_value / portfolio_value) * 100,
                'sizing_method': sizing_method,
                'atr_position_pct': atr_position_pct,
                'limit_position_pct': limit_position_pct,
                'atr_value': atr_value,
                'current_price': current_price
            }
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error calculating ATR position size", error=str(e))
            return {}
    
    def should_average_down(self, ticker: str, current_price: float, 
                           entry_price: float, atr_value: float, 
                           pct_below_previous_buy: float) -> Tuple[bool, float, str]:
        """
        Determine if we should average down based on ATR multiples vs percentage
        
        Args:
            ticker: Stock symbol
            current_price: Current stock price
            entry_price: Original entry price
            atr_value: Current ATR value
            pct_below_previous_buy: Percentage below previous buy threshold
            
        Returns:
            Tuple of (should_average_down, confidence, reasoning)
        """
        try:
            if ticker not in self.positions:
                return False, 0.0, "No existing position"
            
            position = self.positions[ticker]
            price_drop = entry_price - current_price
            price_drop_pct = (price_drop / entry_price) * 100
            
            # Calculate ATR-based thresholds
            atr_2x = atr_value * 2
            atr_3x = atr_value * 3
            atr_4x = atr_value * 4
            
            # Calculate percentage-based threshold
            pct_threshold = entry_price * pct_below_previous_buy
            
            # Determine averaging down levels
            averaging_levels = []
            
            # 2 ATR level
            if price_drop >= atr_2x:
                atr_2x_pct = (atr_2x / entry_price) * 100
                averaging_levels.append({
                    'level': '2x ATR',
                    'atr_threshold': atr_2x,
                    'pct_threshold': atr_2x_pct,
                    'confidence': 0.7
                })
            
            # 3 ATR level
            if price_drop >= atr_3x:
                atr_3x_pct = (atr_3x / entry_price) * 100
                averaging_levels.append({
                    'level': '3x ATR',
                    'atr_threshold': atr_3x,
                    'pct_threshold': atr_3x_pct,
                    'confidence': 0.8
                })
            
            # 4 ATR level
            if price_drop >= atr_4x:
                atr_4x_pct = (atr_4x / entry_price) * 100
                averaging_levels.append({
                    'level': '4x ATR',
                    'atr_threshold': atr_4x,
                    'pct_threshold': atr_4x_pct,
                    'confidence': 0.9
                })
            
            # Check percentage-based threshold
            if price_drop >= pct_threshold:
                averaging_levels.append({
                    'level': 'Percentage',
                    'atr_threshold': pct_threshold,
                    'pct_threshold': pct_below_previous_buy * 100,
                    'confidence': 0.6
                })
            
            if not averaging_levels:
                return False, 0.0, f"Price drop {price_drop_pct:.2f}% below entry, no averaging levels reached"
            
            # Find the highest confidence level
            best_level = max(averaging_levels, key=lambda x: x['confidence'])
            
            reasoning = f"Price dropped {price_drop_pct:.2f}% below entry. {best_level['level']} threshold reached."
            
            return True, best_level['confidence'], reasoning
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error checking averaging down for {ticker}", error=str(e))
            return False, 0.0, f"Error: {str(e)}"
    
    def calculate_averaging_down_size(self, ticker: str, portfolio_value: float, 
                                    current_price: float, atr_value: float,
                                    averaging_level: str) -> Dict:
        """
        Calculate position size for averaging down
        
        Args:
            ticker: Stock symbol
            current_price: Current stock price
            portfolio_value: Total portfolio value
            atr_value: Current ATR value
            averaging_level: Level of averaging (2x, 3x, 4x ATR)
            
        Returns:
            Dict with averaging down details
        """
        try:
            # Base averaging size on ATR level
            if averaging_level == '2x ATR':
                base_pct = 0.5  # 50% of original position
                confidence_boost = 0.1
            elif averaging_level == '3x ATR':
                base_pct = 0.75  # 75% of original position
                confidence_boost = 0.2
            elif averaging_level == '4x ATR':
                base_pct = 1.0  # 100% of original position
                confidence_boost = 0.3
            else:
                base_pct = 0.5
                confidence_boost = 0.1
            
            # Calculate position size
            position_value = portfolio_value * (base_pct / 100)
            shares = int(position_value / current_price)
            actual_position_value = shares * current_price
            
            return {
                'shares': shares,
                'position_value': actual_position_value,
                'position_pct': (actual_position_value / portfolio_value) * 100,
                'averaging_level': averaging_level,
                'confidence_boost': confidence_boost,
                'current_price': current_price
            }
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error calculating averaging down size for {ticker}", error=str(e))
            return {}
    
    def should_take_partial_profit(self, ticker: str, current_price: float, 
                                  entry_price: float, sma_200: float) -> Tuple[bool, float, str]:
        """
        Check if we should sell half position at 50% above 200 SMA
        
        Args:
            ticker: Stock symbol
            current_price: Current stock price
            entry_price: Original entry price
            sma_200: 200-period Simple Moving Average
            
        Returns:
            Tuple of (should_sell_half, confidence, reasoning)
        """
        try:
            if ticker not in self.positions:
                return False, 0.0, "No existing position"
            
            position = self.positions[ticker]
            
            # Check if price is 50% above 200 SMA
            sma_200_50pct_above = sma_200 * 1.5
            
            if current_price >= sma_200_50pct_above:
                # Calculate profit percentage
                profit_pct = ((current_price - entry_price) / entry_price) * 100
                
                reasoning = f"Price {current_price:.2f} is 50%+ above 200 SMA ({sma_200:.2f}). Profit: {profit_pct:.2f}%"
                
                # Higher confidence for larger profits
                if profit_pct >= 100:  # 100%+ profit
                    confidence = 0.95
                elif profit_pct >= 75:  # 75%+ profit
                    confidence = 0.9
                elif profit_pct >= 50:  # 50%+ profit
                    confidence = 0.85
                else:
                    confidence = 0.8
                
                return True, confidence, reasoning
            
            return False, 0.0, f"Price {current_price:.2f} not yet 50% above 200 SMA ({sma_200:.2f})"
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error checking partial profit for {ticker}", error=str(e))
            return False, 0.0, f"Error: {str(e)}"
    
    def add_position(self, ticker: str, entry_price: float, shares: int, 
                    position_value: float, rule_name: str, confidence: float):
        """Add a new position to tracking"""
        try:
            self.positions[ticker] = {
                'entry_price': entry_price,
                'shares': shares,
                'position_value': position_value,
                'rule_name': rule_name,
                'entry_confidence': confidence,
                'entry_date': datetime.now(),
                'averaging_levels': [],  # Track averaging down
                'partial_sales': []      # Track partial profit taking
            }
            
            if self.logger:
                self.logger.info(f"Added position for {ticker}", 
                               ticker=ticker, entry_price=entry_price, shares=shares)
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error adding position for {ticker}", error=str(e))
    
    def update_position(self, ticker: str, action: str, **kwargs):
        """Update existing position"""
        try:
            if ticker not in self.positions:
                return
            
            if action == 'average_down':
                self.positions[ticker]['averaging_levels'].append({
                    'date': datetime.now(),
                    'price': kwargs.get('price'),
                    'shares': kwargs.get('shares'),
                    'level': kwargs.get('level')
                })
                
            elif action == 'partial_sale':
                self.positions[ticker]['partial_sales'].append({
                    'date': datetime.now(),
                    'price': kwargs.get('price'),
                    'shares': kwargs.get('shares'),
                    'reason': kwargs.get('reason')
                })
                
            if self.logger:
                self.logger.info(f"Updated position for {ticker}", 
                               ticker=ticker, action=action, details=kwargs)
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error updating position for {ticker}", error=str(e))
    
    def get_position_summary(self, ticker: str) -> Dict:
        """Get summary of a position"""
        try:
            if ticker not in self.positions:
                return {}
            
            position = self.positions[ticker]
            
            return {
                'ticker': ticker,
                'entry_price': position['entry_price'],
                'total_shares': position['shares'],
                'entry_value': position['position_value'],
                'rule_name': position['rule_name'],
                'entry_confidence': position['entry_confidence'],
                'entry_date': position['entry_date'],
                'averaging_count': len(position['averaging_levels']),
                'partial_sales_count': len(position['partial_sales']),
                'averaging_levels': position['averaging_levels'],
                'partial_sales': position['partial_sales']
            }
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error getting position summary for {ticker}", error=str(e))
            return {}
    
    def get_all_positions(self) -> Dict:
        """Get summary of all positions"""
        try:
            return {
                ticker: self.get_position_summary(ticker)
                for ticker in self.positions.keys()
            }
        except Exception as e:
            if self.logger:
                self.logger.error("Error getting all positions", error=str(e))
            return {}

