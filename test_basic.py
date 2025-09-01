#!/usr/bin/env python3
"""
Basic test script for AI Trading Bot - tests core functionality without market data
"""
import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_basic_imports():
    """Test basic imports"""
    print("Testing basic imports...")
    try:
        from utils.logger import trading_logger
        print("✅ Logger imported successfully")
        
        from utils.technical_indicators import TechnicalIndicators
        print("✅ Technical indicators imported successfully")
        
        from core.data_manager import DataManager
        print("✅ Data manager imported successfully")
        
        from agents.analysis_agent import AnalysisAgent
        print("✅ Analysis agent imported successfully")
        
        from agents.news_agent import NewsAgent
        print("✅ News agent imported successfully")
        
        from agents.master_agent import MasterAgent
        print("✅ Master agent imported successfully")
        
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_config_loading():
    """Test configuration loading"""
    print("\nTesting configuration loading...")
    try:
        import yaml
        with open('config/config.yaml', 'r') as file:
            config = yaml.safe_load(file)
        print("✅ Config loaded successfully")
        print(f"   - API sections: {list(config.get('api', {}).keys())}")
        print(f"   - Trading config: {list(config.get('trading', {}).keys())}")
        return True
    except Exception as e:
        print(f"❌ Config loading error: {e}")
        return False

def test_rules_loading():
    """Test trading rules loading"""
    print("\nTesting trading rules loading...")
    try:
        import json
        with open('rules.json', 'r') as file:
            rules = json.load(file)
        print("✅ Trading rules loaded successfully")
        print(f"   - Total rules: {len(rules.get('rules', []))}")
        
        # Show first few rules
        for i, rule in enumerate(rules.get('rules', [])[:3]):
            print(f"   - Rule {i+1}: {rule.get('name', 'Unknown')} (Priority: {rule.get('priority', 'N/A')})")
        
        return True
    except Exception as e:
        print(f"❌ Rules loading error: {e}")
        return False

def test_logger():
    """Test logger functionality"""
    print("\nTesting logger...")
    try:
        from utils.logger import trading_logger
        logger = trading_logger.get_logger("test")
        logger.info("Test log message")
        print("✅ Logger working successfully")
        return True
    except Exception as e:
        print(f"❌ Logger error: {e}")
        return False

async def test_agent_initialization():
    """Test agent initialization without market data"""
    print("\nTesting agent initialization...")
    try:
        from agents.master_agent import MasterAgent
        
        # Initialize master agent
        master_agent = MasterAgent()
        print("✅ Master agent initialized successfully")
        
        # Test basic methods
        summary = master_agent.get_decision_summary()
        print(f"✅ Decision summary: {summary}")
        
        return True
    except Exception as e:
        print(f"❌ Agent initialization error: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 AI Trading Bot - Basic Functionality Test")
    print("=" * 50)
    
    # Test basic imports
    if not test_basic_imports():
        print("❌ Basic imports failed")
        return False
    
    # Test configuration
    if not test_config_loading():
        print("❌ Configuration loading failed")
        return False
    
    # Test trading rules
    if not test_rules_loading():
        print("❌ Trading rules loading failed")
        return False
    
    # Test logger
    if not test_logger():
        print("❌ Logger test failed")
        return False
    
    # Test agent initialization
    try:
        result = asyncio.run(test_agent_initialization())
        if not result:
            print("❌ Agent initialization failed")
            return False
    except Exception as e:
        print(f"❌ Agent initialization error: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("✅ All basic tests passed! The bot is ready to run.")
    print("\nNext steps:")
    print("1. Create your .env file with API keys")
    print("2. Run: python src/main.py")
    print("3. The bot will analyze your tickers and generate trading decisions")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
