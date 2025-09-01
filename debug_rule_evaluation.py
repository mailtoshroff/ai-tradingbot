#!/usr/bin/env python3
"""
Debug script to test rule evaluation and find the Series boolean error
"""
import pandas as pd
import numpy as np
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from utils.technical_indicators import TechnicalIndicators
from utils.logger import TradingBotLogger

def debug_rule_evaluation():
    """Debug rule evaluation issue"""
    print("🔍 Debugging Rule Evaluation Issue")
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
    print()
    
    # Calculate indicators
    print("🧮 Calculating indicators...")
    indicators = ti.calculate_all_indicators(sample_data, "TEST", "D")
    print(f"📊 Indicators calculated: {len(indicators)}")
    print()
    
    # Test a simple rule evaluation
    print("🧪 Testing simple rule evaluation...")
    try:
        # Create a simple rule
        simple_rule = {
            'name': 'test_sma_cross_21',
            'type': 'buy',
            'priority': 1,
            'description': '21 SMA cross below',
            'period': 'D',
            'length': 21,
            'previous_days': 20
        }
        
        print("📋 Rule:", simple_rule['name'])
        
        # Evaluate the rule
        signal_triggered, confidence, reasoning = ti.evaluate_trading_rule(
            "TEST", simple_rule, indicators
        )
        
        print(f"✅ Rule evaluation successful:")
        print(f"  Signal: {signal_triggered}")
        print(f"  Confidence: {confidence}")
        print(f"  Reasoning: {reasoning}")
        
    except Exception as e:
        print(f"❌ Rule evaluation failed: {e}")
        print(f"❌ Error type: {type(e)}")
        import traceback
        traceback.print_exc()
    
    print()
    
    # Test accessing individual indicators
    print("🧪 Testing individual indicator access...")
    try:
        sma_200 = indicators.get('sma_200', pd.Series([0]))
        print(f"📊 sma_200 type: {type(sma_200)}")
        print(f"📊 sma_200 length: {len(sma_200) if hasattr(sma_200, '__len__') else 'N/A'}")
        
        if hasattr(sma_200, '__len__') and len(sma_200) > 0:
            print("✅ Length check passed")
            if hasattr(sma_200, 'iloc'):
                last_value = sma_200.iloc[-1]
                print(f"✅ Last value (iloc): {last_value}")
            else:
                last_value = sma_200[-1]
                print(f"✅ Last value (index): {last_value}")
        else:
            print("❌ Length check failed")
            
    except Exception as e:
        print(f"❌ Error accessing sma_200: {e}")
        print(f"❌ Error type: {type(e)}")

if __name__ == "__main__":
    debug_rule_evaluation()
