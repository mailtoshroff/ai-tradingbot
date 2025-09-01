#!/usr/bin/env python3
"""
Debug script to check data structure from Alpha Vantage
"""
import sys
import os
import pandas as pd

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def debug_data_structure():
    """Debug the data structure from Alpha Vantage"""
    print("🔍 Debugging Data Structure from Alpha Vantage")
    print("=" * 60)
    
    try:
        from core.data_manager import DataManager
        from dotenv import load_dotenv
        
        # Load environment variables
        load_dotenv()
        
        # Initialize data manager
        data_manager = DataManager()
        print("✅ Data manager initialized")
        
        # Test fetching data for AAPL
        print("\n📊 Fetching AAPL data...")
        data = data_manager.fetch_market_data("AAPL", "D", "30d")
        
        if data is not None and not data.empty:
            print(f"✅ Data fetched successfully")
            print(f"   - Shape: {data.shape}")
            print(f"   - Columns: {list(data.columns)}")
            print(f"   - Data types: {data.dtypes.to_dict()}")
            print(f"   - First few rows:")
            print(data.head())
            
            # Check if 'close' column exists
            if 'close' in data.columns:
                print("\n✅ 'close' column found!")
                print(f"   - Close values: {data['close'].head().tolist()}")
            else:
                print("\n❌ 'close' column NOT found!")
                print("   - Available columns:", list(data.columns))
                
                # Try to find similar columns
                close_like = [col for col in data.columns if 'close' in col.lower() or 'price' in col.lower()]
                if close_like:
                    print(f"   - Close-like columns: {close_like}")
        else:
            print("❌ No data returned")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_data_structure()
