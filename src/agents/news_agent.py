"""
News Agent for gathering and analyzing news sentiment
"""
import asyncio
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta, timezone
import requests
from utils.logger import trading_logger
from utils.email_sender import EmailSender

class NewsAgent:
    """News sentiment analysis agent"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        self.logger = trading_logger.get_logger("news_agent")
        self.config = self._load_config(config_path)
        self.newsapi_key = os.getenv('NEWSAPI_API_KEY', self.config.get('api', {}).get('newsapi', {}).get('api_key', ''))
        self.newsapi_base_url = self.config.get('api', {}).get('newsapi', {}).get('base_url', 'https://newsapi.org/v2')
        
        # Azure OpenAI configuration
        self.azure_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT', self.config.get('api', {}).get('azure_openai', {}).get('endpoint', ''))
        self.azure_api_key = os.getenv('AZURE_OPENAI_API_KEY', self.config.get('api', {}).get('azure_openai', {}).get('api_key', ''))
        self.azure_deployment = os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME', self.config.get('api', {}).get('azure_openai', {}).get('deployment_name', ''))
        
        # News analysis configuration
        self.news_config = self.config.get('news_analysis', {})
        self.lookback_days = self.news_config.get('lookback_days', 7)
        self.max_articles_per_ticker = self.news_config.get('max_articles_per_ticker', 10)
        self.batch_size = self.news_config.get('batch_size', 5)  # Articles per API call
        self.batch_delay = self.news_config.get('batch_delay', 2)  # Seconds between batches
        self.sentiment_cache_ttl = self.news_config.get('sentiment_cache_ttl', 24)  # Hours
        self.sentiment_weights = self.news_config.get('sentiment_weights', {
            'recent_24h': 1.0,  # Full weight for 24-hour news (most important for swing trading)
            'recent_3d': 0.3,   # Reduced weight for older news
            'recent_7d': 0.1,   # Minimal weight for week-old news
            'older': 0.05       # Very low weight for old news
        })
        
        # Agent state
        self.last_news_fetch_time = None
        self.news_cache = {}
        self.sentiment_cache = {}
        self.agent_id = "news_agent"
        
        # Email sender for alerts
        self.email_sender = EmailSender(config_path)
        self.email_sender.set_logger(self.logger)
        
        self.logger.info("News Agent initialized successfully")
    
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
    
    async def analyze_news_for_tickers(self, tickers: List[str]) -> Dict[str, Dict]:
        """Analyze news sentiment for multiple tickers"""
        try:
            self.logger.info(f"Starting news analysis for {len(tickers)} tickers", ticker_count=len(tickers))
            
            news_results = {}
            for ticker in tickers:
                try:
                    ticker_news = await self.analyze_ticker_news(ticker)
                    if ticker_news:
                        news_results[ticker] = ticker_news
                        
                        self.logger.info(f"News analysis completed for {ticker}", 
                                       ticker=ticker, articles_count=len(ticker_news.get('articles', [])))
                    else:
                        self.logger.debug(f"No news found for {ticker}", ticker=ticker)
                        
                except Exception as e:
                    self.logger.error(f"Error analyzing news for {ticker}", 
                                    error=str(e), ticker=ticker)
                    continue
            
            # Update agent state
            self.last_news_fetch_time = datetime.now(timezone.utc)
            
            self.logger.info("News analysis completed for all tickers", 
                           total_tickers=len(tickers), 
                           tickers_with_news=len(news_results))
            
            return news_results
            
        except Exception as e:
            self.logger.error("Error in comprehensive news analysis", error=str(e))
            return {}
    
    async def analyze_ticker_news(self, ticker: str) -> Optional[Dict]:
        """Analyze news for a single ticker"""
        try:
            self.logger.debug(f"Starting news analysis for {ticker}", ticker=ticker)
            
            # Check cache first
            cache_key = f"{ticker}_news"
            if cache_key in self.news_cache:
                cached_news = self.news_cache[cache_key]
                # Check if cache is still valid (less than 2 hours old)
                cache_timestamp = cached_news.get('timestamp', datetime.min)
                # Ensure both datetimes are timezone-aware for comparison
                now = datetime.now(timezone.utc)
                if cache_timestamp.tzinfo is None:
                    cache_timestamp = cache_timestamp.replace(tzinfo=timezone.utc)
                if now - cache_timestamp < timedelta(hours=2):
                    self.logger.debug(f"Using cached news for {ticker}", ticker=ticker)
                    return cached_news['data']
            
            # Fetch news articles
            articles = await self._fetch_news_articles(ticker)
            if not articles:
                return None
            
            # Analyze sentiment for each article
            sentiment_analysis = await self._analyze_articles_sentiment(ticker, articles)
            
            # Calculate overall sentiment score
            overall_sentiment = self._calculate_overall_sentiment(sentiment_analysis)
            
            # Create news analysis result
            now = datetime.now(timezone.utc)
            news_result = {
                'ticker': ticker,
                'articles': articles,
                'sentiment_analysis': sentiment_analysis,
                'overall_sentiment': overall_sentiment,
                'news_count': len(articles),
                'timestamp': now
            }
            
            # Cache the result
            self.news_cache[cache_key] = {
                'data': news_result,
                'timestamp': now
            }
            
            self.logger.info(f"News analysis completed for {ticker}", 
                           ticker=ticker, articles_count=len(articles), 
                           sentiment_score=overall_sentiment['overall_score'])
            
            return news_result
            
        except Exception as e:
            self.logger.error(f"Error analyzing news for ticker {ticker}", 
                            error=str(e), ticker=ticker)
            return None
    
    async def _fetch_news_articles(self, ticker: str) -> List[Dict]:
        """Fetch news articles for a ticker from the last 24 hours"""
        try:
            if not self.newsapi_key:
                self.logger.warning("NewsAPI key not configured, using mock data", ticker=ticker)
                return self._generate_mock_news(ticker)
            
            # Calculate date range - focus on last 24 hours
            end_date = datetime.now()
            start_date = end_date - timedelta(days=self.lookback_days)
            
            # Prepare API request - get more articles to ensure we capture all relevant news
            params = {
                'q': ticker,
                'from': start_date.strftime('%Y-%m-%d'),
                'to': end_date.strftime('%Y-%m-%d'),
                'sortBy': 'publishedAt',
                'language': 'en',
                'pageSize': 100,  # Increased to capture more articles
                'apiKey': self.newsapi_key
            }
            
            # Make API request
            response = requests.get(f"{self.newsapi_base_url}/everything", params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            articles = data.get('articles', [])
            
            # Process articles
            processed_articles = []
            for article in articles:
                try:
                    # Check if article is within last 24 hours
                    # Handle different datetime formats and ensure timezone consistency
                    published_at = article.get('publishedAt', '')
                    if published_at:
                        try:
                            # Try to parse ISO format with timezone
                            if published_at.endswith('Z'):
                                article_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                            else:
                                article_date = datetime.fromisoformat(published_at)
                        except ValueError:
                            # Fallback to parsing without timezone info
                            article_date = datetime.fromisoformat(published_at.split('+')[0].split('Z')[0])
                            # Make it timezone-aware (UTC)
                            article_date = article_date.replace(tzinfo=timezone.utc)
                        
                        # Ensure start_date is also timezone-aware for comparison
                        if start_date.tzinfo is None:
                            start_date = start_date.replace(tzinfo=timezone.utc)
                        
                        if article_date < start_date:
                            continue  # Skip articles older than 24 hours
                    
                    processed_article = {
                        'title': article.get('title', ''),
                        'description': article.get('description', ''),
                        'content': article.get('content', ''),
                        'url': article.get('url', ''),
                        'published_at': article.get('publishedAt', ''),
                        'source': article.get('source', {}).get('name', ''),
                        'relevance_score': self._calculate_relevance_score(ticker, article)
                    }
                    processed_articles.append(processed_article)
                except Exception as e:
                    self.logger.warning(f"Error processing article for {ticker}", 
                                      error=str(e), ticker=ticker)
                    continue
            
            # Sort by relevance and recency
            processed_articles.sort(key=lambda x: (x['relevance_score'], x['published_at']), reverse=True)
            
            # Limit to max articles per ticker (but this should be high enough for 24h coverage)
            final_articles = processed_articles[:self.max_articles_per_ticker]
            
            self.logger.info(f"Fetched {len(final_articles)} news articles for {ticker} from last 24 hours", 
                           ticker=ticker, articles_count=len(final_articles), 
                           total_found=len(processed_articles))
            
            return final_articles
            
        except Exception as e:
            self.logger.error(f"Error fetching news articles for {ticker}", 
                            error=str(e), ticker=ticker)
            return []
    
    def _generate_mock_news(self, ticker: str) -> List[Dict]:
        """Generate mock news data for testing"""
        now = datetime.now(timezone.utc)
        mock_articles = [
            {
                'title': f'Market Update: {ticker} Shows Strong Performance',
                'description': f'{ticker} continues to demonstrate resilience in current market conditions.',
                'content': f'Analysis shows {ticker} maintaining strong fundamentals despite market volatility.',
                'url': f'https://example.com/news/{ticker.lower()}',
                'published_at': now.isoformat(),
                'source': 'Mock News Source',
                'relevance_score': 0.9
            },
            {
                'title': f'{ticker} Technical Analysis: Bullish Signals Emerging',
                'description': f'Technical indicators suggest positive momentum for {ticker}.',
                'content': f'Recent price action and volume patterns indicate potential upside for {ticker}.',
                'url': f'https://example.com/analysis/{ticker.lower()}',
                'published_at': (now - timedelta(hours=6)).isoformat(),
                'source': 'Mock Analysis Source',
                'relevance_score': 0.8
            }
        ]
        return mock_articles
    
    def _calculate_relevance_score(self, ticker: str, article: Dict) -> float:
        """Calculate relevance score for an article"""
        try:
            score = 0.0
            
            # Check title relevance (handle None values)
            title = article.get('title') or ''
            if title and ticker.lower() in title.lower():
                score += 0.4
            elif title and any(word in title.lower() for word in ['stock', 'market', 'trading', 'investment']):
                score += 0.2
            
            # Check description relevance (handle None values)
            description = article.get('description') or ''
            if description and ticker.lower() in description.lower():
                score += 0.3
            elif description and any(word in description.lower() for word in ['earnings', 'revenue', 'growth', 'performance']):
                score += 0.2
            
            # Check content relevance (handle None values)
            content = article.get('content') or ''
            if content and ticker.lower() in content.lower():
                score += 0.2
            elif content and any(word in content.lower() for word in ['financial', 'business', 'company', 'corporate']):
                score += 0.1
            
            # Source credibility bonus (handle None values)
            source_name = article.get('source', {}).get('name') or ''
            if source_name:
                source_name = source_name.lower()
                credible_sources = ['reuters', 'bloomberg', 'cnbc', 'marketwatch', 'yahoo finance']
                if any(credible in source_name for credible in credible_sources):
                    score += 0.1
            
            return min(score, 1.0)
            
        except Exception as e:
            self.logger.error(f"Error calculating relevance score", error=str(e))
            return 0.5
    
    async def _analyze_articles_sentiment(self, ticker: str, articles: List[Dict]) -> List[Dict]:
        """Analyze sentiment for each article using Azure OpenAI with batching"""
        try:
            if not self.azure_api_key or not self.azure_endpoint:
                self.logger.warning("Azure OpenAI not configured, using rule-based sentiment", ticker=ticker)
                return [self._rule_based_sentiment(article) for article in articles]
            
            # Check cache first for individual articles
            sentiment_results = []
            articles_to_analyze = []
            
            for article in articles:
                cache_key = f"{ticker}_{article.get('title', '')[:50]}_{article.get('published_at', '')[:10]}"
                if cache_key in self.sentiment_cache:
                    # Use cached sentiment
                    cached_sentiment = self.sentiment_cache[cache_key]
                    cached_at = cached_sentiment.get('cached_at', datetime.min)
                    # Ensure both datetimes are timezone-aware for comparison
                    now = datetime.now(timezone.utc)
                    if cached_at.tzinfo is None:
                        cached_at = cached_at.replace(tzinfo=timezone.utc)
                    if now - cached_at < timedelta(hours=self.sentiment_cache_ttl):
                        sentiment_results.append(cached_sentiment['data'])
                        continue
                
                articles_to_analyze.append((article, cache_key))
            
            if not articles_to_analyze:
                self.logger.info(f"All articles for {ticker} found in cache", ticker=ticker)
                return sentiment_results
            
            # Batch analyze remaining articles (max 5 per batch to avoid rate limits)
            batch_size = self.batch_size
            batch_delay = self.batch_delay
            for i in range(0, len(articles_to_analyze), batch_size):
                batch = articles_to_analyze[i:i + batch_size]
                batch_results = await self._batch_sentiment_analysis(ticker, [article for article, _ in batch])
                
                # Cache results and add to sentiment_results
                for j, (_, cache_key) in enumerate(batch):
                    if j < len(batch_results):
                        sentiment_data = batch_results[j]
                        # Cache the result
                        self.sentiment_cache[cache_key] = {
                            'data': sentiment_data,
                            'cached_at': datetime.now(timezone.utc)
                        }
                        sentiment_results.append(sentiment_data)
                
                # Add delay between batches to avoid rate limits
                if i + batch_size < len(articles_to_analyze):
                    await asyncio.sleep(batch_delay)
            
            return sentiment_results
            
        except Exception as e:
            self.logger.error(f"Error in sentiment analysis for {ticker}", 
                            error=str(e), ticker=ticker)
            return [self._rule_based_sentiment(article) for article in articles]
    
    async def _batch_sentiment_analysis(self, ticker: str, articles: List[Dict]) -> List[Dict]:
        """Analyze sentiment for multiple articles in a single API call"""
        try:
            import openai
            
            # Configure Azure OpenAI client
            client = openai.AzureOpenAI(
                azure_endpoint=self.azure_endpoint,
                api_key=self.azure_api_key,
                api_version="2024-02-15-preview"
            )
            
            # Prepare batch prompt for multiple articles
            articles_text = ""
            for i, article in enumerate(articles):
                articles_text += f"""
Article {i+1}:
Title: {article.get('title', '')}
Description: {article.get('description', '')}
Content: {article.get('content', '')[:500]}...
---
"""
            
            prompt = f"""
Analyze the sentiment of the following {len(articles)} news articles about {ticker} stock.

{articles_text}

For each article, provide a sentiment analysis with:
1. Overall sentiment (positive, negative, neutral)
2. Sentiment score (-100 to +100, where -100 is extremely negative, +100 is extremely positive)
3. Confidence level (0.0 to 1.0)
4. Key factors influencing the sentiment
5. Market impact assessment (high, medium, low)

Respond in JSON format as an array of results:
[
    {{
        "sentiment": "positive/negative/neutral",
        "score": -100 to 100,
        "confidence": 0.0 to 1.0,
        "factors": ["factor1", "factor2"],
        "market_impact": "high/medium/low",
        "reasoning": "brief explanation"
    }},
    ... (one for each article)
]
"""
            
            # Make API call
            response = client.chat.completions.create(
                model=self.azure_deployment,
                messages=[
                    {"role": "system", "content": "You are an expert financial analyst specializing in sentiment analysis of news articles. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            # Parse response
            response_text = response.choices[0].message.content
            import json
            batch_sentiment_data = json.loads(response_text)
            
            # Ensure we have the right number of results
            if len(batch_sentiment_data) != len(articles):
                self.logger.warning(f"Batch analysis returned {len(batch_sentiment_data)} results for {len(articles)} articles", 
                                  ticker=ticker)
                # Pad with neutral sentiment if needed
                while len(batch_sentiment_data) < len(articles):
                    batch_sentiment_data.append({
                        'sentiment': 'neutral',
                        'score': 0,
                        'confidence': 0.5,
                        'factors': ['Analysis incomplete'],
                        'market_impact': 'low',
                        'reasoning': 'Fallback sentiment due to incomplete analysis'
                    })
                # Truncate if too many
                batch_sentiment_data = batch_sentiment_data[:len(articles)]
            
            # Add article metadata to each result
            for i, (article, sentiment_data) in enumerate(zip(articles, batch_sentiment_data)):
                sentiment_data['article_title'] = article.get('title', '')
                sentiment_data['article_url'] = article.get('url', '')
                sentiment_data['published_at'] = article.get('published_at', '')
                sentiment_data['source'] = article.get('source', '')
            
            self.logger.info(f"Batch sentiment analysis completed for {ticker}: {len(articles)} articles in 1 API call", 
                           ticker=ticker, articles_count=len(articles))
            
            return batch_sentiment_data
            
        except Exception as e:
            self.logger.error(f"Error in batch sentiment analysis for {ticker}", error=str(e), ticker=ticker)
            # Fallback to individual rule-based analysis
            return [self._rule_based_sentiment(article) for article in articles]
    
    def _rule_based_sentiment(self, article: Dict) -> Dict:
        """Rule-based sentiment analysis as fallback"""
        try:
            title = article.get('title', '').lower()
            description = article.get('description', '').lower()
            content = article.get('content', '').lower()
            
            # Positive keywords
            positive_words = ['positive', 'growth', 'increase', 'rise', 'gain', 'profit', 'earnings', 'strong', 'bullish', 'outperform']
            # Negative keywords
            negative_words = ['negative', 'decline', 'decrease', 'fall', 'loss', 'weak', 'bearish', 'underperform', 'risk', 'concern']
            
            # Count positive and negative words
            positive_count = sum(1 for word in positive_words if word in title or word in description or word in content)
            negative_count = sum(1 for word in negative_words if word in title or word in description or word in content)
            
            # Calculate sentiment score
            if positive_count > negative_count:
                sentiment = "positive"
                score = min(50 + (positive_count - negative_count) * 10, 100)
            elif negative_count > positive_count:
                sentiment = "negative"
                score = max(-50 - (negative_count - positive_count) * 10, -100)
            else:
                sentiment = "neutral"
                score = 0
            
            # Calculate confidence based on word count
            total_words = positive_count + negative_count
            confidence = min(0.5 + (total_words * 0.1), 0.9)
            
            return {
                'sentiment': sentiment,
                'score': score,
                'confidence': confidence,
                'factors': [f"Positive words: {positive_count}", f"Negative words: {negative_count}"],
                'market_impact': 'medium' if total_words > 2 else 'low',
                'reasoning': f"Rule-based analysis based on {total_words} sentiment words",
                'article_title': article.get('title', ''),
                'article_url': article.get('url', ''),
                'published_at': article.get('published_at', ''),
                'source': article.get('source', '')
            }
            
        except Exception as e:
            self.logger.error(f"Error in rule-based sentiment analysis", error=str(e))
            return {
                'sentiment': 'neutral',
                'score': 0,
                'confidence': 0.5,
                'factors': ['Error in sentiment analysis'],
                'market_impact': 'low',
                'reasoning': 'Error in sentiment analysis',
                'article_title': article.get('title', ''),
                'article_url': article.get('url', ''),
                'published_at': article.get('published_at', ''),
                'source': article.get('source', '')
            }
    
    def _calculate_overall_sentiment(self, sentiment_analysis: List[Dict]) -> Dict:
        """Calculate overall sentiment score from individual article sentiments"""
        try:
            if not sentiment_analysis:
                return {
                    'overall_sentiment': 'neutral',
                    'overall_score': 0,
                    'overall_confidence': 0.5,
                    'sentiment_distribution': {'positive': 0, 'negative': 0, 'neutral': 0}
                }
            
            # Calculate weighted average sentiment score
            total_weighted_score = 0
            total_weight = 0
            total_confidence = 0
            sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
            
            for i, analysis in enumerate(sentiment_analysis):
                # Weight recent articles more heavily - focus on 24-hour news for swing trading
                if i == 0:  # Most recent (within last few hours)
                    weight = self.sentiment_weights.get('recent_24h', 1.0)
                elif i < 5:  # Recent 5 articles (within last 12 hours)
                    weight = self.sentiment_weights.get('recent_24h', 1.0) * 0.9
                elif i < 10:  # Recent 10 articles (within last 18 hours)
                    weight = self.sentiment_weights.get('recent_24h', 1.0) * 0.7
                elif i < 20:  # Recent 20 articles (within last 24 hours)
                    weight = self.sentiment_weights.get('recent_24h', 1.0) * 0.5
                else:  # Older articles (beyond 24 hours)
                    weight = self.sentiment_weights.get('older', 0.05)
                
                score = analysis.get('score', 0)
                confidence = analysis.get('confidence', 0.5)
                
                total_weighted_score += score * weight * confidence
                total_weight += weight * confidence
                total_confidence += confidence
                
                # Count sentiment types
                sentiment = analysis.get('sentiment', 'neutral')
                sentiment_counts[sentiment] += 1
            
            # Calculate overall metrics
            overall_score = total_weighted_score / total_weight if total_weight > 0 else 0
            overall_confidence = total_confidence / len(sentiment_analysis) if sentiment_analysis else 0.5
            
            # Determine overall sentiment
            if overall_score > 20:
                overall_sentiment = 'positive'
            elif overall_score < -20:
                overall_sentiment = 'negative'
            else:
                overall_sentiment = 'neutral'
            
            return {
                'overall_sentiment': overall_sentiment,
                'overall_score': overall_score,
                'overall_confidence': overall_confidence,
                'sentiment_distribution': sentiment_counts,
                'articles_analyzed': len(sentiment_analysis)
            }
            
        except Exception as e:
            self.logger.error("Error calculating overall sentiment", error=str(e))
            return {
                'overall_sentiment': 'neutral',
                'overall_score': 0,
                'overall_confidence': 0.5,
                'sentiment_distribution': {'positive': 0, 'negative': 0, 'neutral': 0}
            }
    
    def get_news_summary(self) -> Dict:
        """Get summary of news analysis results"""
        try:
            total_articles = sum(len(result.get('articles', [])) for result in self.news_cache.values())
            
            # Count sentiment distribution
            sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
            for result in self.news_cache.values():
                if 'data' in result and 'overall_sentiment' in result['data']:
                    sentiment = result['data']['overall_sentiment']['overall_sentiment']
                    sentiment_counts[sentiment] += 1
            
            summary = {
                'total_tickers_analyzed': len(self.news_cache),
                'total_articles': total_articles,
                'sentiment_distribution': sentiment_counts,
                'last_news_fetch_time': self.last_news_fetch_time.isoformat() if self.last_news_fetch_time else None,
                'news_status': 'completed' if self.last_news_fetch_time else 'pending'
            }
            
            return summary
            
        except Exception as e:
            self.logger.error("Error getting news summary", error=str(e))
            return {}
    
    def clear_news_cache(self):
        """Clear news cache"""
        self.news_cache.clear()
        self.sentiment_cache.clear()
        self.last_news_fetch_time = None
        self.logger.info("News cache cleared")
