"""
Technical indicators utility for the AI Trading Bot
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta

class TechnicalIndicators:
    """Technical analysis indicators calculator"""
    
    def __init__(self):
        self.logger = None  # Will be set by the calling agent
        
    def set_logger(self, logger):
        """Set logger instance"""
        self.logger = logger
    
    def calculate_sma(self, data: pd.DataFrame, period: int) -> pd.Series:
        """Calculate Simple Moving Average"""
        return data['close'].rolling(window=period).mean()
    
    def calculate_ema(self, data: pd.DataFrame, period: int) -> pd.Series:
        """Calculate Exponential Moving Average"""
        return data['close'].ewm(span=period).mean()
    
    def calculate_atr(self, data: pd.DataFrame, period: int = 14, factor: float = 2.0) -> pd.Series:
        """Calculate Average True Range (ATR) using Wilder's smoothing"""
        try:
            if len(data) < period:
                return pd.Series([0] * len(data), index=data.index)
            
            # Calculate True Range
            high_low = data['high'] - data['low']
            high_close = abs(data['high'] - data['close'].shift())
            low_close = abs(data['low'] - data['close'].shift())
            
            true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            
            # Apply Wilder's smoothing (exponential moving average with alpha = 1/period)
            atr = true_range.ewm(alpha=1/period, adjust=False).mean()
            
            return atr
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error calculating ATR", error=str(e))
            return pd.Series([0] * len(data), index=data.index)
    
    def calculate_atr_multiples(self, data: pd.DataFrame, period: int = 14) -> Dict[str, pd.Series]:
        """
        Calculate ATR multiples for position sizing and averaging down
        
        Args:
            data: Price data
            period: ATR period
            
        Returns:
            Dict with ATR and its multiples
        """
        try:
            atr = self.calculate_atr(data, period)
            
            return {
                'atr': atr,
                'atr_2x': atr * 2,
                'atr_3x': atr * 3,
                'atr_4x': atr * 4,
                'atr_5x': atr * 5
            }
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error calculating ATR multiples", error=str(e))
            return {}
    
    def calculate_position_sizing_atr(self, data: pd.DataFrame, portfolio_value: float, 
                                    current_price: float, atr_period: int = 14) -> Dict:
        """
        Calculate position size based on ATR (1 ATR per trade)
        
        Args:
            data: Price data
            portfolio_value: Total portfolio value
            current_price: Current stock price
            atr_period: Period for ATR calculation
            
        Returns:
            Dict with position sizing details
        """
        try:
            atr = self.calculate_atr(data, atr_period)
            current_atr = atr.iloc[-1] if len(atr) > 0 else 0
            
            if current_atr == 0:
                return {}
            
            # Calculate position size based on 1 ATR per trade
            # This means the position value should equal 1 ATR
            atr_position_value = current_atr
            atr_position_pct = (atr_position_value / portfolio_value) * 100
            
            # Calculate shares
            shares = int(atr_position_value / current_price)
            actual_position_value = shares * current_price
            
            return {
                'atr_value': current_atr,
                'atr_position_value': atr_position_value,
                'atr_position_pct': atr_position_pct,
                'shares': shares,
                'actual_position_value': actual_position_value,
                'sizing_method': 'ATR-based (1 ATR per trade)'
            }
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error calculating ATR position sizing", error=str(e))
            return {}
    
    def calculate_atr_trailing_stop(self, data: pd.DataFrame, period: int = 5, 
                                   factor: float = 2.5) -> pd.Series:
        """Calculate ATR Trailing Stop"""
        atr = self.calculate_atr(data, period, factor)
        highest_high = data['high'].rolling(window=period).max()
        return highest_high - atr
    
    def calculate_nymo(self, data: pd.DataFrame) -> pd.Series:
        """Calculate NYMO (McClellan Oscillator)"""
        try:
            # For now, return a simple oscillator based on price momentum
            # In a real implementation, this would use advancing/declining issues data
            if len(data) < 20:
                return pd.Series([0] * len(data), index=data.index)
            
            # Calculate momentum oscillator based on price change
            price_change = data['close'].pct_change(20)
            momentum = (price_change - price_change.rolling(20).mean()) / price_change.rolling(20).std()
            
            # Scale to NYMO-like range (-100 to +100)
            nymo = momentum * 50
            
            return nymo.fillna(0)
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error calculating NYMO", error=str(e))
            return pd.Series([0] * len(data), index=data.index)
    
    def calculate_all_indicators(self, data: pd.DataFrame, ticker: str, period: str = 'D') -> Dict:
        """Calculate all technical indicators for a ticker"""
        try:
            if data.empty:
                return {}
            
            indicators = {'data': data}
            
            # Calculate SMAs
            indicators['sma_21'] = self.calculate_sma(data, 21)
            indicators['sma_50'] = self.calculate_sma(data, 50)
            indicators['sma_200'] = self.calculate_sma(data, 200)
            
            # Calculate EMAs
            indicators['ema_10'] = self.calculate_ema(data, 10)
            indicators['ema_20'] = self.calculate_ema(data, 20)
            indicators['ema_40'] = self.calculate_ema(data, 40)
            
            # Calculate ATR and trailing stop
            indicators['atr'] = self.calculate_atr(data, period=5)
            indicators['atr_trailing_stop'] = self.calculate_atr_trailing_stop(data, period=5)
            
            # Calculate NYMO for daily data
            if period == 'D':
                indicators['nymo'] = self.calculate_nymo(data)
            
            # Calculate price position relative to moving averages
            if len(data) >= 20:
                # Price above previous 20 days average
                indicators['above_previous_20_days'] = data['close'] > data['close'].rolling(20).mean()
                
                # Price above previous 15 days average
                indicators['above_previous_15_days'] = data['close'] > data['close'].rolling(15).mean()
                
                # Price above previous 10 days average
                indicators['above_previous_10_days'] = data['close'] > data['close'].rolling(10).mean()
            
            self.logger.info(f"Calculated {len(indicators)} indicators for {ticker} ({period})", 
                           ticker=ticker, period=period, indicators_count=len(indicators))
            
            return indicators
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error calculating indicators for {ticker}", 
                                error=str(e), ticker=ticker)
            return {}
    
    def evaluate_trading_rule(self, ticker: str, rule: Dict, indicators: Dict) -> Tuple[bool, float, str]:
        """Evaluate a trading rule based on the rule description from rules.json"""
        try:
            rule_name = rule.get('name', '')
            rule_type = rule.get('type', 'buy')
            priority = rule.get('priority', 5)
            description = rule.get('description', '')
            period = rule.get('period', 'D')
            length = rule.get('length', 21)
            previous_days = rule.get('previous_days', 20)
            
            signal_triggered = False
            confidence = 0.0
            reasoning = []
            
            # Get current price and data
            current_price = indicators['data']['close'].iloc[-1]
            data = indicators['data']
            
            # Check if price is above the previous days average (common requirement)
            if 'previous_days' in rule:
                # Calculate average of last N days
                if len(data) >= previous_days:
                    previous_avg = data['close'].tail(previous_days).mean()
                    if current_price > previous_avg:
                        reasoning.append(f"Price above previous {previous_days} days average")
                        confidence += 0.2
                    else:
                        reasoning.append(f"Price below previous {previous_days} days average")
                        confidence -= 0.3
                        return False, confidence, "; ".join(reasoning)
            
            # Rule-specific logic based on description
            if 'sma_cross' in rule_name:
                if '21' in rule_name:
                    # 21 SMA cross below logic
                    sma_21 = indicators.get(f'sma_{length}', pd.Series([0]))
                    if hasattr(sma_21, '__len__') and len(sma_21) >= 2:
                        # Check if price crossed below 21 SMA
                        prev_price = data['close'].iloc[-2]
                        prev_sma = sma_21.iloc[-2] if hasattr(sma_21, 'iloc') else sma_21[-2]
                        current_sma = sma_21.iloc[-1] if hasattr(sma_21, 'iloc') else sma_21[-1]
                        
                        # Price was above SMA yesterday, now below (crossing down)
                        if prev_price > prev_sma and current_price < current_sma:
                            signal_triggered = True
                            confidence = 0.8
                            reasoning.append(f"Price crossed below {length}-period SMA")
                            
                            # Check if above 50 and 200 SMA (for priority 1-2 rules)
                            if priority <= 2:
                                sma_50 = indicators.get('sma_50', pd.Series([0]))
                                sma_200 = indicators.get('sma_200', pd.Series([0]))
                                if (hasattr(sma_50, '__len__') and len(sma_50) > 0 and 
                                    hasattr(sma_200, '__len__') and len(sma_200) > 0):
                                    sma_50_val = sma_50.iloc[-1] if hasattr(sma_50, 'iloc') else sma_50[-1]
                                    sma_200_val = sma_200.iloc[-1] if hasattr(sma_200, 'iloc') else sma_200[-1]
                                    if current_price > sma_50_val and current_price > sma_200_val:
                                        reasoning.append("Price above 50 and 200 SMA")
                                        confidence += 0.1
                                    else:
                                        confidence -= 0.2
                                        reasoning.append("Price below 50 or 200 SMA")
                
                elif '50' in rule_name:
                    # 50 SMA cross below logic
                    sma_50 = indicators.get(f'sma_{length}', pd.Series([0]))
                    if hasattr(sma_50, '__len__') and len(sma_50) >= 2:
                        prev_price = data['close'].iloc[-2]
                        prev_sma = sma_50.iloc[-2] if hasattr(sma_50, 'iloc') else sma_50[-2]
                        current_sma = sma_50.iloc[-1] if hasattr(sma_50, 'iloc') else sma_50[-1]
                        
                        if prev_price > prev_sma and current_price < current_sma:
                            signal_triggered = True
                            confidence = 0.7
                            reasoning.append(f"Price crossed below {length}-period SMA")
                            
                            # Check if above 200 SMA (for priority 2 rule)
                            if priority == 2:
                                sma_200 = indicators.get('sma_200', pd.Series([0]))
                                if hasattr(sma_200, '__len__') and len(sma_200) > 0:
                                    sma_200_val = sma_200.iloc[-1] if hasattr(sma_200, 'iloc') else sma_200[-1]
                                    if current_price > sma_200_val:
                                        reasoning.append("Price above 200 SMA")
                                        confidence += 0.1
                                    else:
                                        confidence -= 0.2
                                        reasoning.append("Price below 200 SMA")
                
                elif '200' in rule_name:
                    # 200 SMA cross below logic
                    sma_200 = indicators.get(f'sma_{length}', pd.Series([0]))
                    if hasattr(sma_200, '__len__') and len(sma_200) >= 2:
                        prev_price = data['close'].iloc[-2]
                        prev_sma = sma_200.iloc[-2] if hasattr(sma_200, 'iloc') else sma_200[-2]
                        current_sma = sma_200.iloc[-1] if hasattr(sma_200, 'iloc') else sma_200[-1]
                        
                        if prev_price > prev_sma and current_price < current_sma:
                            signal_triggered = True
                            confidence = 0.6
                            reasoning.append(f"Price crossed below {length}-period SMA")
            
            elif 'ema_cross' in rule_name:
                if '10' in rule_name:
                    # 10 EMA cross below logic
                    ema_10 = indicators.get(f'ema_{length}', pd.Series([0]))
                    ema_20 = indicators.get('ema_20', pd.Series([0]))
                    ema_40 = indicators.get('ema_40', pd.Series([0]))
                    sma_200 = indicators.get('sma_200', pd.Series([0]))
                    
                    if (hasattr(ema_10, '__len__') and len(ema_10) >= 2 and 
                        hasattr(ema_20, '__len__') and len(ema_20) > 0 and 
                        hasattr(ema_40, '__len__') and len(ema_40) > 0):
                        prev_price = data['close'].iloc[-2]
                        prev_ema = ema_10.iloc[-2] if hasattr(ema_10, 'iloc') else ema_10[-2]
                        current_ema = ema_10.iloc[-1] if hasattr(ema_10, 'iloc') else ema_10[-1]
                        
                        # Check if price crossed below 10 EMA
                        if prev_price > prev_ema and current_price < current_ema:
                            signal_triggered = True
                            confidence = 0.75
                            reasoning.append(f"Price crossed below {length}-period EMA")
                            
                            # Check if above 20, 40, and 200 SMA
                            ema_20_val = ema_20.iloc[-1] if hasattr(ema_20, 'iloc') else ema_20[-1]
                            ema_40_val = ema_40.iloc[-1] if hasattr(ema_40, 'iloc') else ema_40[-1]
                            sma_200_val = sma_200.iloc[-1] if hasattr(sma_200, 'iloc') else sma_200[-1]
                            
                            if (current_price > ema_20_val and 
                                current_price > ema_40_val and 
                                current_price > sma_200_val):
                                reasoning.append("Price above 20, 40, and 200 SMA")
                                confidence += 0.1
                            else:
                                confidence -= 0.2
                                reasoning.append("Price below 20, 40, or 200 SMA")
                
                elif '20' in rule_name:
                    # 20 EMA cross below logic
                    ema_20 = indicators.get(f'ema_{length}', pd.Series([0]))
                    ema_40 = indicators.get('ema_40', pd.Series([0]))
                    sma_200 = indicators.get('sma_200', pd.Series([0]))
                    
                    if (hasattr(ema_20, '__len__') and len(ema_20) >= 2 and 
                        hasattr(ema_40, '__len__') and len(ema_40) > 0 and 
                        hasattr(sma_200, '__len__') and len(sma_200) > 0):
                        prev_price = data['close'].iloc[-2]
                        prev_ema = ema_20.iloc[-2] if hasattr(ema_20, 'iloc') else ema_20[-2]
                        current_ema = ema_20.iloc[-1] if hasattr(ema_20, 'iloc') else ema_20[-1]
                        
                        # Check if price crossed below 20 EMA
                        if prev_price > prev_ema and current_price < current_ema:
                            signal_triggered = True
                            confidence = 0.7
                            reasoning.append(f"Price crossed below {length}-period EMA")
                            
                            # Check if above 40 and 200 SMA
                            ema_40_val = ema_40.iloc[-1] if hasattr(ema_40, 'iloc') else ema_40[-1]
                            sma_200_val = sma_200.iloc[-1] if hasattr(sma_200, 'iloc') else sma_200[-1]
                            
                            if (current_price > ema_40_val and 
                                current_price > sma_200_val):
                                reasoning.append("Price above 40 and 200 SMA")
                                confidence += 0.1
                            else:
                                confidence -= 0.2
                                reasoning.append("Price below 40 or 200 SMA")
                
                elif '40' in rule_name:
                    # 40 EMA cross below logic
                    ema_40 = indicators.get(f'ema_{length}', pd.Series([0]))
                    sma_200 = indicators.get('sma_200', pd.Series([0]))
                    
                    if (hasattr(ema_40, '__len__') and len(ema_40) >= 2 and 
                        hasattr(sma_200, '__len__') and len(sma_200) > 0):
                        prev_price = data['close'].iloc[-2]
                        prev_ema = ema_40.iloc[-2] if hasattr(ema_40, 'iloc') else ema_40[-2]
                        current_ema = ema_40.iloc[-1] if hasattr(ema_40, 'iloc') else ema_40[-1]
                        
                        # Check if price crossed below 40 EMA
                        if prev_price > prev_ema and current_price < current_ema:
                            signal_triggered = True
                            confidence = 0.65
                            reasoning.append(f"Price crossed below {length}-period EMA")
                            
                            # Check if above 200 SMA
                            sma_200_val = sma_200.iloc[-1] if hasattr(sma_200, 'iloc') else sma_200[-1]
                            if current_price > sma_200_val:
                                reasoning.append("Price above 200 SMA")
                                confidence += 0.1
                            else:
                                confidence -= 0.2
                                reasoning.append("Price below 200 SMA")
            
            elif 'atr' in rule_name:
                # ATR trailing stop logic - check if price crossed below the stop
                atr_trailing_stop = indicators.get('atr_trailing_stop', pd.Series([0]))
                if hasattr(atr_trailing_stop, '__len__') and len(atr_trailing_stop) >= 2:
                    prev_price = data['close'].iloc[-2]
                    prev_stop = atr_trailing_stop.iloc[-2] if hasattr(atr_trailing_stop, 'iloc') else atr_trailing_stop[-2]
                    current_stop = atr_trailing_stop.iloc[-1] if hasattr(atr_trailing_stop, 'iloc') else atr_trailing_stop[-1]
                    
                    # Check if price crossed below ATR trailing stop
                    if prev_price > prev_stop and current_price < current_stop:
                        signal_triggered = True
                        confidence = 0.7
                        reasoning.append("Price crossed below ATR trailing stop")
                    else:
                        reasoning.append("Price did not cross below ATR trailing stop")
                        confidence -= 0.3
            
            elif 'nymo' in rule_name:
                # NYMO threshold check
                nymo_threshold = rule.get('nymo_threshold', -50)
                nymo_value = indicators.get('nymo', pd.Series([0]))
                
                if hasattr(nymo_value, '__len__') and len(nymo_value) > 0:
                    nymo_val = nymo_value.iloc[-1] if hasattr(nymo_value, 'iloc') else nymo_value[-1]
                    if nymo_val < nymo_threshold:
                        signal_triggered = True
                        confidence = 0.8
                        reasoning.append(f"NYMO below {nymo_threshold}")
                        
                        # Higher confidence for more extreme NYMO values
                        if nymo_threshold == -100:
                            confidence = 0.95
                        elif nymo_threshold == -70:
                            confidence = 0.9
            
            # Final confidence adjustment based on priority
            if signal_triggered:
                # Higher priority rules get confidence boost
                priority_boost = (10 - priority) * 0.05
                confidence = min(1.0, confidence + priority_boost)
                reasoning.append(f"Priority {priority} rule")
            
            reasoning_text = "; ".join(reasoning)
            
            if self.logger:
                self.logger.info(f"Rule evaluation for {ticker}", 
                               ticker=ticker, rule=rule_name, 
                               signal_triggered=signal_triggered, 
                               confidence=confidence, reasoning=reasoning_text)
            
            return signal_triggered, confidence, reasoning_text
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error evaluating rule for {ticker}", 
                                error=str(e), ticker=ticker, rule=rule.get('name', 'unknown'))
            return False, 0.0, f"Error: {str(e)}"
