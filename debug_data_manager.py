#!/usr/bin/env python3
"""
Debug script to test the data manager directly
"""
import pandas as pd
import numpy as np
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from core.data_manager import DataManager

def debug_data_manager():
    """Debug data manager issue"""
    print("🔍 Debugging Data Manager Issue")
    print("=" * 50)
    
    # Initialize data manager
    data_manager = DataManager("config/config.yaml")
    
    print("📊 Data manager initialized")
    print()
    
    # Test with a specific ticker
    test_ticker = "QQQ"
    print(f"🧪 Testing with ticker: {test_ticker}")
    
    try:
        # Get indicators
        print("📈 Getting indicators...")
        indicators = data_manager.calculate_indicators_for_ticker(test_ticker)
        
        if indicators:
            print(f"✅ Indicators retrieved: {len(indicators)}")
            print(f"📊 Indicators keys: {list(indicators.keys())}")
            print()
            
            # Check SMA values specifically
            print("🔍 Checking SMA values...")
            for sma_key in ['sma_21', 'sma_50', 'sma_200']:
                if sma_key in indicators:
                    sma_value = indicators[sma_key]
                    print(f"📊 {sma_key}:")
                    print(f"  Type: {type(sma_value)}")
                    print(f"  Shape: {sma_value.shape if hasattr(sma_value, 'shape') else 'N/A'}")
                    print(f"  Length: {len(sma_value) if hasattr(sma_value, '__len__') else 'N/A'}")
                    
                    # Check if it's actually SMA data or price data
                    if hasattr(sma_value, 'iloc'):
                        first_value = sma_value.iloc[0]
                        last_value = sma_value.iloc[-1]
                        print(f"  First value: {first_value}")
                        print(f"  Last value: {last_value}")
                        
                        # Check if it looks like SMA (should be relatively stable)
                        if pd.isna(first_value) and not pd.isna(last_value):
                            print(f"  ✅ Looks like SMA (NaN at start, valid at end)")
                        else:
                            print(f"  ⚠️  Might not be SMA data")
                    print()
                else:
                    print(f"❌ {sma_key} not found in indicators")
                    print()
            
            # Check if data is the same as any SMA
            print("🔍 Checking for data duplication...")
            data = indicators.get('data')
            if data is not None:
                print(f"📊 Data shape: {data.shape}")
                print(f"📊 Data columns: {list(data.columns)}")
                
                # Check if any SMA is identical to data
                for sma_key in ['sma_21', 'sma_50', 'sma_200']:
                    if sma_key in indicators:
                        sma_value = indicators[sma_key]
                        if hasattr(sma_value, 'equals') and hasattr(data, 'equals'):
                            if sma_value.equals(data):
                                print(f"⚠️  {sma_key} is identical to data!")
                            elif sma_value.equals(data['close']):
                                print(f"⚠️  {sma_key} is identical to data['close']!")
                            else:
                                print(f"✅ {sma_key} is different from data")
                        else:
                            print(f"⚠️  Cannot compare {sma_key} with data")
                print()
            
        else:
            print("❌ No indicators retrieved")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"❌ Error type: {type(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_data_manager()
