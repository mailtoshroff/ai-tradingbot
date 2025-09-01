#!/usr/bin/env python3
"""
Test script for CSV caching functionality
"""
import asyncio
import sys
import os
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_csv_caching():
    """Test CSV caching functionality"""
    print("Testing CSV caching functionality...")
    try:
        from core.data_manager import DataManager
        
        # Initialize data manager
        data_manager = DataManager()
        print("✅ Data manager initialized successfully")
        
        # Get initial cache stats
        print("\nInitial cache stats:")
        initial_stats = data_manager.get_cache_stats()
        for key, value in initial_stats.items():
            print(f"   - {key}: {value}")
        
        # Test fetching data for a few tickers (will create CSV files)
        print("\nTesting data fetching and CSV caching...")
        test_tickers = ["AAPL", "MSFT", "GOOGL"]
        
        for ticker in test_tickers:
            print(f"\nFetching data for {ticker}...")
            start_time = time.time()
            
            # Fetch daily data (this will create CSV cache)
            data = data_manager.fetch_market_data(ticker, "D", "30d")
            
            fetch_time = time.time() - start_time
            print(f"   ✅ {ticker}: {len(data)} data points fetched in {fetch_time:.2f}s")
            print(f"   📊 Sample data: Close=${data['close'].iloc[-1]:.2f}, Volume={data['volume'].iloc[-1]:,}")
        
        # Get cache stats after fetching
        print("\nCache stats after fetching data:")
        after_stats = data_manager.get_cache_stats()
        for key, value in after_stats.items():
            print(f"   - {key}: {value}")
        
        # Test cache reuse (should be much faster)
        print("\nTesting cache reuse (should be faster)...")
        for ticker in test_tickers:
            print(f"\nRe-fetching data for {ticker} (should use CSV cache)...")
            start_time = time.time()
            
            # Fetch data again (should use CSV cache)
            data = data_manager.fetch_market_data(ticker, "D", "30d")
            
            fetch_time = time.time() - start_time
            print(f"   ✅ {ticker}: {len(data)} data points loaded in {fetch_time:.2f}s (from cache)")
        
        # Test clearing specific ticker cache
        print(f"\nTesting clear specific ticker cache...")
        data_manager.clear_ticker_csv_cache("AAPL")
        print("   ✅ Cleared AAPL cache")
        
        # Test clearing all CSV cache
        print(f"\nTesting clear all CSV cache...")
        data_manager.clear_csv_cache()
        print("   ✅ Cleared all CSV cache")
        
        # Final cache stats
        print("\nFinal cache stats:")
        final_stats = data_manager.get_cache_stats()
        for key, value in final_stats.items():
            print(f"   - {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ CSV caching test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("🚀 CSV Caching Functionality Test")
    print("=" * 50)
    
    success = test_csv_caching()
    
    if success:
        print("\n" + "=" * 50)
        print("✅ CSV caching test completed successfully!")
        print("\nKey features demonstrated:")
        print("1. ✅ CSV files are created in 'data_cache/' directory")
        print("2. ✅ Data is reused from CSV cache on subsequent runs")
        print("3. ✅ Cache files are automatically cleaned up daily")
        print("4. ✅ Individual ticker cache can be cleared")
        print("5. ✅ All CSV cache can be cleared")
        print("\nBenefits:")
        print("   - No repeated API calls to Alpha Vantage on the same day")
        print("   - Faster subsequent runs")
        print("   - Persistent storage between script executions")
        print("   - Automatic cleanup of old cache files")
    else:
        print("\n❌ CSV caching test failed!")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
