#!/usr/bin/env python3
"""
Comprehensive debugging script for the AI Trading Bot
"""
import sys
import os
import time
import traceback
import asyncio

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_step_by_step():
    """Test each component step by step to identify the issue"""
    print("🔍 Step-by-Step Bot Debugging")
    print("=" * 50)
    
    step = 1
    
    # Step 1: Basic imports
    print(f"\n{step}. Testing basic imports...")
    try:
        import pandas as pd
        import numpy as np
        import yaml
        print("   ✅ Basic libraries imported successfully")
        step += 1
    except Exception as e:
        print(f"   ❌ Basic import error: {e}")
        return False
    
    # Step 2: Logger
    print(f"\n{step}. Testing logger...")
    try:
        from utils.logger import trading_logger
        logger = trading_logger.get_logger("debug")
        logger.info("Logger test successful")
        print("   ✅ Logger working")
        step += 1
    except Exception as e:
        print(f"   ❌ Logger error: {e}")
        traceback.print_exc()
        return False
    
    # Step 3: Configuration loading
    print(f"\n{step}. Testing configuration loading...")
    try:
        import yaml
        with open("config/config.yaml", 'r') as file:
            config = yaml.safe_load(file)
        print(f"   ✅ Config loaded: {len(config)} sections")
        step += 1
    except Exception as e:
        print(f"   ❌ Config loading error: {e}")
        traceback.print_exc()
        return False
    
    # Step 4: Trading rules loading
    print(f"\n{step}. Testing trading rules loading...")
    try:
        import json
        with open("rules.json", 'r') as file:
            rules = json.load(file)
        print(f"   ✅ Trading rules loaded: {len(rules.get('rules', []))} rules")
        step += 1
    except Exception as e:
        print(f"   ❌ Trading rules loading error: {e}")
        traceback.print_exc()
        return False
    
    # Step 5: Data Manager initialization
    print(f"\n{step}. Testing Data Manager initialization...")
    try:
        from core.data_manager import DataManager
        print("   ✅ Data Manager imported")
        
        start_time = time.time()
        data_manager = DataManager()
        init_time = time.time() - start_time
        
        print(f"   ✅ Data Manager initialized in {init_time:.2f}s")
        step += 1
    except Exception as e:
        print(f"   ❌ Data Manager error: {e}")
        traceback.print_exc()
        return False
    
    # Step 6: Test data fetching (with timeout)
    print(f"\n{step}. Testing data fetching (with 30s timeout)...")
    try:
        import threading
        
        # Windows-compatible timeout using threading
        data = None
        fetch_completed = threading.Event()
        fetch_error = None
        
        def fetch_data():
            nonlocal data, fetch_error
            try:
                data = data_manager.fetch_market_data("AAPL", "D", "30d")
                fetch_completed.set()
            except Exception as e:
                fetch_error = e
                fetch_completed.set()
        
        # Start data fetching in a separate thread
        fetch_thread = threading.Thread(target=fetch_data)
        fetch_thread.daemon = True
        fetch_thread.start()
        
        start_time = time.time()
        print("   🔄 Fetching AAPL data...")
        
        # Wait for completion or timeout
        if fetch_completed.wait(timeout=30):
            if fetch_error:
                raise fetch_error
            
            fetch_time = time.time() - start_time
            
            if data is not None and not data.empty:
                print(f"   ✅ Data fetched successfully in {fetch_time:.2f}s")
                print(f"      - Data points: {len(data)}")
                print(f"      - Columns: {list(data.columns)}")
                print(f"      - Latest close: ${data['close'].iloc[-1]:.2f}")
            else:
                print("   ⚠️ Data fetched but empty or None")
        else:
            print("   ❌ Data fetching timed out after 30 seconds - this is where the bot gets stuck!")
            return False
        
        step += 1
        
    except Exception as e:
        print(f"   ❌ Data fetching error: {e}")
        traceback.print_exc()
        return False
    
    # Step 7: Test cache functionality
    print(f"\n{step}. Testing cache functionality...")
    try:
        cache_stats = data_manager.get_cache_stats()
        print(f"   ✅ Cache stats: {cache_stats}")
        
        # Check if CSV files were created
        if os.path.exists("data_cache"):
            csv_files = [f for f in os.listdir("data_cache") if f.endswith('.csv')]
            print(f"   📁 CSV cache files: {csv_files}")
        else:
            print("   📁 No data_cache directory found")
        
        step += 1
    except Exception as e:
        print(f"   ❌ Cache test error: {e}")
        traceback.print_exc()
        return False
    
    # Step 8: Test technical indicators
    print(f"\n{step}. Testing technical indicators...")
    try:
        from utils.technical_indicators import TechnicalIndicators
        
        tech_indicators = TechnicalIndicators()
        tech_indicators.set_logger(logger)
        
        print("   ✅ Technical indicators initialized")
        
        # Test a simple calculation
        if data is not None and not data.empty:
            sma = tech_indicators.calculate_sma(data, 20)
            if sma is not None and not sma.empty:
                print(f"   ✅ SMA calculation successful: {sma.iloc[-1]:.2f}")
            else:
                print("   ⚠️ SMA calculation returned empty result")
        
        step += 1
    except Exception as e:
        print(f"   ❌ Technical indicators error: {e}")
        traceback.print_exc()
        return False
    
    # Step 9: Test agents (without full execution)
    print(f"\n{step}. Testing agent imports...")
    try:
        from agents.analysis_agent import AnalysisAgent
        from agents.news_agent import NewsAgent
        from agents.master_agent import MasterAgent
        
        print("   ✅ All agents imported successfully")
        step += 1
    except Exception as e:
        print(f"   ❌ Agent import error: {e}")
        traceback.print_exc()
        return False
    
    print(f"\n{step}. Testing main execution...")
    try:
        # Test main.py import without execution
        import importlib.util
        
        spec = importlib.util.spec_from_file_location("main", "src/main.py")
        main_module = importlib.util.module_from_spec(spec)
        
        print("   ✅ Main module can be imported")
        step += 1
    except Exception as e:
        print(f"   ❌ Main module import error: {e}")
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 50)
    print("✅ All components tested successfully!")
    print("\nThe bot should work now. If it still gets stuck,")
    print("the issue might be in the main execution loop.")
    
    return True

def test_main_execution():
    """Test the main execution with timeout"""
    print("\n🚀 Testing main execution (with timeout)...")
    print("=" * 50)
    
    try:
        import threading
        
        # Windows-compatible timeout using threading
        execution_completed = threading.Event()
        execution_error = None
        execution_result = None
        
        def run_main():
            nonlocal execution_error, execution_result
            try:
                # Import and run main
                from main import main
                execution_result = main()
                execution_completed.set()
            except Exception as e:
                execution_error = e
                execution_completed.set()
        
        # Start main execution in a separate thread
        main_thread = threading.Thread(target=run_main)
        main_thread.daemon = True
        main_thread.start()
        
        print("Starting main execution...")
        start_time = time.time()
        
        # Wait for completion or timeout
        if execution_completed.wait(timeout=60):
            if execution_error:
                raise execution_error
            
            exec_time = time.time() - start_time
            print(f"✅ Main execution completed in {exec_time:.2f}s")
            return True
        else:
            print("❌ Main execution timed out after 60 seconds - this confirms the bot gets stuck!")
            print("The issue is likely in the main execution loop or agent coordination.")
            return False
        
    except Exception as e:
        print(f"❌ Main execution error: {e}")
        traceback.print_exc()
        return False

def main():
    """Main debugging function"""
    print("🚀 AI Trading Bot Comprehensive Debug")
    print("=" * 50)
    
    # Step-by-step testing
    if not test_step_by_step():
        print("\n❌ Step-by-step testing failed!")
        print("Fix the issues above before proceeding.")
        return False
    
    # Test main execution
    print("\n" + "=" * 50)
    print("Testing main execution...")
    
    if test_main_execution():
        print("\n🎉 Bot is working correctly!")
        return True
    else:
        print("\n🔧 Bot has execution issues that need fixing.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
