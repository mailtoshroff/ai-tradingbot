"""
Data Manager for handling market data and technical indicators
"""
import json
import os
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from alpha_vantage.timeseries import TimeSeries
from utils.logger import trading_logger
from utils.technical_indicators import TechnicalIndicators

class DataManager:
    """Manages market data and technical indicators"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        self.logger = trading_logger.get_logger("data_manager")
        self.config = self._load_config(config_path)
        self.trading_rules = self._load_trading_rules()
        self.technical_indicators = TechnicalIndicators()
        self.technical_indicators.set_logger(self.logger)
        
        # Alpha Vantage configuration
        self.alpha_vantage_key = os.getenv('ALPHA_VANTAGE_API_KEY', 
                                          self.config.get('api', {}).get('alpha_vantage', {}).get('api_key', ''))
        self.alpha_vantage_ts = TimeSeries(key=self.alpha_vantage_key, output_format='pandas') if self.alpha_vantage_key else None
        
        # Cache for storing calculated indicators
        self.indicators_cache = {}
        self.data_cache = {}
        
        # CSV cache directory
        self.csv_cache_dir = "data_cache"
        self._ensure_cache_directory()
        
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration"""
        try:
            import yaml
            with open(config_path, 'r') as file:
                config = yaml.safe_load(file)
            return config
        except Exception as e:
            self.logger.error("Error loading config", error=str(e))
            return {}
    
    def _load_trading_rules(self) -> Dict:
        """Load trading rules from rules.json"""
        try:
            with open("rules.json", 'r') as file:
                rules = json.load(file)
            self.logger.info("Trading rules loaded successfully", rules_count=len(rules.get('rules', [])))
            return rules
        except Exception as e:
            self.logger.error("Error loading trading rules", error=str(e))
            return {'rules': []}
    
    def _ensure_cache_directory(self):
        """Ensure the CSV cache directory exists"""
        try:
            if not os.path.exists(self.csv_cache_dir):
                os.makedirs(self.csv_cache_dir)
                self.logger.info(f"Created cache directory: {self.csv_cache_dir}")
        except Exception as e:
            self.logger.error(f"Error creating cache directory", error=str(e))
    
    def _get_csv_cache_path(self, ticker: str, period: str, interval: str) -> str:
        """Get the CSV cache file path for a ticker and timeframe"""
        safe_ticker = ticker.replace('/', '_').replace('\\', '_')  # Safe filename
        return os.path.join(self.csv_cache_dir, f"{safe_ticker}_{period}_{interval}.csv")
    
    def _is_cache_valid(self, cache_path: str) -> bool:
        """Check if CSV cache is still valid (same day)"""
        try:
            if not os.path.exists(cache_path):
                return False
            
            # Check if file was created today
            file_time = datetime.fromtimestamp(os.path.getmtime(cache_path))
            today = datetime.now().date()
            return file_time.date() == today
            
        except Exception as e:
            self.logger.error(f"Error checking cache validity", error=str(e))
            return False
    
    def _load_from_csv_cache(self, cache_path: str) -> Optional[pd.DataFrame]:
        """Load data from CSV cache"""
        try:
            if not os.path.exists(cache_path):
                return None
            
            data = pd.read_csv(cache_path, index_col=0, parse_dates=True)
            self.logger.debug(f"Loaded data from CSV cache: {cache_path}")
            return data
            
        except Exception as e:
            self.logger.error(f"Error loading from CSV cache", error=str(e))
            return None
    
    def _save_to_csv_cache(self, data: pd.DataFrame, cache_path: str):
        """Save data to CSV cache"""
        try:
            data.to_csv(cache_path)
            self.logger.debug(f"Saved data to CSV cache: {cache_path}")
        except Exception as e:
            self.logger.error(f"Error saving to CSV cache", error=str(e))
    
    def _cleanup_old_cache_files(self):
        """Clean up CSV cache files older than 1 day"""
        try:
            today = datetime.now().date()
            for filename in os.listdir(self.csv_cache_dir):
                if filename.endswith('.csv'):
                    file_path = os.path.join(self.csv_cache_dir, filename)
                    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    
                    if file_time.date() < today:
                        os.remove(file_path)
                        self.logger.info(f"Cleaned up old cache file: {filename}")
                        
        except Exception as e:
            self.logger.error(f"Error cleaning up old cache files", error=str(e))
    
    def get_all_tickers(self) -> List[str]:
        """Get all unique tickers from trading rules"""
        tickers = set()
        for rule in self.trading_rules.get('rules', []):
            if 'stocks' in rule:
                tickers.update(rule['stocks'].keys())
        return list(tickers)
    
    def get_ticker_rules(self, ticker: str) -> List[Dict]:
        """Get all trading rules for a specific ticker"""
        ticker_rules = []
        for rule in self.trading_rules.get('rules', []):
            if 'stocks' in rule and ticker in rule['stocks']:
                ticker_rules.append(rule)
        return ticker_rules
    
    def fetch_market_data(self, ticker: str, period: str = 'D', 
                          interval: str = '365d') -> Optional[pd.DataFrame]:
        """Fetch market data for a ticker using Alpha Vantage with CSV caching"""
        try:
            # Get CSV cache path
            csv_cache_path = self._get_csv_cache_path(ticker, period, interval)
            
            # Check if CSV cache is valid (same day)
            if self._is_cache_valid(csv_cache_path):
                self.logger.info(f"Using CSV cache for {ticker}", ticker=ticker)
                data = self._load_from_csv_cache(csv_cache_path)
                if data is not None:
                    # Also update in-memory cache
                    cache_key = f"{ticker}_{period}_{interval}"
                    self.data_cache[cache_key] = {
                        'data': data,
                        'timestamp': datetime.now()
                    }
                    return data
            
            # Clean up old cache files at the start of each day
            if datetime.now().hour == 0:  # Only once per day
                self._cleanup_old_cache_files()
            
            # Check if Alpha Vantage is configured
            if not self.alpha_vantage_ts:
                self.logger.warning("Alpha Vantage not configured, using mock data", ticker=ticker)
                mock_data = self._generate_mock_data(ticker, period, interval)
                # Save mock data to CSV for consistency
                self._save_to_csv_cache(mock_data, csv_cache_path)
                return mock_data
            
            # Fetch new data from Alpha Vantage
            try:
                self.logger.info(f"Fetching fresh data from Alpha Vantage for {ticker}", ticker=ticker)
                
                if period == 'D':
                    # Daily data
                    data, meta_data = self.alpha_vantage_ts.get_daily(symbol=ticker, outputsize='full')
                    # Rename columns to match expected format
                    data.columns = ['open', 'high', 'low', 'close', 'volume']
                    # Sort by date (oldest first)
                    data = data.sort_index()
                    # Limit to requested interval
                    if interval == '365d':
                        data = data.tail(365)
                    elif interval == '30d':
                        data = data.tail(30)
                    elif interval == '60d':
                        data = data.tail(60)
                elif period == 'W':
                    # Weekly data
                    data, meta_data = self.alpha_vantage_ts.get_weekly(symbol=ticker)
                    data.columns = ['open', 'high', 'low', 'close', 'volume']
                    data = data.sort_index()
                    if interval == '52w':
                        data = data.tail(52)
                elif period == 'M':
                    # Monthly data
                    data, meta_data = self.alpha_vantage_ts.get_monthly(symbol=ticker)
                    data.columns = ['open', 'high', 'low', 'close', 'volume']
                    data = data.sort_index()
                    if interval == '12m':
                        data = data.tail(12)
                else:
                    raise ValueError(f"Unsupported period: {period}")
                
                if data.empty:
                    self.logger.warning(f"No data received for {ticker}", ticker=ticker, period=period)
                    mock_data = self._generate_mock_data(ticker, period, interval)
                    self._save_to_csv_cache(mock_data, csv_cache_path)
                    return mock_data
                
                # Save to CSV cache
                self._save_to_csv_cache(data, csv_cache_path)
                
                # Update in-memory cache
                cache_key = f"{ticker}_{period}_{interval}"
                self.data_cache[cache_key] = {
                    'data': data,
                    'timestamp': datetime.now()
                }
                
                self.logger.info(f"Fetched and cached market data for {ticker}", 
                               ticker=ticker, period=period, data_points=len(data))
                
                return data
                
            except Exception as e:
                self.logger.warning(f"Alpha Vantage API error for {ticker}, using mock data", 
                                  error=str(e), ticker=ticker)
                mock_data = self._generate_mock_data(ticker, period, interval)
                self._save_to_csv_cache(mock_data, csv_cache_path)
                return mock_data
            
        except Exception as e:
            self.logger.error(f"Error fetching market data for {ticker}", 
                            error=str(e), ticker=ticker, period=period)
            mock_data = self._generate_mock_data(ticker, period, interval)
            csv_cache_path = self._get_csv_cache_path(ticker, period, interval)
            self._save_to_csv_cache(mock_data, csv_cache_path)
            return mock_data
    
    def calculate_indicators_for_ticker(self, ticker: str, period: str = 'D', 
                                      interval: str = '365d') -> Optional[Dict]:
        """Calculate all technical indicators for a ticker"""
        try:
            cache_key = f"{ticker}_{period}_{interval}_indicators"
            
            # Check cache first
            if cache_key in self.indicators_cache:
                cached_indicators = self.indicators_cache[cache_key]
                # Check if cache is still valid (less than 30 minutes old)
                if datetime.now() - cached_indicators.get('timestamp', datetime.min) < timedelta(minutes=30):
                    self.logger.debug(f"Using cached indicators for {ticker}", ticker=ticker)
                    return cached_indicators['indicators']
            
            # Fetch data and calculate indicators
            data = self.fetch_market_data(ticker, period, interval)
            if data is None:
                return None
            
            indicators = self.technical_indicators.calculate_all_indicators(data, ticker, period)
            
            # Cache the indicators
            self.indicators_cache[cache_key] = {
                'indicators': indicators,
                'timestamp': datetime.now()
            }
            
            self.logger.info(f"Calculated indicators for {ticker}", 
                           ticker=ticker, period=period, indicators_count=len(indicators))
            
            return indicators
            
        except Exception as e:
            self.logger.error(f"Error calculating indicators for {ticker}", 
                            error=str(e), ticker=ticker, period=period)
            return None
    
    def evaluate_all_rules_for_ticker(self, ticker: str) -> List[Dict]:
        """Evaluate all trading rules for a ticker"""
        try:
            ticker_rules = self.get_ticker_rules(ticker)
            if not ticker_rules:
                self.logger.warning(f"No rules found for {ticker}", ticker=ticker)
                return []
            
            signals = []
            
            for rule in ticker_rules:
                # Get the appropriate period and interval for this rule
                period = rule.get('period', 'D')
                interval = rule.get('interval', '365d')
                
                # Calculate indicators for this timeframe
                indicators = self.calculate_indicators_for_ticker(ticker, period, interval)
                if indicators is None:
                    continue
                
                # Evaluate the rule
                signal_triggered, confidence, reasoning = self.technical_indicators.evaluate_trading_rule(
                    ticker, rule, indicators
                )
                
                if signal_triggered:
                    # Get stock-specific configuration
                    stock_config = rule['stocks'].get(ticker, {})
                    
                    signal = {
                        'ticker': ticker,
                        'rule_name': rule['name'],
                        'rule_type': rule['type'],
                        'priority': rule['priority'],
                        'signal': 'BUY' if rule['type'] == 'buy' else 'SELL',
                        'confidence': confidence,
                        'reasoning': reasoning,
                        'period': period,
                        'interval': interval,
                        'stock_config': stock_config,
                        'indicators': indicators,
                        'timestamp': datetime.now()
                    }
                    
                    signals.append(signal)
                    
                    self.logger.info(f"Signal generated for {ticker}", 
                                   ticker=ticker, rule=rule['name'], 
                                   signal=signal['signal'], confidence=confidence)
            
            # Sort signals by priority (highest priority first)
            signals.sort(key=lambda x: x['priority'])
            
            self.logger.info(f"Evaluated {len(ticker_rules)} rules for {ticker}, generated {len(signals)} signals", 
                           ticker=ticker, rules_evaluated=len(ticker_rules), signals_generated=len(signals))
            
            return signals
            
        except Exception as e:
            self.logger.error(f"Error evaluating rules for {ticker}", 
                            error=str(e), ticker=ticker)
            return []
    
    def get_portfolio_data(self, tickers: List[str]) -> Dict:
        """Get current portfolio data for multiple tickers"""
        try:
            portfolio_data = {}
            
            for ticker in tickers:
                try:
                    # Get daily data for metrics
                    daily_data = self.fetch_market_data(ticker, 'D', '30d')
                    if daily_data is not None and not daily_data.empty:
                        current_price = daily_data['close'].iloc[-1]
                        
                        # Calculate 200 SMA
                        sma_200 = self.technical_indicators.calculate_sma(daily_data, 200)
                        current_sma_200 = sma_200.iloc[-1] if not sma_200.empty else None
                        
                        # Calculate ATR
                        atr = self.technical_indicators.calculate_atr(daily_data, period=5, factor=2.5)
                        current_atr = atr.iloc[-1] if not atr.empty else None
                        
                        portfolio_data[ticker] = {
                            'current_price': current_price,
                            'sma_200': current_sma_200,
                            'atr': current_atr,
                            'timestamp': datetime.now()
                        }
                except Exception as e:
                    self.logger.warning(f"Error getting portfolio data for {ticker}", error=str(e))
                    continue
            
            self.logger.info(f"Retrieved portfolio data for {len(portfolio_data)} tickers", 
                           tickers_count=len(portfolio_data))
            
            return portfolio_data
            
        except Exception as e:
            self.logger.error("Error getting portfolio data", error=str(e))
            return {}
    
    def _generate_mock_data(self, ticker: str, period: str, interval: str) -> pd.DataFrame:
        """Generate mock market data for testing when API is not available"""
        try:
            import numpy as np
            
            # Generate realistic mock data
            if period == 'D':
                days = 365 if interval == '365d' else 30 if interval == '30d' else 60
                dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
            elif period == 'W':
                weeks = 52 if interval == '52w' else 12
                dates = pd.date_range(end=datetime.now(), periods=weeks, freq='W')
            elif period == 'M':
                months = 12 if interval == '12m' else 6
                dates = pd.date_range(end=datetime.now(), periods=months, freq='M')
            else:
                dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
            
            # Generate realistic price data
            np.random.seed(hash(ticker) % 1000)  # Consistent seed for each ticker
            
            base_price = 100.0 + (hash(ticker) % 200)  # Different base price for each ticker
            price_changes = np.random.normal(0, 0.02, len(dates))  # 2% daily volatility
            
            prices = [base_price]
            for change in price_changes[1:]:
                new_price = prices[-1] * (1 + change)
                prices.append(max(new_price, 1.0))  # Ensure price doesn't go below $1
            
            # Generate OHLC data
            data = pd.DataFrame({
                'open': prices,
                'high': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
                'low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
                'close': prices,
                'volume': np.random.randint(1000000, 10000000, len(dates))
            }, index=dates)
            
            # Ensure high >= open, close and low <= open, close
            data['high'] = data[['open', 'close']].max(axis=1) * (1 + abs(np.random.normal(0, 0.005)))
            data['low'] = data[['open', 'close']].min(axis=1) * (1 - abs(np.random.normal(0, 0.005)))
            
            self.logger.info(f"Generated mock data for {ticker}", 
                           ticker=ticker, period=period, data_points=len(data))
            
            return data
            
        except Exception as e:
            self.logger.error(f"Error generating mock data for {ticker}", error=str(e))
            # Return minimal mock data
            dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
            return pd.DataFrame({
                'open': [100.0] * 30,
                'high': [105.0] * 30,
                'low': [95.0] * 30,
                'close': [100.0] * 30,
                'volume': [1000000] * 30
            }, index=dates)
    
    def clear_cache(self):
        """Clear all cached data"""
        self.indicators_cache.clear()
        self.data_cache.clear()
        self.logger.info("In-memory cache cleared")
    
    def clear_csv_cache(self):
        """Clear all CSV cache files"""
        try:
            for filename in os.listdir(self.csv_cache_dir):
                if filename.endswith('.csv'):
                    file_path = os.path.join(self.csv_cache_dir, filename)
                    os.remove(file_path)
                    self.logger.info(f"Removed CSV cache file: {filename}")
            self.logger.info("CSV cache cleared")
        except Exception as e:
            self.logger.error(f"Error clearing CSV cache", error=str(e))
    
    def clear_ticker_csv_cache(self, ticker: str):
        """Clear CSV cache for a specific ticker"""
        try:
            for filename in os.listdir(self.csv_cache_dir):
                if filename.startswith(f"{ticker}_") and filename.endswith('.csv'):
                    file_path = os.path.join(self.csv_cache_dir, filename)
                    os.remove(file_path)
                    self.logger.info(f"Removed CSV cache file for {ticker}: {filename}")
        except Exception as e:
            self.logger.error(f"Error clearing CSV cache for {ticker}", error=str(e))
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        try:
            csv_files = [f for f in os.listdir(self.csv_cache_dir) if f.endswith('.csv')]
            csv_cache_size = len(csv_files)
            
            # Calculate total CSV cache size in MB
            total_csv_size_mb = 0
            for filename in csv_files:
                file_path = os.path.join(self.csv_cache_dir, filename)
                if os.path.exists(file_path):
                    total_csv_size_mb += os.path.getsize(file_path) / (1024 * 1024)
            
            return {
                'indicators_cache_size': len(self.indicators_cache),
                'data_cache_size': len(self.data_cache),
                'total_memory_cache_size': len(self.indicators_cache) + len(self.data_cache),
                'csv_cache_files_count': csv_cache_size,
                'csv_cache_total_size_mb': round(total_csv_size_mb, 2),
                'csv_cache_directory': self.csv_cache_dir
            }
        except Exception as e:
            self.logger.error(f"Error getting cache stats", error=str(e))
            return {
                'indicators_cache_size': len(self.indicators_cache),
                'data_cache_size': len(self.data_cache),
                'total_memory_cache_size': len(self.indicators_cache) + len(self.data_cache),
                'csv_cache_files_count': 0,
                'csv_cache_total_size_mb': 0,
                'csv_cache_directory': self.csv_cache_dir
            }
