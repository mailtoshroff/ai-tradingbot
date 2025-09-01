#!/usr/bin/env python3
"""
Debug script to test technical indicators directly
"""
import pandas as pd
import numpy as np
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from utils.technical_indicators import TechnicalIndicators
from utils.logger import TradingBotLogger

def debug_technical_indicators():
    """Debug technical indicators issue"""
    print("🔍 Debugging Technical Indicators Issue")
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
    print()
    
    # Test individual SMA calculation
    print("🧮 Testing individual SMA calculation...")
    sma_21 = ti.calculate_sma(sample_data, 21)
    sma_50 = ti.calculate_sma(sample_data, 50)
    sma_200 = ti.calculate_sma(sample_data, 200)
    
    print(f"📈 SMA 21 type: {type(sma_21)}")
    print(f"📈 SMA 21 shape: {sma_21.shape}")
    print(f"📈 SMA 21 first 5 values: {sma_21.head()}")
    print(f"📈 SMA 21 last 5 values: {sma_21.tail()}")
    print()
    
    print(f"📈 SMA 50 type: {type(sma_50)}")
    print(f"📈 SMA 50 shape: {sma_50.shape}")
    print(f"📈 SMA 50 first 5 values: {sma_50.head()}")
    print(f"📈 SMA 50 last 5 values: {sma_50.tail()}")
    print()
    
    print(f"📈 SMA 200 type: {type(sma_200)}")
    print(f"📈 SMA 200 shape: {sma_200.shape}")
    print(f"📈 SMA 200 first 5 values: {sma_200.head()}")
    print(f"📈 SMA 200 last 5 values: {sma_200.tail()}")
    print()
    
    # Test calculate_all_indicators
    print("🧮 Testing calculate_all_indicators...")
    indicators = ti.calculate_all_indicators(sample_data, "TEST", "D")
    print(f"📊 Indicators calculated: {len(indicators)}")
    print(f"📊 Indicators keys: {list(indicators.keys())}")
    print()
    
    # Check if the individual SMAs match the ones in indicators
    print("🔍 Checking SMA consistency...")
    print(f"📊 Individual SMA 21 equals indicators['sma_21']: {sma_21.equals(indicators['sma_21'])}")
    print(f"📊 Individual SMA 50 equals indicators['sma_50']: {sma_50.equals(indicators['sma_50'])}")
    print(f"📊 Individual SMA 200 equals indicators['sma_200']: {sma_200.equals(indicators['sma_200'])}")
    print()
    
    # Check if any SMA is accidentally the same as the data
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
    debug_technical_indicators()
