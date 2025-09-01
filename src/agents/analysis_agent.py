"""
Analysis Agent for technical analysis and rule evaluation
"""
import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from core.data_manager import DataManager
from utils.logger import trading_logger
from utils.technical_indicators import TechnicalIndicators
import pandas as pd

class AnalysisAgent:
    """Technical Analysis Agent for evaluating trading rules"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        self.logger = trading_logger.get_logger("analysis_agent")
        self.data_manager = DataManager(config_path)
        self.technical_indicators = TechnicalIndicators()
        self.technical_indicators.set_logger(self.logger)
        
        # Agent state
        self.last_analysis_time = None
        self.analysis_results = {}
        self.agent_id = "analysis_agent"
        
        self.logger.info("Analysis Agent initialized successfully")
    
    async def analyze_all_tickers(self) -> Dict[str, List[Dict]]:
        """Analyze all tickers and evaluate trading rules"""
        try:
            self.logger.info("Starting comprehensive ticker analysis")
            
            # Get all tickers from trading rules
            tickers = self.data_manager.get_all_tickers()
            if not tickers:
                self.logger.warning("No tickers found in trading rules")
                return {}
            
            self.logger.info(f"Analyzing {len(tickers)} tickers", ticker_count=len(tickers))
            
            # Analyze each ticker
            analysis_results = {}
            for ticker in tickers:
                try:
                    ticker_signals = await self.analyze_ticker(ticker)
                    if ticker_signals:
                        analysis_results[ticker] = ticker_signals
                        
                        self.logger.info(f"Analysis completed for {ticker}", 
                                       ticker=ticker, signals_count=len(ticker_signals))
                    else:
                        self.logger.debug(f"No signals generated for {ticker}", ticker=ticker)
                        
                except Exception as e:
                    self.logger.error(f"Error analyzing {ticker}", 
                                    error=str(e), ticker=ticker)
                    continue
            
            # Update agent state
            self.last_analysis_time = datetime.now()
            self.analysis_results = analysis_results
            
            self.logger.info("Comprehensive ticker analysis completed", 
                           total_tickers=len(tickers), 
                           tickers_with_signals=len(analysis_results),
                           total_signals=sum(len(signals) for signals in analysis_results.values()))
            
            return analysis_results
            
        except Exception as e:
            self.logger.error("Error in comprehensive ticker analysis", error=str(e))
            return {}
    
    async def analyze_ticker(self, ticker: str) -> List[Dict]:
        """Analyze a single ticker and evaluate all applicable rules"""
        try:
            self.logger.debug(f"Starting analysis for {ticker}", ticker=ticker)
            
            # Evaluate all trading rules for this ticker
            signals = self.data_manager.evaluate_all_rules_for_ticker(ticker)
            
            if not signals:
                return []
            
            # Enhance signals with additional analysis
            enhanced_signals = []
            for signal in signals:
                try:
                    enhanced_signal = await self.enhance_signal_analysis(signal)
                    enhanced_signals.append(enhanced_signal)
                except Exception as e:
                    self.logger.error(f"Error enhancing signal for {ticker}", 
                                    error=str(e), ticker=ticker, rule=signal.get('rule_name', 'unknown'))
                    # Add the original signal without enhancement
                    enhanced_signals.append(signal)
            
            # Sort by priority and confidence
            enhanced_signals.sort(key=lambda x: (x['priority'], x['confidence']), reverse=True)
            
            self.logger.info(f"Analysis completed for {ticker}", 
                           ticker=ticker, signals_count=len(enhanced_signals))
            
            return enhanced_signals
            
        except Exception as e:
            self.logger.error(f"Error analyzing ticker {ticker}", 
                            error=str(e), ticker=ticker)
            return []
    
    async def enhance_signal_analysis(self, signal: Dict) -> Dict:
        """Enhance signal with additional technical analysis"""
        try:
            ticker = signal['ticker']
            indicators = signal.get('indicators', {})
            
            enhanced_signal = signal.copy()
            
            # Add trend analysis
            enhanced_signal['trend_analysis'] = await self._analyze_trend(ticker, indicators)
            
            # Add support/resistance levels
            enhanced_signal['support_resistance'] = await self._calculate_support_resistance(ticker, indicators)
            
            # Add volatility analysis
            enhanced_signal['volatility_analysis'] = await self._analyze_volatility(ticker, indicators)
            
            # Add momentum analysis
            enhanced_signal['momentum_analysis'] = await self._analyze_momentum(ticker, indicators)
            
            # Add risk assessment
            enhanced_signal['risk_assessment'] = await self._assess_risk(ticker, signal, indicators)
            
            # Add market context
            enhanced_signal['market_context'] = await self._analyze_market_context(ticker, indicators)
            
            return enhanced_signal
            
        except Exception as e:
            self.logger.error(f"Error enhancing signal analysis", 
                            error=str(e), ticker=signal.get('ticker', 'unknown'))
            return signal
    
    async def _analyze_trend(self, ticker: str, indicators: Dict) -> Dict:
        """Analyze trend direction and strength"""
        try:
            trend_analysis = {
                'short_term_trend': 'neutral',
                'medium_term_trend': 'neutral',
                'long_term_trend': 'neutral',
                'trend_strength': 0.0,
                'trend_consistency': 0.0
            }
            
            if 'data' not in indicators:
                return trend_analysis
            
            data = indicators['data']
            
            # Short-term trend (21 SMA)
            if 'sma_21' in indicators:
                sma_21 = indicators['sma_21']
                current_price = data['close'].iloc[-1]
                sma_21_current = sma_21.iloc[-1]
                
                if current_price > sma_21_current:
                    trend_analysis['short_term_trend'] = 'bullish'
                elif current_price < sma_21_current:
                    trend_analysis['short_term_trend'] = 'bearish'
            
            # Medium-term trend (50 SMA)
            if 'sma_50' in indicators:
                sma_50 = indicators['sma_50']
                current_price = data['close'].iloc[-1]
                sma_50_current = sma_50.iloc[-1]
                
                if current_price > sma_50_current:
                    trend_analysis['medium_term_trend'] = 'bullish'
                elif current_price < sma_50_current:
                    trend_analysis['medium_term_trend'] = 'bearish'
            
            # Long-term trend (200 SMA)
            if 'sma_200' in indicators:
                sma_200 = indicators['sma_200']
                current_price = data['close'].iloc[-1]
                sma_200_current = sma_200.iloc[-1]
                
                if current_price > sma_200_current:
                    trend_analysis['long_term_trend'] = 'bullish'
                elif current_price < sma_200_current:
                    trend_analysis['long_term_trend'] = 'bearish'
            
            # Calculate trend strength based on price distance from moving averages
            trend_strength = 0.0
            if 'sma_21' in indicators and 'sma_50' in indicators:
                price = data['close'].iloc[-1]
                sma_21_val = indicators['sma_21'].iloc[-1]
                sma_50_val = indicators['sma_50'].iloc[-1]
                
                # Calculate percentage distance from moving averages
                dist_21 = abs(price - sma_21_val) / sma_21_val
                dist_50 = abs(price - sma_50_val) / sma_50_val
                
                trend_strength = (dist_21 + dist_50) / 2
                trend_analysis['trend_strength'] = min(trend_strength, 1.0)
            
            return trend_analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing trend for {ticker}", 
                            error=str(e), ticker=ticker)
            return {'short_term_trend': 'neutral', 'medium_term_trend': 'neutral', 
                   'long_term_trend': 'neutral', 'trend_strength': 0.0, 'trend_consistency': 0.0}
    
    async def _calculate_support_resistance(self, ticker: str, indicators: Dict) -> Dict:
        """Calculate support and resistance levels"""
        try:
            support_resistance = {
                'support_levels': [],
                'resistance_levels': [],
                'key_levels': []
            }
            
            if 'data' not in indicators:
                return support_resistance
            
            data = indicators['data']
            
            # Use recent highs and lows as resistance and support
            recent_data = data.tail(20)  # Last 20 periods
            
            # Find local highs and lows
            highs = recent_data['high'].nlargest(3)
            lows = recent_data['low'].nsmallest(3)
            
            current_price = data['close'].iloc[-1]
            
            # Resistance levels (above current price)
            for high in highs:
                if high > current_price:
                    support_resistance['resistance_levels'].append(float(high))
            
            # Support levels (below current price)
            for low in lows:
                if low < current_price:
                    support_resistance['support_levels'].append(float(low))
            
            # Key levels (moving averages)
            if 'sma_21' in indicators:
                sma_21 = indicators['sma_21'].iloc[-1]
                support_resistance['key_levels'].append(('SMA 21', float(sma_21)))
            
            if 'sma_50' in indicators:
                sma_50 = indicators['sma_50'].iloc[-1]
                support_resistance['key_levels'].append(('SMA 50', float(sma_50)))
            
            if 'sma_200' in indicators:
                sma_200 = indicators['sma_200'].iloc[-1]
                support_resistance['key_levels'].append(('SMA 200', float(sma_200)))
            
            return support_resistance
            
        except Exception as e:
            self.logger.error(f"Error calculating support/resistance for {ticker}", 
                            error=str(e), ticker=ticker)
            return {'support_levels': [], 'resistance_levels': [], 'key_levels': []}
    
    async def _analyze_volatility(self, ticker: str, indicators: Dict) -> Dict:
        """Analyze volatility characteristics"""
        try:
            volatility_analysis = {
                'current_volatility': 'normal',
                'volatility_trend': 'stable',
                'atr_value': 0.0,
                'volatility_percentile': 0.0
            }
            
            if 'atr' in indicators:
                atr_series = indicators['atr']
                if not atr_series.empty:
                    current_atr = atr_series.iloc[-1]
                    volatility_analysis['atr_value'] = float(current_atr)
                    
                    # Calculate volatility percentile
                    atr_values = atr_series.dropna()
                    if len(atr_values) > 0:
                        percentile = (atr_values < current_atr).mean()
                        volatility_analysis['volatility_percentile'] = float(percentile)
                        
                        # Categorize volatility
                        if percentile < 0.25:
                            volatility_analysis['current_volatility'] = 'low'
                        elif percentile > 0.75:
                            volatility_analysis['current_volatility'] = 'high'
                        else:
                            volatility_analysis['current_volatility'] = 'normal'
            
            return volatility_analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing volatility for {ticker}", 
                            error=str(e), ticker=ticker)
            return {'current_volatility': 'normal', 'volatility_trend': 'stable', 
                   'atr_value': 0.0, 'volatility_percentile': 0.0}
    
    async def _analyze_momentum(self, ticker: str, indicators: Dict) -> Dict:
        """Analyze momentum indicators"""
        try:
            momentum_analysis = {
                'rsi_signal': 'neutral',
                'macd_signal': 'neutral',
                'momentum_strength': 0.0
            }
            
            if 'data' not in indicators:
                return momentum_analysis
            
            data = indicators['data']
            
            # Calculate RSI (simplified)
            if len(data) >= 14:
                delta = data['close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                
                current_rsi = rsi.iloc[-1]
                if not pd.isna(current_rsi):
                    if current_rsi > 70:
                        momentum_analysis['rsi_signal'] = 'overbought'
                    elif current_rsi < 30:
                        momentum_analysis['rsi_signal'] = 'oversold'
                    else:
                        momentum_analysis['rsi_signal'] = 'neutral'
                    
                    # Calculate momentum strength
                    momentum_analysis['momentum_strength'] = abs(current_rsi - 50) / 50
            
            return momentum_analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing momentum for {ticker}", 
                            error=str(e), ticker=ticker)
            return {'rsi_signal': 'neutral', 'macd_signal': 'neutral', 'momentum_strength': 0.0}
    
    async def _assess_risk(self, ticker: str, signal: Dict, indicators: Dict) -> Dict:
        """Assess risk for the trading signal"""
        try:
            risk_assessment = {
                'risk_level': 'medium',
                'risk_score': 0.5,
                'risk_factors': [],
                'position_size_recommendation': 'normal'
            }
            
            risk_score = 0.5  # Base risk score
            
            # Volatility risk
            if 'atr' in indicators:
                atr_series = indicators['atr']
                if not atr_series.empty:
                    current_atr = atr_series.iloc[-1]
                    price = indicators['data']['close'].iloc[-1]
                    atr_percent = current_atr / price
                    
                    if atr_percent > 0.05:  # High volatility
                        risk_score += 0.2
                        risk_assessment['risk_factors'].append('High volatility')
                    elif atr_percent < 0.02:  # Low volatility
                        risk_score -= 0.1
                        risk_assessment['risk_factors'].append('Low volatility')
            
            # Trend risk
            if signal.get('trend_analysis', {}).get('long_term_trend') == 'bearish':
                risk_score += 0.2
                risk_assessment['risk_factors'].append('Bearish long-term trend')
            
            # Rule priority risk
            priority = signal.get('priority', 5)
            if priority <= 3:  # High priority rules
                risk_score -= 0.1
                risk_assessment['risk_factors'].append('High priority rule')
            elif priority >= 7:  # Low priority rules
                risk_score += 0.1
                risk_assessment['risk_factors'].append('Low priority rule')
            
            # Confidence risk
            confidence = signal.get('confidence', 0.5)
            if confidence < 0.6:
                risk_score += 0.2
                risk_assessment['risk_factors'].append('Low confidence signal')
            elif confidence > 0.8:
                risk_score -= 0.1
                risk_assessment['risk_factors'].append('High confidence signal')
            
            # Clamp risk score
            risk_score = max(0.0, min(1.0, risk_score))
            risk_assessment['risk_score'] = risk_score
            
            # Determine risk level
            if risk_score < 0.3:
                risk_assessment['risk_level'] = 'low'
                risk_assessment['position_size_recommendation'] = 'aggressive'
            elif risk_score > 0.7:
                risk_assessment['risk_level'] = 'high'
                risk_assessment['position_size_recommendation'] = 'conservative'
            else:
                risk_assessment['risk_level'] = 'medium'
                risk_assessment['position_size_recommendation'] = 'normal'
            
            return risk_assessment
            
        except Exception as e:
            self.logger.error(f"Error assessing risk for {ticker}", 
                            error=str(e), ticker=ticker)
            return {'risk_level': 'medium', 'risk_score': 0.5, 
                   'risk_factors': ['Error in risk assessment'], 'position_size_recommendation': 'normal'}
    
    async def _analyze_market_context(self, ticker: str, indicators: Dict) -> Dict:
        """Analyze broader market context"""
        try:
            market_context = {
                'market_regime': 'normal',
                'sector_trend': 'neutral',
                'correlation_risk': 'medium'
            }
            
            # This is a simplified market context analysis
            # In a real implementation, you'd analyze broader market indices
            
            if 'nymo' in indicators:
                nymo_value = indicators['nymo'].iloc[-1]
                if not pd.isna(nymo_value):
                    if nymo_value < -70:
                        market_context['market_regime'] = 'oversold'
                    elif nymo_value > 70:
                        market_context['market_regime'] = 'overbought'
                    else:
                        market_context['market_regime'] = 'normal'
            
            return market_context
            
        except Exception as e:
            self.logger.error(f"Error analyzing market context for {ticker}", 
                            error=str(e), ticker=ticker)
            return {'market_regime': 'normal', 'sector_trend': 'neutral', 'correlation_risk': 'medium'}
    
    def get_analysis_summary(self) -> Dict:
        """Get summary of analysis results"""
        try:
            total_signals = sum(len(signals) for signals in self.analysis_results.values())
            
            # Count signals by type
            buy_signals = 0
            sell_signals = 0
            
            for ticker_signals in self.analysis_results.values():
                for signal in ticker_signals:
                    if signal.get('signal') == 'BUY':
                        buy_signals += 1
                    elif signal.get('signal') == 'SELL':
                        sell_signals += 1
            
            summary = {
                'total_tickers_analyzed': len(self.analysis_results),
                'total_signals': total_signals,
                'buy_signals': buy_signals,
                'sell_signals': sell_signals,
                'last_analysis_time': self.last_analysis_time.isoformat() if self.last_analysis_time else None,
                'analysis_status': 'completed' if self.last_analysis_time else 'pending'
            }
            
            return summary
            
        except Exception as e:
            self.logger.error("Error getting analysis summary", error=str(e))
            return {}
    
    def clear_analysis_results(self):
        """Clear analysis results"""
        self.analysis_results.clear()
        self.last_analysis_time = None
        self.logger.info("Analysis results cleared")
