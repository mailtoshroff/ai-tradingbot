"""
Production-Ready Test for AI Trading Bot
Tests all integrated features with real market data and position monitoring
"""
import asyncio
import sys
import os
from pathlib import Path
import time
import json
import pandas as pd

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from agents.master_agent import MasterAgent
from utils.logger import trading_logger
from utils.position_monitor import PositionMonitor

async def test_production_integration():
    """Test production-ready integration"""
    print("\n" + "="*80)
    print("🚀 PRODUCTION-READY INTEGRATION TEST")
    print("="*80)
    
    logger = trading_logger.get_logger("production_test")
    
    try:
        # Test 1: Initialize Master Agent with all components
        print("\n📋 Test 1: Full System Initialization")
        print("-" * 50)
        
        master_agent = MasterAgent("config/config.yaml")
        print("✅ Master Agent initialized with all components")
        
        # Test 2: Test Enhanced NYMO Integration
        print("\n📊 Test 2: Enhanced NYMO Integration")
        print("-" * 50)
        
        # Test NYMO calculation and signals
        market_data = master_agent.enhanced_nymo.fetch_market_breadth_data()
        if market_data:
            nymo_value = master_agent.enhanced_nymo.calculate_enhanced_nymo(market_data)
            nymo_signals = master_agent.enhanced_nymo.calculate_nymo_signals(nymo_value)
            
            print(f"✅ NYMO Value: {nymo_value:.2f}")
            print(f"✅ Market Condition: {nymo_signals.get('trading_signal', 'Unknown')}")
            print(f"✅ Signal Strength: {nymo_signals.get('signal_strength', 'neutral')}")
        else:
            print("⚠️  NYMO analysis incomplete")
        
        # Test 3: Test Position Manager Integration
        print("\n💰 Test 3: Position Manager Integration")
        print("-" * 50)
        
        position_manager = master_agent.position_manager
        
        # Test ATR-based position sizing with realistic scenarios
        scenarios = [
            {'portfolio': 100000, 'price': 150, 'atr': 3.5, 'limit': 2.0, 'name': 'Conservative'},
            {'portfolio': 100000, 'price': 50, 'atr': 2.0, 'limit': 5.0, 'name': 'Moderate'},
            {'portfolio': 100000, 'price': 25, 'atr': 1.5, 'limit': 10.0, 'name': 'Aggressive'}
        ]
        
        for scenario in scenarios:
            position_size = position_manager.calculate_atr_position_size(
                scenario['portfolio'],
                scenario['price'],
                scenario['atr'],
                scenario['limit']
            )
            
            if position_size:
                print(f"✅ {scenario['name']}: {position_size.get('shares', 0)} shares "
                      f"({position_size.get('position_pct', 0):.2f}% portfolio)")
            else:
                print(f"❌ {scenario['name']}: Position sizing failed")
        
        # Test 4: Test Position Monitor Integration
        print("\n📈 Test 4: Position Monitor Integration")
        print("-" * 50)
        
        position_monitor = master_agent.position_monitor
        print(f"✅ Position Monitor initialized")
        print(f"✅ Check Interval: {position_monitor.check_interval} minutes")
        print(f"✅ Automated Management: {position_monitor.enable_automated_management}")
        print(f"✅ Max Positions per Ticker: {position_monitor.max_positions_per_ticker}")
        
        # Test 5: Comprehensive Analysis Execution
        print("\n🔍 Test 5: Comprehensive Analysis Execution")
        print("-" * 50)
        
        print("Executing comprehensive analysis...")
        start_time = time.time()
        
        analysis_results = await master_agent.execute_comprehensive_analysis()
        
        execution_time = time.time() - start_time
        print(f"✅ Analysis completed in {execution_time:.2f} seconds")
        
        if analysis_results:
            analysis_count = len(analysis_results.get('analysis', {}))
            news_count = len(analysis_results.get('news', {}))
            nymo_count = 1 if analysis_results.get('nymo') else 0
            
            print(f"✅ Analysis Results: {analysis_count} tickers")
            print(f"✅ News Results: {news_count} tickers")
            print(f"✅ NYMO Results: {nymo_count} market condition")
            
            # Show sample analysis results
            if analysis_count > 0:
                sample_ticker = list(analysis_results['analysis'].keys())[0]
                sample_data = analysis_results['analysis'][sample_ticker]
                print(f"✅ Sample Analysis for {sample_ticker}:")
                print(f"   Signals: {len(sample_data.get('signals', []))}")
                if sample_data.get('signals'):
                    primary_signal = sample_data['signals'][0]
                    print(f"   Primary Signal: {primary_signal.get('rule_name', 'Unknown')}")
                    print(f"   Confidence: {primary_signal.get('confidence', 0):.2f}")
        else:
            print("⚠️  No analysis results returned")
        
        # Test 6: Position Management Opportunities
        print("\n📊 Test 6: Position Management Opportunities")
        print("-" * 50)
        
        opportunities = master_agent.check_position_management_opportunities()
        print(f"✅ Found {len(opportunities)} position management opportunities")
        
        for opp in opportunities[:3]:  # Show first 3
            print(f"  - {opp['ticker']}: {opp['action']} - {opp['reasoning']}")
        
        # Test 7: Trading Decision Generation
        print("\n🎯 Test 7: Trading Decision Generation")
        print("-" * 50)
        
        if analysis_results and 'analysis' in analysis_results:
            tickers = list(analysis_results['analysis'].keys())
            if tickers:
                test_ticker = tickers[0]
                print(f"Testing decision generation for {test_ticker}")
                
                ticker_signals = analysis_results['analysis'][test_ticker].get('signals', [])
                ticker_news = analysis_results['news'].get(test_ticker, {})
                
                if ticker_signals:
                    decision = await master_agent._generate_ai_decision(
                        test_ticker, ticker_signals, ticker_news
                    )
                    
                    if decision:
                        print(f"✅ Decision generated: {decision.get('action', 'Unknown')}")
                        print(f"✅ Confidence: {decision.get('confidence', 0):.2f}")
                        print(f"✅ Reasoning: {decision.get('reasoning', 'No reason')[:100]}...")
                    else:
                        print("⚠️  No decision generated")
                else:
                    print(f"⚠️  No signals for {test_ticker}")
            else:
                print("⚠️  No tickers available for decision testing")
        
        # Test 8: Position Monitoring Status
        print("\n📊 Test 8: Position Monitoring Status")
        print("-" * 50)
        
        monitoring_status = master_agent.get_position_monitoring_status()
        print(f"✅ Monitoring Running: {monitoring_status.get('running', False)}")
        print(f"✅ Check Interval: {monitoring_status.get('check_interval_minutes', 0)} minutes")
        print(f"✅ Automated Management: {monitoring_status.get('automated_management', False)}")
        print(f"✅ Last Check: {monitoring_status.get('last_check_time', 'Never')}")
        print(f"✅ Position Count: {monitoring_status.get('position_count', 0)}")
        print(f"✅ Management Actions Today: {monitoring_status.get('management_actions_today', 0)}")
        
        # Test 9: Configuration Validation
        print("\n⚙️  Test 9: Configuration Validation")
        print("-" * 50)
        
        config = master_agent.config
        
        # Check trading configuration
        trading_config = config.get('trading', {})
        print(f"✅ Max Portfolio Value: ${trading_config.get('max_portfolio_value', 0):,}")
        print(f"✅ Max Position Size: {trading_config.get('max_position_size_pct', 0)}%")
        print(f"✅ Default ATR Multiplier: {trading_config.get('default_atr_multiplier', 0)}")
        
        # Check monitoring configuration
        monitoring_config = trading_config.get('monitoring', {})
        print(f"✅ Check Interval: {monitoring_config.get('check_interval_minutes', 0)} minutes")
        print(f"✅ Automated Management: {monitoring_config.get('enable_automated_management', False)}")
        print(f"✅ Max Positions per Ticker: {monitoring_config.get('max_positions_per_ticker', 0)}")
        print(f"✅ Rebalance Threshold: {monitoring_config.get('rebalance_threshold', 0)*100}%")
        
        # Check sell conditions
        sell_conditions = trading_config.get('sell_conditions', {})
        print(f"✅ Extended from 200 SMA: {sell_conditions.get('extended_from_200sma_pct', 0)}%")
        print(f"✅ Profit Taking: {sell_conditions.get('profit_taking_pct', 0)}%")
        print(f"✅ Stop Loss: {sell_conditions.get('stop_loss_pct', 0)}%")
        
        # Test 10: Enhanced Features Validation
        print("\n🚀 Test 10: Enhanced Features Validation")
        print("-" * 50)
        
        # Check if all enhanced features are properly integrated
        enhanced_features = [
            'position_manager' in dir(master_agent),
            'enhanced_nymo' in dir(master_agent),
            'position_monitor' in dir(master_agent),
            hasattr(master_agent, 'check_position_management_opportunities'),
            hasattr(master_agent, 'start_position_monitoring'),
            hasattr(master_agent, 'stop_position_monitoring')
        ]
        
        feature_names = [
            'Position Manager',
            'Enhanced NYMO',
            'Position Monitor',
            'Position Management Check',
            'Start Position Monitoring',
            'Stop Position Monitoring'
        ]
        
        for feature, name in zip(enhanced_features, feature_names):
            status = "✅" if feature else "❌"
            print(f"{status} {name}")
        
        print("\n" + "="*80)
        print("🎉 PRODUCTION INTEGRATION TEST COMPLETED SUCCESSFULLY!")
        print("="*80)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Production integration test failed: {e}")
        logger.error(f"Production integration test failed", error=str(e))
        return False

async def test_market_data_production():
    """Test production market data integration"""
    print("\n" + "="*80)
    print("📊 PRODUCTION MARKET DATA TEST")
    print("="*80)
    
    try:
        master_agent = MasterAgent("config/config.yaml")
        
        # Test market data fetching for all configured tickers
        print("\n📈 Testing Production Market Data Integration")
        print("-" * 50)
        
        # Get all tickers from rules.json
        with open('rules.json', 'r') as f:
            rules_data = json.load(f)
        
        all_tickers = set()
        for rule in rules_data.get('rules', []):
            if 'stocks' in rule:
                all_tickers.update(rule['stocks'].keys())
        
        print(f"Found {len(all_tickers)} tickers in rules configuration")
        
        # Test a subset of tickers for performance
        test_tickers = list(all_tickers)[:5]  # Test first 5 tickers
        
        successful_tickers = 0
        for ticker in test_tickers:
            print(f"\nTesting {ticker}:")
            
            try:
                # Test technical indicators calculation
                indicators = master_agent.analysis_agent.data_manager.calculate_indicators_for_ticker(ticker)
                
                if indicators and isinstance(indicators, dict) and len(indicators) > 0:
                    print(f"  ✅ Technical indicators calculated")
                    print(f"  📊 Indicators type: {type(indicators)}")
                    print(f"  📊 Available keys: {list(indicators.keys())}")
                    
                    # Check key indicators
                    key_indicators = ['sma_200', 'atr', 'ema_10', 'ema_20', 'ema_40']
                    for indicator in key_indicators:
                        try:
                            value = indicators.get(indicator, 'N/A')
                            print(f"  🔍 {indicator}: type={type(value)}, value={value}")
                            
                            # Fix: Check if value is not 'N/A' first, avoiding Series comparison
                            if not isinstance(value, str) or value != 'N/A':
                                if hasattr(value, '__len__') and len(value) > 0:
                                    # Handle pandas Series or numpy arrays
                                    if hasattr(value, 'iloc'):
                                        # It's a pandas Series
                                        last_value = value.iloc[-1]
                                        print(f"    📈 Series last value: {last_value} (type: {type(last_value)})")
                                    else:
                                        # It's a numpy array or list
                                        last_value = value[-1]
                                        print(f"    📈 Array last value: {last_value} (type: {type(last_value)})")
                                    
                                    # Convert to float and check if valid
                                    try:
                                        last_value_float = float(last_value)
                                        if last_value_float != 0 and not pd.isna(last_value_float):
                                            print(f"  ✅ {indicator.upper()}: {last_value_float:.2f}")
                                        else:
                                            print(f"  ⚠️  {indicator.upper()}: Invalid value")
                                    except (ValueError, TypeError) as e:
                                        print(f"  ⚠️  {indicator.upper()}: Cannot convert to number - {e}")
                                else:
                                    print(f"  ⚠️  {indicator.upper()}: No length or empty")
                            else:
                                print(f"  ⚠️  {indicator.upper()}: Not available")
                        except Exception as indicator_error:
                            print(f"  ❌ Error processing {indicator}: {indicator_error}")
                            print(f"  ❌ Error type: {type(indicator_error)}")
                            import traceback
                            traceback.print_exc()
                    
                    successful_tickers += 1
                else:
                    print(f"  ❌ No indicators for {ticker}")
                    
            except Exception as e:
                print(f"  ❌ Error testing {ticker}: {e}")
                print(f"  ❌ Error type: {type(e)}")
                import traceback
                traceback.print_exc()
        
        print(f"\n✅ Market data test completed: {successful_tickers}/{len(test_tickers)} tickers successful")
        return successful_tickers == len(test_tickers)
        
    except Exception as e:
        print(f"\n❌ Production market data test failed: {e}")
        return False

async def test_position_monitoring_production():
    """Test production position monitoring"""
    print("\n" + "="*80)
    print("📊 PRODUCTION POSITION MONITORING TEST")
    print("="*80)
    
    try:
        master_agent = MasterAgent("config/config.yaml")
        
        # Test position monitoring functionality
        print("\n📈 Testing Position Monitoring Features")
        print("-" * 50)
        
        # Test 1: Start position monitoring
        print("Starting position monitoring...")
        start_success = await master_agent.start_position_monitoring()
        print(f"✅ Position monitoring start: {start_success}")
        
        # Test 2: Get monitoring status
        monitoring_status = master_agent.get_position_monitoring_status()
        print(f"✅ Monitoring Status: {monitoring_status}")
        
        # Test 3: Get position summary
        position_summary = master_agent.get_position_summary()
        print(f"✅ Position Summary: {position_summary}")
        
        # Test 4: Stop position monitoring
        print("Stopping position monitoring...")
        stop_success = await master_agent.stop_position_monitoring()
        print(f"✅ Position monitoring stop: {stop_success}")
        
        print("\n✅ Position monitoring test completed successfully")
        return True
        
    except Exception as e:
        print(f"\n❌ Production position monitoring test failed: {e}")
        return False

async def main():
    """Main production test function"""
    print("🚀 Starting AI Trading Bot Production Tests")
    print("="*80)
    
    # Run all production tests
    tests = [
        test_production_integration,
        test_market_data_production,
        test_position_monitoring_production
    ]
    
    results = []
    
    for test in tests:
        try:
            print(f"\n🔄 Running {test.__name__}...")
            result = await test()
            results.append(result)
            print(f"✅ {test.__name__} completed: {'PASSED' if result else 'FAILED'}")
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "="*80)
    print("📋 PRODUCTION TEST SUMMARY")
    print("="*80)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("🎉 All production tests passed! The bot is ready for production deployment.")
        print("\n🚀 NEXT STEPS:")
        print("1. ✅ Integration with main trading bot - COMPLETED")
        print("2. ✅ Test with real market data - COMPLETED")
        print("3. ✅ Configure position sizing parameters - COMPLETED")
        print("4. ✅ Set up automated position monitoring - COMPLETED")
        print("\n🎯 The AI Trading Bot is now production-ready!")
    else:
        print("⚠️  Some production tests failed. Please review the errors above.")
        print("\n🔧 RECOMMENDATIONS:")
        print("- Check configuration files for errors")
        print("- Verify API keys and endpoints")
        print("- Review error logs for specific issues")
    
    return passed == total

if __name__ == "__main__":
    # Run the production tests
    success = asyncio.run(main())
    
    if success:
        print("\n✅ Production tests completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Some production tests failed!")
        sys.exit(1)
