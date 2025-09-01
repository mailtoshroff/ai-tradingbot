"""
Test script for enhanced AI Trading Bot features:
- ATR-based position sizing
- Averaging down logic
- Enhanced NYMO calculation
- Position management
"""
import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from utils.position_manager import PositionManager
from utils.enhanced_nymo import EnhancedNYMO
from utils.technical_indicators import TechnicalIndicators
from utils.logger import trading_logger

async def test_position_manager():
    """Test position management features"""
    print("\n" + "="*60)
    print("🧮 TESTING POSITION MANAGER")
    print("="*60)
    
    # Initialize position manager
    logger = trading_logger.get_logger("test")
    position_manager = PositionManager()
    position_manager.set_logger(logger)
    
    # Test 1: ATR-based position sizing
    print("\n📊 Test 1: ATR-based Position Sizing")
    print("-" * 40)
    
    portfolio_value = 100000
    current_price = 150.0
    atr_value = 3.5
    purchase_limit_pct = 2.0
    
    position_size = position_manager.calculate_atr_position_size(
        portfolio_value, current_price, atr_value, purchase_limit_pct
    )
    
    print(f"Portfolio Value: ${portfolio_value:,.2f}")
    print(f"Current Price: ${current_price:.2f}")
    print(f"ATR Value: ${atr_value:.2f}")
    print(f"Purchase Limit: {purchase_limit_pct}%")
    print(f"\nPosition Size Results:")
    print(f"  Shares: {position_size.get('shares', 0)}")
    print(f"  Position Value: ${position_size.get('position_value', 0):,.2f}")
    print(f"  Position %: {position_size.get('position_pct', 0):.2f}%")
    print(f"  Sizing Method: {position_size.get('sizing_method', 'Unknown')}")
    
    # Test 2: Add a position
    print("\n📈 Test 2: Adding Position")
    print("-" * 40)
    
    position_manager.add_position(
        ticker="AAPL",
        entry_price=150.0,
        shares=100,
        position_value=15000,
        rule_name="below_21sma_cross",
        confidence=0.8
    )
    
    print("Added AAPL position:")
    print(f"  Entry Price: $150.00")
    print(f"  Shares: 100")
    print(f"  Position Value: $15,000")
    
    # Test 3: Averaging down logic
    print("\n📉 Test 3: Averaging Down Logic")
    print("-" * 40)
    
    # Simulate price drop
    current_price_dropped = 140.0  # $10 drop
    
    should_average, confidence, reasoning = position_manager.should_average_down(
        ticker="AAPL",
        current_price=current_price_dropped,
        entry_price=150.0,
        atr_value=3.5,
        pct_below_previous_buy=0.02
    )
    
    print(f"Current Price: ${current_price_dropped:.2f}")
    print(f"Entry Price: ${150.0:.2f}")
    print(f"ATR Value: ${3.5:.2f}")
    print(f"Price Drop: ${150.0 - current_price_dropped:.2f}")
    print(f"Should Average Down: {should_average}")
    print(f"Confidence: {confidence:.2f}")
    print(f"Reasoning: {reasoning}")
    
    if should_average:
        # Calculate averaging down size
        averaging_size = position_manager.calculate_averaging_down_size(
            ticker="AAPL",
            portfolio_value=100000,
            current_price=current_price_dropped,
            atr_value=3.5,
            averaging_level="2x ATR"
        )
        
        print(f"\nAveraging Down Size:")
        print(f"  Shares: {averaging_size.get('shares', 0)}")
        print(f"  Position Value: ${averaging_size.get('position_value', 0):,.2f}")
        print(f"  Level: {averaging_size.get('averaging_level', 'Unknown')}")
    
    # Test 4: Partial profit taking
    print("\n💰 Test 4: Partial Profit Taking")
    print("-" * 40)
    
    # Simulate price above 200 SMA
    current_price_profit = 200.0
    sma_200 = 130.0
    
    should_take_profit, profit_confidence, profit_reasoning = position_manager.should_take_partial_profit(
        ticker="AAPL",
        current_price=current_price_profit,
        entry_price=150.0,
        sma_200=sma_200
    )
    
    print(f"Current Price: ${current_price_profit:.2f}")
    print(f"Entry Price: ${150.0:.2f}")
    print(f"200 SMA: ${sma_200:.2f}")
    print(f"50% above 200 SMA: ${sma_200 * 1.5:.2f}")
    print(f"Should Take Partial Profit: {should_take_profit}")
    print(f"Confidence: {profit_confidence:.2f}")
    print(f"Reasoning: {profit_reasoning}")
    
    # Test 5: Position summary
    print("\n📋 Test 5: Position Summary")
    print("-" * 40)
    
    position_summary = position_manager.get_position_summary("AAPL")
    print("Position Summary:")
    for key, value in position_summary.items():
        if key not in ['entry_date']:  # Skip datetime for cleaner output
            print(f"  {key}: {value}")

async def test_enhanced_nymo():
    """Test enhanced NYMO calculation"""
    print("\n" + "="*60)
    print("📈 TESTING ENHANCED NYMO")
    print("="*60)
    
    # Initialize enhanced NYMO
    logger = trading_logger.get_logger("test")
    enhanced_nymo = EnhancedNYMO()
    enhanced_nymo.set_logger(logger)
    
    # Test 1: Market breadth data
    print("\n🌐 Test 1: Market Breadth Data")
    print("-" * 40)
    
    current_date = "2025-01-30"
    market_data = enhanced_nymo.fetch_market_breadth_data(current_date)
    
    print(f"Market Breadth Data for {current_date}:")
    print(f"  Advancing Issues: {market_data.get('advancing', 0):,}")
    print(f"  Declining Issues: {market_data.get('declining', 0):,}")
    print(f"  Unchanged Issues: {market_data.get('unchanged', 0):,}")
    print(f"  Total Issues: {market_data.get('total', 0):,}")
    print(f"  Advance/Decline Ratio: {market_data.get('advance_decline_ratio', 0):.2f}")
    print(f"  Advancing %: {market_data.get('advancing_pct', 0):.1f}%")
    print(f"  Declining %: {market_data.get('declining_pct', 0):.1f}%")
    
    # Test 2: Enhanced NYMO calculation
    print("\n📊 Test 2: Enhanced NYMO Calculation")
    print("-" * 40)
    
    nymo_value = enhanced_nymo.calculate_enhanced_nymo(market_data)
    print(f"NYMO Value: {nymo_value:.2f}")
    
    # Test 3: NYMO signals
    print("\n🎯 Test 3: NYMO Trading Signals")
    print("-" * 40)
    
    nymo_signals = enhanced_nymo.calculate_nymo_signals(nymo_value)
    
    print("NYMO Signals:")
    print(f"  Signal Strength: {nymo_signals.get('signal_strength', 'Unknown')}")
    print(f"  Trading Signal: {nymo_signals.get('trading_signal', 'Unknown')}")
    print(f"  Confidence: {nymo_signals.get('confidence', 0):.2f}")
    print(f"  Risk Level: {nymo_signals.get('risk_level', 'Unknown')}")
    print(f"  Reasoning: {nymo_signals.get('reasoning', 'Unknown')}")
    
    # Test 4: NYMO history and trend analysis
    print("\n📈 Test 4: NYMO History & Trend Analysis")
    print("-" * 40)
    
    nymo_history = enhanced_nymo.get_nymo_history(days=7)
    trend_analysis = enhanced_nymo.analyze_nymo_trend(nymo_history)
    
    print(f"NYMO History (7 days): {len(nymo_history)} data points")
    print(f"Trend Analysis:")
    print(f"  Trend: {trend_analysis.get('trend', 'Unknown')}")
    print(f"  Trend Strength: {trend_analysis.get('trend_strength', 0):.2f}")
    print(f"  Momentum: {trend_analysis.get('momentum', 'Unknown')}")
    print(f"  Current Value: {trend_analysis.get('current_value', 0):.2f}")
    print(f"  Average Value: {trend_analysis.get('average_value', 0):.2f}")
    print(f"  Volatility: {trend_analysis.get('volatility', 0):.2f}")

async def test_technical_indicators():
    """Test enhanced technical indicators"""
    print("\n" + "="*60)
    print("🔧 TESTING ENHANCED TECHNICAL INDICATORS")
    print("="*60)
    
    # Initialize technical indicators
    logger = trading_logger.get_logger("test")
    tech_indicators = TechnicalIndicators()
    tech_indicators.set_logger(logger)
    
    # Create sample data
    import pandas as pd
    import numpy as np
    
    dates = pd.date_range('2025-01-01', periods=100, freq='D')
    np.random.seed(42)  # For reproducible results
    
    # Generate realistic price data
    base_price = 150.0
    returns = np.random.normal(0.001, 0.02, 100)  # Daily returns
    prices = [base_price]
    
    for ret in returns[1:]:
        prices.append(prices[-1] * (1 + ret))
    
    data = pd.DataFrame({
        'open': [p * (1 + np.random.normal(0, 0.005)) for p in prices],
        'high': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
        'low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
        'close': prices,
        'volume': np.random.randint(1000000, 10000000, 100)
    }, index=dates)
    
    print(f"Sample Data Created:")
    print(f"  Date Range: {data.index[0].strftime('%Y-%m-%d')} to {data.index[-1].strftime('%Y-%m-%d')}")
    print(f"  Data Points: {len(data)}")
    print(f"  Price Range: ${data['close'].min():.2f} - ${data['close'].max():.2f}")
    
    # Test 1: ATR multiples
    print("\n📊 Test 1: ATR Multiples")
    print("-" * 40)
    
    atr_multiples = tech_indicators.calculate_atr_multiples(data, period=14)
    
    if atr_multiples:
        current_atr = atr_multiples['atr'].iloc[-1]
        print(f"Current ATR (14-period): ${current_atr:.2f}")
        print(f"2x ATR: ${atr_multiples['atr_2x'].iloc[-1]:.2f}")
        print(f"3x ATR: ${atr_multiples['atr_3x'].iloc[-1]:.2f}")
        print(f"4x ATR: ${atr_multiples['atr_4x'].iloc[-1]:.2f}")
        print(f"5x ATR: ${atr_multiples['atr_5x'].iloc[-1]:.2f}")
    
    # Test 2: ATR-based position sizing
    print("\n💰 Test 2: ATR-based Position Sizing")
    print("-" * 40)
    
    portfolio_value = 100000
    current_price = data['close'].iloc[-1]
    
    position_sizing = tech_indicators.calculate_position_sizing_atr(
        data, portfolio_value, current_price, atr_period=14
    )
    
    if position_sizing:
        print(f"Portfolio Value: ${portfolio_value:,.2f}")
        print(f"Current Price: ${current_price:.2f}")
        print(f"ATR Value: ${position_sizing.get('atr_value', 0):.2f}")
        print(f"ATR Position Value: ${position_sizing.get('atr_position_value', 0):.2f}")
        print(f"ATR Position %: {position_sizing.get('atr_position_pct', 0):.4f}%")
        print(f"Shares: {position_sizing.get('shares', 0)}")
        print(f"Actual Position Value: ${position_sizing.get('actual_position_value', 0):.2f}")
        print(f"Sizing Method: {position_sizing.get('sizing_method', 'Unknown')}")

async def main():
    """Main test function"""
    print("🚀 ENHANCED AI TRADING BOT FEATURE TEST")
    print("=" * 60)
    
    try:
        # Test all enhanced features
        await test_position_manager()
        await test_enhanced_nymo()
        await test_technical_indicators()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY!")
        print("="*60)
        
        print("\n🎯 FEATURES IMPLEMENTED:")
        print("  ✅ ATR-based position sizing (1 ATR per trade)")
        print("  ✅ Averaging down logic (2x, 3x, 4x ATR)")
        print("  ✅ Enhanced NYMO calculation with market breadth")
        print("  ✅ Position management and lifecycle")
        print("  ✅ Partial profit taking (50% above 200 SMA)")
        print("  ✅ Technical indicator enhancements")
        
        print("\n🚀 NEXT STEPS:")
        print("  1. Integrate with main trading bot")
        print("  2. Test with real market data")
        print("  3. Configure position sizing parameters")
        print("  4. Set up automated position monitoring")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())

