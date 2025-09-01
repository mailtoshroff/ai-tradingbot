# 🤖 AI Trading Bot - Agentic AI Auto Trading System

A sophisticated, multi-agent AI trading bot that performs swing trading based on technical analysis, news sentiment, and expert AI decision-making using Azure OpenAI.

## 🚀 Features

### **Multi-Agent Architecture**
- **Analysis Agent**: Technical analysis and rule evaluation
- **News Agent**: News sentiment analysis and scoring
- **Master Agent**: AI-powered decision making and coordination

### **Advanced Technical Analysis**
- Multiple timeframe analysis (Daily, Weekly, Monthly)
- SMA/EMA crossovers (21, 50, 200 periods)
- ATR (Average True Range) with Wilder's smoothing
- NYMO market breadth indicator
- Support/resistance level calculation
- Trend strength and momentum analysis

### **AI-Powered Decision Making**
- Azure OpenAI integration for expert trading decisions
- Sophisticated prompt engineering for agentic AI behavior
- Multi-factor analysis combining technical and sentiment data
- Risk assessment and position sizing recommendations
- Confidence scoring and reasoning transparency

### **News Sentiment Analysis**
- Real-time news gathering via NewsAPI
- Azure OpenAI-powered sentiment analysis
- Relevance scoring and weighted sentiment calculation
- Market impact assessment

### **Risk Management**
- ATR-based position sizing
- Portfolio-level risk controls
- Multi-level averaging down strategies
- No stop-loss (as per requirements)
- Extended position management

### **Automation & Monitoring**
- Scheduled market analysis (9:30 AM, 12:00 PM, 4:00 PM)
- Comprehensive email reporting
- Real-time logging and monitoring
- Graceful error handling and fallbacks

### **Intelligent Data Caching**
- **CSV-Based Caching**: Historical data stored in CSV files for reuse
- **Daily Cache Validity**: Data cached per day to avoid repeated API calls
- **Automatic Cleanup**: Old cache files removed automatically
- **Performance Optimization**: Subsequent runs use cached data for speed
- **Alpha Vantage API Efficiency**: Minimizes API calls to stay within rate limits

## 🏗️ Architecture

```
AI Trading Bot
├── Analysis Agent
│   ├── Technical Indicators Calculator
│   ├── Rule Evaluation Engine
│   └── Signal Enhancement
├── News Agent
│   ├── News API Integration
│   ├── Sentiment Analysis
│   └── Relevance Scoring
├── Master Agent
│   ├── AI Decision Engine
│   ├── Multi-Agent Coordination
│   └── Trading Logic Orchestration
└── Core Infrastructure
    ├── Data Management
    ├── Email Notifications
    ├── Logging & Monitoring
    └── Configuration Management
```

## 📋 Requirements

### **System Requirements**
- Python 3.8+
- Windows 10/11, macOS, or Linux
- 4GB+ RAM
- Stable internet connection

### **API Keys Required**
- **Alpaca Trading API**: For market data and trading execution
- **Azure OpenAI**: For AI-powered decision making
- **NewsAPI**: For news sentiment analysis
- **SMTP**: For email notifications

## 🛠️ Installation

### **1. Clone the Repository**
```bash
git clone <repository-url>
cd ai-tradingbot
```

### **2. Create Virtual Environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### **3. Install Dependencies**
```bash
pip install -r requirements.txt
```

### **4. Environment Configuration**
Create a `.env` file in the root directory:
```env
# Alpaca Trading API
ALPACA_API_KEY=your_alpaca_api_key_here
ALPACA_API_SECRET=your_alpaca_api_secret_here

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your_azure_openai_api_key_here
AZURE_OPENAI_DEPLOYMENT_NAME=your_deployment_name_here

# News API
NEWSAPI_API_KEY=your_newsapi_key_here

# Alpha Vantage (for market data)
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_api_key_here

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=your_app_password_here
RECIPIENT_EMAILS=recipient1@email.com,recipient2@email.com

# Trading Configuration
MAX_PORTFOLIO_VALUE=100000
MAX_POSITION_SIZE_PCT=10
MIN_POSITION_SIZE=1000
AUTO_EXECUTE_TRADES=false  # Set to true to automatically execute trades
```

### **5. Configuration File**
The `config/config.yaml` file contains additional configuration options. Review and modify as needed.

## 🚀 Usage

### **Quick Start - Single Run**
```bash
# Run analysis once and exit
python src/main.py
```

### **Continuous Operation**
```bash
# Run continuously with scheduled analysis
python src/main.py
```

### **Environment Variable Control**
```bash
# Run in single mode
set RUN_MODE=once  # Windows
export RUN_MODE=once  # Linux/Mac

python src/main.py
```

## 📊 Trading Rules

The bot implements sophisticated swing trading rules based on the `rules.json` configuration:

### **Buy Signals**
1. **SMA Crossovers**: Price crosses below 21/50/200 SMA while above longer-term SMAs
2. **EMA Crossovers**: Weekly EMA crossovers with trend confirmation
3. **ATR Trailing Stops**: Price breaches ATR-based trailing stops
4. **NYMO Extremes**: Market breadth indicators at extreme levels

### **Position Sizing**
- Based on ATR (Average True Range)
- Configurable portfolio percentage limits
- Risk-adjusted allocation per ticker

### **Averaging Down Strategy**
- Buy more when position is down 2 ATR
- Additional buys at 3 ATR and 4 ATR levels
- Percentage-based position increases

### **Sell Conditions**
- Sell half when price is 50% above 200 SMA
- No selling at a loss (as per requirements)
- Take profit at 100% gain

## 🔧 Configuration

### **Trading Parameters**
```yaml
trading:
  max_portfolio_value: 100000
  max_position_size_pct: 10
  min_position_size: 1000
  default_atr_multiplier: 1.0
  
  averaging:
    atr_thresholds: [2.0, 3.0, 4.0]
    position_increase_pct: [25, 25, 25]
  
  sell_conditions:
    extended_from_200sma_pct: 50
    profit_taking_pct: 100
```

### **Technical Analysis**
```yaml
technical_analysis:
  default_lookback_days: 365
  sma_periods: [21, 50, 200]
  ema_periods: [10, 20, 40]
  atr_period: 5
  atr_factor: 2.5
```

### **Schedule Configuration**
```yaml
schedule:
  market_open_analysis: "09:30"
  intraday_monitoring: "12:00"
  end_of_day_report: "16:00"
  timezone: "America/New_York"
```

## 📧 Email Reports

The bot sends comprehensive email reports including:

- **Trading Signals**: Buy/Sell/Hold recommendations with reasoning
- **Portfolio Status**: Current positions and performance
- **Risk Assessment**: Risk factors and position sizing
- **Market Context**: Broader market considerations

## 🔍 Monitoring & Logging

### **Log Files**
- Location: `logs/trading_bot.log`
- Structured logging with JSON format
- Rotating log files with configurable size limits

### **Log Levels**
- **INFO**: Normal operations and decisions
- **WARNING**: Non-critical issues
- **ERROR**: Errors requiring attention
- **DEBUG**: Detailed debugging information

### **Monitoring Dashboard**
The bot provides programmatic access to:
- Analysis summaries
- News sentiment summaries
- Trading decision summaries
- Cache statistics

## 🧪 Testing

### **Paper Trading**
- Configure Alpaca for paper trading
- Test strategies without real money
- Validate rule effectiveness

### **Backtesting**
- Historical rule validation
- Performance metrics calculation
- Risk analysis and optimization

## ⚠️ Risk Disclaimer

**IMPORTANT**: This trading bot is for educational and research purposes. Trading involves substantial risk of loss and is not suitable for all investors. Past performance does not guarantee future results.

### **Risk Factors**
- Market volatility and unpredictability
- Technical analysis limitations
- News sentiment interpretation risks
- AI decision-making uncertainties
- System failures and technical issues

### **Recommendations**
- Start with paper trading
- Use only risk capital
- Monitor performance closely
- Understand all trading rules
- Have fallback strategies

## 🚨 Troubleshooting

### **Common Issues**

#### **API Connection Errors**
- Verify API keys and endpoints
- Check internet connectivity
- Validate API rate limits

#### **Data Fetching Issues**
- Ensure market hours (9:30 AM - 4:00 PM ET)
- Check ticker symbols in rules.json
- Verify data source availability

### **CSV Caching System**
The bot now includes an intelligent CSV-based caching system:
- **Automatic Caching**: Historical data is automatically saved to CSV files in `data_cache/` directory
- **Daily Cache**: Data is cached per day and reused throughout the day
- **No Repeated API Calls**: Alpha Vantage API is only called once per ticker per day
- **Automatic Cleanup**: Old cache files are automatically removed daily
- **Manual Cache Management**: Methods available to clear specific ticker or all cache files

#### **Email Configuration**
- Test SMTP settings
- Verify app passwords for Gmail
- Check firewall/antivirus settings

### **Debug Mode**
Enable debug logging in `config/config.yaml`:
```yaml
logging:
  level: "DEBUG"
```

## 🔮 Future Enhancements

### **Planned Features**
- Real-time market data streaming
- Advanced portfolio optimization
- Machine learning model training
- Web-based dashboard
- Mobile notifications
- Integration with additional brokers

### **Advanced AI Features**
- Reinforcement learning for strategy optimization
- Multi-modal analysis (charts, news, social media)
- Predictive market regime detection
- Dynamic rule adaptation

## 📚 API Documentation

### **Core Classes**

#### **MasterAgent**
```python
# Execute comprehensive analysis
results = await master_agent.execute_comprehensive_analysis()

# Get decision summary
summary = master_agent.get_decision_summary()

# Send trading report
await master_agent.send_trading_report()
```

#### **AnalysisAgent**
```python
# Analyze specific ticker
signals = await analysis_agent.analyze_ticker("AAPL")

# Get analysis summary
summary = analysis_agent.get_analysis_summary()
```

#### **NewsAgent**
```python
# Analyze news for tickers
news_results = await news_agent.analyze_news_for_tickers(["AAPL", "MSFT"])

# Get news summary
summary = news_agent.get_news_summary()
```

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines for:
- Code style and standards
- Testing requirements
- Documentation updates
- Feature proposals

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

For support and questions:
- Create an issue on GitHub
- Check the troubleshooting section
- Review the configuration examples
- Consult the API documentation

---

**Happy Trading! 🚀📈**

*Remember: The best trading strategy is the one you understand and can execute consistently.*
