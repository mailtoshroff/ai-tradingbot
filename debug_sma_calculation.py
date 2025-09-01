#!/usr/bin/env python3
"""
Debug script to test SMA calculation
"""
import pandas as pd
import numpy as np
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from utils.technical_indicators import TechnicalIndicators
from utils.logger import TradingBotLogger

def debug_sma_calculation():
    """Debug SMA calculation issue"""
    print("🔍 Debugging SMA Calculation Issue")
    print("=" * 50)
    
    # Initialize logger
    logger = TradingBotLogger()
    logger_instance = logger.get_logger("debug")
    
    # Initialize technical indicators
    ti = TechnicalIndicators()
    ti.set_logger(logger_instance)
    
    # Create sample data
    dates = pd.date_range('2024-01-01', periods=365, freq='D')
    sample_data = pd.DataFrame({
        'open': np.random.uniform(100, 200, 365),
        'high': np.random.uniform(200, 300, 365),
        'low': np.random.uniform(50, 100, 365),
        'close': np.random.uniform(100, 200, 365),
        'volume': np.random.randint(1000000, 10000000, 365)
    }, index=dates)
    
    print(f"📊 Sample data shape: {sample_data.shape}")
    print(f"📊 Sample data columns: {list(sample_data.columns)}")
    print(f"📊 First few rows:")
    print(sample_data.head())
    print()
    
    # Test individual SMA calculation
    print("🧮 Testing individual SMA calculation...")
    sma_21 = ti.calculate_sma(sample_data, 21)
    print(f"📈 SMA 21 type: {type(sma_21)}")
    print(f"📈 SMA 21 shape: {sma_21.shape}")
    print(f"📈 SMA 21 first 5 values: {sma_21.head()}")
    print(f"📈 SMA 21 last 5 values: {sma_21.tail()}")
    print()
    
    # Test calculate_all_indicators
    print("🧮 Testing calculate_all_indicators...")
    indicators = ti.calculate_all_indicators(sample_data, "TEST", "D")
    print(f"📊 Indicators type: {type(indicators)}")
    print(f"📊 Indicators keys: {list(indicators.keys())}")
    print()
    
    # Check SMA values
    for sma_key in ['sma_21', 'sma_50', 'sma_200']:
        if sma_key in indicators:
            sma_value = indicators[sma_key]
            print(f"🔍 {sma_key}:")
            print(f"  Type: {type(sma_value)}")
            print(f"  Shape: {sma_value.shape if hasattr(sma_value, 'shape') else 'N/A'}")
            print(f"  Length: {len(sma_value) if hasattr(sma_value, '__len__') else 'N/A'}")
            if hasattr(sma_value, 'iloc'):
                print(f"  Last value: {sma_value.iloc[-1]}")
            elif hasattr(sma_value, '__len__') and len(sma_value) > 0:
                print(f"  Last value: {sma_value[-1]}")
            print()
    
    # Test the specific issue from the error
    print("🧪 Testing the specific error condition...")
    try:
        sma_200 = indicators.get('sma_200', pd.Series([0]))
        print(f"📊 sma_200 type: {type(sma_200)}")
        print(f"📊 sma_200 value: {sma_200}")
        
        if hasattr(sma_200, '__len__') and len(sma_200) > 0:
            print("✅ Length check passed")
            if hasattr(sma_200, 'iloc'):
                last_value = sma_200.iloc[-1]
                print(f"✅ Using iloc[-1]: {last_value}")
            else:
                last_value = sma_200[-1]
                print(f"✅ Using [-1]: {last_value}")
        else:
            print("❌ Length check failed")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"❌ Error type: {type(e)}")

if __name__ == "__main__":
    debug_sma_calculation()
