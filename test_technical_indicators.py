#!/usr/bin/env python3
"""
Test script for technical indicators after fixing the data structure issue
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_technical_indicators():
    """Test technical indicators calculation"""
    print("🔍 Testing Technical Indicators After Fix")
    print("=" * 60)
    
    try:
        from core.data_manager import DataManager
        from dotenv import load_dotenv
        
        # Load environment variables
        load_dotenv()
        
        # Initialize data manager
        data_manager = DataManager()
        print("✅ Data manager initialized")
        
        # Test calculating indicators for AAPL
        print("\n📊 Testing indicators calculation for AAPL...")
        indicators = data_manager.calculate_indicators_for_ticker("AAPL", "D", "30d")
        
        if indicators is not None:
            print("✅ Indicators calculated successfully!")
            print(f"   - Indicators count: {len(indicators)}")
            print(f"   - Available indicators: {list(indicators.keys())}")
            
            # Check specific indicators
            if 'sma_21' in indicators:
                sma_21 = indicators['sma_21']
                print(f"   - SMA 21: {sma_21.iloc[-1]:.2f}")
            
            if 'close' in indicators.get('data', {}).columns:
                print("   - ✅ 'close' column found in data")
            else:
                print("   - ❌ 'close' column missing from data")
                
        else:
            print("❌ Failed to calculate indicators")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_technical_indicators()
