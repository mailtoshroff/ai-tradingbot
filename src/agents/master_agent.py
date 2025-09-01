"""
Master Agent for coordinating analysis, news, and making final trading decisions
"""
import asyncio
import os
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import json
import pandas as pd
from agents.analysis_agent import AnalysisAgent
from agents.news_agent import NewsAgent
from utils.logger import trading_logger
from utils.email_sender import EmailSender
from utils.position_manager import PositionManager
from utils.enhanced_nymo import EnhancedNYMO
from utils.position_monitor import PositionMonitor

class MasterAgent:
    """Master Agent for coordinating all analysis and making trading decisions"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        self.logger = trading_logger.get_logger("master_agent")
        self.config = self._load_config(config_path)
        
        # Initialize sub-agents
        self.analysis_agent = AnalysisAgent(config_path)
        self.news_agent = NewsAgent(config_path)
        
        # Azure OpenAI configuration
        self.azure_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT', self.config.get('api', {}).get('azure_openai', {}).get('endpoint', ''))
        self.azure_api_key = os.getenv('AZURE_OPENAI_API_KEY', self.config.get('api', {}).get('azure_openai', {}).get('api_key', ''))
        self.azure_api_version = os.getenv('AZURE_OPENAI_API_VERSION', self.config.get('api', {}).get('azure_openai', {}).get('api_version', '2024-02-15-preview'))
        self.azure_deployment = os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME', self.config.get('api', {}).get('azure_openai', {}).get('deployment_name', ''))
        
        # Alpaca configuration
        self.alpaca_api_key = os.getenv('ALPACA_API_KEY', self.config.get('alpaca', {}).get('api_key', ''))
        self.alpaca_api_secret = os.getenv('ALPACA_API_SECRET', self.config.get('alpaca', {}).get('api_secret', ''))
        self.alpaca_base_url = self.config.get('alpaca', {}).get('base_url', 'https://paper-api.alpaca.markets')
        self.alpaca_data_url = self.config.get('alpaca', {}).get('data_url', 'https://data.alpaca.markets')
        
        # Initialize Alpaca client
        self.alpaca_client = None
        if self.alpaca_api_key and self.alpaca_api_secret:
            try:
                import alpaca_trade_api as tradeapi
                self.alpaca_client = tradeapi.REST(
                    self.alpaca_api_key,
                    self.alpaca_api_secret,
                    self.alpaca_base_url,
                    api_version='v2'
                )
                self.logger.info("Alpaca client initialized successfully")
            except Exception as e:
                self.logger.error("Failed to initialize Alpaca client", error=str(e))
                self.alpaca_client = None
        
        # Agent state
        self.last_decision_time = None
        self.trading_decisions = {}
        self.agent_id = "master_agent"
        
        # Email sender
        self.email_sender = EmailSender(config_path)
        self.email_sender.set_logger(self.logger)
        
        # Initialize position manager and enhanced NYMO
        self.position_manager = PositionManager()
        self.enhanced_nymo = EnhancedNYMO()
        self.position_manager.set_logger(self.logger)
        self.enhanced_nymo.set_logger(self.logger)
        
        # Initialize position monitor
        self.position_monitor = PositionMonitor(self, self.config)
        
        self.logger.info("Master Agent initialized successfully")
    
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
    
    async def execute_comprehensive_analysis(self) -> Dict[str, Any]:
        """Execute comprehensive analysis using all agents"""
        try:
            self.logger.info("Starting comprehensive analysis execution")
            
            # Get all tickers to analyze
            tickers = self.analysis_agent.data_manager.get_all_tickers()
            if not tickers:
                self.logger.warning("No tickers found for analysis")
                return {}
            
            self.logger.info(f"Executing analysis for {len(tickers)} tickers", ticker_count=len(tickers))
            
            # Execute analysis in parallel
            analysis_task = asyncio.create_task(self.analysis_agent.analyze_all_tickers())
            news_task = asyncio.create_task(self.news_agent.analyze_news_for_tickers(tickers))
            
            # Execute enhanced NYMO analysis
            nymo_task = asyncio.create_task(self.enhanced_nymo.analyze_market_conditions())
            
            # Wait for all tasks to complete
            analysis_results, news_results, nymo_results = await asyncio.gather(
                analysis_task, news_task, nymo_task, return_exceptions=True
            )
            
            # Handle any exceptions
            if isinstance(analysis_results, Exception):
                self.logger.error("Analysis agent failed", error=str(analysis_results))
                analysis_results = {}
            if isinstance(news_results, Exception):
                self.logger.error("News agent failed", error=str(news_results))
                news_results = {}
            if isinstance(nymo_results, Exception):
                self.logger.error("Enhanced NYMO failed", error=str(nymo_results))
                nymo_results = {}
            
            # Integrate NYMO signals into analysis
            if nymo_results and not isinstance(nymo_results, Exception):
                analysis_results = self._integrate_nymo_signals(analysis_results, nymo_results)
            
            # Store results for reporting
            self.last_analysis_results = analysis_results
            self.last_news_results = news_results
            self.last_nymo_results = nymo_results
            
            return {
                'analysis': analysis_results,
                'news': news_results,
                'nymo': nymo_results
            }
            
        except Exception as e:
            self.logger.error("Error in comprehensive analysis", error=str(e))
            return {}
            
            # Wait for both tasks to complete
            analysis_results, news_results = await asyncio.gather(analysis_task, news_task)
            
            # Generate trading decisions
            trading_decisions = await self._generate_trading_decisions(analysis_results, news_results)
            
            # Update agent state
            self.last_decision_time = datetime.now()
            self.trading_decisions = trading_decisions
            self.last_analysis_results = analysis_results
            self.last_news_results = news_results
            
            # Display results in table format
            self._display_results_table(analysis_results, news_results, trading_decisions)
            
            self.logger.info("Comprehensive analysis execution completed", 
                           total_tickers=len(tickers),
                           decisions_generated=len(trading_decisions))
            
            return {
                'analysis_results': analysis_results,
                'news_results': news_results,
                'trading_decisions': trading_decisions,
                'execution_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error("Error in comprehensive analysis execution", error=str(e))
            return {}
    
    def _display_results_table(self, analysis_results: Dict, news_results: Dict, trading_decisions: Dict):
        """Display analysis results in a formatted table"""
        try:
            print("\n" + "="*120)
            print("AI TRADING BOT ANALYSIS RESULTS")
            print("="*120)
            
            # Create table headers
            headers = ["Ticker", "Tech Signals", "Sentiment Score", "Final Decision", "Confidence", "Reasoning"]
            print(f"{headers[0]:<8} {headers[1]:<25} {headers[2]:<15} {headers[3]:<12} {headers[4]:<10} {headers[5]}")
            print("-" * 120)
            
            # Get ALL tickers that were analyzed (not just ones with signals)
            all_tickers = self.analysis_agent.data_manager.get_all_tickers()
            
            for ticker in sorted(all_tickers):
                # Get technical signals
                tech_signals = analysis_results.get(ticker, [])
                tech_signal_text = self._format_tech_signals(tech_signals)
                
                # Get sentiment score
                ticker_news = news_results.get(ticker, {})
                sentiment_score = self._get_sentiment_score(ticker_news)
                
                # Get final decision
                decision = trading_decisions.get(ticker, {})
                final_decision = decision.get('action', 'HOLD')
                confidence = decision.get('confidence', 0.0)
                reasoning = decision.get('reasoning', 'No signals triggered')
                
                # Format the row
                print(f"{ticker:<8} {tech_signal_text:<25} {sentiment_score:<15} {final_decision:<12} {confidence:<10.2f} {reasoning[:50]}...")
            
            print("-" * 120)
            
            # Summary statistics
            total_signals = sum(len(signals) for signals in analysis_results.values())
            total_news = sum(len(news.get('articles', [])) for news in news_results.values())
            buy_signals = sum(1 for d in trading_decisions.values() if d.get('action') == 'BUY')
            sell_signals = sum(1 for d in trading_decisions.values() if d.get('action') == 'SELL')
            
            print(f"\nSUMMARY:")
            print(f"Total Technical Signals: {total_signals}")
            print(f"Total News Articles: {total_news}")
            print(f"Buy Decisions: {buy_signals}")
            print(f"Sell Decisions: {sell_signals}")
            print(f"Hold Decisions: {len(trading_decisions) - buy_signals - sell_signals}")
            
        except Exception as e:
            self.logger.error("Error displaying results table", error=str(e))
    
    def _format_tech_signals(self, signals: List[Dict]) -> str:
        """Format technical signals for display"""
        if not signals:
            return "None"
        
        # Get the highest priority signal
        primary_signal = signals[0]
        rule_name = primary_signal.get('rule_name', 'Unknown')
        signal_type = primary_signal.get('signal', 'HOLD')
        
        return f"{rule_name[:20]}"
    
    def _get_sentiment_score(self, ticker_news: Dict) -> str:
        """Get formatted sentiment score"""
        if not ticker_news:
            return "No News"
        
        overall_sentiment = ticker_news.get('overall_sentiment', {})
        score = overall_sentiment.get('overall_score', 0)
        sentiment = overall_sentiment.get('overall_sentiment', 'neutral')
        
        if score > 20:
            return f"Bullish ({score:.1f})"
        elif score < -20:
            return f"Bearish ({score:.1f})"
        else:
            return f"Neutral ({score:.1f})"
    
    async def _generate_trading_decisions(self, analysis_results: Dict, news_results: Dict) -> Dict[str, Dict]:
        """Generate final trading decisions using Azure OpenAI"""
        try:
            self.logger.info("Generating trading decisions using AI analysis")
            
            trading_decisions = {}
            
            # Process each ticker that has analysis results
            for ticker, ticker_signals in analysis_results.items():
                try:
                    if not ticker_signals:
                        continue
                    
                    # Get news sentiment for this ticker
                    ticker_news = news_results.get(ticker, {})
                    
                    # Generate decision using Azure OpenAI
                    decision = await self._generate_ai_decision(ticker, ticker_signals, ticker_news)
                    
                    if decision:
                        trading_decisions[ticker] = decision
                        
                        self.logger.info(f"Trading decision generated for {ticker}", 
                                       ticker=ticker, decision=decision.get('action', 'HOLD'))
                    
                except Exception as e:
                    self.logger.error(f"Error generating decision for {ticker}", 
                                    error=str(e), ticker=ticker)
                    continue
            
            self.logger.info(f"Generated {len(trading_decisions)} trading decisions", 
                           decisions_count=len(trading_decisions))
            
            return trading_decisions
            
        except Exception as e:
            self.logger.error("Error generating trading decisions", error=str(e))
            return {}
    
    async def _calculate_position_size(self, ticker: str, decision: Dict, 
                                     portfolio_value: float, analysis: Dict) -> Dict:
        """
        Calculate position size using ATR vs purchase_limit_pct (whichever is less)
        
        Args:
            ticker: Stock symbol
            decision: Trading decision
            portfolio_value: Total portfolio value
            analysis: Technical analysis results
            
        Returns:
            Dict with position sizing details
        """
        try:
            # Get current price and ATR from analysis
            current_price = analysis.get('data', {}).get('close', {}).iloc[-1] if analysis.get('data') is not None else 0
            atr_value = analysis.get('atr', {}).iloc[-1] if analysis.get('atr') is not None else 0
            
            if not current_price or not atr_value:
                self.logger.warning(f"Missing price or ATR data for {ticker}")
                return {}
            
            # Get purchase limit from rules
            purchase_limit_pct = self._get_purchase_limit_pct(ticker, decision.get('rule_name', ''))
            
            # Calculate ATR-based position size
            position_details = self.position_manager.calculate_atr_position_size(
                portfolio_value, current_price, atr_value, purchase_limit_pct
            )
            
            if position_details:
                self.logger.info(f"Position sizing for {ticker}", 
                               ticker=ticker, sizing_method=position_details.get('sizing_method'),
                               position_pct=position_details.get('position_pct'))
            
            return position_details
            
        except Exception as e:
            self.logger.error(f"Error calculating position size for {ticker}", error=str(e))
            return {}
    
    def _get_purchase_limit_pct(self, ticker: str, rule_name: str) -> float:
        """Get purchase limit percentage from rules for a ticker"""
        try:
            # Load trading rules
            rules_path = "rules.json"
            with open(rules_path, 'r') as file:
                rules_data = json.load(file)
            
            # Find the rule that matches the rule_name
            for rule in rules_data.get('rules', []):
                if rule.get('name') == rule_name:
                    # Get the stock-specific configuration
                    stock_config = rule.get('stocks', {}).get(ticker, {})
                    if stock_config:
                        return stock_config.get('purchase_limit_pct', 1.0)
            
            # Default if not found
            return 1.0
            
        except Exception as e:
            self.logger.error(f"Error getting purchase limit for {ticker}", error=str(e))
            return 1.0
    
    async def check_averaging_down_opportunities(self) -> List[Dict]:
        """
        Check for averaging down opportunities based on ATR multiples
        
        Returns:
            List of averaging down opportunities
        """
        try:
            opportunities = []
            
            # Get current positions
            positions = self.position_manager.get_all_positions()
            
            for ticker, position in positions.items():
                # Get current market data
                current_data = await self.analysis_agent.data_manager.fetch_market_data(ticker, 'D', '365d')
                if not current_data:
                    continue
                
                current_price = current_data['close'].iloc[-1]
                atr_value = current_data['atr'].iloc[-1] if 'atr' in current_data else 0
                entry_price = position.get('entry_price', 0)
                
                if not atr_value or not entry_price:
                    continue
                
                # Check if we should average down
                should_average, confidence, reasoning = self.position_manager.should_average_down(
                    ticker, current_price, entry_price, atr_value, 0.02  # Default 2%
                )
                
                if should_average:
                    # Calculate averaging down size
                    portfolio_value = await self._get_account_info().get('equity', 100000)
                    averaging_size = self.position_manager.calculate_averaging_down_size(
                        ticker, portfolio_value, current_price, atr_value, '2x ATR'  # Default level
                    )
                    
                    opportunities.append({
                        'ticker': ticker,
                        'current_price': current_price,
                        'entry_price': entry_price,
                        'atr_value': atr_value,
                        'confidence': confidence,
                        'reasoning': reasoning,
                        'averaging_size': averaging_size
                    })
            
            return opportunities
            
        except Exception as e:
            self.logger.error("Error checking averaging down opportunities", error=str(e))
            return []
    
    async def check_partial_profit_opportunities(self) -> List[Dict]:
        """
        Check for partial profit taking opportunities (50% above 200 SMA)
        
        Returns:
            List of partial profit opportunities
        """
        try:
            opportunities = []
            
            # Get current positions
            positions = self.position_manager.get_all_positions()
            
            for ticker, position in positions.items():
                # Get current market data
                current_data = await self.analysis_agent.data_manager.fetch_market_data(ticker, 'D', '365d')
                if not current_data:
                    continue
                
                current_price = current_data['close'].iloc[-1]
                sma_200 = current_data['sma_200'].iloc[-1] if 'sma_200' in current_data else 0
                entry_price = position.get('entry_price', 0)
                
                # Check if we should take partial profits
                should_sell, confidence, reasoning = self.position_manager.should_take_partial_profit(
                    ticker, current_price, entry_price, sma_200
                )
                
                if should_sell:
                    opportunities.append({
                        'ticker': ticker,
                        'current_price': current_price,
                        'entry_price': entry_price,
                        'sma_200': sma_200,
                        'confidence': confidence,
                        'reasoning': reasoning,
                        'action': 'SELL_HALF'
                    })
            
            return opportunities
            
        except Exception as e:
            self.logger.error("Error checking partial profit opportunities", error=str(e))
            return []
    
    async def get_enhanced_nymo_signals(self) -> Dict:
        """
        Get enhanced NYMO signals using real market breadth data
        
        Returns:
            Dict with NYMO signals and analysis
        """
        try:
            # Fetch current market breadth data
            current_date = datetime.now().strftime('%Y-%m-%d')
            market_data = self.enhanced_nymo.fetch_market_breadth_data(current_date)
            
            if not market_data:
                return {}
            
            # Calculate enhanced NYMO
            nymo_value = self.enhanced_nymo.calculate_enhanced_nymo(market_data)
            
            # Generate trading signals
            nymo_signals = self.enhanced_nymo.calculate_nymo_signals(nymo_value)
            
            # Get NYMO history and trend analysis
            nymo_history = self.enhanced_nymo.get_nymo_history(days=30)
            trend_analysis = self.enhanced_nymo.analyze_nymo_trend(nymo_history)
            
            return {
                'current_nymo': nymo_value,
                'market_breadth': market_data,
                'signals': nymo_signals,
                'history': nymo_history,
                'trend_analysis': trend_analysis,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error("Error getting enhanced NYMO signals", error=str(e))
            return {}
    
    async def integrate_nymo_into_decisions(self, trading_decisions: List[Dict]) -> List[Dict]:
        """
        Integrate enhanced NYMO signals into trading decisions
        
        Args:
            trading_decisions: List of existing trading decisions
            
        Returns:
            List of enhanced trading decisions
        """
        try:
            # Get NYMO signals
            nymo_data = await self.get_enhanced_nymo_signals()
            
            if not nymo_data:
                return trading_decisions
            
            nymo_signals = nymo_data.get('signals', {})
            nymo_value = nymo_data.get('current_nymo', 0)
            
            # Enhance trading decisions with NYMO
            enhanced_decisions = []
            
            for decision in trading_decisions:
                enhanced_decision = decision.copy()
                
                # Add NYMO context
                enhanced_decision['nymo_context'] = {
                    'nymo_value': nymo_value,
                    'signal_strength': nymo_signals.get('signal_strength', 'neutral'),
                    'risk_level': nymo_signals.get('risk_level', 'medium'),
                    'market_sentiment': nymo_signals.get('trading_signal', 'HOLD')
                }
                
                # Adjust confidence based on NYMO
                if nymo_signals.get('signal_strength') == 'extreme_bearish' and decision.get('action') == 'BUY':
                    enhanced_decision['confidence'] = min(1.0, decision.get('confidence', 0.0) + 0.1)
                    enhanced_decision['reasoning'] += f" | NYMO extreme bearish ({nymo_value:.1f}) - strong contrarian signal"
                
                elif nymo_signals.get('signal_strength') == 'extreme_bullish' and decision.get('action') == 'SELL':
                    enhanced_decision['confidence'] = min(1.0, decision.get('confidence', 0.0) + 0.1)
                    enhanced_decision['reasoning'] += f" | NYMO extreme bullish ({nymo_value:.1f}) - strong profit-taking signal"
                
                enhanced_decisions.append(enhanced_decision)
            
            return enhanced_decisions
            
        except Exception as e:
            self.logger.error("Error integrating NYMO into decisions", error=str(e))
            return trading_decisions
    
    async def _generate_ai_decision(self, ticker: str, ticker_signals: List[Dict], 
                                   ticker_news: Dict) -> Optional[Dict]:
        """Generate AI-powered trading decision using Azure OpenAI"""
        try:
            if not self.azure_api_key or not self.azure_endpoint:
                self.logger.warning("Azure OpenAI not configured, using rule-based decision", ticker=ticker)
                return self._rule_based_decision(ticker, ticker_signals, ticker_news)
            
            # Prepare comprehensive analysis data for AI
            analysis_summary = self._prepare_analysis_summary(ticker, ticker_signals)
            news_summary = self._prepare_news_summary(ticker, ticker_news)
            
            # Create expert trading prompt
            prompt = self._create_expert_trading_prompt(ticker, analysis_summary, news_summary)
            
            # Get AI decision
            ai_decision = await self._get_azure_openai_decision(prompt)
            
            if ai_decision:
                # Enhance decision with additional metadata
                enhanced_decision = self._enhance_decision_with_metadata(ticker, ai_decision, ticker_signals, ticker_news)
                return enhanced_decision
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error generating AI decision for {ticker}", 
                            error=str(e), ticker=ticker)
            # Fallback to rule-based decision
            return self._rule_based_decision(ticker, ticker_signals, ticker_news)
    
    def _prepare_analysis_summary(self, ticker: str, ticker_signals: List[Dict]) -> Dict:
        """Prepare technical analysis summary for AI prompt"""
        try:
            if not ticker_signals:
                return {}
            
            # Get the highest priority signal
            primary_signal = ticker_signals[0]
            
            summary = {
                'ticker': ticker,
                'primary_signal': {
                    'rule_name': primary_signal.get('rule_name', ''),
                    'signal_type': primary_signal.get('signal', ''),
                    'priority': primary_signal.get('priority', 0),
                    'confidence': primary_signal.get('confidence', 0.0),
                    'reasoning': primary_signal.get('reasoning', '')
                },
                'technical_indicators': {
                    'trend_analysis': primary_signal.get('trend_analysis', {}),
                    'support_resistance': primary_signal.get('support_resistance', {}),
                    'volatility_analysis': primary_signal.get('volatility_analysis', {}),
                    'momentum_analysis': primary_signal.get('momentum_analysis', {}),
                    'risk_assessment': primary_signal.get('risk_assessment', {})
                },
                'all_signals_count': len(ticker_signals),
                'signal_details': []
            }
            
            # Add details for all signals
            for signal in ticker_signals[:3]:  # Top 3 signals
                summary['signal_details'].append({
                    'rule': signal.get('rule_name', ''),
                    'priority': signal.get('priority', 0),
                    'confidence': signal.get('confidence', 0.0),
                    'reasoning': signal.get('reasoning', '')
                })
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error preparing analysis summary for {ticker}", 
                            error=str(e), ticker=ticker)
            return {}
    
    def _prepare_news_summary(self, ticker: str, ticker_news: Dict) -> Dict:
        """Prepare news sentiment summary for AI prompt"""
        try:
            if not ticker_news:
                return {}
            
            overall_sentiment = ticker_news.get('overall_sentiment', {})
            
            summary = {
                'ticker': ticker,
                'sentiment': {
                    'overall_sentiment': overall_sentiment.get('overall_sentiment', 'neutral'),
                    'sentiment_score': overall_sentiment.get('overall_score', 0.0),
                    'confidence': overall_sentiment.get('overall_confidence', 0.5),
                    'sentiment_distribution': overall_sentiment.get('sentiment_distribution', {})
                },
                'articles_count': ticker_news.get('news_count', 0),
                'recent_articles': []
            }
            
            # Add recent articles
            articles = ticker_news.get('articles', [])
            for article in articles[:3]:  # Top 3 articles
                summary['recent_articles'].append({
                    'title': article.get('title', '')[:100],
                    'sentiment': article.get('sentiment', 'neutral'),
                    'relevance_score': article.get('relevance_score', 0.0)
                })
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error preparing news summary for {ticker}", 
                            error=str(e), ticker=ticker)
            return {}
    
    def _create_expert_trading_prompt(self, ticker: str, analysis_summary: Dict, 
                                     news_summary: Dict) -> str:
        """Create expert trading prompt for Azure OpenAI"""
        try:
            prompt = f"""
You are an expert swing trader with 20+ years of experience in technical analysis and market psychology. 
Analyze the following data for {ticker} and provide a trading decision.

TECHNICAL ANALYSIS:
{json.dumps(analysis_summary, indent=2)}

NEWS SENTIMENT:
{json.dumps(news_summary, indent=2)}

Based on this analysis, provide a trading decision in the following JSON format:
{{
    "action": "BUY/SELL/HOLD",
    "confidence": 0.0-1.0,
    "reasoning": "Detailed explanation of your decision",
    "position_size_pct": 0.0-10.0,
    "entry_strategy": "How to enter the position",
    "exit_strategy": "When to exit the position",
    "risk_management": "Risk management approach"
}}

Consider:
1. Technical signal strength and priority
2. News sentiment impact
3. Market conditions and volatility
4. Risk-reward ratio
5. Position sizing based on confidence

Respond only with valid JSON.
"""
            return prompt
            
        except Exception as e:
            self.logger.error(f"Error creating expert trading prompt for {ticker}", 
                            error=str(e), ticker=ticker)
            return ""
    
    async def _get_azure_openai_decision(self, prompt: str) -> Optional[Dict]:
        """Get trading decision from Azure OpenAI"""
        try:
            import openai
            
            # Configure Azure OpenAI client
            client = openai.AzureOpenAI(
                azure_endpoint=self.azure_endpoint,
                api_key=self.azure_api_key,
                api_version=self.azure_api_version
            )
            
            # Make API call
            response = client.chat.completions.create(
                model=self.azure_deployment,
                messages=[
                    {"role": "system", "content": "You are an expert swing trader. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            # Parse response
            response_text = response.choices[0].message.content
            decision = json.loads(response_text)
            
            return decision
            
        except Exception as e:
            self.logger.error("Error getting Azure OpenAI decision", error=str(e))
            return None
    
    def _enhance_decision_with_metadata(self, ticker: str, ai_decision: Dict, 
                                       ticker_signals: List[Dict], ticker_news: Dict) -> Dict:
        """Enhance AI decision with additional metadata"""
        try:
            # Get primary signal for correlation
            primary_signal = ticker_signals[0] if ticker_signals else {}
            
            enhanced_decision = {
                'ticker': ticker,
                'action': ai_decision.get('action', 'HOLD'),
                'confidence': ai_decision.get('confidence', 0.5),
                'position_size_pct': ai_decision.get('position_size_pct', 0.0),
                'reasoning': ai_decision.get('reasoning', ''),
                'entry_strategy': ai_decision.get('entry_strategy', 'Market order'),
                'exit_strategy': ai_decision.get('exit_strategy', 'Based on technical levels'),
                'risk_management': ai_decision.get('risk_management', 'Standard position sizing'),
                'timestamp': datetime.now().isoformat(),
                'agent_id': self.agent_id,
                'decision_method': 'azure_openai',
                'signal_correlation': {
                    'primary_rule': primary_signal.get('rule_name', ''),
                    'rule_priority': primary_signal.get('priority', 0),
                    'rule_confidence': primary_signal.get('confidence', 0.0),
                    'total_signals': len(ticker_signals)
                }
            }
            
            return enhanced_decision
            
        except Exception as e:
            self.logger.error(f"Error enhancing decision for {ticker}", 
                            error=str(e), ticker=ticker)
            return ai_decision
    
    def _rule_based_decision(self, ticker: str, ticker_signals: List[Dict], 
                            ticker_news: Dict) -> Dict:
        """Generate rule-based trading decision as fallback"""
        try:
            if not ticker_signals:
                return {
                    'ticker': ticker,
                    'action': 'HOLD',
                    'confidence': 0.0,
                    'position_size_pct': 0.0,
                    'reasoning': 'No technical signals generated',
                    'entry_strategy': 'N/A',
                    'exit_strategy': 'N/A',
                    'risk_management': 'N/A',
                    'timestamp': datetime.now().isoformat(),
                    'agent_id': self.agent_id,
                    'decision_method': 'rule_based_fallback'
                }
            
            # Get the highest priority signal
            primary_signal = ticker_signals[0]
            
            # Determine action based on signal
            action = primary_signal.get('signal', 'HOLD')
            confidence = primary_signal.get('confidence', 0.5)
            
            # Calculate position size based on confidence and risk
            position_size_pct = min(confidence * 5.0, 10.0)  # Max 10% of portfolio
            
            # Generate reasoning
            reasoning = f"Rule-based decision: {primary_signal.get('rule_name', 'Unknown rule')} triggered with {confidence:.2f} confidence. {primary_signal.get('reasoning', '')}"
            
            # Add news sentiment if available
            if ticker_news:
                news_sentiment = ticker_news.get('overall_sentiment', {}).get('overall_sentiment', 'neutral')
                reasoning += f" News sentiment: {news_sentiment}."
            
            decision = {
                'ticker': ticker,
                'action': action,
                'confidence': confidence,
                'position_size_pct': position_size_pct,
                'reasoning': reasoning,
                'entry_strategy': 'Market order based on signal',
                'exit_strategy': 'Based on technical levels',
                'risk_management': 'Standard position sizing',
                'timestamp': datetime.now().isoformat(),
                'agent_id': self.agent_id,
                'decision_method': 'rule_based_fallback',
                'signal_correlation': {
                    'primary_rule': primary_signal.get('rule_name', ''),
                    'rule_priority': primary_signal.get('priority', 0),
                    'rule_confidence': confidence,
                    'total_signals': len(ticker_signals)
                }
            }
            
            return decision
            
        except Exception as e:
            self.logger.error(f"Error in rule-based decision for {ticker}", 
                            error=str(e), ticker=ticker)
            return {
                'ticker': ticker,
                'action': 'HOLD',
                'confidence': 0.0,
                'position_size_pct': 0.0,
                'reasoning': f'Error in decision generation: {str(e)}',
                'entry_strategy': 'N/A',
                'exit_strategy': 'N/A',
                'risk_management': 'N/A',
                'timestamp': datetime.now().isoformat(),
                'agent_id': self.agent_id,
                'decision_method': 'error_fallback'
            }
    
    async def execute_trades(self) -> Dict[str, Dict]:
        """Execute trades based on trading decisions"""
        try:
            if not self.alpaca_client:
                self.logger.warning("Alpaca client not available, cannot execute trades")
                return {}
            
            if not self.trading_decisions:
                self.logger.info("No trading decisions to execute")
                return {}
            
            execution_results = {}
            
            for ticker, decision in self.trading_decisions.items():
                try:
                    action = decision.get('action', 'HOLD')
                    
                    if action == 'HOLD':
                        continue
                    
                    # Execute the trade
                    execution_result = await self._execute_single_trade(ticker, decision)
                    execution_results[ticker] = execution_result
                    
                    if execution_result.get('success'):
                        self.logger.info(f"Trade executed successfully for {ticker}", 
                                       ticker=ticker, action=action)
                    else:
                        self.logger.error(f"Trade execution failed for {ticker}", 
                                        ticker=ticker, error=execution_result.get('error'))
                        
                except Exception as e:
                    self.logger.error(f"Error executing trade for {ticker}", 
                                    error=str(e), ticker=ticker)
                    execution_results[ticker] = {
                        'success': False,
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    }
            
            return execution_results
            
        except Exception as e:
            self.logger.error("Error executing trades", error=str(e))
            return {}
    
    async def _execute_single_trade(self, ticker: str, decision: Dict) -> Dict:
        """Execute a single trade"""
        try:
            action = decision.get('action', 'HOLD')
            position_size_pct = decision.get('position_size_pct', 0.0)
            
            if action == 'HOLD' or position_size_pct <= 0:
                return {
                    'success': False,
                    'error': 'Invalid action or position size',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Get account information
            account = self.alpaca_client.get_account()
            portfolio_value = float(account.portfolio_value)
            
            # Calculate position size
            position_value = portfolio_value * (position_size_pct / 100.0)
            
            # Get current market price
            bars = self.alpaca_client.get_bars(ticker, '1Min', limit=1)
            if not bars:
                return {
                    'success': False,
                    'error': 'Unable to get current market price',
                    'timestamp': datetime.now().isoformat()
                }
            
            current_price = float(bars[0].c)
            shares = int(position_value / current_price)
            
            if shares <= 0:
                return {
                    'success': False,
                    'error': 'Position size too small',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Execute the order
            if action == 'BUY':
                order = self.alpaca_client.submit_order(
                    symbol=ticker,
                    qty=shares,
                    side='buy',
                    type='market',
                    time_in_force='day'
                )
            elif action == 'SELL':
                order = self.alpaca_client.submit_order(
                    symbol=ticker,
                    qty=shares,
                    side='sell',
                    type='market',
                    time_in_force='day'
                )
            else:
                return {
                    'success': False,
                    'error': f'Unknown action: {action}',
                    'timestamp': datetime.now().isoformat()
                }
            
            return {
                'success': True,
                'order_id': order.id,
                'symbol': ticker,
                'action': action,
                'shares': shares,
                'price': current_price,
                'value': position_value,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error executing trade for {ticker}", 
                            error=str(e), ticker=ticker)
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_account_info(self) -> Dict:
        """Get real account information from Alpaca"""
        try:
            if not self.alpaca_client:
                return {
                    'error': 'Alpaca client not available',
                    'total_value': 0,
                    'cash': 0,
                    'positions': {}
                }
            
            # Get account information
            account = self.alpaca_client.get_account()
            positions = self.alpaca_client.list_positions()
            
            # Calculate total portfolio value
            total_value = float(account.portfolio_value)
            cash = float(account.cash)
            
            # Get position details
            position_details = {}
            for position in positions:
                position_details[position.symbol] = {
                    'quantity': int(position.qty),
                    'market_value': float(position.market_value),
                    'avg_entry_price': float(position.avg_entry_price),
                    'current_price': float(position.current_price),
                    'unrealized_pl': float(position.unrealized_pl)
                }
            
            return {
                'total_value': total_value,
                'cash': cash,
                'positions': position_details,
                'buying_power': float(account.buying_power),
                'day_trade_count': int(account.daytrade_count),
                'last_equity': float(account.last_equity),
                'long_market_value': float(account.long_market_value),
                'short_market_value': float(account.short_market_value)
            }
            
        except Exception as e:
            self.logger.error("Error getting account info", error=str(e))
            return {
                'error': str(e),
                'total_value': 0,
                'cash': 0,
                'positions': {}
            }
    
    async def send_trading_report(self) -> bool:
        """Send comprehensive trading report via email"""
        try:
            # Always send a comprehensive report with analysis data
            portfolio_status = self.get_account_info()
            
            # Prepare comprehensive trading signals for email (including analysis data)
            trading_signals = []
            
            # Get all tickers that were analyzed
            all_tickers = self.analysis_agent.data_manager.get_all_tickers()
            
            for ticker in sorted(all_tickers):
                # Get analysis data for this ticker
                analysis_data = getattr(self, 'last_analysis_results', {}).get(ticker, {})
                news_data = getattr(self, 'last_news_results', {}).get(ticker, {})
                decision = self.trading_decisions.get(ticker, {})
                
                # Format technical signals
                tech_signals = "None"
                if analysis_data:
                    signals = analysis_data.get('signals', [])
                    if signals:
                        primary_signal = signals[0]
                        tech_signals = primary_signal.get('rule_name', 'Unknown')[:20]
                
                # Format sentiment score
                sentiment_score = "No News"
                if news_data:
                    overall_sentiment = news_data.get('overall_sentiment', {})
                    score = overall_sentiment.get('overall_score', 0)
                    if score > 20:
                        sentiment_score = f"Bullish ({score:.1f})"
                    elif score < -20:
                        sentiment_score = f"Bearish ({score:.1f})"
                    else:
                        sentiment_score = f"Neutral ({score:.1f})"
                
                signal = {
                    'ticker': ticker,
                    'signal': decision.get('action', 'HOLD'),
                    'confidence': decision.get('confidence', 0.0),
                    'reasoning': decision.get('reasoning', 'No signals triggered'),
                    'priority': decision.get('signal_correlation', {}).get('rule_priority', 0),
                    'tech_signals': tech_signals,
                    'sentiment_score': sentiment_score
                }
                trading_signals.append(signal)
            
            # Send comprehensive email report with analysis table
            success = self.email_sender.send_trading_report(trading_signals, portfolio_status)
            
            if success:
                self.logger.info("Comprehensive trading report email sent successfully")
            else:
                self.logger.error("Failed to send trading report email")
            
            return success
            
        except Exception as e:
            self.logger.error("Error sending trading report", error=str(e))
            return False
    
    def get_decision_summary(self) -> Dict:
        """Get summary of trading decisions"""
        try:
            if not self.trading_decisions:
                return {}
            
            # Count decisions by action
            action_counts = {'BUY': 0, 'SELL': 0, 'HOLD': 0}
            confidence_sum = 0.0
            total_decisions = len(self.trading_decisions)
            
            for decision in self.trading_decisions.values():
                action = decision.get('action', 'HOLD')
                action_counts[action] += 1
                confidence_sum += decision.get('confidence', 0.0)
            
            avg_confidence = confidence_sum / total_decisions if total_decisions > 0 else 0.0
            
            summary = {
                'total_decisions': total_decisions,
                'action_distribution': action_counts,
                'average_confidence': avg_confidence,
                'last_decision_time': self.last_decision_time.isoformat() if self.last_decision_time else None,
                'decision_status': 'completed' if self.last_decision_time else 'pending'
            }
            
            return summary
            
        except Exception as e:
            self.logger.error("Error getting decision summary", error=str(e))
            return {}
    
    def clear_decisions(self):
        """Clear trading decisions"""
        self.trading_decisions.clear()
        self.last_decision_time = None
        self.logger.info("Trading decisions cleared")
    
    async def start_position_monitoring(self):
        """Start automated position monitoring"""
        try:
            await self.position_monitor.start_monitoring()
            self.logger.info("Position monitoring started successfully")
            return True
        except Exception as e:
            self.logger.error("Error starting position monitoring", error=str(e))
            return False
    
    async def stop_position_monitoring(self):
        """Stop automated position monitoring"""
        try:
            await self.position_monitor.stop_monitoring()
            self.logger.info("Position monitoring stopped successfully")
            return True
        except Exception as e:
            self.logger.error("Error stopping position monitoring", error=str(e))
            return False
    
    def get_position_monitoring_status(self) -> Dict:
        """Get position monitoring status"""
        return self.position_monitor.get_monitoring_status()
    
    def get_position_summary(self) -> Dict:
        """Get summary of current positions"""
        return self.position_monitor.get_position_summary()
    
    def _get_nymo_context_for_ticker(self, ticker: str, nymo_signals: Dict, nymo_thresholds: List[float]) -> Optional[Dict]:
        """Get NYMO context for a specific ticker"""
        try:
            if not nymo_signals or 'nymo_value' not in nymo_signals:
                return None
            
            nymo_value = nymo_signals['nymo_value']
            market_condition = nymo_signals.get('market_condition', 'neutral')
            
            # Determine if this ticker should be affected by NYMO
            # Only QQQ and SPY are directly affected by NYMO
            nymo_affected_tickers = ['QQQ', 'SPY', 'VGT', 'VOO']
            if ticker not in nymo_affected_tickers:
                return None
            
            context = {
                'nymo_value': nymo_value,
                'market_condition': market_condition,
                'threshold_levels': nymo_thresholds,
                'is_extreme': abs(nymo_value) > max(nymo_thresholds),
                'signal_strength': self._calculate_nymo_signal_strength(nymo_value, nymo_thresholds)
            }
            
            return context
            
        except Exception as e:
            self.logger.error(f"Error getting NYMO context for {ticker}", error=str(e))
            return None
    
    def _calculate_nymo_confidence_adjustment(self, nymo_context: Dict) -> float:
        """Calculate confidence adjustment based on NYMO context"""
        try:
            if not nymo_context:
                return 0.0
            
            nymo_value = nymo_context.get('nymo_value', 0)
            signal_strength = nymo_context.get('signal_strength', 0)
            
            # Positive adjustment for extreme values (strong signals)
            if abs(nymo_value) > 70:
                return 0.1 * signal_strength
            elif abs(nymo_value) > 50:
                return 0.05 * signal_strength
            else:
                return 0.0
                
        except Exception as e:
            self.logger.error("Error calculating NYMO confidence adjustment", error=str(e))
            return 0.0
    
    def _calculate_nymo_signal_strength(self, nymo_value: float, thresholds: List[float]) -> float:
        """Calculate signal strength based on NYMO value and thresholds"""
        try:
            if not thresholds:
                return 0.0
            
            # Find the highest threshold that the NYMO value exceeds
            max_threshold = max(thresholds)
            if abs(nymo_value) <= max_threshold:
                return 0.0
            
            # Calculate strength as percentage above max threshold
            strength = (abs(nymo_value) - max_threshold) / max_threshold
            return min(1.0, strength)
            
        except Exception as e:
            self.logger.error("Error calculating NYMO signal strength", error=str(e))
            return 0.0
    
    def check_position_management_opportunities(self) -> List[Dict]:
        """Check for position management opportunities (averaging down, profit taking)"""
        try:
            if not self.alpaca_client:
                self.logger.warning("Alpaca client not available for position management")
                return []
            
            opportunities = []
            
            # Get current positions
            try:
                positions = self.alpaca_client.list_positions()
            except Exception as e:
                self.logger.error("Error fetching positions from Alpaca", error=str(e))
                return []
            
            for position in positions:
                ticker = position.symbol
                current_price = float(position.current_price)
                entry_price = float(position.avg_entry_price)
                shares = int(position.qty)
                
                # Get current ATR for this ticker
                atr_data = self.analysis_agent.data_manager.calculate_indicators_for_ticker(ticker)
                if not atr_data or 'atr' not in atr_data:
                    continue
                
                atr_value = atr_data['atr']
                
                # Check averaging down opportunities
                avg_down_opp = self.position_manager.should_average_down(
                    ticker, current_price, entry_price, atr_value, 0.02
                )
                
                if avg_down_opp[0]:  # should_average_down returns tuple
                    opportunities.append({
                        'ticker': ticker,
                        'action': 'AVERAGE_DOWN',
                        'current_price': current_price,
                        'entry_price': entry_price,
                        'shares': shares,
                        'atr_value': atr_value,
                        'confidence': avg_down_opp[1],
                        'reasoning': avg_down_opp[2]
                    })
                
                # Check profit taking opportunities (sell half at 50% above 200 SMA)
                # This is more realistic than the previous 50% above 200 SMA
                sma_200 = atr_data.get('sma_200', 0)
                if sma_200 > 0:
                    profit_threshold = sma_200 * 1.15  # 15% above 200 SMA (more realistic)
                    if current_price >= profit_threshold:
                        opportunities.append({
                            'ticker': ticker,
                            'action': 'PARTIAL_PROFIT_TAKING',
                            'current_price': current_price,
                            'entry_price': entry_price,
                            'shares': shares // 2,  # Sell half
                            'sma_200': sma_200,
                            'profit_pct': ((current_price - entry_price) / entry_price) * 100,
                            'confidence': 0.9,
                            'reasoning': f"Price {current_price:.2f} above 200 SMA {sma_200:.2f} - taking partial profits"
                        })
            
            return opportunities
            
        except Exception as e:
            self.logger.error("Error checking position management opportunities", error=str(e))
            return []
