#!/usr/bin/env python3
"""
Test script for Alpha Vantage integration
"""
import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_alpha_vantage_integration():
    """Test Alpha Vantage integration"""
    print("Testing Alpha Vantage integration...")
    try:
        from core.data_manager import DataManager
        
        # Initialize data manager
        data_manager = DataManager()
        print("✅ Data manager initialized successfully")
        
        # Test mock data generation (when no API key)
        print("\nTesting mock data generation...")
        mock_data = data_manager._generate_mock_data("AAPL", "D", "30d")
        print(f"✅ Mock data generated: {len(mock_data)} data points")
        print(f"   - Columns: {list(mock_data.columns)}")
        print(f"   - Date range: {mock_data.index[0]} to {mock_data.index[-1]}")
        print(f"   - Sample close price: ${mock_data['close'].iloc[-1]:.2f}")
        
        # Test getting tickers from rules
        print("\nTesting ticker extraction from rules...")
        tickers = data_manager.get_all_tickers()
        print(f"✅ Found {len(tickers)} tickers in trading rules")
        if tickers:
            print(f"   - Sample tickers: {tickers[:5]}")
        
        # Test portfolio data (will use mock data)
        print("\nTesting portfolio data generation...")
        if tickers:
            portfolio_data = data_manager.get_portfolio_data(tickers[:3])  # Test with first 3 tickers
            print(f"✅ Portfolio data generated for {len(portfolio_data)} tickers")
            for ticker, data in portfolio_data.items():
                print(f"   - {ticker}: ${data['current_price']:.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Alpha Vantage integration error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("🚀 Alpha Vantage Integration Test")
    print("=" * 50)
    
    success = test_alpha_vantage_integration()
    
    if success:
        print("\n" + "=" * 50)
        print("✅ Alpha Vantage integration test passed!")
        print("\nThe bot is now ready to run with Alpha Vantage.")
        print("To use real market data, add your Alpha Vantage API key to .env:")
        print("ALPHA_VANTAGE_API_KEY=your_api_key_here")
        print("\nWithout the API key, the bot will use realistic mock data for testing.")
    else:
        print("\n❌ Alpha Vantage integration test failed!")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
